=================================================================
``pansi.color`` -- Colour conversion and general colour functions
=================================================================

.. module:: pansi.color

The ``pansi.color`` module primarily defines functions for resolving colours
defined by various colour systems. Specifically, the functions here align
closely with the colour functions available in CSS, allowing both numeric and
percentage arguments (the latter expressed as strings).

All such functions allow an optional ``alpha`` argument to be passed,
denoting transparency, and return hex strings of the form ``'#RRGGBB'`` or
``'#RRGGBBAA'`` (depending on whether transparency was specified).

Beyond these, several general purpose functions that relate to colour
management and conversion are also included, along with a dictionary mapping
web colour names to (red, green, blue) component triples.

.. seealso:: For functions that apply colour to text, see the
    :py:mod:`pansi.text` module.


RGB
===
.. autofunction:: rgb
.. autofunction:: decode_hex_color

.. seealso::

    - `CSS Color Module Level 4 -- sRGB Colors <https://drafts.csswg.org/css-color/#numeric-srgb>`_


CSS Named Colors
================
.. data:: WEB_PALETTE

.. seealso::

    - `CSS Color Module Level 4 -- Color Keywords <https://drafts.csswg.org/css-color/#color-keywords>`_


HSL
===
.. autofunction:: hsl

.. seealso::

    - `CSS Color Module Level 4 -- HSL Colors <https://drafts.csswg.org/css-color/#the-hsl-notation>`_


HWB
===
.. autofunction:: hwb

.. seealso::

    - `CSS Color Module Level 4 -- HWB Colors <https://drafts.csswg.org/css-color/#the-hwb-notation>`_


CIE Lab, CIE LCH, Oklab, and Oklch
==================================
.. autofunction:: lab
.. autofunction:: lch
.. autofunction:: oklab
.. autofunction:: oklch

.. seealso::

    - `A perceptual color space for image processing (Oklab) <https://bottosson.github.io/posts/oklab/>`_

    - `CSS Color Module Level 4 -- Device-independent Colors <https://drafts.csswg.org/css-color/#lab-colors>`_
