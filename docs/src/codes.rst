============================
Pansi control code reference
============================

.. module:: pansi
    :no-index:

This page provides a full listing of all available control code values.


C0 control codes, SPACE and DELETE
==================================

====  =============  =========================  ======  =========  =======
Code  Attribute      ASCII/Unicode Name         Caret   Backslash  Standard
----  -------------  -------------------------  ------  ---------  -------
00    .. data:: NUL  NULL                       ``^@``
01    .. data:: SOH  START OF HEADING           ``^A``
02    .. data:: STX  START OF TEXT              ``^B``
03    .. data:: ETX  END OF TEXT                ``^C``
04    .. data:: EOT  END OF TRANSMISSION        ``^D``
05    .. data:: ENQ  ENQUIRY                    ``^E``
06    .. data:: ACK  ACKNOWLEDGE                ``^F``             ECMA-48 § 8.3.1
07    .. data:: BEL  BELL                       ``^G``  ``\a``     ECMA-48 § 8.3.3
08    .. data:: BS   BACKSPACE                  ``^H``  ``\b``     ECMA-48 § 8.3.5
09    .. data:: HT   HORIZONTAL TABULATION      ``^I``  ``\t``
0A    .. data:: LF   LINE FEED                  ``^J``  ``\n``
0B    .. data:: VT   VERTICAL TABULATION        ``^K``  ``\v``
0C    .. data:: FF   FORM FEED                  ``^L``  ``\f``
0D    .. data:: CR   CARRIAGE RETURN            ``^M``  ``\r``
0E    .. data:: SO   SHIFT OUT                  ``^N``
0F    .. data:: SI   SHIFT IN                   ``^O``
10    .. data:: DLE  DATA LINK ESCAPE           ``^P``
11    .. data:: DC1  DEVICE CONTROL ONE         ``^Q``
12    .. data:: DC2  DEVICE CONTROL TWO         ``^R``
13    .. data:: DC3  DEVICE CONTROL THREE       ``^S``
14    .. data:: DC4  DEVICE CONTROL FOUR        ``^T``
15    .. data:: NAK  NEGATIVE ACKNOWLEDGE       ``^U``
16    .. data:: SYN  SYNCHRONOUS IDLE           ``^V``
17    .. data:: ETB  END OF TRANSMISSION BLOCK  ``^W``
18    .. data:: CAN  CANCEL                     ``^X``
19    .. data:: EM   END OF MEDIUM              ``^Y``
1A    .. data:: SUB  SUBSTITUTE                 ``^Z``
1B    .. data:: ESC  ESCAPE                     ``^[``
1C    .. data:: FS   FILE SEPARATOR             ``^\``
1D    .. data:: GS   GROUP SEPARATOR            ``^]``
1E    .. data:: RS   RECORD SEPARATOR           ``^^``
1F    .. data:: US   UNIT SEPARATOR             ``^_``
20    .. data:: SP   SPACE
7F    .. data:: DEL  DELETE                     ``^?``
====  =============  =========================  ======  =========  =======

.. seealso::
    - `Unicode C0 Controls and Basic Latin <https://www.unicode.org/charts/PDF/U0000.pdf>`_
    - `Unicode Name Aliases <https://www.unicode.org/Public/UCD/latest/ucd/NameAliases.txt>`_


C1 control codes
================
C1 control codes occupy code points U+0080 to U+009F inclusive in Unicode, and
the same codes in some 8-bit extensions of ASCII. But as the availability of
these code points is not as ubiquitous as the C0 control codes, each comes
with a 7-bit alternative sequence. These take the form of escape
sequences, where the second character is in the range U+0040 to U+005F
inclusive. The module level attributes listed below all resolve to the

====  =============  ========================================  ==========  =======
Code  Attribute      ASCII/Unicode Name                        Escape      Standard
----  -------------  ----------------------------------------  ----------  -------
80    .. data:: PAD  PADDING CHARACTER                         ``{ESC}@``
81    .. data:: HOP  HIGH OCTET PRESET                         ``{ESC}A``
82    .. data:: BPH  BREAK PERMITTED HERE                      ``{ESC}B``  ECMA-48 § 8.3.4
83    .. data:: NBH  NO BREAK HERE                             ``{ESC}C``
84    .. data:: IND  INDEX                                     ``{ESC}D``
85    .. data:: NEL  NEXT LINE                                 ``{ESC}E``
86    .. data:: SSA  START OF SELECTED AREA                    ``{ESC}F``
87    .. data:: ESA  END OF SELECTED AREA                      ``{ESC}G``
88    .. data:: HTS  HORIZONTAL TABULATION SET                 ``{ESC}H``
89    .. data:: HTJ  HORIZONTAL TABULATION WITH JUSTIFICATION  ``{ESC}I``
8A    .. data:: VTS  VERTICAL TABULATION SET                   ``{ESC}J``
8B    .. data:: PLD  PARTIAL LINE DOWN                         ``{ESC}K``
8C    .. data:: PLU  PARTIAL LINE UP                           ``{ESC}L``
8D    .. data:: RI   REVERSE INDEX                             ``{ESC}M``
8E    .. data:: SS2  SINGLE SHIFT TWO                          ``{ESC}N``
8F    .. data:: SS3  SINGLE SHIFT THREE                        ``{ESC}O``
90    .. data:: DCS  DEVICE CONTROL STRING                     ``{ESC}P``  ECMA-48 § 8.3.27
91    .. data:: PU1  PRIVATE USE ONE                           ``{ESC}Q``
92    .. data:: PU2  PRIVATE USE TWO                           ``{ESC}R``
93    .. data:: STS  SET TRANSMIT STATE                        ``{ESC}S``
94    .. data:: CCH  CANCEL CHARACTER                          ``{ESC}T``
95    .. data:: MW   MESSAGE WAITING                           ``{ESC}U``
96    .. data:: SPA  START OF PROTECTED AREA                   ``{ESC}V``
97    .. data:: EPA  END OF PROTECTED AREA                     ``{ESC}W``
98    .. data:: SOS  START OF STRING                           ``{ESC}X``  ECMA-48 § 8.3.128
99    .. data:: SGC  SINGLE GRAPHIC CHARACTER INTRODUCER       ``{ESC}Y``
9A    .. data:: SCI  SINGLE CHARACTER INTRODUCER               ``{ESC}Z``
9B    .. data:: CSI  CONTROL SEQUENCE INTRODUCER               ``{ESC}[``
9C    .. data:: ST   STRING TERMINATOR                         ``{ESC}\``
9D    .. data:: OSC  OPERATING SYSTEM COMMAND                  ``{ESC}]``  ECMA-48 § 8.3.89
9E    .. data:: PM   PRIVACY MESSAGE                           ``{ESC}^``  ECMA-48 § 8.3.94
9F    .. data:: APC  APPLICATION PROGRAM COMMAND               ``{ESC}_``  ECMA-48 § 8.3.2
====  =============  ========================================  ==========  =======

.. data:: C1_CONTROL_TO_ESC_SEQUENCE

    A translation table for use with :py:func:`str.translate` that maps C1
    control characters to their 7-bit escape sequence alternatives.


Newlines
========

.. data:: CRLF
.. data:: UNICODE_NEWLINES


.. seealso::
    - `Unicode 16.0.0 -- 5.8 Newline Guidelines <https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-5/#G10213>`_
