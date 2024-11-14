#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

# Copyright 2020, Nigel Small
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from io import StringIO, TextIOBase
from select import select
from sys import stdin, stdout
from termios import tcgetattr, tcsetattr, TCSAFLUSH
from tty import setraw, setcbreak
from unicodedata import category, east_asian_width

from ._codes import *
from ._sgr import *


__version__ = "2024.11.0"


class TerminalInput(TextIOBase):

    def __init__(self, stream=stdin):
        super().__init__()
        stream = stream or stdin
        if not hasattr(stream, "read") or not callable(stream.read):
            raise ValueError(f"Stream {stream!r} has no read method")
        if not hasattr(stream, "readable") or not callable(stream.readable) or not stream.readable():
            raise ValueError(f"Stream {stream!r} is not readable")
        self._stream = stream
        self._buffer = []  # list of chars
        self._closed = False

    def __iter__(self):
        return self

    def __next__(self):
        """ Read and return the next character unit.
        """
        ch = self._read_char()
        if not ch:
            raise StopIteration
        elif ch == CR:
            seq = [ch]
            if self._peek_char() == LF:
                ch = self._read_char()
                seq.append(ch)
            return "".join(seq)
        elif ch == ESC:
            # Escape sequence
            ch = self._read_char()
            seq = [ESC, ch]
            if ch == '[' or ch == 'O':
                # CSI ('{ESC}[') or SS3 ('{ESC}O')
                while True:
                    ch = self._read_char()
                    seq.append(ch)
                    if '@' <= ch <= '~':
                        break
            elif ch in {'P', 'X', ']', '^', '_'}:
                # Sequences terminated by ST
                # APC = f"{ESC}_"   # ECMA-48 § 8.3.2
                # DCS = f"{ESC}P"   # ECMA-48 § 8.3.27
                # OSC = f"{ESC}]"   # ECMA-48 § 8.3.89
                # PM  = f"{ESC}^"   # ECMA-48 § 8.3.94
                # SOS = f"{ESC}X"   # ECMA-48 § 8.3.128
                while True:
                    ch = self._read_char()
                    seq.append(ch)
                    if seq[-2:] == [ESC, '\\']:
                        break
            elif '@' <= ch <= '_':
                pass  # TODO: other type Fe
            elif '`' <= ch <= '~':
                pass  # TODO: type Fs
            elif '0' <= ch <= '?':
                pass  # TODO: type Fp
            elif ' ' <= ch <= '/':
                pass  # TODO: type nF
                while True:
                    ch = self._read_char()
                    seq.append(ch)
                    if '0' <= ch <= '~':
                        break
            return "".join(seq)
        else:
            return ch

    def __del__(self):
        super().__del__()

    def _check_closed(self):
        if self._closed:
            raise ValueError("Terminal input is closed")

    def _check_readable(self):
        if not self.readable():
            raise OSError("Terminal input is not readable")

    def _check_waitable(self):
        if not self.readable():
            raise OSError("Terminal input is not waitable")

    def _peek_char(self):
        if self._buffer:
            return self._buffer[0]
        ch = self._stream.read(1)
        if ch:
            self._buffer.append(ch)
        return ch

    def _read_char(self):
        if self._buffer:
            return self._buffer.pop(0)
        else:
            return self._stream.read(1)

    def close(self):
        self._closed = True

    @property
    def closed(self):
        return self._closed

    def fileno(self):
        self._check_closed()
        return self._stream.fileno()

    def isatty(self):
        self._check_closed()
        try:
            return self._stream.isatty()
        except (AttributeError, TypeError):
            return False

    def _read_units(self, size=-1, break_on_newline=False) -> [str]:
        self._check_closed()
        self._check_readable()
        buffer = []
        count = 0
        while size is None or size < 0 or count < size:
            count += 1
            try:
                char_unit = next(self)
            except StopIteration:
                break
            else:
                buffer.append(char_unit)
                if char_unit in UNICODE_NEWLINES and break_on_newline:
                    break
        return buffer

    def read(self, size=-1) -> str:
        """ Read and return at most size character units from the stream as a
        single string. If size is negative or None, reads until EOF.

        :param size: number of character units to read
        :returns: string containing the full sequence of characters read
        """
        if size is None or size < 0:
            self._check_closed()
            self._check_readable()
            buffer = "".join(self._buffer)
            self._buffer.clear()
            return buffer + self._stream.read()
        else:
            return "".join(self._read_units(size=size))

    def readable(self):
        return self._stream.readable()

    def readline(self, size=-1, /):
        return "".join(self._read_units(size=size, break_on_newline=True))

    def wait(self, timeout=None) -> bool:
        """ Wait until data is available for reading, or timeout.
        """
        self._check_closed()
        self._check_waitable()
        ready, _, _ = select([self._stream], [], [], timeout)
        return bool(ready)

    def waitable(self) -> bool:
        return hasattr(self._stream, "fileno") and callable(self._stream.fileno)


