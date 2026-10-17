# Adding a template: terminal output and control languages

Twenty-odd entries here exist to describe a terminal: the escape sequences, the
image protocols, the screen-addressing languages. They are the family this
repository's own demo is made of, so the standard they have to meet is the one
`run.sh` already passes.

## The trap

`print("Hello World!")` in a terminal-control language is almost always wrong,
because those languages do not print characters. They *move the cursor*, *set
attributes*, *address cells*, and *push and pop* saved state. Output is a side
effect of positioning.

## The families

| family | entry | what its Hello World is |
|---|---|---|
| cursor and screen control | ANSI escape codes, ECMA-48, VT52, VT100, VT220, xterm control sequences | the sequences themselves, with what each one does |
| truecolour and attributes | 24-bit colour, ANSI colour | an SGR sequence selecting a colour |
| inline images | Kitty graphics protocol, iTerm2 inline images, Sixel, iTerm inline image | the protocol's own handshake |
| character sets | Teletext, VT52 charset, PETSCII, CP437 | the bytes that switch the charset and print |

## The SGR sequence, worked out

The one everybody gets wrong by one is the colour code. `ESC [ … m` is *Select
Graphic Rendition*, and the numbers are additive bit flags:

```
ESC[1m        bold          0x01
ESC[4m        underline     0x04
ESC[7m        reverse       0x08
ESC[30m       black fg      30
ESC[31m       red fg        31
...
ESC[39m       default fg    39
ESC[40m       black bg      40
...
ESC[49m       default bg    49
ESC[0m        reset         0
```

So "red, bold, on white" is `ESC[31;1;47m` in one sequence and
`ESC[1m ESC[31m ESC[47m` in three, and the combined form is the one that is
worth showing because the parameter is a list and the *matters come first*:

```
printf '\033[1;38;2;255;0;127m'   # bold, truecolour RGB(255,0,127)
```

That is the escape `run.sh` uses to draw the rainbow, and the `38;2;r;g;b`
triple is the whole of truecolour: mode 2 means the components are 8-bit
values rather than an indexed palette entry.

## What the non-printing ones do

- **Cursor position** — `ESC[row;colH` is 1-based and origin-dependent.
- **Save and restore** — `ESC7` and `ESC8` (DECSC/DECRC), which is how `run.sh`
  keeps a prompt in place while a sweep is drawing over it.
- **Erase display** — `ESC[2J`, and `ESC[0K` to clear to end of line.
- **Scroll region** — `ESC[r;sr`, which is how a full-screen TUI avoids
  scrolling the scrollback.

A file whose content is "which of these do you want" is a description, and that
is a legitimate answer for an entry whose language *is* a description. But the
six SGR variants get real sequences, because an SGR sequence is a program.

## The image protocols

**Sixel** is the interesting one and also the one to be careful with. A Sixel
graphic is `ESC P q` … `ESC \\`, and inside it `?` re-introduces the colour
registers by index: `?` selects from a palette the terminal builds from `#n;2;r;g;b`
definitions. Getting the terminator wrong leaves the terminal in DCS state,
which is the same class of bug as the demo crash in E31 — an escape sequence
that was right in every visible way and left the screen wrong.

**Kitty graphics** and **iTerm2 inline images** are newer and much simpler:
transmit base64, then place. Both are "a greeting, as an image, above the
prompt", which is a legitimate Hello World and a slightly odd one — worth a
comment saying why the text version is not in the file.

## Before you write one

- Does the language print characters, or position them? Positioning is the
  common case and needs a sequence, not a `print`.
- Is the escape stateful? `ESC7` without `ESC8` and a final `ESC[0m` will be
  noticed.
- Is the greeting better as text than as an image? Sometimes yes, and then say
  why rather than emitting base64.
- For anything with a terminator, check the terminator. It is the byte nobody
  reviews and the byte the terminal remembers.