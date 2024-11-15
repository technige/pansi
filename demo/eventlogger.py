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


from re import compile as re_compile

from pansi import Terminal


class Demo:

    def __init__(self):
        self.terminal = Terminal()
        self.terminal.add_event_listener("keypress", self.on_keypress)
        self.terminal.add_event_listener("resize", self.on_resize)

    def on_keypress(self, event):
        self.terminal.print(f"Input event {event!r}")

    def on_resize(self, event):
        self.terminal.print(f"Resize event {event!r}")

    def run(self):
        self.terminal.hide_cursor()
        self.terminal.show_alternate_screen(mode="raw")
        try:
            self.terminal.set_cursor_position(0, 0)
            self.terminal.loop(break_key=re_compile(r"[Qq]"))
        except KeyboardInterrupt:
            pass
        finally:
            self.terminal.hide_alternate_screen()
            self.terminal.show_cursor()


def main():
    Demo().run()


if __name__ == "__main__":
    main()
