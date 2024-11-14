#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#
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


from fcntl import ioctl
from io import StringIO, TextIOBase
from os import ctermid, open as os_open, close as os_close, O_RDONLY
from re import compile as re_compile
from select import select
from signal import signal, SIGWINCH
from struct import pack, unpack
from sys import stdin, stdout
from termios import tcgetattr, tcsetattr, TCSAFLUSH, TIOCGWINSZ
from time import monotonic
from tty import setraw, setcbreak

from ._codes import CSI, APC
from ._measurement import CursorPosition, RectangularArea


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


class Terminal:

    def __init__(self, cin=stdin, cout=stdout):
        self._input = TerminalInput(cin)
        self._output = TerminalOutput(cout)
        self._event_listeners = {}
        signal(SIGWINCH, lambda _signal, _frame: self._dispatch_event("resize", self.get_size()))

    def add_event_listener(self, event_type, listener):
        self._event_listeners.setdefault(event_type, []).append(listener)

    def remove_event_listener(self, event_type, listener):
        try:
            listeners = self._event_listeners[event_type]
        except KeyError:
            pass  # no such event type
        else:
            try:
                listeners.remove(listener)
            except ValueError:
                pass  # no such listener

    def _dispatch_event(self, event_type, data):
        for listener in self._event_listeners.get(event_type, []):
            if callable(listener):
                listener(data)

    def loop(self, /, until=None, timeout=None):
        t0 = monotonic()
        remaining = timeout
        while timeout is None or remaining >= 0:
            if timeout is None:
                char_seq = self._input.read(1)
            else:
                elapsed = monotonic() - t0
                remaining = timeout - elapsed
                if self._input.wait(timeout=max(0, remaining)):
                    char_seq = self._input.read(1)
                else:
                    break
            if until:
                match = until.match(char_seq)
                if match:
                    # print(f"Found match after {monotonic() - t0}s")
                    return match
            # TODO: handle mouse events separately, if possible
            if char_seq.startswith(APC):
                event_type = "__apc__"
            else:
                event_type = "keypress"
            self._dispatch_event(event_type, char_seq)
        return None

    def get_info(self):
        info = {}
        from ._kitty import get_kitty_info
        info.update(get_kitty_info(self))
        return info

    def get_size(self) -> RectangularArea:
        try:
            buffer = pack('HHHH', 0, 0, 0, 0)
            fd = os_open(ctermid(), O_RDONLY)
            result = ioctl(fd, TIOCGWINSZ, buffer)
            os_close(fd)
        except OSError:
            lines, columns, pixel_width, pixel_height = 0, 0, 0, 0
        else:
            lines, columns, pixel_width, pixel_height = unpack('HHHH', result)
        if lines == 0 and columns == 0:
            self._output.write(f"{CSI}18t")
            self._output.flush()
            match = self.loop(until=re_compile(r"\x1B\[8;(\d*);(\d*)t"), timeout=0.025)
            if match:
                lines = int(match.group(1))
                columns = int(match.group(2))
            else:
                lines = 24
                columns = 80
        if pixel_width == 0 and pixel_height == 0:
            self._output.write(f"{CSI}14t")
            self._output.flush()
            match = self.loop(until=re_compile(r"\x1B\[4;(\d*);(\d*)t"), timeout=0.025)
            if match:
                pixel_height = int(match.group(1))
                pixel_width = int(match.group(2))
            else:
                pixel_height = 16 * lines
                pixel_width = 8 * columns
        return RectangularArea(lines, columns, pixel_width, pixel_height)

    def get_cursor_position(self) -> CursorPosition:
        self._output.write(f"{CSI}6n")
        self._output.flush()
        match = self.loop(until=re_compile(r"\x1B\[(\d*);(\d*)R"), timeout=0.025)
        if match:
            return CursorPosition(line=int(match.group(1)), column=int(match.group(2)))
        else:
            raise OSError("Cursor position unavailable")

    def set_cursor_position(self, /, line, column):
        self._output.write(f"{CSI}{line};{column}H")

    def clear(self):
        self._output.write(f"{CSI}H{CSI}2J")

    def show_alternate_screen(self):
        self._output.write(f"{CSI}?1049h")
        self._output.flush()
        self._output.set_tty_mode("cbreak")

    def hide_alternate_screen(self):
        self._output.reset_tty_mode()
        self._output.write(f"{CSI}?1049l")
        self._output.flush()

    def show_cursor(self):
        self._output.write(f"{CSI}?25h")
        self._output.flush()

    def hide_cursor(self):
        self._output.write(f"{CSI}?25l")
        self._output.flush()

    # def keypad_on(self):
    #     self._cout.write(f"{CSI}?1h{ESC}=")
    #     self._cout.flush()

    # def keypad_off(self):
    #     self._cout.write(f"{CSI}?1l{ESC}>")
    #     self._cout.flush()

    def write(self, s, /, **style):
        self._output.write(s, **style)

    def flush(self):
        self._output.flush()

    def print(self, *objects, sep=' ', end='\n', flush=False, **style):
        """ Print one or more objects to the terminal output.

        This method is largely compatible with the builtin ``print`` function,
        missing only the `file` argument and supporting a number of additional
        keyword arguments.

        As with :py:func:`print`, all non-keyword arguments are converted to
        strings using :py:func:`str`, but also with styling applied if any
        `style` keywords are supplied.

        The full list of supported style keywords are documented as part of the
        :meth:`TerminalOutput.write` method, but include the following:

        - ``color``
        - ``background_color``
        - ``font_weight``
        - ``font_style``
        - ``text_decoration``

        :param objects:
        :param sep:
        :param end:
        :param flush:
        :param style:
        """
        for i, obj in enumerate(objects):
            if i > 0:
                self._output.write(sep)
            self._output.write(str(obj), **style)
        self._output.write(end)
        if flush:
            self._output.flush()

    def draw(self, image, /, method="auto"):
        raise NotImplementedError
