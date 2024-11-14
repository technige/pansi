from io import StringIO
from unittest import TestCase

from pansi import TerminalOutput


def decorate(text, **style):
    sio = StringIO()
    to = TerminalOutput(sio)
    to.write(text, **style)
    return sio.getvalue()


class TerminalOutputTest(TestCase):

    def test_styled_output(self):
        self.assertEqual(
            decorate("H2O", color="blue", vertical_align="sub"),
            "\x1b[94mH₂O\x1b[0m")

    def test_multiline_output(self):
        self.assertEqual(
            decorate("one\ntwo", color="red"),
            "\x1b[91mone\x1b[0m\n\x1b[91mtwo\x1b[0m")
