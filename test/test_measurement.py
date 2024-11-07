from unittest import TestCase

from pansi.text import Text


class ControlCharactersMeasurementTest(TestCase):

    def test_newlines_at_end(self):
        from pansi.codes import UNICODE_NEWLINES
        for newline in UNICODE_NEWLINES:
            with self.subTest(newline=newline):
                text = Text(f"abcdefg{newline}")
                expected = [
                    ((0, 1), 'a'), ((0, 1), 'b'), ((0, 1), 'c'), ((0, 1), 'd'),
                    ((0, 1), 'e'), ((0, 1), 'f'), ((0, 1), 'g'), ((1, -7), text[-1]),
                ]
                actual = list(zip(text.measurements, list(text)))
                self.assertEqual(actual, expected)

    def test_tabs(self):
        text = Text("\thello\tworld")
        expected = [
            ((0, 8), '\t'), ((0, 1), 'h'), ((0, 1), 'e'), ((0, 1), 'l'),
            ((0, 1), 'l'), ((0, 1), 'o'), ((0, 3), '\t'), ((0, 1), 'w'),
            ((0, 1), 'o'), ((0, 1), 'r'), ((0, 1), 'l'), ((0, 1), 'd'),
        ]
        actual = list(zip(text.measurements, list(text)))
        self.assertEqual(actual, expected)

    def test_tabs_and_newline(self):
        text = Text("\thello\tworld\n")
        expected = [
            ((0, 8), '\t'), ((0, 1), 'h'), ((0, 1), 'e'), ((0, 1), 'l'),
            ((0, 1), 'l'), ((0, 1), 'o'), ((0, 3), '\t'), ((0, 1), 'w'),
            ((0, 1), 'o'), ((0, 1), 'r'), ((0, 1), 'l'), ((0, 1), 'd'),
            ((1, -21), '\n'),
        ]
        actual = list(zip(text.measurements, list(text)))
        self.assertEqual(actual, expected)

    def test_c0_controls(self):
        from pansi.codes import \
            NUL, BEL, CAN, EM, SUB, ESC, \
            SOH, STX, ETX, EOT, ENQ, ACK, DLE, NAK, SYN, ETB, \
            SI, SO, \
            DC1, DC2, DC3, DC4, \
            FS, GS, RS, US
        zero_size_c0_controls = [
            NUL, BEL, CAN, EM, SUB, ESC,
            SOH, STX, ETX, EOT, ENQ, ACK, DLE, NAK, SYN, ETB,   # TC
            SI, SO,                                             # LS
            DC1, DC2, DC3, DC4,                                 # DC
            FS, GS, RS, US,                                     # IS
        ]
        for text in zero_size_c0_controls:
            with self.subTest(text=Text(text)):
                (line_advance, width), _ = next(measure(text))
                self.assertEqual(line_advance, 0)
                self.assertEqual(width, 0)

    def test_backspace(self):
        from pansi.codes import BS
        text = Text(BS)
        (line_advance, width), _ = next(measure(text))
        self.assertEqual(line_advance, 0)
        self.assertEqual(width, -1)

    def test_del(self):
        from pansi.codes import DEL
        text = DEL
        (line_advance, width), _ = next(measure(text))
        self.assertEqual(line_advance, 0)
        self.assertEqual(width, 0)
