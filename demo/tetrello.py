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

from pansi import Terminal, ANY_KEY


logo = """\
▀█▀ ▄▄ ▀█▀ ▄▄▄ █▀ ▄  █  ▄▄▄
 █  █   █  █ █ █  █  █  █ █
 █  █▄  █  █▄▀ █▀ █  █  █ █
 █  █   █  █ █ █  █  █  █ █
 ▀  █▄  ▀  █ █ ▀▀ █▄ ▀▀ █▄█
"""


class Tetrello:

    def __init__(self):
        self.terminal = Terminal()

    def title(self):
        screen = self.terminal.screen()  # TODO: declarative
        screen.paste(logo, display="block", align="center")
        screen.paste("Press any key to start", display="block", align="center")
        screen.render()

        def render(_event):
            screen.render()

        self.terminal.add_event_listener("resize", render)
        self.terminal.loop(break_key=ANY_KEY)
        self.terminal.remove_event_listener("resize", render)

    def play(self):
        self.terminal.screen()
        self.terminal.print("Main screen")
        self.terminal.print("Press [Q] to exit")
        self.terminal.loop(break_key=re_compile(r"[Qq]"))

    def run(self):
        try:
            self.title()
            self.play()
        except KeyboardInterrupt:
            pass
        finally:
            self.terminal.close()


def main():
    Tetrello().run()


if __name__ == "__main__":
    main()
