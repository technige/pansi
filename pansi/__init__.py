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
from sys import stdin
from unicodedata import category, east_asian_width


__version__ = "2024.11.0"


# ------------- # -- # -- # ------------------------- # ---- # --------------------------------------------------------
# C0 control codes
# ------------- # -- # -- # ------------------------- # ---- # --------------------------------------------------------
NUL = "\x00"    # ^@ |    | null                      |      | does nothing
SOH = "\x01"    # ^A |    | start of header           | TC₁  | start of transmission header
STX = "\x02"    # ^B |    | start of text             | TC₂  | start of transmission content
ETX = "\x03"    # ^C |    | end of text               | TC₃  | SIGINT, end of transmission content
EOT = "\x04"    # ^D |    | end of transmission       | TC₄  | EOF, end of transmission
ENQ = "\x05"    # ^E |    | enquiry                   | TC₅  |
ACK = "\x06"    # ^F |    | acknowledge               | TC₆  |
BEL = "\x07"    # ^G | \a | bell                      |      | audio signal
BS = "\x08"     # ^H | \b | backspace                 | FE₀  | move cursor left 1 cell
HT = "\x09"     # ^I | \t | horizontal tab            | FE₁  | move cursor right to next multiple of 8
LF = "\x0A"     # ^J | \n | line feed                 | FE₂  | newline
VT = "\x0B"     # ^K | \v | vertical tab              | FE₃  |
FF = "\x0C"     # ^L | \f | form feed                 | FE₄  | clear
CR = "\x0D"     # ^M | \r | carriage return           | FE₅  | newline
SO = "\x0E"     # ^N |    | shift out                 | LS₀  |
SI = "\x0F"     # ^O |    | shift in                  | LS₁  |
DLE = "\x10"    # ^P |    | data link escape          | TC₇  |
DC1 = "\x11"    # ^Q |    | device control 1          | DC₁  | XON, resume transmission (e.g. buffer ready)
DC2 = "\x12"    # ^R |    | device control 2          | DC₂  |
DC3 = "\x13"    # ^S |    | device control 3          | DC₃  | XOFF, pause transmission (e.g. buffer full)
DC4 = "\x14"    # ^T |    | device control 4          | DC₄  |
NAK = "\x15"    # ^U |    | negative acknowledge      | TC₈  |
SYN = "\x16"    # ^V |    | synchronous idle          | TC₉  |
ETB = "\x17"    # ^W |    | end of transmission block | TC₁₀ | end of transmission block
CAN = "\x18"    # ^X |    | cancel                    |      |
EM = "\x19"     # ^Y |    | end of medium             |      |
SUB = "\x1A"    # ^Z |    | substitute                |      | SIGTSTP
ESC = "\x1B"    # ^[ |    | escape                    |      | escape sequence initiator
FS = "\x1C"     # ^\ |    | file separator            | IS₄  | delimiter, SIGQUIT
GS = "\x1D"     # ^] |    | group separator           | IS₃  | delimiter
RS = "\x1E"     # ^^ |    | record separator          | IS₂  | delimiter
US = "\x1F"     # ^_ |    | unit separator            | IS₁  | delimiter
# ------------- # -- # -- # ------------------------- # ---- # --------------------------------------------------------
# SPACE and DELETE
# ------------- # -- # -- # ------------------------- # ---- # --------------------------------------------------------
SP = "\x20"               # space
DEL = "\x7F"              # delete                    |      |
# ------------- # -- # -- # ------------------------- # ---- # --------------------------------------------------------
# C1 control codes
# ------------------ # -- # --------------------------- # ---- # ------------------------------------------------------
PAD = f"{ESC}@"      # 80 | padding character
HOP = f"{ESC}A"      # 81 | high octet preset
BPH = f"{ESC}B"      # 82 | break permitted here
NBH = f"{ESC}C"      # 83 | no break here
IND = f"{ESC}D"      # 84 | index
NEL = f"{ESC}E"      # 85 | next line
SSA = f"{ESC}F"      # 86 | start of selected area
ESA = f"{ESC}G"      # 87 | end of selected area
HTS = f"{ESC}H"      # 88 | horizontal tabulation set
HTJ = f"{ESC}I"      # 89 | horizontal tabulation with justification
VTS = f"{ESC}J"      # 8A | vertical tabulation set
PLD = f"{ESC}K"      # 8B | partial line down
PLU = f"{ESC}L"      # 8C | partial line up
RI = f"{ESC}M"       # 8D | reverse index
SS2 = f"{ESC}N"      # 8E | single-shift 2              |      | en.wikipedia.org/wiki/ISO/IEC_2022#Shift_functions
SS3 = f"{ESC}O"      # 8F | single-shift 3
DCS = f"{ESC}P"      # 90 | device control string
PU1 = f"{ESC}Q"      # 91 | private use 1
PU2 = f"{ESC}R"      # 92 | private use 2
STS = f"{ESC}S"      # 93 | Set transmit state
CCH = f"{ESC}T"      # 94 | cancel character
MW = f"{ESC}U"       # 95 | message waiting
SPA = f"{ESC}V"      # 96 | start of protected area
EPA = f"{ESC}W"      # 97 | end of protected area
SOS = f"{ESC}X"      # 98 | start of string
SGC = f"{ESC}Y"      # 99 | single graphic character introducer
SCI = f"{ESC}Z"      # 9A | single character introducer
CSI = f"{ESC}["      # 9B | control sequence introducer
ST = f"{ESC}\\"      # 9C | string terminator
OSC = f"{ESC}]"      # 9D | operating system command
PM = f"{ESC}^"       # 9E | privacy message
APC = f"{ESC}_"      # 9F | application program command
# ------------------ # -- # --------------------------- # ---- # ------------------------------------------------------

