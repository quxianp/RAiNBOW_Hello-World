# Adding a template: the TeX and troff families

Eight entries that typeset rather than print, and the reason they are hard is
that *every one of them has no output operation*.

## The trap

`\print{Hello World!}` is not a thing in any of these. What they have instead is
a **typesetter**: a program describes a document, and a separate program -- pdfTeX,
troff, the TeX engine -- lays it out and produces the output. The greeting in a
TeX file is *content to typeset*, not a call to print.

Getting that distinction right is the difference between a file that compiles
and one that does not.

## The families

| entry | engine | its Hello World |
|---|---|---|
| TeX | pdfTeX / XeTeX / LuaTeX | `\documentclass{article}\begin{document}Hello World!\end{document}` |
| LaTeX | the macro layer on TeX | the same, and it is the common case |
| LaTeX Beamer | LaTeX with a presentation class | `\documentclass{beamer}\begin{document}\begin{frame}Hello World!\end{frame}\end{document}` |
| Typst | its own engine, modern syntax | `#set page(width: 10cm)\nHello World!` |
| troff / groff / nroff | the Unix typesetter | `.TH HELLO 1\n.SH NAME\nHello World!` |
| roff | the macro language troff reads | same as troff |
| scdoc | a man-page formatter | `hello(1)\n\n# NAME\n\nHello World!\n` |
| M4 | a macro preprocessor, not a typesetter | see below |

## The three shapes, and they are genuinely different

**A full document.** LaTeX needs `\documentclass` and `\begin{document}`. A file
with `Hello World!` in it and no document class does not compile, and the error
is about the end of the file rather than about the greeting.

**A man page.** troff's man macros are request macros on lines beginning with
`.`:

```troff
.TH HELLO 1
.SH NAME
Hello World!
```

That is the whole program. `.TH` sets the header and `.SH` starts a section, and
the greeting is the body of that section.

**A preprocessor.** M4 has no output at all in the printing sense: it is a macro
expander, and its "Hello World" is a macro whose *expansion* is the greeting:

```m4
define(`HELLO', `Hello World!')dnl
HELLO
```

`dnl` discards the rest of the line so the definition does not print itself,
which is the detail everybody forgets and which is why every M4 example starts
with it.

## Typst is the one worth knowing

Typst is a modern reimplementation with `{ }` for code, `#` before it, and no
mandatory preamble — the document is the file:

```typst
#set page(width: 10cm)
Hello World!
```

There is no `\begin{document}` and no document class. A Typst file with
`\documentclass` in it is a file that does not compile, and Typst's error messages
point at the backslash.

## Before you write one

- Does this engine require a preamble? LaTeX and troff-man do; Typst and scdoc
  do not.
- Is the greeting *content* or a *call*? In all eight it is content.
- Does the macro language print its own definitions? M4 does unless you say
  `dnl`.
- Does the format have a header structure that the greeting belongs in? A man
  page's greeting belongs under `.SH NAME`, not at the top of the file.