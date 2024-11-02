# Pansi

Pansi is a text mode rendering library. It provides a clean and simple
interface for working with text and graphics in the terminal, using ANSI escape
sequences for rendering. The library provides the following modules:

- `pansi.text` -- text colouring and styling
- `pansi.image` -- terminal-based image rendering
- `pansi.screen` -- full screen layout handling

Most modern terminals support ANSI rendering, but the exact feature sets
available do vary. Bear in mind that not every listed function might work in
every terminal, and check the documentation for your terminal software to make
sure.


## `pansi.text`

The `pansi.text` module provides a suite of functions for colouring and styling
terminal text, using ANSI escape sequences. Functions are designed to align as
closely as possible to CSS rules and properties, for ease of use.

### Colours

Let's start with something simple. The following example will render the word
"world" in green:

<pre style="color:silver;background-color:black"><code>&gt;&gt;&gt; from pansi.text import green
&gt;&gt;&gt; print(f"Hello, {green}world{~green}!")
Hello, <span style="color:green">world</span>!
</code></pre>
