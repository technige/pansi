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


from collections import namedtuple
from fcntl import ioctl
from os import ctermid, open as os_open, close as os_close, O_RDONLY
from signal import signal, SIGWINCH
from struct import pack, unpack
from re import compile as re_compile
from sys import stdin, stdout
from termios import tcgetattr, tcsetattr, TCSAFLUSH, TIOCGWINSZ
from time import monotonic
from tty import setcbreak

from pansi import CSI, TerminalInput


pos = namedtuple("pos", ["line", "column"])
rect = namedtuple("rect", ["lines", "columns", "pixel_width", "pixel_height"])


class Terminal:

    def __init__(self, cin=stdin, cout=stdout):
        self._input = TerminalInput(cin)
        self._cout = cout
        self._normal_mode = None        # used to store mode when switching to alternate screen
        self._event_listeners = {}
        signal(SIGWINCH, lambda _signal, _frame: self._dispatch_event("resize", self.get_size()))

    def add_event_listener(self, event_type, listener):
        self._event_listeners.setdefault(event_type, []).append(listener)

    def remove_event_listener(self):
        raise NotImplementedError

    def _dispatch_event(self, event_type, data):
        for listener in self._event_listeners.get(event_type, []):
            if callable(listener):
                listener(data)

    def loop(self, /, until=None, timeout=None):
        t0 = monotonic()
        remaining = timeout
        while timeout is None or remaining >= 0:
            if timeout is None:
                char_seq = self._input.read(1)
            else:
                elapsed = monotonic() - t0
                remaining = timeout - elapsed
                if self._input.wait(timeout=max(0, remaining)):
                    char_seq = self._input.read(1)
                else:
                    break
            if until:
                match = until.match(char_seq)
                if match:
                    # print(f"Found match after {monotonic() - t0}s")
                    return match
            # TODO: handle mouse events separately, if possible
            self._dispatch_event("keypress", char_seq)
        return None

    def get_size(self) -> rect:
        try:
            buffer = pack('HHHH', 0, 0, 0, 0)
            fd = os_open(ctermid(), O_RDONLY)
            result = ioctl(fd, TIOCGWINSZ, buffer)
            os_close(fd)
        except OSError:
            lines, columns, pixel_width, pixel_height = 0, 0, 0, 0
        else:
            lines, columns, pixel_width, pixel_height = unpack('HHHH', result)
        if lines == 0 and columns == 0:
            self._cout.write(f"{CSI}18t")
            self._cout.flush()
            match = self.loop(until=re_compile(r"\x1B\[8;(\d*);(\d*)t"), timeout=0.025)
            if match:
                lines = int(match.group(1))
                columns = int(match.group(2))
            else:
                lines = 24
                columns = 80
        if pixel_width == 0 and pixel_height == 0:
            self._cout.write(f"{CSI}14t")
            self._cout.flush()
            match = self.loop(until=re_compile(r"\x1B\[4;(\d*);(\d*)t"), timeout=0.025)
            if match:
                pixel_height = int(match.group(1))
                pixel_width = int(match.group(2))
            else:
                pixel_height = 16 * lines
                pixel_width = 8 * columns
        return rect(lines, columns, pixel_width, pixel_height)

    def get_cursor_position(self) -> pos:
        self._cout.write(f"{CSI}6n")
        self._cout.flush()
        match = self.loop(until=re_compile(r"\x1B\[(\d*);(\d*)R"), timeout=0.025)
        if match:
            return pos(line=int(match.group(1)), column=int(match.group(2)))
        else:
            raise OSError("Cursor position unavailable")

    def set_cursor_position(self, /, line, column):
        self._cout.write(f"{CSI}{line};{column}H")

    def clear(self):
        self._cout.write(f"{CSI}H{CSI}2J")

    def show_alternate_screen(self):
        self._cout.write(f"{CSI}?1049h")
        self._cout.flush()
        self._normal_mode = tcgetattr(self._cout)
        setcbreak(self._cout)

    def hide_alternate_screen(self):
        tcsetattr(self._cout, TCSAFLUSH, self._normal_mode)
        self._cout.write(f"{CSI}?1049l")
        self._cout.flush()

    def show_cursor(self):
        self._cout.write(f"{CSI}?25h")
        self._cout.flush()

    def hide_cursor(self):
        self._cout.write(f"{CSI}?25l")
        self._cout.flush()

    # def keypad_on(self):
    #     self._cout.write(f"{CSI}?1h{ESC}=")
    #     self._cout.flush()

    # def keypad_off(self):
    #     self._cout.write(f"{CSI}?1l{ESC}>")
    #     self._cout.flush()

    def write(self, *values):
        for value in values:
            self._cout.write(str(value))

    def flush(self):
        self._cout.flush()


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
