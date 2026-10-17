# Adding a template: APL, J and their descendants

Six entries, all of them array languages with a stack-shaped or tacit
programming model, and all of them with an output operation that is not called
anything you'd guess.

## The trap

APL writes right to left, and so do its descendants. A Hello World written
left to right is not a Hello World; it is a program that does nothing, because
the expression is read from the right. Every APL-family program on this
repository's language bar has to be written backwards, and that is the single
thing that distinguishes them from everything else in `hello/`.

## APL's actual output operation

APL's output is `⎕←` — quad-left-arrow — which displays the value assigned to
it:

```apl
⎕←'Hello World!'
```

Read right to left, because APL does: a character-matrix literal, then `⎕←`,
which displays it. There is no `print`, no `printf`, and no implicit echo you can
rely on — a bare literal at the top level happens to be echoed by most
interpreters, but relying on that is relying on an implementation detail rather
than on the language, and a file in this repository should not.

The shape `value ← ⎕← expression` — assign *and* display — is the idiomatic one,
because it keeps the value available:

```apl
greeting ← ⎕← 'Hello World!'
```

## The families

| entry | reads | output operation | its Hello World |
|---|---|---|---|
| APL | right to left | `⎕←` | `⎕←'Hello World!'` |
| Dyalog APL | right to left | `⎕←` | the same; it is Dyalog's dialect of APL |
| J | right to left | `echo` | `echo 'Hello World!'` |
| K | right to left | **none** | a comment: K is a function library |
| q / kdb+ | right to left, SQL-like | the REPL echoes each statement | `"Hello World!"` |
| kdb+ | as q | as q | `"Hello World!"` |

## J is the one to get right

J's output is `echo`, which is monadic and dyadic:

```j
   echo 'Hello World!'
```

The monadic form prints and returns its argument, which is what makes it usable
in a pipeline. The dyadic form prints two things and returns a list. That
detail is the only reason `echo` and not something else.

**K has no output operation at all.** It is a dialect of APL used as a
function library — `.k` files define functions and are loaded into a REPL. So a
K entry's greeting is a comment, and the comment should say K has no output
rather than inventing one. This is the qshape of `CSP` and `Surface code`, and
it is the correct answer.

**q is SQL wearing a programming language's syntax.** Its statements read right
to left like everything else in the family, and the REPL prints the result of
each one:

```q
"Hello World!"
```

That is a complete q program. No function, no assignment, no semicolon.

## The thing that catches everyone

**Array languages have no strings.** `⌈⌈` is a character matrix and `'Hello
World!'` is a character matrix, and a character matrix is not a string — so a
"greeting" in APL is a 12-by-1 matrix of characters and the interesting question
is not whether you can build it but how you display it.

Where you get the characters from varies by dialect and is worth not guessing:
`↑` upcases and takes, `'abc'` is a literal, `⎕UCS` is Unicode in Dyalog and
absent elsewhere. Getting it wrong produces a program that displays nothing at
all, which is why the files here use the literal and explain why.

## Before you write one

- Does this dialect read right to left? All six do.
- What is the output operation — `⎕←`, `echo`, `q)`, or none?
- Is it a dialect or a different language? Dyalog APL is a dialect; K is a
  different language with no output.
- Does it have strings, or character matrices? It has character matrices.