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


from collections.abc import Sequence
from io import StringIO
from math import cos, sin, tau
from re import compile as re_compile
from typing import Iterable
from unicodedata import category, east_asian_width


from pansi.codes import (
    BS, HT, CR, LF, CRLF, UNICODE_NEWLINES,
    ESC, CSI, C1_CONTROL_TO_ESCAPE_SEQUENCE,
    DEL, APC,
)
from pansi._math import clamp, linear_to_gamma

# Patterns
_PADDED_SEGMENT_BREAK = re_compile(r"[ \t]*(\r\n|\n|\r)[ \t]*")
_TWO_OR_MORE_SPACES = re_compile(r"  +")
_COLOR_FUNCTION = re_compile(r"(\w+)\((.*?)(/(.*?))?\)")


# Translation tables
_TEXT_TO_SUBSCRIPT = str.maketrans(dict(zip("()+-0123456789=aehklmnopst",
                                            "₍₎₊₋₀₁₂₃₄₅₆₇₈₉₌ₐₑₕₖₗₘₙₒₚₛₜ")))
_TEXT_TO_SUPERSCRIPT = str.maketrans(dict(zip("()+-0123456789=in",
                                              "⁽⁾⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹⁼ⁱⁿ")))

# SGR parameters for named web colours
#
# The original 16 colours are derived from CGA, and so we map them here
# to the ANSI terminal equivalents. In many cases, the actual terminal
# implementations will render colours that differ from the precise
# definitions given for web colours, so this is a trade-off. Given the
# lack of importance named colours have in contemporary web design, it
# is arguably better to align them more closely with the intended design
# of this module: ANSI terminal colours.
#
#   FG  BG  Description       Web color name(s)  CGA
#   --  --  ----------------  -----------------  ----
#   30  40  "dark black"      black              #000
#   31  41  "dark red"        maroon             #A00
#   32  42  "dark green"      green              #0A0
#   33  43  "dark yellow"     olive              #A50
#   34  44  "dark blue"       navy               #00A
#   35  45  "dark magenta"    purple             #A0A
#   36  46  "dark cyan"       teal               #0AA
#   37  47  "dark white"      silver             #AAA
#   90 100  "bright black"    gray, grey         #555
#   91 101  "bright red"      red                #F55
#   92 102  "bright green"    lime               #5F5
#   93 103  "bright yellow"   yellow             #FF5
#   94 104  "bright blue"     blue               #55F
#   95 105  "bright magenta"  fuchsia, magenta   #F5F
#   96 106  "bright cyan"     aqua, cyan         #5FF
#   97 107  "bright white"    white              #FFF
#
# https://en.wikipedia.org/wiki/Color_Graphics_Adapter#Color_palette
# https://int10h.org/blog/2022/06/ibm-5153-color-true-cga-palette/
# https://www.w3.org/TR/REC-html40/types.html#h-6.5
#
_NAMED_COLOR_PARAMETERS = {
    "aliceblue": (240, 248, 255),
    "antiquewhite": (250, 235, 215),
    "aqua": 96,
    "aquamarine": (127, 255, 212),
    "azure": (240, 255, 255),
    "beige": (245, 245, 220),
    "bisque": (255, 228, 196),
    "black": 30,
    "blanchedalmond": (255, 235, 205),
    "blue": 94,
    "blueviolet": (138, 43, 226),
    "brown": (165, 42, 42),
    "burlywood": (222, 184, 135),
    "cadetblue": (95, 158, 160),
    "chartreuse": (127, 255, 0),
    "chocolate": (210, 105, 30),
    "coral": (255, 127, 80),
    "cornflowerblue": (100, 149, 237),
    "cornsilk": (255, 248, 220),
    "crimson": (220, 20, 60),
    "cyan": 96,
    "darkblue": (0, 0, 139),
    "darkcyan": (0, 139, 139),
    "darkgoldenrod": (184, 134, 11),
    "darkgray": (169, 169, 169),
    "darkgreen": (0, 100, 0),
    "darkgrey": (169, 169, 169),
    "darkkhaki": (189, 183, 107),
    "darkmagenta": (139, 0, 139),
    "darkolivegreen": (85, 107, 47),
    "darkorange": (255, 140, 0),
    "darkorchid": (153, 50, 204),
    "darkred": (139, 0, 0),
    "darksalmon": (233, 150, 122),
    "darkseagreen": (143, 188, 143),
    "darkslateblue": (72, 61, 139),
    "darkslategray": (47, 79, 79),
    "darkslategrey": (47, 79, 79),
    "darkturquoise": (0, 206, 209),
    "darkviolet": (148, 0, 211),
    "deeppink": (255, 20, 147),
    "deepskyblue": (0, 191, 255),
    "dimgray": (105, 105, 105),
    "dimgrey": (105, 105, 105),
    "dodgerblue": (30, 144, 255),
    "firebrick": (178, 34, 34),
    "floralwhite": (255, 250, 240),
    "forestgreen": (34, 139, 34),
    "fuchsia": 95,
    "gainsboro": (220, 220, 220),
    "ghostwhite": (248, 248, 255),
    "gold": (255, 215, 0),
    "goldenrod": (218, 165, 32),
    "gray": 90,
    "green": 32,
    "greenyellow": (173, 255, 47),
    "grey": 90,
    "honeydew": (240, 255, 240),
    "hotpink": (255, 105, 180),
    "indianred": (205, 92, 92),
    "indigo": (75, 0, 130),
    "ivory": (255, 255, 240),
    "khaki": (240, 230, 140),
    "lavender": (230, 230, 250),
    "lavenderblush": (255, 240, 245),
    "lawngreen": (124, 252, 0),
    "lemonchiffon": (255, 250, 205),
    "lightblue": (173, 216, 230),
    "lightcoral": (240, 128, 128),
    "lightcyan": (224, 255, 255),
    "lightgoldenrodyellow": (250, 250, 210),
    "lightgray": (211, 211, 211),
    "lightgreen": (144, 238, 144),
    "lightgrey": (211, 211, 211),
    "lightpink": (255, 182, 193),
    "lightsalmon": (255, 160, 122),
    "lightseagreen": (32, 178, 170),
    "lightskyblue": (135, 206, 250),
    "lightslategray": (119, 136, 153),
    "lightslategrey": (119, 136, 153),
    "lightsteelblue": (176, 196, 222),
    "lightyellow": (255, 255, 224),
    "lime": 92,
    "limegreen": (50, 205, 50),
    "linen": (250, 240, 230),
    "magenta": 95,
    "maroon": 31,
    "mediumaquamarine": (102, 205, 170),
    "mediumblue": (0, 0, 205),
    "mediumorchid": (186, 85, 211),
    "mediumpurple": (147, 112, 219),
    "mediumseagreen": (60, 179, 113),
    "mediumslateblue": (123, 104, 238),
    "mediumspringgreen": (0, 250, 154),
    "mediumturquoise": (72, 209, 204),
    "mediumvioletred": (199, 21, 133),
    "midnightblue": (25, 25, 112),
    "mintcream": (245, 255, 250),
    "mistyrose": (255, 228, 225),
    "moccasin": (255, 228, 181),
    "navajowhite": (255, 222, 173),
    "navy": 34,
    "oldlace": (253, 245, 230),
    "olive": 33,
    "olivedrab": (107, 142, 35),
    "orange": (255, 165, 0),
    "orangered": (255, 69, 0),
    "orchid": (218, 112, 214),
    "palegoldenrod": (238, 232, 170),
    "palegreen": (152, 251, 152),
    "paleturquoise": (175, 238, 238),
    "palevioletred": (219, 112, 147),
    "papayawhip": (255, 239, 213),
    "peachpuff": (255, 218, 185),
    "peru": (205, 133, 63),
    "pink": (255, 192, 203),
    "plum": (221, 160, 221),
    "powderblue": (176, 224, 230),
    "purple": 35,
    "rebeccapurple": (102, 51, 153),
    "red": 91,
    "rosybrown": (188, 143, 143),
    "royalblue": (65, 105, 225),
    "saddlebrown": (139, 69, 19),
    "salmon": (250, 128, 114),
    "sandybrown": (244, 164, 96),
    "seagreen": (46, 139, 87),
    "seashell": (255, 245, 238),
    "sienna": (160, 82, 45),
    "silver": 37,
    "skyblue": (135, 206, 235),
    "slateblue": (106, 90, 205),
    "slategray": (112, 128, 144),
    "slategrey": (112, 128, 144),
    "snow": (255, 250, 250),
    "springgreen": (0, 255, 127),
    "steelblue": (70, 130, 180),
    "tan": (210, 180, 140),
    "teal": 36,
    "thistle": (216, 191, 216),
    "tomato": (255, 99, 71),
    "turquoise": (64, 224, 208),
    "violet": (238, 130, 238),
    "wheat": (245, 222, 179),
    "white": 97,
    "whitesmoke": (245, 245, 245),
    "yellow": 93,
    "yellowgreen": (154, 205, 50),
}


