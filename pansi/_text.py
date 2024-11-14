#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
from io import StringIO

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


from ._sgr import (SGR, blink, bold, double_underline, italic,
                   light, line_through, overline, underline)


# Translation tables
TO_SUBSCRIPT = str.maketrans(dict(zip("()+-0123456789=aehklmnopst",
                                      "₍₎₊₋₀₁₂₃₄₅₆₇₈₉₌ₐₑₕₖₗₘₙₒₚₛₜ")))
TO_SUPERSCRIPT = str.maketrans(dict(zip("()+-0123456789=in",
                                        "⁽⁾⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹⁼ⁱⁿ")))


def color(value, web_palette_only=False) -> str:
    """ Generate ANSI escape code string for given foreground colour value.
    """
    try:
        sgr = SGR.for_color(value, web_palette_only=web_palette_only)
    except ValueError:
        return ""
    else:
        return str(sgr)


def background_color(value, web_palette_only=False) -> str:
    """ Generate ANSI escape code string for given background colour value.
    """
    try:
        sgr = SGR.for_color(value, background=True, web_palette_only=web_palette_only)
    except ValueError:
        return ""
    else:
        return str(sgr)


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
