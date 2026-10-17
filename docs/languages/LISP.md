# Adding a template: the Lisp families

Ten-odd entries with "Lisp" in the name, and the differences between them are
where the work is.

## The trap

`(print "Hello World!")` is Common Lisp. It is not Scheme, where the idiom is
two expressions, and it is not Clojure, where `println` is a macro that appends
a newline you did not write.

| entry | its actual Hello World |
|---|---|
| Common Lisp / Standard Lisp | `(print "Hello World!")` |
| Scheme | `(display "Hello World!") (newline)` — two expressions |
| Racket | `#lang racket (displayln "Hello World!")` — the module matters |
| Clojure | `(println "Hello World!")` — a macro, and the newline is implicit |
| Emacs Lisp | runs in an editor with no standard output |
| ClojureScript | compiles to JavaScript; the source is Clojure |
| Emacs Lisp (interpreter form) | see above |

The Scheme two-expression form is the one people get wrong, because
`print` in Scheme does not add a newline and most Schemes have no `print` at
all. `display` then `newline` is the real answer and it is two lines for a
reason.

## Closely related, often confused

- **Racket** and **DrRacket** are the same language in two environments; DrRacket
  is the teaching environment, so its entry is an Racket program.
- **Clojure** and **ClojureScript** differ only in target, and Linguist counts
  them separately, so the same program appears twice. That is not duplication of
  effort — it is an honest description of what the repository contains.
- **Hy** is a Lisp that *looks like Python*: `(print "Hello World!")`, and it
  compiles to Clojure.
- **Fennel** and **Janet** are Lisps that compile to Lua and to C respectively.
- **Emacs Lisp** has no REPL in this repository's sense: it runs inside an editor.
  Its entry is a `princ` form.

## The trap with INHERIT

`INHERIT` exists for exactly this — dialects that share a parent's syntax. A
`Clojure EDN` file genuinely has Clojure's reader syntax. But `Scheme` and
`Common Lisp` share a parent *and* differ in output, so they must not inherit
each other, and `check_templates.py` keeps a list of the pairs that must not.

When in doubt: write the second program. It is four lines.

## Before you write one

- Does the language add a newline itself, or must you? That is the whole
  difference between `print`, `display` and `println`.
- Is there a module or `use` form the language requires?
- Does it run somewhere other than a terminal? If so, `display` is not available.