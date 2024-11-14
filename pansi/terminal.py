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
from termios import TIOCGWINSZ
from time import monotonic

from pansi import CSI, APC, TerminalInput, TerminalOutput


CursorPosition = namedtuple("CursorPosition", ["line", "column"])
RectangularArea = namedtuple("RectangularArea", ["lines", "columns", "pixel_width", "pixel_height"])


class Terminal:

    def __init__(self, cin=stdin, cout=stdout):
        self._input = TerminalInput(cin)
        self._output = TerminalOutput(cout)
        self._event_listeners = {}
        signal(SIGWINCH, lambda _signal, _frame: self._dispatch_event("resize", self.get_size()))

    def add_event_listener(self, event_type, listener):
        self._event_listeners.setdefault(event_type, []).append(listener)

    def remove_event_listener(self, event_type, listener):
        try:
            listeners = self._event_listeners[event_type]
        except KeyError:
            pass  # no such event type
        else:
            try:
                listeners.remove(listener)
            except ValueError:
                pass  # no such listener

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
            if char_seq.startswith(APC):
                event_type = "__apc__"
            else:
                event_type = "keypress"
            self._dispatch_event(event_type, char_seq)
        return None

    def get_info(self):
        info = {}
        from ._kitty import get_kitty_info
        info.update(get_kitty_info(self))
        return info

    def get_size(self) -> RectangularArea:
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
            self._output.write(f"{CSI}18t")
            self._output.flush()
            match = self.loop(until=re_compile(r"\x1B\[8;(\d*);(\d*)t"), timeout=0.025)
            if match:
                lines = int(match.group(1))
                columns = int(match.group(2))
            else:
                lines = 24
                columns = 80
        if pixel_width == 0 and pixel_height == 0:
            self._output.write(f"{CSI}14t")
            self._output.flush()
            match = self.loop(until=re_compile(r"\x1B\[4;(\d*);(\d*)t"), timeout=0.025)
            if match:
                pixel_height = int(match.group(1))
                pixel_width = int(match.group(2))
            else:
                pixel_height = 16 * lines
                pixel_width = 8 * columns
        return RectangularArea(lines, columns, pixel_width, pixel_height)

    def get_cursor_position(self) -> CursorPosition:
        self._output.write(f"{CSI}6n")
        self._output.flush()
        match = self.loop(until=re_compile(r"\x1B\[(\d*);(\d*)R"), timeout=0.025)
        if match:
            return CursorPosition(line=int(match.group(1)), column=int(match.group(2)))
        else:
            raise OSError("Cursor position unavailable")

    def set_cursor_position(self, /, line, column):
        self._output.write(f"{CSI}{line};{column}H")

    def clear(self):
        self._output.write(f"{CSI}H{CSI}2J")

    def show_alternate_screen(self):
        self._output.write(f"{CSI}?1049h")
        self._output.flush()
        self._output.set_tty_mode("cbreak")

    def hide_alternate_screen(self):
        self._output.reset_tty_mode()
        self._output.write(f"{CSI}?1049l")
        self._output.flush()

    def show_cursor(self):
        self._output.write(f"{CSI}?25h")
        self._output.flush()

    def hide_cursor(self):
        self._output.write(f"{CSI}?25l")
        self._output.flush()

    # def keypad_on(self):
    #     self._cout.write(f"{CSI}?1h{ESC}=")
    #     self._cout.flush()

    # def keypad_off(self):
    #     self._cout.write(f"{CSI}?1l{ESC}>")
    #     self._cout.flush()

    def write(self, s, /, **style):
        self._output.write(s, **style)

    def flush(self):
        self._output.flush()

    def print(self, *objects, sep=' ', end='\n', flush=False, **style):
        """ Print one or more objects to the terminal output.

        This method is largely compatible with the builtin ``print`` function,
        missing only the `file` argument and supporting a number of additional
        keyword arguments.

        As with :py:func:`print`, all non-keyword arguments are converted to
        strings using :py:func:`str`, but also with styling applied if any
        `style` keywords are supplied.

        The full list of supported style keywords are documented as part of the
        :meth:`TerminalOutput.write` method, but include the following:

        - ``color``
        - ``background_color``
        - ``font_weight``
        - ``font_style``
        - ``text_decoration``

        :param objects:
        :param sep:
        :param end:
        :param flush:
        :param style:
        """
        for i, obj in enumerate(objects):
            if i > 0:
                self._output.write(sep)
            self._output.write(str(obj), **style)
        self._output.write(end)
        if flush:
            self._output.flush()

    def draw(self, image, /, method="auto"):
        raise NotImplementedError
