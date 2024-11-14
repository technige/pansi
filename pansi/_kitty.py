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


""" Functionality specific to the Kitty Terminal Emulator
"""

from re import compile as re_compile

from ._codes import APC, CSI, ST


def get_kitty_info(terminal):
    info = {}
    identifier = 31

    def on_apc(event):
        pattern = re_compile(r"\x1B_Gi=(\d+);([^\x1B]*)\x1B\\")
        match = pattern.match(event.key)
        if match and match.group(1) == str(identifier):
            info["kitty_graphics_protocol"] = match.group(2)

    terminal.add_event_listener("__apc__", on_apc)
    try:
        terminal.write(f"{APC}Gi={identifier},s=1,v=1,a=q,t=d,f=24;AAAA{ST}{CSI}c")
        terminal.flush()
        match = terminal.loop(until=re_compile(r"\x1B\[\?((\d*)(;(\d*))*)c"))
        if match:
            info["emulation_level"] = int(match.group(2))
        return info
    finally:
        terminal.remove_event_listener("__apc__", on_apc)
