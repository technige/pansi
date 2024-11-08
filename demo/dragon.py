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


from pansi.codes import black_bg, invert, reset
from pansi.text import color, background_color


print(f"""\
{color('#040')}{background_color('#0F0')} !"#$%&'()*+,-./0123456789:;<=>?
@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]↑←
{invert}@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]↑←{~invert}
{color('#0F0')}{black_bg} ▗▖▄▝▐▞▟▘▚▌▙▀▜▛█{color('#FF0')} ▗▖▄▝▐▞▟▘▚▌▙▀▜▛█
{color('#00F')} ▗▖▄▝▐▞▟▘▚▌▙▀▜▛█{color('#F00')} ▗▖▄▝▐▞▟▘▚▌▙▀▜▛█
{color('#FFF')} ▗▖▄▝▐▞▟▘▚▌▙▀▜▛█{color('#0FF')} ▗▖▄▝▐▞▟▘▚▌▙▀▜▛█
{color('#F0F')} ▗▖▄▝▐▞▟▘▚▌▙▀▜▛█{color('#FF8000')} ▗▖▄▝▐▞▟▘▚▌▙▀▜▛█{reset}""")