class TerminalOutput(TextIOBase):

    def __init__(self, stream=stdout):
        stream = stream or stdout
        if not hasattr(stream, "write") or not callable(stream.write):
            raise ValueError(f"Stream {stream!r} has no write method")
        if not hasattr(stream, "writable") or not callable(stream.writable) or not stream.writable():
            raise ValueError(f"Stream {stream!r} is not writable")
        self._stream = stream
        self._original_mode = tcgetattr(self._stream)
        self._closed = False

    def __del__(self):
        super().__del__()

    def _check_closed(self):
        if self._closed:
            raise ValueError("Terminal output is closed")

    def _check_writable(self):
        if not self.writable():
            raise OSError("Terminal output is not writable")

    def set_tty_mode(self, value):
        if value == "raw":
            setraw(self._stream, TCSAFLUSH)
        elif value == "cbreak":
            setcbreak(self._stream, TCSAFLUSH)
        else:
            raise ValueError(f"Unsupported tty mode {value!r}")

    def reset_tty_mode(self):
        tcsetattr(self._stream, TCSAFLUSH, self._original_mode)

    def flush(self):
        self._stream.flush()

    def write(self, s, /,
              color=None,
              background_color=None,
              font_weight=None,
              font_style=None,
              text_decoration=None,
              vertical_align=None):
        from . import _text
        if vertical_align == "sub":
            text = str(s).translate(_text.TO_SUBSCRIPT)
        elif vertical_align == "super":
            text = str(s).translate(_text.TO_SUPERSCRIPT)
        else:
            text = str(s)
        seq = [
            _text.color(color),
            _text.background_color(background_color),
            _text.font_weight(font_weight),
            _text.font_style(font_style),
            _text.text_decoration(text_decoration),
        ]
        prefix = ''.join(map(str, seq))
        if prefix:
            # If the text contains newlines (e.g. <pre>) then we should add
            # the style codes to each line. Without this, styled output
            # displayed in applications like `less` applies the style to
            # the first line only.
            units = []
            for line in text.splitlines(keepends=True):
                # Break the line into char sequences
                line_units = list(TerminalInput(StringIO(line)))
                # Separate out trailing newlines
                newlines = []
                while line_units and line_units[-1] in UNICODE_NEWLINES:
                    newlines.insert(0, line_units.pop(-1))
                # Store the prefix
                units.append(prefix)
                # Store the line content (without newlines)
                units.extend(line_units)
                # Store a reset if one does not already exist
                if line_units[-1] not in {f"{CSI}0m", f"{CSI}m"}:
                    units.append(reset)
                # Store the newlines
                units.extend(newlines)
            self._stream.write("".join(map(str, units)))
        else:
            self._stream.write(text)

    def writable(self) -> bool:
        return self._stream.writable()

    def writelines(self, lines, /,
                   color=None,
                   background_color=None,
                   font_weight=None,
                   font_style=None,
                   text_decoration=None,
                   vertical_align=None):
        for line in lines:
            self.write(line, color, background_color, font_weight,
                       font_style, text_decoration, vertical_align)


def measure_text(text, tab_size: int = 8) -> [int]:
    r""" Measure the total forward advance of one or more lines of text,
    returning an array of measurements, one per line.

    Notes:
    - Regular characters occupy one cell
    - Non-printable characters and escape sequences occupy zero cells
    - Full width characters occupy two cells

    >>> measure_text("hello, world")
    [12]
    >>> measure_text(f"hello, {green}world{reset}")
    [12]
    >>> measure_text("hello, ｗｏｒｌｄ")
    [17]
    >>> measure_text(f"hello, {green}ｗｏｒｌｄ{reset}")
    [17]
    >>> measure_text("hello\nworld")
    [5, 5]
    """
    tin = TerminalInput(StringIO(text))
    measurements = []
    cursor = 0
    while True:
        char_unit = tin.read(1)
        if not char_unit:
            break
        # Measurement can generally be taken by looking at only the
        # first character in a sequence. But C1 control codes might
        # be represented in expanded ESC+X form, so we should
        # normalise those.
        first_char = char_unit[0]
        if first_char == ESC and len(char_unit) > 1:
            second_char = char_unit[1]
            if "@" <= second_char <= "_":
                # collapse 7-bit C1 control codes to 8-bit equivalents
                first_char = chr(0x40 + ord(second_char))
        # Now, check specific edge cases and fall back to checking the
        # Unicode general category.
        if first_char in UNICODE_NEWLINES:
            # This detects:
            # - CR, LF, CRLF (CRLF will be tested as CR, but whatever)
            # - NEL (both 7-bit and 8-bit representations)
            # - VT, FF
            # - LS, PS
            measurements.append(cursor)
            cursor = 0
        elif first_char == BS:
            if cursor > 0:
                cursor -= 1
            # width = -1
        elif first_char == HT:
            # Advance to next multiple of tab_size. This formula should
            # only ever return values between 1 and tab_size inclusive.
            advance = tab_size - (cursor % tab_size)
            cursor += advance
        elif first_char < " ":
            # Other control characters do not affect the cursor:
            # - NUL, BEL, CAN, EM, SUB, ESC
            # - TC (SOH, STX, ETX, EOT, ENQ, ACK, DLE, NAK, SYN, ETB)
            # - LS (SI, SO)
            # - DC (DC1, DC2, DC3, DC4)
            # - IS (FS, GS, RS, US)
            pass  # no advance
        elif first_char <= "~":
            # Anything else in ASCII range is printable and one cell wide.
            cursor += 1
        elif DEL <= first_char <= APC:
            # TODO: this isn't true for all of these
            pass  # no advance
        else:
            # For everything else, check the Unicode general category.
            major, minor = category(first_char)
            is_printable = major in {'L', 'N', 'P', 'S'} or (major, minor) == ('Z', 's')
            if is_printable:
                cursor += (2 if east_asian_width(first_char) in {'F', 'W'} else 1)
            else:
                pass  # not printable, so no visible size
    measurements.append(cursor)
    return measurements
