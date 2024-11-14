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

from pansi import CSI, grey, Terminal


class HexViewer:

    line_width = 16

    @classmethod
    def load(cls, filename):
        with open(filename, "rb") as f:
            return cls(f.read())

    def __init__(self, data):
        self.terminal = Terminal()
        self.terminal.add_event_listener("keypress", self.on_keypress)
        self.terminal.add_event_listener("resize", self.on_resize)
        self.data = data
        self.data_lines = self._count_data_lines()
        self.line_offset = 0

    def _count_data_lines(self):
        count = len(self.data) / self.line_width
        if count == int(count):
            return int(count)
        else:
            return int(count + 1)

    def on_keypress(self, data):
        if data == f"{CSI}A" and self.line_offset > 0:
            self.line_offset -= 1
            self.render()
        elif data == f"{CSI}B" and self.line_offset < self.data_lines - self.terminal.get_size().lines + 1:
            self.line_offset += 1
            self.render()

    def on_resize(self, data):
        self.render()

    def run(self):
        self.terminal.hide_cursor()
        self.terminal.show_alternate_screen()
        try:
            self.terminal.set_cursor_position(0, 0)
            self.render()
            self.terminal.loop()
        except KeyboardInterrupt:
            pass
        finally:
            self.terminal.hide_alternate_screen()
            self.terminal.show_cursor()

    def render(self):
        byte_offset = self.line_offset * self.line_width
        self.terminal.clear()
        terminal_size = self.terminal.get_size()
        for line_no, offset in enumerate(range(byte_offset, len(self.data), self.line_width)):
            if line_no < terminal_size.lines - 1:
                line = self.data[offset:(offset + 16)]
                printable_line = "".join(chr(ch) if 32 <= ch <= 126 else f"{grey}·{~grey}" for ch in line)
                byte_hex = ' '.join(f'{value:02X}' for value in line)
                print(f"{offset:08X}  {byte_hex:<47}  {printable_line}")
            else:
                break
        self.terminal.flush()


def main():
    parser = ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()
    HexViewer.load(args.filename).run()


if __name__ == "__main__":
    main()
