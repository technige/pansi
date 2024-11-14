#!/usr/bin/env python
# -*- encoding: utf-8 -*-

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


term = Terminal()
term.print(" !\"#$%&'()*+,-./0123456789:;<=>?", color="#040", background_color="#0F0")
term.print("@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]↑←", color="#040", background_color="#0F0")
term.print("@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]↑←", color="#0F0", background_color="#040")
for i, fg in enumerate(["#0F0", "#FF0", "#00F", "#F00", "#FFF", "#0FF", "#F0F", "#FF8000"]):
    term.print(" ▗▖▄▝▐▞▟▘▚▌▙▀▜▛█", color=fg, background_color="black", end=("" if i % 2 == 0 else "\n"))
