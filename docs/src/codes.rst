==============================================================
``pansi.codes`` -- Raw control characters and escape sequences
==============================================================

.. module:: pansi.codes


C0 control codes
================
TODO

.. seealso::
    - `Unicode C0 Controls and Basic Latin <https://www.unicode.org/charts/PDF/U0000.pdf>`_


C1 control codes
================
TODO


SGR sequences
-------------
Most modern terminal emulation software comes with the ability to colour and
style text. This functionality is accessed via particular a particular subset
of ANSI Escape sequences called Select Graphic Rendition (SGR) control
sequences. As defined here, the particular control characters involved are as
follows::

    # Escape (ESC)
    # ASCII and Unicode C0 control code at code point U+001B.
    ESC = "\x1B"

    # Control Sequence Introducer (CSI)
    # This is originally a C1 control code from extended ASCII, still available
    # at Unicode code point U+009B, but most typically implemented in its 7-bit
    # compatibility form, ESC followed by '['.
    CSI = f"{ESC}["

    # Select Graphic Rendition (SGR)
    # This is a parameterised CSI sequence, terminated with an 'm' character.
    # Parameters are stringified base-10 integer values, separated by
    # semicolons. The example below constructs the SGR colour selection sequence
    # for the web colour 'rebeccapurple'.
    params = [38, 2, 102, 51, 153]
    SGR = f"{CSI}{';'.join(map(str, params))}m"

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
TODO

.. seealso::
    - `Unicode 16.0.0 -- 5.8 Newline Guidelines <https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-5/#G10213>`_
