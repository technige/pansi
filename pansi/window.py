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
from queue import SimpleQueue
from sys import stdin, stdout
from termios import tcgetattr, tcsetattr, TCSAFLUSH, TIOCGWINSZ
from tty import setcbreak

from pansi.codes import CSI, ST, DCS, ESC, OSC, TerminalInput

xy = namedtuple("xy", ["x", "y"])


class Event:

    def __init__(self):
        pass

    def __repr__(self):
        return f"{type(self).__name__}()"


class InputEvent(Event):

    def __init__(self, data):
        super().__init__()
        self.data = data

    def __repr__(self):
        return f"{type(self).__name__}(data={self.data!r})"


class Dimensions:

    def __init__(self, /, xy_ch: (int, int), xy_px: (int, int)):
        self._x_ch = xy_ch[0]
        self._y_ch = xy_ch[1]
        self._x_px = xy_px[0]
        self._y_px = xy_px[1]

    def __repr__(self):
        return (f"<{type(self).__name__} "
                f"({self._x_ch}×{self._y_ch})ch "
                f"({self._x_px}×{self._y_px})px>")

    def __getitem__(self, unit) -> xy:
        unit = unit.lower()

        # Typographic measurements
        #
        #         <──1ch───>
        #         <───────1ic───────>
        #  ∧   ∧  ┌────────┬────────┐  ∧
        #  │   │  │   █    ┆        │  │
        #  │   │  │  █ █   ┆        │  │
        #  │   │  │ █   █  ┆        │  │
        #  │   │  │█     █ ┆███████ │  │
        # 1ch 1ic ├█┄┄┄┄┄█┄┼┄┄┄┄██┄┄┤ 1em ∧
        #  │   │  │███████ ┆   █    │  │  │
        #  │   │  │█     █ ┆ ██     │  │ 1ex
        #  │   │  │█     █ ┆███████ │  │  │
        #  │   │  │        ┆        │  │  │
        #  ∨   ∨  └────────┴────────┘  ∨  ∨
        #         <───────1em───────>
        #         <──1ex───>
        #
        if unit == "ch":
            return xy(self._x_ch, self._y_ch)
        elif unit == "ex":
            return xy(self._x_ch, self._y_ch * 2)
        elif unit in {"em", "cap", "ic", "lh"}:
            return xy(self._x_ch / 2, self._y_ch)

        # Pixel measurement
        if unit == "px":
            return xy(self._x_px, self._y_px)

        # Imperial measurements
        x_in = self._x_px / 96
        y_in = self._y_px / 96
        if unit == "in":
            return xy(x_in, y_in)
        elif unit == "pc":
            return xy(x_in * 6, y_in * 6)
        elif unit == "pt":
            return xy(x_in * 72, y_in * 72)

        # Metric measurements
        x_cm = x_in * 2.54
        y_cm = y_in * 2.54
        if unit == "cm":
            return xy(x_cm, y_cm)
        elif unit == "mm":
            return xy(x_cm * 10, y_cm * 10)
        elif unit == "q":
            return xy(x_cm * 40, y_cm * 40)

        raise KeyError(f"Unsupported unit {unit!r}")


