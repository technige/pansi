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


from ._codes import CSI


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


class SGR:
    """ Hold the parameters of an SGR control sequence, along with an
    optional reset code.
    """

    @classmethod
    def for_color(cls, value, background=False, web_palette_only=False):
        """ Construct an :py:class:`pansi.SGR` object for a given color value.
        The input can be either a hex colour value, a named colour, or an RGB
        tuple composed of numbers and/or percentages. The literal string value
        ``'default'`` can also be passed to explicitly select the terminal
        default colour.

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
            return cls(48 if background else 38, 2,
                       c[0], c[1], c[2], reset=default)
        else:
            name = value.lower()
            if name == "default":
                return cls(default)
            elif name in CGA_PALETTE and not web_palette_only:
                fg, bg = CGA_PALETTE[name]
                return cls(bg if background else fg, reset=default)
            elif name in WEB_PALETTE:
                r, g, b = WEB_PALETTE[name]
                return cls(48 if background else 38, 2, r, g, b, reset=default)
            else:
                raise ValueError(f"Unrecognised color name {value!r}")

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