# https://www.unicode.org/Public/UCD/latest/ucd/NameAliases.txt

# Translation table for C1 Control characters to equivalent 7-bit escape sequence.
#
# An 8-bit coded character in column 08 or 09 is equivalent to a 7-bit
# coded ESCAPE sequence consisting of ESC followed by the character from
# the corresponding row of columns 4 and 5 respectively.
#
# https://www.ecma-international.org/wp-content/uploads/ECMA-35_1st_edition_december_1971.pdf [8.2.2]
#
C1_CONTROL_TO_ESC_SEQUENCE = str.maketrans(dict(zip(map(chr, range(0x80, 0xA0)),
                                                    (f"{ESC}{chr(x)}" for x in range(0x40, 0x60)))))


class SGR:
    """ Hold the parameters of an SGR control sequence, along with an
    optional reset code.
    """

    def __init__(self, *parameters, reset=None):
        self.parameters = parameters
        if not reset:
            self.reset = ()
        elif isinstance(reset, tuple):
            self.reset = reset
        else:
            self.reset = (reset,)

    def __repr__(self):
        args = list(map(repr, self.parameters))
        if self.reset:
            if len(self.reset) == 1:
                args.append(f"reset={self.reset[0]!r}")
            else:
                args.append(f"reset={self.reset!r}")
        return f"{type(self).__name__}({', '.join(args)})"

    def __str__(self):
        return f"{CSI}{';'.join(map(str, self.parameters))}m"

    def __invert__(self):
        if self.reset:
            return self.__class__(*self.reset, reset=self.parameters)
        else:
            return self


#: The *reset* SGR sequence removes all current styling effects and returns the
#: text to its default appearance. Given that the ability to nest sequences is
#: less flexible and less visible than the equivalent in (for example) HTML,
#: this sequence is useful in many applications to undo a stack of effects.
#:
#: Note that *reset* also has an equivalent implicit form, ``f"{CSI}m``, which
#: includes no parameters, but operates identically. The explicit form is
#: preferred here for clarity and compatibility.
reset = SGR(0)

# Font weight and style
bold = SGR(1, reset=22)
light = SGR(2, reset=22)
italic = SGR(3, reset=23)
underline = SGR(4, reset=24)
blink = SGR(5, reset=25)
invert = SGR(7, reset=27)
line_through = SGR(9, reset=29)
double_underline = SGR(21, reset=24)

# Foreground SGRs for original 16 CGA/web colours
black = SGR(30, reset=39)
maroon = SGR(31, reset=39)
green = SGR(32, reset=39)
olive = SGR(33, reset=39)
navy = SGR(34, reset=39)
purple = SGR(35, reset=39)
teal = SGR(36, reset=39)
silver = SGR(37, reset=39)
default_fg = SGR(39)
gray = grey = SGR(90, reset=39)
red = SGR(91, reset=39)
lime = SGR(92, reset=39)
yellow = SGR(93, reset=39)
blue = SGR(94, reset=39)
fuchsia = magenta = SGR(95, reset=39)
aqua = cyan = SGR(96, reset=39)
white = SGR(97, reset=39)

# Background SGRs for original 16 CGA/web colours
black_bg = SGR(40, reset=49)
maroon_bg = SGR(41, reset=49)
green_bg = SGR(42, reset=49)
olive_bg = SGR(43, reset=49)
navy_bg = SGR(44, reset=49)
purple_bg = SGR(45, reset=49)
teal_bg = SGR(46, reset=49)
silver_bg = SGR(47, reset=49)
default_bg = SGR(49)

