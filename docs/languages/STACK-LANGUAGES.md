# Adding a template: stack and concatenative languages

PostScript, Forth, Factor and a handful of others, plus the sixty golfing
languages covered in `GOLF.md`. The shared idea is a stack: you push values and
you consume them, and there is no local variable to print from.

## The trap

`print("Hello World!")` is a statement in a language with a store of variables.
Every language in this family has a *stack*, and the question a Hello World has
to answer is "how does a value get from the stack to the screen", which is a
different question in each one.

## The four shapes

**Forth: `EMIT` on a stack of character codes.**

```forth
: HELLO 72 101 108 108 111 32 87 111 114 108 100 33 EMIT ;
```

`EMIT` takes one character code off the stack and writes it. There is no string
type in Forth, which is why the whole program is a colon definition that pushes
twelve numbers and calls `EMIT` twelve times — and why a Forth Hello World is
*longer* than a C one. That is correct, not a mistake.

A shorter variant pushes a string and walks it, which needs `EACH` and a string
literal the dialect has to support:

```forth
: HELLO S" Hello World!" TYPE ;
```

**PostScript: `show` on a string already on the stack.**

```postscript
/Helvetica findfont 24 scalefont setfont
72 720 moveto (Hello World!) show
```

Two details. `show` prints the string, and it is not a print function — you must
have the string on the stack, and PostScript has no string *literal* in the
program text sense, only `(...)` which pushes one. And `moveto` sets the current
point, because PostScript has no cursor model at all: it draws.

**Factor: `print` with a string on the quotation's output.**

```factor
"Hello World!" print
```

Factor does have strings and does have `print`. It is the friendliest member of
this family and its program is four words.

**J and APL** are in `APL-FAMILY.md`, and Forth's descendants — JForth,
ANS Forth, Forth-83 — differ in which standard library words exist, not in the
shape.

## The two PostScript traps

**The font.** `show` with no font set uses whatever the current graphics state
has, and the graphics state is a *dictionary* you may not have. A PostScript
program that starts with `show` prints nothing visible on some interpreters. So
the font and the size come first.

**The parentheses are literal.** `(Hello World!)` pushes a string, and
parentheses inside it have to be escaped by doubling. A greeting with an
apostrophe in it is not a PostScript greeting.

## Why Forth is long, and why that is the answer

The instinct is to reach for `S" …"` and assume it works. It does not in ANSI
Forth: `S"` is not in the 1994 core standard, it is a common *extension*, and
whether a given Forth has it decides whether that Hello World runs.

The version that cannot fail is the twelve-number `EMIT` definition, because
`EMIT`, `:`, `;` and the number literals are in every Forth there is. Writing
the long one and saying why is more useful than writing the short one and hoping.

## Before you write one

- Does this language have strings, or is everything a character code? Forth
  does not have strings.
- What is the output operation — `EMIT`, `TYPE`, `show`, `print`, or `GET`?
- Does the output operation need something set up first? PostScript needs a font
  and a current point; Forth needs nothing.
- Is the word you are about to use in the standard, or a dialect extension? For
  Forth and PostScript that is the whole question.
- Does it draw rather than print? PostScript does. Then the program is a drawing
  and the greeting is text placed on it.