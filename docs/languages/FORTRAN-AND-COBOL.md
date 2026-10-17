# Adding a template: the Fortran and COBOL families

Nine Fortran entries and four COBOL entries, because Linguist distinguishes them
per standard, and they are **not** interchangeable.

## The trap

The obvious move is one Fortran program, inherited across all nine. It is wrong in
five of them, and wrong in the way that is hard to see: a fixed-form program in
free-form F90 is not a Fortran program at all, and the columns it depends on are
exactly what free form removed.

| entry | form | what it actually is |
|---|---|---|
| Fortran 77 | fixed | `      PROGRAM HELLO` — six columns of margin, column 7 is the verb |
| Fortran 90, 95, 2003, 2008, 2018 | free | `program hello … end program hello` |
| Fortran IV | fixed | not a `WRITE` — a `READ`, a `FORMAT` and a `WRITE` |
| Modern Fortran, Intel Fortran | free | same as F90, which is why those two are separate entries at all |
| Fixed Form Fortran | fixed | same shape as 77, and a distinct Linguist name for it |
| Formative Fortran | fixed | the pre-1966 style, with its own `FORMAT` discipline |

## What each family actually wants

**Fixed form** is a card-punch layout that outlived its punch. Columns 1–6 are
the statement number, column 7 is the operation, and columns beyond 72 are
ignored. `WRITE(*,*)` is F77; `WRITE(6,10)` with a `FORMAT` is F77 too but
older.

**Free form** dropped all of that, so `print *,` and `end program` are correct.

**COBOL** is the same story with a different shape: free format, but
case-insensitive, with a division structure. The classic form is

```
       IDENTIFICATION DIVISION.
       PROGRAM-ID. HELLO.
       PROCEDURE DIVISION.
           DISPLAY "Hello World!".
           STOP RUN.
```

## FLOW-MATIC

IBM wrote COBOL, and FLOW-MATIC is what it was written *in* — an IBM report
generator with no loop control, structured as a page of verbs in columns. Its
program is a set of `DISPLAY` verbs and nothing else.

A Flow-MATIC program is best recorded as a comment block rather than as
half-remembered syntax. Misaligning a verb by one column produces something that
looks like the language and is not, which is the failure mode this repository's
whole template policy exists to avoid (see `docs/HOW-FILES-GET-THEIR-CONTENT.md`).

## Things worth knowing before you write one

- `FLOW-MATIC` is not a COBOL dialect you can reach by changing keywords.
- `UNIVAC 1103` Fortran is column-7 significant for the same reason and has a
  different `FORMAT` convention.
- Do not put a Fortran program in a `.mod` or `.work` file. Those are Go module
  declarations and they have no body.