overline = SGR(53, reset=55)

gray_bg = grey_bg = SGR(100, reset=49)
red_bg = SGR(101, reset=49)
lime_bg = SGR(102, reset=49)
yellow_bg = SGR(103, reset=49)
blue_bg = SGR(104, reset=49)
fuchsia_bg = magenta_bg = SGR(105, reset=49)
aqua_bg = cyan_bg = SGR(106, reset=49)
white_bg = SGR(107, reset=49)


# Newlines
#
# https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-5/#G10213
CRLF = f"{CR}{LF}"
C1_NEL = "\x85"
LS = "\u2028"
PS = "\u2029"
UNICODE_NEWLINES = {CR, LF, CRLF, NEL, C1_NEL, VT, FF, LS, PS}


class TerminalInput(TextIOBase):

    def __init__(self, channel=stdin):
        super().__init__()
        channel = channel or stdin
        if not hasattr(channel, "read") or not callable(channel.read):
            raise ValueError(f"Channel {channel!r} has no read method")
        if not hasattr(channel, "readable") or not callable(channel.readable) or not channel.readable():
            raise ValueError(f"Channel {channel!r} is not readable")
        self._channel = channel
        self._buffer = []  # list of chars
        self._closed = False

    def __del__(self):
        super().__del__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError

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
        ch = self._channel.read(1)
        if ch:
            self._buffer.append(ch)
        return ch

    def _read_char(self):
        if self._buffer:
            return self._buffer.pop(0)
        else:
            return self._channel.read(1)

    def close(self):
        self._closed = True

    @property
    def closed(self):
        return self._closed

    def fileno(self):
        self._check_closed()
        return self._channel.fileno()

    def isatty(self):
        self._check_closed()
        try:
            return self._channel.isatty()
        except (AttributeError, TypeError):
            return False

    def _read(self, size=-1, break_on_newline=False):
        self._check_closed()
        self._check_readable()
        buffer = []
        count = 0
        while size is None or size < 0 or count < size:
            count += 1
            ch = self._read_char()
            if not ch:
                break
            elif ch == CR:
                buffer.append(ch)
                if self._peek_char() == LF:
                    ch = self._read_char()
                    buffer.append(ch)
                if break_on_newline:
                    break
            elif ch in UNICODE_NEWLINES:
                buffer.append(ch)
                if break_on_newline:
                    break
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
                elif ch == "E":
                    buffer.extend(seq)
                    if break_on_newline:
                        break
                elif ch in {'P', 'X', ']', '^', '_'}:
                    # Sequences terminated by ST
                    # APC = f"{ESC}_"   # ECMA-48 § 8.3.2
                    # DCS = f"{ESC}P"   # ECMA-48 § 8.3.27
                    # OSC = f"{ESC}]"   # ECMA-48 § 8.3.89
                    # PM = f"{ESC}^"   # ECMA-48 § 8.3.94
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
                buffer.extend(seq)
            else:
                buffer.append(ch)
        return "".join(buffer)

    def read(self, size=-1) -> str:
        """ Read and return at most size characters from the stream as a
        single str. If size is negative or None, reads until EOF.

        :param size:
        :returns: string containing the full sequence of characters read
        """
        if size is None or size < 0:
            self._check_closed()
            self._check_readable()
            buffer = "".join(self._buffer)
            self._buffer.clear()
            return buffer + self._channel.read()
        else:
            return self._read(size=size)

    def readable(self):
        return self._channel.readable()

    def readline(self, size=-1, /):
        return self._read(size=size, break_on_newline=True)

    def wait(self, timeout=None) -> bool:
        """ Wait until data is available for reading, or timeout.
        """
        self._check_closed()
        self._check_waitable()
        ready, _, _ = select([self._channel], [], [], timeout)
        return bool(ready)

    def waitable(self) -> bool:
        return hasattr(self._channel, "fileno") and callable(self._channel.fileno)


def measure_text(text, tab_size: int = 8) -> [int]:
    r""" Measure the forward advance of one or more lines of text, returning
    an array of sizes, one per line.

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
    line_widths = []
    cursor = 0
    while True:
        char_seq = tin.read(1)
        if not char_seq:
            break
        # Measurement can generally be taken by looking at only the
        # first character in a sequence. But C1 control codes might
        # be represented in expanded ESC+X form, so we should
        # normalise those.
        first_char = char_seq[0]
        if first_char == ESC and len(char_seq) > 1:
            second_char = char_seq[1]
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
            line_widths.append(cursor)
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
    line_widths.append(cursor)
    return line_widths
