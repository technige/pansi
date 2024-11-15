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


from collections import namedtuple
from io import StringIO
from unicodedata import category, east_asian_width

from ._codes import BS, HT, ESC, DEL, APC, UNICODE_NEWLINES


RectangularArea = namedtuple("RectangularArea", ["lines", "columns", "pixel_width", "pixel_height"])


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
    from ._term import TerminalInput
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
