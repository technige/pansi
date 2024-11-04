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
from sys import stdin, stdout
from termios import tcgetattr, tcsetattr, TCSAFLUSH, TIOCGWINSZ
from tty import setcbreak

from pansi.codes import ESC, CSI


px = namedtuple("px", ["x", "y"])
ch = namedtuple("ch", ["x", "y"])


class Screen:

    @classmethod
    def wrapper(cls, func, *args, **kwargs):
        with Screen() as screen:
            return func(screen, *args, **kwargs)

    def __init__(self, cout=stdout, cin=stdin, cbreak=True, cursor=False):
        self._cout = cout
        self._cin = cin
        self._cbreak = cbreak
        self._cursor = cursor
        self._original_mode = None

    def _read_ss3(self, seq):
        while True:
            ch = self._cin.read(1)
            seq += ch
            if 0x40 <= ord(ch) <= 0x7E:
                break
        return seq

    def _read_csi(self, seq):
        while True:
            ch = self._cin.read(1)
            seq += ch
            if 0x40 <= ord(ch) <= 0x7E:
                break
        return seq

    def _read_esc(self, seq):
        ch = self._cin.read(1)
        seq += ch
        if ch == "[":
            return self._read_csi(seq)
        elif ch == "O":
            return self._read_ss3(seq)
        else:
            raise OSError(f"Unknown input sequence {seq!r}")

    def read_key(self):
        seq = ""
        ch = self._cin.read(1)
        seq += ch
        if ch == ESC:
            return self._read_esc(seq)
        else:
            return seq

    def read_response(self):
        seq = self.read_key()
        if seq.startswith(f"{ESC}["):
            args = tuple(map(int, seq[2:-1].split(";")))
            function = seq[-1]
            return args, function
        else:
            raise OSError(f"Unexpected response {seq!r}")

    @property
    def viewport_ch(self) -> ch:
        import struct
        import os
        try:
            # Create a buffer for the ioctl call
            buf = struct.pack('HHHH', 0, 0, 0, 0)

            # Make the ioctl call
            fd = os.open(os.ctermid(), os.O_RDONLY)
            result = ioctl(fd, TIOCGWINSZ, buf)
            os.close(fd)

            # Unpack the result
            lines, cols, _, _ = struct.unpack('HHHH', result)
        except OSError:
            # Fallback method using environment variables
            lines = int(os.environ.get('LINES', 24))
            cols = int(os.environ.get('COLUMNS', 80))
        return ch(x=cols, y=lines)

    @property
    def viewport_px(self) -> px:
        self._cout.write(f"{CSI}14t")
        self._cout.flush()
        args, function = self.read_response()
        if function == "t":
            if args[0] == 4:
                return px(x=args[2], y=args[1])
            else:
                raise OSError(f"Unexpected response {function!r} {args[0]!r}")
        else:
            raise OSError(f"Unexpected response {function!r}")

    @property
    def cell_px(self) -> px:
        self._cout.write(f"{CSI}16t")
        self._cout.flush()
        args, function = self.read_response()
        if function == "t":
            if args[0] == 6:
                return px(x=args[2], y=args[1])
            else:
                raise OSError(f"Unexpected response {function!r} {args[0]!r}")
        else:
            raise OSError(f"Unexpected response {function!r}")

    @property
    def cur_pos(self):
        self._cout.write(f"{CSI}6n")
        self._cout.flush()
        args, function = self.read_response()
        if function == "R":
            return args
        else:
            raise OSError(f"Unexpected response {function!r}")

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
        # self.keypad_on()

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

    # def keypad_on(self):
    #     self.cout.write(f"{CSI}?1h{ESC}=")
    #     self.cout.flush()

    # def keypad_off(self):
    #     self.cout.write(f"{CSI}?1l{ESC}>")
    #     self.cout.flush()

    def write(self, *values):
        for value in values:
            self._cout.write(str(value))

    def flush(self):
        self._cout.flush()
