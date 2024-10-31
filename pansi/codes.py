#!/usr/bin/env python3
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


# ------------- # -- # -- # ------------------------- # ---- # --------------------------------------------------------
# C0 control codes
# ------------- # -- # -- # ------------------------- # ---- # --------------------------------------------------------
NUL = "\x00"    # ^@ |    | null                      |      | does nothing
SOH = "\x01"    # ^A |    | start of header           | TC₁  | start of transmission header
STX = "\x02"    # ^B |    | start of text             | TC₂  | start of transmission content
ETX = "\x03"    # ^C |    | end of text               | TC₃  | SIGINT, end of transmission content
EOT = "\x04"    # ^D |    | end of transmission       | TC₄  | EOF, end of transmission
ENQ = "\x05"    # ^E |    | enquiry                   | TC₅  |
ACK = "\x06"    # ^F |    | acknowledge               | TC₆  |
BEL = "\x07"    # ^G | \a | bell                      |      | audio signal
BS = "\x08"     # ^H | \b | backspace                 | FE₀  | move cursor left 1 cell
HT = "\x09"     # ^I | \t | horizontal tab            | FE₁  | move cursor right to next multiple of 8
LF = "\x0A"     # ^J | \n | line feed                 | FE₂  | newline
VT = "\x0B"     # ^K | \v | vertical tab              | FE₃  |
FF = "\x0C"     # ^L | \f | form feed                 | FE₄  | clear
CR = "\x0D"     # ^M | \r | carriage return           | FE₅  | newline
SO = "\x0E"     # ^N |    | shift out                 | LS₀  |
SI = "\x0F"     # ^O |    | shift in                  | LS₁  |
DLE = "\x10"    # ^P |    | data link escape          | TC₇  |
DC1 = "\x11"    # ^Q |    | device control 1          | DC₁  | XON, resume transmission (e.g. buffer ready)
DC2 = "\x12"    # ^R |    | device control 2          | DC₂  |
DC3 = "\x13"    # ^S |    | device control 3          | DC₃  | XOFF, pause transmission (e.g. buffer full)
DC4 = "\x14"    # ^T |    | device control 4          | DC₄  |
NAK = "\x15"    # ^U |    | negative acknowledge      | TC₈  |
SYN = "\x16"    # ^V |    | synchronous idle          | TC₉  |
ETB = "\x17"    # ^W |    | end of transmission block | TC₁₀ | end of transmission block
CAN = "\x18"    # ^X |    | cancel                    |      |
EM = "\x19"     # ^Y |    | end of medium             |      |
SUB = "\x1A"    # ^Z |    | substitute                |      | SIGTSTP
ESC = "\x1B"    # ^[ |    | escape                    |      | escape sequence initiator
FS = "\x1C"     # ^\ |    | file separator            | IS₄  | delimiter, SIGQUIT
GS = "\x1D"     # ^] |    | group separator           | IS₃  | delimiter
RS = "\x1E"     # ^^ |    | record separator          | IS₂  | delimiter
US = "\x1F"     # ^_ |    | unit separator            | IS₁  | delimiter
# ------------- # -- # -- # ------------------------- # ---- # --------------------------------------------------------
# DEL only
# ------------- # -- # -- # ------------------------- # ---- # --------------------------------------------------------
DEL = "\x7F"              # delete                    |      |
# ------------- # -- # -- # ------------------------- # ---- # --------------------------------------------------------
# C1 control codes
# ------------------ # -- # --------------------------- # ---- # ------------------------------------------------------
PAD = f"{ESC}@"      # 80 | padding character           |      |
HOP = f"{ESC}A"      # 81 | high octet preset           |      |
BPH = f"{ESC}B"      # 82 | break permitted here        |      |
NBH = f"{ESC}C"      # 83 | no break here               |      |
IND = f"{ESC}D"      # 84 | index                       |      |
NEL = f"{ESC}E"      # 85 | next line                   |      |
SS2 = f"{ESC}N"      # 8E | single-shift 2              |      | en.wikipedia.org/wiki/ISO/IEC_2022#Shift_functions
SS3 = f"{ESC}O"      # 8F | single-shift 3              |
DCS = f"{ESC}P"      # 90 | device control string       |
SOS = f"{ESC}X"      # 98 | start of string             |
CSI = f"{ESC}["      # 9B | control sequence introducer |
ST = f"{ESC}\\"      # 9C | string terminator           |
OSC = f"{ESC}]"      # 9D | operating system command    |
PM = f"{ESC}^"       # 9E | privacy message             |
APC = f"{ESC}_"      # 9F | application program command |
# ------------------ # -- # --------------------------- # ---- # ------------------------------------------------------

# Translation table for C1 Control characters to equivalent 7-bit escape sequence.
#
# An 8-bit coded character in column 08 or 09 is equivalent to a 7-bit
# coded ESCAPE sequence consisting of ESC followed by the character from
# the corresponding row of columns 4 and 5 respectively.
#
# https://www.ecma-international.org/wp-content/uploads/ECMA-35_1st_edition_december_1971.pdf [8.2.2]
#
C1_CONTROL_TO_ESCAPE_SEQUENCE = str.maketrans(dict(zip(map(chr, range(0x80, 0xA0)),
                                                       (f"\x1B{chr(x)}" for x in range(0x40, 0x60)))))

# Other


# Newlines
#
# https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-5/#G10213
CRLF = f"{CR}{LF}"
C1_NEL = "\x85"
LS = "\u2028"
PS = "\u2029"
UNICODE_NEWLINES = {CR, LF, CRLF, NEL, C1_NEL, VT, FF, LS, PS}
