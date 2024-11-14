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


from os import path

from PIL import Image, ImageFont, ImageDraw

from pansi.color import WEB_PALETTE


# TODO: stop hard-coding this
FONTS = path.expanduser("~/fonts/ttf")


class Span:

    default_color = "silver"

    def __init__(self, text, /, **style):
        self.text = text
        self.style = style

    @property
    def color(self) -> (int, int, int):
        return WEB_PALETTE.get(self.style.get("color"), self.default_color)


class TextImage:

    def __init__(self):
        self.font = ImageFont.truetype(path.join("FONTS", "DejaVuSansMono.ttf"), 15)
        self.background_color = WEB_PALETTE.get("black")
        self.line_height = 20
        self.width = 80 * 10
        self.vertical_margin = 15
        self.horizontal_margin = 15

    def draw(self, text: [[str | Span]]) -> Image:
        width = self.width + (2 * self.horizontal_margin)
        height = len(text) * self.line_height + (2 * self.vertical_margin)
        img = Image.new("RGB", (width, height), self.background_color)
        draw = ImageDraw.Draw(img)
        y = self.vertical_margin
        for line in text:
            x = self.horizontal_margin
            for span in line:
                if isinstance(span, Span):
                    text = span.text
                    color = span.color
                else:
                    text = str(span)
                    color = Span.default_color
                draw.text((x, y), text, fill=color, font=self.font)
                x += draw.textlength(text, font=self.font)
            y += self.line_height
        return img


def main():
    text = [
        [">>> from pansi.text import green"],
        [">>> print(f\"Hello, {green}world{~green}!\")"],
        ["Hello, ", Span("world", color="green"), "!"],
    ]
    TextImage().draw(text).save("a.png")


if __name__ == "__main__":
    main()