class SGR:
    """ The control sequence '[CSI]{parameters}m' is known as 'Select
    Graph Rendition' or 'SGR'. This is used to control display attributes
    such as colour and text style in terminals that support this (which
    most modern terminals do).
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


def color_sgr(value, background=False) -> SGR:
    """ Resolve a colour value string into an RGB 3-tuple or ANSI
    integer colour code.

    Note: alpha values are ignored and discarded.

    :param value:
    :param background:
    :return: SGR
    """
    default = 49 if background else 39
    value = str(value).strip()
    if value.startswith("#"):
        code_len = len(value)
        if code_len in {4, 5}:
            # '#RGB' or '#RGBA'
            r = int(value[1], 16) * 17
            g = int(value[2], 16) * 17
            b = int(value[3], 16) * 17
            return SGR(48 if background else 38, 2, r, g, b, reset=default)
        elif code_len in {7, 9}:
            # '#RRGGBB' or '#RRGGBBAA'
            r = int(value[1:3], 16)
            g = int(value[3:5], 16)
            b = int(value[5:7], 16)
            return SGR(48 if background else 38, 2, r, g, b, reset=default)
        else:
            raise ValueError(f"Unusable hex color code {value!r}")
    else:
        try:
            param = _NAMED_COLOR_PARAMETERS[value.lower()]
        except KeyError:
            raise ValueError(f"Unrecognised color name {value!r}")
        else:
            if isinstance(param, int):
                return SGR(param + 10 if background else param, reset=default)
            else:
                return SGR(48 if background else 38, 2, *param, reset=default)


# Reset
reset = f"{CSI}0m"

# Font weight and style
bold = SGR(1, reset=22)
light = SGR(2, reset=22)
italic = SGR(3, reset=23)
underline = SGR(4, reset=24)
blink = SGR(5, reset=25)
invert = SGR(7, reset=27)
line_through = SGR(9, reset=29)
double_underline = SGR(21, reset=24)
overline = SGR(53, reset=55)

# Foreground SGRs for original 16 CGA/web colours
black = color_sgr("black")
maroon = color_sgr("maroon")
green = color_sgr("green")
olive = color_sgr("olive")
navy = color_sgr("navy")
purple = color_sgr("purple")
teal = color_sgr("teal")
silver = color_sgr("silver")
gray = grey = color_sgr("gray")
red = color_sgr("red")
lime = color_sgr("lime")
yellow = color_sgr("yellow")
blue = color_sgr("blue")
fuchsia = magenta = color_sgr("fuchsia")
aqua = cyan = color_sgr("aqua")
white = color_sgr("white")

# Background SGRs for original 16 CGA/web colours
on_black = color_sgr("black", background=True)
on_maroon = color_sgr("maroon", background=True)
on_green = color_sgr("green", background=True)
on_olive = color_sgr("olive", background=True)
on_navy = color_sgr("navy", background=True)
on_purple = color_sgr("purple", background=True)
on_teal = color_sgr("teal", background=True)
on_silver = color_sgr("silver", background=True)
on_gray = on_grey = color_sgr("gray", background=True)
on_red = color_sgr("red", background=True)
on_lime = color_sgr("lime", background=True)
on_yellow = color_sgr("yellow", background=True)
on_blue = color_sgr("blue", background=True)
on_fuchsia = on_magenta = color_sgr("fuchsia", background=True)
on_aqua = on_cyan = color_sgr("aqua", background=True)
on_white = color_sgr("white", background=True)


def color(value) -> str:
    """ Generate ANSI escape code string for given foreground colour value.
    """
    try:
        sgr = color_sgr(value)
    except ValueError:
        return ""
    else:
        return str(sgr)


def background_color(value) -> str:
    """ Generate ANSI escape code string for given background colour value.
    """
    try:
        sgr = color_sgr(value, background=True)
    except ValueError:
        return ""
    else:
        return str(sgr)


def rgb(red, green, blue, alpha=None) -> str:
    r""" Generate a color value string from component RGB values.

    The red, green and blue values represent their respective colour
    channels. Each value can be represented as a number between 0 and
    255, a percentage string between '0%' and '100%', the keyword 'none',
    or an actual None value (the latter two of which are equivalent to 0).

    The alpha value represents the alpha channel (transparency). This can
    be supplied as a number between 0 and 1, a percentage string between
    '0%' and '100%', the keyword 'none' or a None value. Here, 'none' can
    be used to explicitly specify no alpha channel (which in effect gives
    100% opacity).

    :param red: red channel
    :param green: green channel
    :param blue: blue channel
    :param alpha: alpha channel (transparency)
    :return: RGB hex string value in either '#RRGGBB' or '#RRGGBBAA' form
    """
    red = round(clamp(red, (0, 255)))
    green = round(clamp(green, (0, 255)))
    blue = round(clamp(blue, (0, 255)))
    if str(alpha).lower() == "none":
        return f"#{red:02X}{green:02X}{blue:02X}"
    else:
        alpha = round(255 * clamp(alpha, (0, 1)))
        return f"#{red:02X}{green:02X}{blue:02X}{alpha:02X}"


def hsl(hue, saturation, lightness, alpha=None):
    raise NotImplementedError  # TODO


def hwb(hue, whiteness, blackness, alpha=None):
    raise NotImplementedError  # TODO


def lab(l, a, b, alpha=None):
    raise NotImplementedError  # TODO


def lch(l, c, h, alpha=None):
    raise NotImplementedError  # TODO


def oklab(lightness, a, b, alpha=None):
    r""" Generate a color value string from component OkLab values.

    :param lightness:
    :param a:
    :param b:
    :param alpha:
    :returns:
    """
    # TODO: Percent reference range
    #   for a and b: -100% = -0.4, 100% = 0.4
    lightness = clamp(lightness, (0, 1))
    l = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3

    # Convert linear RGB to sRGB
    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

    # Scale RGB values and
    # hand off to rgb function
    return rgb(255 * linear_to_gamma(r),
               255 * linear_to_gamma(g),
               255 * linear_to_gamma(b),
               alpha=alpha)


def oklch(lightness, chroma, hue, alpha=None):
    r""" Generate a color value string from component OkLCH values.

    :param lightness:
    :param chroma:
    :param hue: angular hue, measured in degrees
    :param alpha:
    :returns:
    """
    chroma = clamp(chroma, (0, 0.4))  # TODO: resolve percentages but allow overflow
    hue_rad = hue * tau / 360  # Convert from degrees to radians (TODO: allow other angular units)
    a = chroma * cos(hue_rad)
    b = chroma * sin(hue_rad)
    return oklab(lightness, a, b, alpha=alpha)


def font_weight(value) -> str:
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


def font_style(value) -> str:
    r""" Generate ANSI escape sequence for the given font style.
    """
    value = str(value)
    if value in {"italic", "oblique"}:
        return str(italic)
    elif value == "normal":
        return str(~italic)
    else:
        return ""


def text_decoration(value) -> str:
    r""" Generate ANSI escape sequence for the given text-decoration value.

    >>> text_decoration('underline')
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