class Window:

    @classmethod
    def wrapper(cls, func, *args, **kwargs):
        with Window() as window:
            return func(window, *args, **kwargs)

    def __init__(self, cin=stdin, cout=stdout, cbreak=True, cursor=False):
        self._input = TerminalInput(cin)
        self._cout = cout
        self._cbreak = cbreak
        self._cursor = cursor
        self._original_mode = None
        self._xtwinops_queue = SimpleQueue()  # TODO: lock
        self._event_listeners = {
            "XTWINOPS": [self._xtwinops_queue.put_nowait],
        }

    def __enter__(self):
        self.show()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.hide()

    def add_event_listener(self, event_type, listener):
        self._event_listeners.setdefault(event_type, []).append(listener)

    # @property
    # def size_ch(self) -> ch:
    #     import os
    #     import struct
    #     try:
    #         # Create a buffer for the ioctl call
    #         buf = struct.pack('HHHH', 0, 0, 0, 0)
    #
    #         # Make the ioctl call
    #         fd = os.open(os.ctermid(), os.O_RDONLY)
    #         result = ioctl(fd, TIOCGWINSZ, buf)
    #         os.close(fd)
    #
    #         # Unpack the result
    #         lines, cols, _, _ = struct.unpack('HHHH', result)
    #     except OSError:
    #         # Fallback method using environment variables
    #         lines = int(os.environ.get('LINES', 24))
    #         cols = int(os.environ.get('COLUMNS', 80))
    #     return ch(x=cols, y=lines)

    def _trigger_xtwinops_event(self, code):
        # TODO: lock queue
        try:
            self._cout.write(code)
            self._cout.flush()
            self._read_until_report()
            input_event = self._xtwinops_queue.get()
            return input_event
        finally:
            pass  # TODO: unlock queue

    @property
    def size(self) -> Dimensions:
        input_event = self._trigger_xtwinops_event(f"{CSI}14t")
        px_args = input_event.data[2:-1].split(";")
        input_event = self._trigger_xtwinops_event(f"{CSI}18t")
        ch_args = input_event.data[2:-1].split(";")
        return Dimensions(xy_ch=(int(ch_args[2]), int(ch_args[1])),
                          xy_px=(int(px_args[2]), int(px_args[1])))

    @property
    def cur_pos(self):
        input_event = self._trigger_xtwinops_event(f"{CSI}6n")
        args = tuple(map(int, input_event.data[2:-1].split(";")))
        return args[1], args[0]

    @cur_pos.setter
    def cur_pos(self, row_column):
        row, column = row_column
        self._cout.write(f"{CSI}{row};{column}H")

    def cursor_forward_tab(self, stops=1):
        self._cout.write(f"{CSI}{stops}I")

    def clear(self):
        self._cout.write(f"{CSI}H{CSI}2J")

    def show(self):
        if not self._cursor:
            self.hide_cursor()
        self._cout.write(f"{CSI}?1049h")
        self._cout.flush()
        self._original_mode = tcgetattr(self._cout)
        setcbreak(self._cout)
        # self.keypad_on()  # changes (e.g.) [UP] from f"{CSI}A" to f"{SS3}A"

    def hide(self):
        # self.keypad_off()
        tcsetattr(self._cout, TCSAFLUSH, self._original_mode)
        self._cout.write(f"{CSI}?1049l")
        self._cout.flush()
        self.show_cursor()

    def show_cursor(self):
        self._cout.write(f"{CSI}?25h")
        self._cout.flush()

    def hide_cursor(self):
        self._cout.write(f"{CSI}?25l")
        self._cout.flush()

    def keypad_on(self):
        self._cout.write(f"{CSI}?1h{ESC}=")
        self._cout.flush()

    def keypad_off(self):
        self._cout.write(f"{CSI}?1l{ESC}>")
        self._cout.flush()

    def write(self, *values):
        for value in values:
            self._cout.write(str(value))

    def flush(self):
        self._cout.flush()

    def _read_next(self):
        c = self._input.read(1)
        if c.startswith(CSI) and c[-1] in "cRt":
            event_type = "XTWINOPS"
            event = InputEvent(c)
        elif c.startswith(DCS) and c.endswith(ST):
            event_type = "XTWINOPS"  # actually, DEVICE CONTROL
            event = InputEvent(c)
        elif c.startswith(OSC) and c.endswith(ST):
            event_type = "XTWINOPS"  # actually, OPERATING SYSTEM COMMAND
            event = InputEvent(c)
        else:
            event_type = "keypress"
            event = InputEvent(c)
        for listener in self._event_listeners.get(event_type, []):
            if callable(listener):
                listener(event)
        return event_type

    def _read_until_report(self):
        while True:
            event_type = self._read_next()
            if event_type == "XTWINOPS":
                break

    def loop(self):
        while True:
            self._read_next()


class Demo:

    def __init__(self):
        self.window = Window()
        self.window.add_event_listener("keypress", self.on_key)

    def on_key(self, input_event):
        if input_event.data == "1":
            window_size = self.window.size
            self.window.write(f"Window size = {window_size['ch']!r}ch / {window_size['in']!r}in\n")
            self.window.flush()
        else:
            self.window.write(f"Received event {input_event!r}\n")
            self.window.flush()

    def run(self):
        self.window.show()
        try:
            self.window.cur_pos = (0, 0)
            self.window.loop()
        except KeyboardInterrupt:
            pass
        finally:
            self.window.hide()


def main():
    Demo().run()


if __name__ == "__main__":
    main()
