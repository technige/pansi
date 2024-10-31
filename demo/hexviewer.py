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


from argparse import ArgumentParser

from pansi.codes import CSI
from pansi.screen import Screen
from pansi.text import grey


class HexViewer:

    line_width = 16

    def __init__(self, screen, data):
        self.screen = screen
        self.data = data

    def count_data_lines(self):
        count = len(self.data) / self.line_width
        if count == int(count):
            return int(count)
        else:
            return int(count + 1)

    def render(self, line_offset):
        byte_offset = line_offset * self.line_width
        self.screen.clear()
        n_lines, n_cols = self.screen.size
        for line_no, offset in enumerate(range(byte_offset, len(self.data), self.line_width)):
            if line_no < n_lines - 1:
                line = self.data[offset:(offset + 16)]
                printable_line = "".join(chr(ch) if 32 <= ch <= 126 else f"{grey}·{~grey}" for ch in line)
                byte_hex = ' '.join(f'{value:02X}' for value in line)
                print(f"{offset:08X}  {byte_hex:<47}  {printable_line}")
            else:
                break
        self.screen.flush()


def main():
    parser = ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()
    screen = Screen()
    try:
        screen.hide_cursor()
        screen.show()
        with open(args.filename, "rb") as f:
            data = f.read()
        viewer = HexViewer(screen, data)
        line_offset = 0
        while True:
            viewer.render(line_offset)
            key = screen.read_key()
            if key == f"{CSI}A" and line_offset > 0:
                line_offset -= 1
            elif key == f"{CSI}B" and line_offset < viewer.count_data_lines() - screen.size[0] + 1:
                line_offset += 1
            elif key == "q":
                break
    except KeyboardInterrupt:
        pass  # Ctrl+C to exit
    finally:
        screen.hide()
        screen.show_cursor()


if __name__ == "__main__":
    main()
