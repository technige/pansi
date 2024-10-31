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


def clamp(value, bounds):
    lower_bound, upper_bound = bounds
    if value:
        str_value = str(value).lower()
        if str_value == "none":
            num_value = 0
        else:
            percentage = str_value.endswith("%")
            str_value = str_value.rstrip("%")
            try:
                num_value = float(str_value)
            except ValueError:
                num_value = 0
            if percentage:
                num_value = (num_value / 100.0) * (upper_bound - lower_bound) + lower_bound
    else:
        num_value = 0
    return (lower_bound if num_value < lower_bound else
            upper_bound if num_value > upper_bound else
            num_value)


def linear_to_gamma(c):
    if c >= 0.0031308:
        return 1.055 * (c ** (1 / 2.4)) - 0.055
    else:
        return 12.92 * c
