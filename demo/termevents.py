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


from pansi import Terminal


class Demo:

    def __init__(self):
        self.terminal = Terminal()
        self.terminal.add_event_listener("keypress", self.on_keypress)
        self.terminal.add_event_listener("resize", self.on_resize)

    def on_keypress(self, data):
        self.terminal.write(f"Input event (data = {data!r})\n")
        self.terminal.flush()

    def on_resize(self, data):
        self.terminal.write(f"Resize event (data = {data!r})\n")
        self.terminal.flush()

    def run(self):
        self.terminal.hide_cursor()
        self.terminal.show_alternate_screen()
        try:
            self.terminal.set_cursor_position(0, 0)
            self.terminal.loop()
        except KeyboardInterrupt:
            pass
        finally:
            self.terminal.hide_alternate_screen()
            self.terminal.show_cursor()


def main():
    Demo().run()


if __name__ == "__main__":
    main()
