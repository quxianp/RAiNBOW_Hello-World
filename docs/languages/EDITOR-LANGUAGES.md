# Adding a template: the editor languages

Half a dozen entries here that do not run in a terminal at all. They are loaded
by a program — an editor — and their output is a side effect of editing: a
buffer, a status line, a message area.

## The trap

`print("Hello World!")` in Emacs Lisp or Vim script is a program that runs, but
not one that greets anybody. In both languages the conventional way to say
something is to a *display*, and the display belongs to a window that may not
exist.

## The entries

| entry | loaded by | its Hello World |
|---|---|---|
| Emacs Lisp | Emacs | a `message` form |
| Emacs Lisp (mode) | `define-derived-mode` | a mode definition whose `body` is the greeting |
| Vim script | Vim | a function, or `echom` |
| Vim Snippet | Vim | a snippet expansion with `$1` placeholders |
| Vim Help File | `vimdoc` | a help file: tags, then the text |
| TextMate Properties | TextMate/Sublime | a property list for a scope |

## `message` and `echom` are the right answers, and the difference is real

**Emacs Lisp** has `message`, which writes to the echo area, and `princ`, which
writes to a stream — and the standard is that a function *returns* a string and
lets the caller display it. A minimal Emacs Lisp program:

```elisp
(message "Hello World!")
```

`princ` is used when the return value matters and the message does not. For a
Hello World, `message` is the honest choice: it is the thing a person sees.

**Vim script** has `echom` for the message line and `echo` for the same, plus
`echohl` to highlight it. The one nobody remembers is that `:echo` output goes
into the message history, which makes it the one to use when you want to see it
after the redraw.

## A derived mode is not a program

An Emacs Lisp *mode* entry is not a script you run. It is a definition that runs
when a file is opened:

```elisp
(define-derived-mode hello-mode
  fundamental-mode "Hello"
  "A mode that says hello."
  (interactive)
  (message "Hello World!"))
```

The `body` is where the greeting goes and the docstring is where the mode's
name belongs. Writing a `main`-style program into a mode entry produces a file
that loads without doing anything visible, which is the same failure as the Opsin
case in a different disguise.

## Vim help files have a required first line

A `:help` file is not free text. It has a **tag line** in double quotes, and
help finds it there:

```
*hello.txt*    A file that greets you

==============================================================================
CONTENTS                                                *hello-contents*

    1. Introduction ................................ |hello-introduction|

==============================================================================
1. INTRODUCTION                                     *hello-introduction*

Hello World!                                                        *hello-hello*
```

Two tags on that last line, one for the section and one for the subject, and
the alignment matters because the tags are what jump. A vimdoc file without a
tag line is a file `:help` will not open.

## Snippets are templates, and the greeting goes in the body

A Vim snippet is a snippet file with a `${1:default}` placeholder:

```vim
snippet hello "Hello World!" b
Hello World!${1}
endsnippet
```

The `b` is the trigger letter. That is the whole format: a header, the text, an
`endsnippet`. No output operation, because expanding a snippet *is* the output.

## Before you write one

- Which program loads this file, and is it running when the file is opened?
- Is the greeting a message to a user, or a return value? `message` and `echom`
  are messages; `princ` is a value.
- Does the file have a required header — a tag line, a trigger letter, a mode
  name? Those are not decoration.
- Would the file do anything visible at all if loaded? If not, it is a snippet,
  a help file or a mode, and the file should say which.