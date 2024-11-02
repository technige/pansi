==========================================
``pansi.text`` -- Coloured and styled text
==========================================

.. module:: pansi.text


SGR sequences
=============
Most modern terminal emulation software comes with the ability to colour and
style text. This functionality is accessed via particular a particular subset
of ANSI Escape sequences called Select Graphic Rendition (SGR) control
sequences. As defined in :mod:`pansi.codes`, the particular control characters
involved are as follows::

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

.. autodata:: reset
.. autoclass:: SGR

.. seealso::
    - `Unicode C0 Controls and Basic Latin <https://www.unicode.org/charts/PDF/U0000.pdf>`_
    - `Unicode C1 Controls and Latin-1 Supplement <https://www.unicode.org/charts/PDF/U0080.pdf>`_
    - `XTerm Control Sequences -- Functions using CSI <https://invisible-island.net/xterm/ctlseqs/ctlseqs.html#h3-Functions-using-CSI-_-ordered-by-the-final-character_s_>`_


Terminal colours and CGA
========================
.. autodata:: CGA_PALETTE


Text objects
============
.. autoclass:: Text


Font weight
===========
.. autofunction:: font_weight
.. data:: bold
.. data:: light


Font style
==========
.. autofunction:: font_style
.. data:: italic


Text decoration
===============
.. autofunction:: text_decoration
.. data:: underline
.. data:: line_through
.. data:: double_underline
.. data:: overline
.. data:: blink


Colour
======

SGR generators
--------------
.. data:: invert
.. autofunction:: color_sgr

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

.. data:: on_aqua
.. data:: on_black
.. data:: on_blue
.. data:: on_cyan
.. data:: on_fuchsia
.. data:: on_gray
.. data:: on_grey
.. data:: on_green
.. data:: on_lime
.. data:: on_magenta
.. data:: on_maroon
.. data:: on_navy
.. data:: on_olive
.. data:: on_purple
.. data:: on_red
.. data:: on_silver
.. data:: on_teal
.. data:: on_white
.. data:: on_yellow

Escape sequence generators
--------------------------
.. autofunction:: color
.. autofunction:: background_color