def _apply_vertical_align(text, value):
    if value == "sub":
        return text.translate(_TEXT_TO_SUBSCRIPT)
    elif value == "super":
        return text.translate(_TEXT_TO_SUPERSCRIPT)
    else:
        return text


class Text(Sequence):

    def __init__(self, text, tab_size=8, encoding="utf-8", errors="strict"):
        if isinstance(text, self.__class__):
            self._raw = text._raw
            if tab_size == text._tab_size:
                self._units = text._units
                self._tab_size = text._tab_size
                self._measurements = text._measurements
            else:
                self._units: [str] = list(_iter_text_units(StringIO(self._raw)))
                self._tab_size: int = tab_size
                self._measurements: [(int, int)] = None
        else:
            try:
                text = text.read()
            except AttributeError:
                pass
            try:
                text = text.decode(encoding, errors)
            except AttributeError:
                pass
            self._raw: str = str(text).translate(C1_CONTROL_TO_ESCAPE_SEQUENCE)
            self._units: [str] = list(_iter_text_units(StringIO(self._raw)))
            self._tab_size: int = tab_size
            self._measurements: [(int, int)] = None
        self._color = color
        self._background_color = background_color
        self._font_weight = font_weight
        self._font_style = font_style
        self._text_decoration = text_decoration

    @property
    def tab_size(self):
        return self._tab_size

    @property
    def measurements(self):
        if self._measurements is None:
            self._measurements = list(_iter_text_measurements(self._units, self._tab_size))
        return self._measurements

    def __repr__(self):
        return f"{self.__class__.__name__}({self._raw!r})"

    def __str__(self):
        return self._raw

    def __eq__(self, other):
        return self._raw == str(other)

    def __hash__(self):
        return hash(self._raw)

    def __iter__(self):
        return iter(self._units)

    def __len__(self):
        return len(self._units)

    def __getitem__(self, index):
        item = self._units.__getitem__(index)
        if isinstance(index, slice):
            return self.__class__("".join(item))
        else:
            return item

    def __contains__(self, item):
        return str(item) in self._raw

    def __add__(self, other):
        return self.__class__(self._raw + str(other))

    def __radd__(self, other):
        return self.__class__(str(other) + self._raw)

    def _copy_with(self, code):
        if code:
            if self._raw.endswith(f"{CSI}0m") or self._raw.endswith(f"{CSI}m"):
                return self.__class__(f"{code}{self._raw}")
            else:
                return self.__class__(f"{code}{self._raw}{reset}")
        else:
            return self

    def plain(self):
        raise NotImplementedError  # TODO: remove all style codes

    def style(self, /, color=None, background_color=None, font_weight=None, font_style=None,
              text_decoration=None, vertical_align=None):
        """

        >>> Text("H2O").style(color="blue", vertical_align="sub")
        Text('\x1b[94mH₂O\x1b[0m')

        :param color:
        :param background_color:
        :param font_weight:
        :param font_style:
        :param text_decoration:
        :param vertical_align:
        :return:
        """
        text = _apply_vertical_align(self._raw, vertical_align)
        seq = [
            self._color(color),
            self._background_color(background_color),
            self._font_weight(font_weight),
            self._font_style(font_style),
            self._text_decoration(text_decoration),
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
                line_units = list(Text(line))
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
            return self.__class__("".join(map(str, units)))
        else:
            return self

    def translate(self, table):
        """ Return a copy of the text in which each character has been
        mapped through the given translation table.
        """
        units = []
        for unit in self._units:
            try:
                b = ord(unit)
            except TypeError:
                units.append(unit)
            else:
                try:
                    translated = table[b]
                except KeyError:
                    units.append(unit)
                else:
                    units.append(translated)
        return self.__class__("".join(units))

    def render(self, /, white_space="normal") -> str:
        collapsible = white_space in {"normal", "nowrap", "pre-line"}

        units = []
        line = 0
        column = 0
        last_palpable_unit = None
        for unit, (advance, width) in zip(self._units, self.measurements):
            include = True
            if collapsible and unit == " " and last_palpable_unit == " ":
                include = False
            if include:
                units.append(unit)
                line += advance
                column += width
                if width > 0:
                    print(f"Setting LPU to {unit!r}")
                    last_palpable_unit = unit
        return "".join(units)

        # text = self._raw
        # if white_space in {"normal", "nowrap", "pre-line"}:
        #     text = _PADDED_SEGMENT_BREAK.sub("\n", text)
        #     text = text.replace("\t", " ")
        #     text = text.replace("\n", " ")
        #     text = _TWO_OR_MORE_SPACES.sub(" ", text)
        # return text


def _iter_text_units(sio: StringIO) -> Iterable[str]:
    r""" Read a text, yielding each character or character sequence
    in turn. Characters are yielded individually, except for the
    following:

    - CRLF
    - ANSI escape sequences
    - Characters followed by combining characters

    Notes:
        - C1 control characters will be automatically converted to
          escape sequences (e.g. `\x85` -> `\x1bE`)
        - combining characters following C0 controls or newlines
          will be discarded

    """
    ch = sio.read(1)
    while ch:
        if ch == ESC:
            # Escape sequence
            ch = sio.read(1)
            seq = [ESC, ch]
            if ch == '[' or ch == 'O':
                # CSI ('{ESC}[') or SS3 ('{ESC}O')
                while True:
                    ch = sio.read(1)
                    seq.append(ch)
                    if '@' <= ch <= '~':
                        break
            elif ch in {'P', 'X', ']', '^', '_'}:
                # Sequences terminated by ST
                while True:
                    ch = sio.read(1)
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
                    ch = sio.read(1)
                    seq.append(ch)
                    if '0' <= ch <= '~':
                        break
            value = ''.join(seq)
        elif ch == CR:
            marker = sio.tell()
            if sio.read(1) == LF:
                value = CRLF
            else:
                sio.seek(marker)
                value = CR
        elif "\x80" <= ch <= "\x9F":
            value = ch.translate(C1_CONTROL_TO_ESCAPE_SEQUENCE)
        else:
            value = ch
        # Check for combining characters
        combiners = []
        while True:
            marker = sio.tell()
            cc = sio.read(1)
            if not cc:
                break
            cat = category(cc)
            if cat[0] == "M":
                combiners.append(cc)
            else:
                sio.seek(marker)
                break
        # Yield the value, plus any combiners
        if combiners:
            yield value + "".join(combiners)
        else:
            yield value
        ch = sio.read(1)


def _iter_text_measurements(units: [str], tab_size: int) -> ((int, int), str):
    r""" Iterate through a text string or iterable sequence of characters,
    yielding a (line_advance, width) tuple for each.

    line_advance - change in vertical cursor position
    width        - change in horizontal cursor position
    char_seq     - the character or character sequence

    For width:
    - Regular characters occupy one cell
    - Non-printable characters and escape sequences occupy zero cells
    - Full width characters occupy two cells

    >>> text_width = lambda s: sum(width for ((_, width), _) in measure(s))
    >>> text_width("hello, world")
    12
    >>> text_width(f"hello, {ansi_green}world{reset}")
    [12]
    >>> measure_text("hello, ｗｏｒｌｄ")
    [17]
    >>> measure_text(f"hello, {ansi_green}ｗｏｒｌｄ{reset}")
    [17]
    >>> measure_text("hello\nworld")
    """
    # TODO tab, newline
    y = 0
    x = 0
    for char_seq in units:
        # Measurement can generally be taken by looking at only the
        # first character. But C1 control codes might be represented
        # in expanded ESC+X form, so we should normalise those.
        first_char = char_seq[0]
        if first_char == ESC and len(char_seq) > 1:
            second_char = char_seq[1]
            if "@" <= second_char <= "_":
                # collapse 7-bit C1 control codes to 8-bit equivalents
                first_char = chr(0x40 + ord(second_char))
        # For most values, no vertical movement occurs, so we can
        # save code by assuming a default of zero.
        line = 0
        # Now, check specific edge cases and fall back to checking the
        # Unicode general category.
        if first_char in UNICODE_NEWLINES:
            # This detects:
            # - CR, LF, CRLF (CRLF will be tested as CR, but whatever)
            # - NEL (both 7-bit and 8-bit representations)
            # - VT, FF
            # - LS, PS
            line = 1
            width = -x
        elif first_char == BS:
            width = -1
        elif first_char == HT:
            # Advance to next multiple of tab_size. This formula should
            # only ever return values between 1 and tab_size inclusive.
            width = tab_size - (x % tab_size)
        elif first_char < " ":
            # Other control characters do not affect the cursor:
            # - NUL, BEL, CAN, EM, SUB, ESC
            # - TC (SOH, STX, ETX, EOT, ENQ, ACK, DLE, NAK, SYN, ETB)
            # - LS (SI, SO)
            # - DC (DC1, DC2, DC3, DC4)
            # - IS (FS, GS, RS, US)
            width = 0
        elif first_char <= "~":
            # Anything else in ASCII range is printable and one cell wide.
            width = 1
        elif DEL <= first_char <= APC:
            # TODO: this isn't true for all of these
            width = 0
        else:
            # For everything else, check the Unicode general category.
            major, minor = category(first_char)
            is_printable = major in {'L', 'N', 'P', 'S'} or (major, minor) == ('Z', 's')
            if is_printable:
                width = (2 if east_asian_width(first_char) in {'F', 'W'} else 1)
            else:
                width = 0  # not printable, so no visible size
        yield line, width
        y += line
        x += width
