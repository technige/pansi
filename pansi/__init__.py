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
UNICODE_NEWLINES = {CR, LF, CRLF, NEL, "\x85", VT, FF, "\u2028", "\u2029"}


# Translation tables
TO_SUBSCRIPT = str.maketrans(dict(zip("()+-0123456789=aehklmnopst",
                                      "₍₎₊₋₀₁₂₃₄₅₆₇₈₉₌ₐₑₕₖₗₘₙₒₚₛₜ")))
TO_SUPERSCRIPT = str.maketrans(dict(zip("()+-0123456789=in",
                                        "⁽⁾⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹⁼ⁱⁿ")))


#: Dictionary mapping the original set of named web colors to a pair of ANSI
#: terminal colour codes corresponding to foreground and background selectors.
#:
#: The original sixteen web colours were derived from CGA, an IBM graphics
#: card that established a standard for colour palettes used in computer
#: displays. Within those sixteen colours were eight low intensity colours
#: and eight high intensity colours. These in turn map to the sixteen base
#: colours still used in terminal emulators today.
#:
#: In practice, terminal emulation software renders a range of different
#: shades for these colours, although the selector codes remain the same.
#:
#: +-----------+------------------------+------------------+----------+
#: | Selector  |                        |                  |          |
#: +-----+-----+                        |                  |          |
#: |  FG |  BG | Description            | Web color names  |    CGA   |
#: +=====+=====+========================+==================+==========+
#: |  30 |  40 | low intensity black    | black            | ``#000`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  31 |  41 | low intensity red      | maroon           | ``#A00`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  32 |  42 | low intensity green    | green            | ``#0A0`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  33 |  43 | low intensity yellow   | olive            | ``#A50`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  34 |  44 | low intensity blue     | navy             | ``#00A`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  35 |  45 | low intensity magenta  | purple           | ``#A0A`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  36 |  46 | low intensity cyan     | teal             | ``#0AA`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  37 |  47 | low intensity white    | silver           | ``#AAA`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  90 | 100 | high intensity black   | grey, gray       | ``#555`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  91 | 101 | high intensity red     | red              | ``#F55`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  92 | 102 | high intensity green   | lime             | ``#5F5`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  93 | 103 | high intensity yellow  | yellow           | ``#FF5`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  94 | 104 | high intensity blue    | blue             | ``#55F`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  95 | 105 | high intensity magenta | fuchsia, magenta | ``#F5F`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  96 | 106 | high intensity cyan    | aqua, cyan       | ``#5FF`` |
#: +-----+-----+------------------------+------------------+----------+
#: |  97 | 107 | high intensity white   | white            | ``#FFF`` |
#: +-----+-----+------------------------+------------------+----------+
#:
#: - https://en.wikipedia.org/wiki/Color_Graphics_Adapter#Color_palette
#: - https://int10h.org/blog/2022/06/ibm-5153-color-true-cga-palette/
#: - https://www.w3.org/TR/REC-html40/types.html#h-6.5
#:
CGA_PALETTE = {
    "aqua": (96, 106),      # alias for "cyan"
    "black": (30, 40),
    "blue": (94, 104),
    "cyan": (96, 106),      # alias for "aqua"
    "fuchsia": (95, 105),   # alias for "magenta"
    "gray": (90, 100),      # alias for "grey"
    "green": (32, 42),
    "grey": (90, 100),      # alias for "gray"
    "lime": (92, 102),
    "magenta": (95, 105),   # alias for "fuchsia"
    "maroon": (31, 41),
    "navy": (34, 44),
    "olive": (33, 43),
    "purple": (35, 45),
    "red": (91, 101),
    "silver": (37, 47),
    "teal": (36, 46),
    "white": (97, 107),
    "yellow": (93, 103),
}


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
        self._closed = False

    def __del__(self):
        super().__del__()

    def _check_closed(self):
        if self._closed:
            raise ValueError("Terminal output is closed")

    def _check_writable(self):
        if not self.writable():
            raise OSError("Terminal output is not writable")

    def _color_sgr(self, value, background=False, web_palette_only=False) -> SGR:
        """ Construct an :py:class:`pansi.codes.SGR` object for a given color value. The input can be any
        of a hex colour value, a named colour, or an RGB tuple composed of numbers
        and/or percentages. The string value ``'default'`` can also be passed to
        explicitly select the terminal default colour.

        Note: alpha values are accepted, but ignored and discarded.

        :param value:
        :param background:
        :param web_palette_only: if true, use the web palette for all named
            colours instead of falling back to terminal palette for basic
            CGA colours
        :return: SGR
        """
        from pansi.color import WEB_PALETTE, decode_hex_color, rgb
        default = 49 if background else 39
        if isinstance(value, tuple):
            value = rgb(*value)
        else:
            value = str(value).strip()
        if value.startswith("#"):
            c = decode_hex_color(value)
            return SGR(48 if background else 38, 2,
                       c[0], c[1], c[2], reset=default)
        else:
            name = value.lower()
            if name == "default":
                return SGR(default)
            elif name in CGA_PALETTE and not web_palette_only:
                fg, bg = CGA_PALETTE[name]
                return SGR(bg if background else fg, reset=default)
            elif name in WEB_PALETTE:
                r, g, b = WEB_PALETTE[name]
                return SGR(48 if background else 38, 2, r, g, b, reset=default)
            else:
                raise ValueError(f"Unrecognised color name {value!r}")

    def color(self, value, web_palette_only=False) -> str:
        """ Generate ANSI escape code string for given foreground colour value.
        """
        try:
            sgr = self._color_sgr(value, web_palette_only=web_palette_only)
        except ValueError:
            return ""
        else:
            return str(sgr)

    def background_color(self, value, web_palette_only=False) -> str:
        """ Generate ANSI escape code string for given background colour value.
        """
        try:
            sgr = self._color_sgr(value, background=True, web_palette_only=web_palette_only)
        except ValueError:
            return ""
        else:
            return str(sgr)

    def font_weight(self, value) -> str:
        r""" Generate ANSI escape sequence for the given font weight. Values
        correspond to CSS font-weight values 'bold' and 'normal' or numeric
        equivalents.

        >>> font_weight('bold')
        '\x1b[1m'

        """
        try:
            weight = int(value)
        except (ValueError, TypeError):
            # compare as string
            weight = str(value)
            if weight == "bold":
                return str(bold)
            elif value == "normal":
                return str(~bold)
            else:
                return ""
        else:
            # compare as integer
            if weight > 500:
                return str(bold)
            elif weight < 400:
                return str(light)
            else:
                return str(~bold)

    def font_style(self, value) -> str:
        r""" Generate ANSI escape sequence for the given font style.
        """
        value = str(value)
        if value in {"italic", "oblique"}:
            return str(italic)
        elif value == "normal":
            return str(~italic)
        else:
            return ""

    def text_decoration(self, value) -> str:
        r""" Generate ANSI escape sequence for the given text-decoration value.

        >>> self.text_decoration('underline')
        '\x1b[4m'

        """
        values = str(value).lower().split()
        codes = []
        if "underline" in values:
            if "double" in values:
                codes.append(double_underline)
            else:
                codes.append(underline)
        if "blink" in values:
            codes.append(blink)
        if "line-through" in values:
            codes.append(line_through)
        if "overline" in values:
            codes.append(overline)
        return "".join(map(str, codes))

    def write(self, s, /,
              color=None,
              background_color=None,
              font_weight=None,
              font_style=None,
              text_decoration=None,
              vertical_align=None):
        if vertical_align == "sub":
            text = str(s).translate(TO_SUBSCRIPT)
        elif vertical_align == "super":
            text = str(s).translate(TO_SUPERSCRIPT)
        else:
            text = str(s)
        seq = [
            self.color(color),
            self.background_color(background_color),
            self.font_weight(font_weight),
            self.font_style(font_style),
            self.text_decoration(text_decoration),
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

    def measure(self, text, tab_size: int = 8) -> [int]:
        r""" Measure the total forward advance of one or more lines of text,
        returning an array of measurements, one per line.

        Notes:
        - Regular characters occupy one cell
        - Non-printable characters and escape sequences occupy zero cells
        - Full width characters occupy two cells

        >>> self.measure("hello, world")
        [12]
        >>> self.measure(f"hello, {green}world{reset}")
        [12]
        >>> self.measure("hello, ｗｏｒｌｄ")
        [17]
        >>> self.measure(f"hello, {green}ｗｏｒｌｄ{reset}")
        [17]
        >>> self.measure("hello\nworld")
        [5, 5]
        """
        tin = TerminalInput(StringIO(text))
        measurements = []
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
