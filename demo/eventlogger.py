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


class EventLogger:

    def __init__(self):
        self.terminal = Terminal(full_screen=True, raw=True)
        self.terminal.add_event_listener("keypress", self.on_keypress)
        self.terminal.add_event_listener("resize", self.on_resize)

    def on_keypress(self, event):
        self.terminal.print(f"{event!r}")

    def on_resize(self, event):
        self.terminal.print(f"{event!r}")
        self.terminal.print(f"Terminal size = {self.terminal.get_size()!r}")

    def run(self):
        self.terminal.cursor.hide()
        try:
            self.terminal.loop(break_key="\x03")
        except KeyboardInterrupt:
            pass


def main():
    EventLogger().run()


if __name__ == "__main__":
    main()
