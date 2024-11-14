====================================
Pansi -- Text mode rendering library
====================================

Pansi is a text mode rendering library that is designed to be simple and
familiar to most Python programmers.
The root module contains most of the common functionality; several supporting
modules exist to provide additional functionality.

.. toctree::
    :maxdepth: 1
    :caption: Modules:

    text
    color
    image

.. toctree::
    :maxdepth: 1
    :caption: References:

    codes


.. module:: pansi

Control codes
-------------
Pansi provides predefined variables for all C0 and C1 control codes available
in ASCII and Unicode. These include :py:attr:`ESC`, which is most commonly
used to introduce a terminal escape sequence. For a full list of available
codes, visit the `Pansi control code reference <codes.html>`_.


CSI sequences
-------------
By far the most common C1 control character to encounter in the wild is
:py:attr:`CSI`. As per its name, this introduces control sequences that are
typically used to control the environment within a terminal or terminal
emulator. For example, the sequence ``f"{CSI}2J"`` can be used to clear the
screen.

The CSI function is typically identified by the final character of the
sequence. In the example above, this is ``'J'``. In between, a number of
stringified base-10 integer values are included, separated by semicolons.


SGR sequences
-------------
Most modern terminal emulation software comes with the ability to colour and
style text. This functionality is accessed via a particular subset
of CSI sequences called Select Graphic Rendition (SGR) control sequences.

SGR sequences use CSI function ``'m'``, so begin with ``CSI`` and end with
``'m'``. The example below constructs the SGR foreground colour selection
sequence for the web colour *rebeccapurple*:

    >>> params = [38, 2, 102, 51, 153]
    >>> f"{CSI}{';'.join(map(str, params))}m"
    '\x1b[38;2;102;51;153m'

SGR selections are grouped by the first parameter value. In the example above,
selection 38 allows selection of the foreground colour. The second parameter,
2, further clarifies that the colour should be determined by raw red, green and
blue colour channel values. The remaining three parameters are those channel
values in order.

The SGR mechanism also allows a limited ability to reset individual sections.
To reset the foreground colour back to its default, for example, a single
parameter with value 39 can be used.

.. autoclass:: SGR

.. data:: reset
.. data:: bold
.. data:: light
.. data:: italic
.. data:: underline
.. data:: blink
.. data:: invert
.. data:: line_through
.. data:: double_underline
.. data:: overline

.. data:: aqua
.. data:: black
.. data:: blue
.. data:: cyan
.. data:: fuchsia
.. data:: gray
.. data:: grey
.. data:: green
.. data:: lime
.. data:: magenta
.. data:: maroon
.. data:: navy
.. data:: olive
.. data:: purple
.. data:: red
.. data:: silver
.. data:: teal
.. data:: white
.. data:: yellow
.. data:: default_fg

.. data:: aqua_bg
.. data:: black_bg
.. data:: blue_bg
.. data:: cyan_bg
.. data:: fuchsia_bg
.. data:: gray_bg
.. data:: grey_bg
.. data:: green_bg
.. data:: lime_bg
.. data:: magenta_bg
.. data:: maroon_bg
.. data:: navy_bg
.. data:: olive_bg
.. data:: purple_bg
.. data:: red_bg
.. data:: silver_bg
.. data:: teal_bg
.. data:: white_bg
.. data:: yellow_bg
.. data:: default_bg


.. seealso::
    - `Unicode C1 Controls and Latin-1 Supplement <https://www.unicode.org/charts/PDF/U0080.pdf>`_
    - `XTerm Control Sequences -- Functions using CSI <https://invisible-island.net/xterm/ctlseqs/ctlseqs.html#h3-Functions-using-CSI-_-ordered-by-the-final-character_s_>`_


Newlines
========

.. data:: CRLF
.. data:: UNICODE_NEWLINES


.. seealso::
    - `Unicode 16.0.0 -- 5.8 Newline Guidelines <https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-5/#G10213>`_
