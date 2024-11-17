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


# TODO: rename this module


from collections import namedtuple
from io import StringIO
from re import compile as re_compile
from unicodedata import category, east_asian_width

from ._codes import BS, HT, ESC, DEL, CSI, APC, UNICODE_NEWLINES


class Rect(tuple):

    def __new__(cls, x=0, y=0, width=0, height=0):
        return tuple.__new__(cls, (x, y, width, height))

    def __repr__(self):
        return f"{type(self).__name__}(x={self.x!r}, y={self.y!r}, width={self.width!r}, height={self.height!r})"

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    @property
    def width(self):
        return self[2]

    @property
    def height(self):
        return self[3]

    @property
    def top(self):
        return self.y if self.height >= 0 else self.y + self.height

    @property
    def right(self):
        return self.x + self.width if self.width >= 0 else self.x

    @property
    def bottom(self):
        return self.y + self.height if self.height >= 0 else self.y

    @property
    def left(self):
        return self.x if self.width >= 0 else self.x + self.width


class Measurable:

    def measure(self, unit="ch") -> Rect:
        raise NotImplementedError


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


class Cursor(Measurable):

    def __init__(self, terminal):
        self._terminal = terminal

    def show(self):
        self._terminal.write(f"{CSI}?25h")
        self._terminal.flush()

    def hide(self):
        self._terminal.write(f"{CSI}?25l")
        self._terminal.flush()

    def measure(self, unit="ch") -> Rect:
        if unit != "ch":
            raise NotImplementedError
        self._terminal.write(f"{CSI}6n")
        self._terminal.flush()
        match = self._terminal.loop(break_key=re_compile(r"\x1B\[(\d*);(\d*)R"), timeout=self._terminal._response_timeout)
        if match:
            line = int(match.group(1))
            column = int(match.group(2))
            return Rect(column - 1, line - 1, 1, 1)
        else:
            raise OSError("Cursor position unavailable")

    # def get_position(self) -> Position:
    #     self._terminal.write(f"{CSI}6n")
    #     self._terminal.flush()
    #     match = self._terminal.loop(break_key=re_compile(r"\x1B\[(\d*);(\d*)R"), timeout=self._terminal._response_timeout)
    #     if match:
    #         return Position(top=int(match.group(1)), left=int(match.group(2)))
    #     else:
    #         raise OSError("Cursor position unavailable")

    def move_to(self, position: Rect, /, x=0, y=0):
        line = position.y + y + 1
        column = position.x + x + 1
        self._terminal.write(f"{CSI}{line};{column}H")

    # def set_position(self, /, line, column):
    #     self._terminal.write(f"{CSI}{line};{column}H")


class Screen(Measurable):

    def __init__(self, terminal):
        self._terminal = terminal
        self._boxes = []

    @property
    def terminal(self):
        return self._terminal

    def paste(self, content, /, **style):
        self._boxes.append(Box(content, **style))

    def measure(self, unit="ch") -> Rect:
        return self._terminal.measure(unit)

    def render(self):
        self._terminal.write(f"{CSI}?1049h")
        self._terminal.write(f"{CSI}H{CSI}2J")
        size: Rect = self._terminal.measure()
        for box in self._boxes:
            box_size: Rect = box.measure()
            pos: Rect = self._terminal.cursor.measure()
            if box.display == "block":
                if pos.x == 0:
                    y = pos.y
                else:
                    y = pos.y + 1
                if box.align == "center":
                    x = (size.width - box_size.width) // 2
                elif box.align == "right":
                    x = size.width - box_size.width
                else:  # "left" or "start" (with ltr direction)
                    x = 1
                pos = Rect(x, y, pos.width, pos.height)
            for y, text in enumerate(box.lines()):
                self._terminal.cursor.move_to(pos, y=y)
                self._terminal.write(f"{text}")
            if box.display == "block":
                self._terminal.cursor.move_to(Rect(0, pos.top + box_size.height))
            elif box.display == "inline":
                self._terminal.cursor.move_to(Rect(pos.left + box_size.width, pos.top))  # assume inline, move to right
        self._terminal.flush()


class Box(Measurable):

    def __init__(self, content, /, **style):
        content = str(content).rstrip()
        lines = content.splitlines(keepends=False)
        widths = measure_text(content)
        self._height = len(lines)
        self._width = max(widths)
        self._lines = [line + (" " * (self._width - widths[i])) for i, line in enumerate(lines)]
        self._style = style

    # TODO: rename this relative to "content"
    def lines(self):
        return iter(self._lines)

    @property
    def align(self):
        return self._style.get("align", "start")

    @property
    def display(self):
        return self._style.get("display", "inline")

    def measure(self, unit="ch") -> Rect:
        if unit != "ch":
            raise NotImplementedError
        return Rect(0, 0, self._width, self._height)
