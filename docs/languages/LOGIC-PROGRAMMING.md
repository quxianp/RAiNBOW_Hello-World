# Adding a template: the logic-programming family

Prolog, Mercury, Logtalk, Curry and a dozen dialects, plus the theorem provers
in `PROVERS-AND-SOLVERS.md`. One idea, and it is an idea about *direction*.

## The trap

Prolog has no `print` in its language proper. `write/1` is in the standard
library, and the *program* is a set of facts and rules. So the question "what is
Prolog's Hello World" is really two questions, and the answer to the first one
changes the second.

A Prolog program that says hello is:

```prolog
:- initialization(main).

main :-
    write('Hello World!'), nl.
```

`write` and `nl` are predicates in the library; `:- initialization(main)` is what
makes the program run it. The `:-` prefix means "directive at load time", and it
is the whole difference between a script and a file of rules.

## The variants are not interchangeable

| entry | dialect | its Hello World |
|---|---|---|
| Prolog | ISO, `write/1` | `main :- write('Hello World!'), nl.` |
| SWI-Prolog | SWI | `:- initialization(main).` + the same |
| GNU Prolog | gprolog | same, and it has a `main/0` convention of its own |
| Logtalk | Prolog + objects | same, plus `object(main).` |
| Mercury | typed Prolog | `:- module hello_world.` + `main` with a type signature |
| Curry | functional logic | `main = putStrLn "Hello World!"` — not Prolog at all |
| Prolog (visual) | **Prolog is a language of two-dimensional programs.** A `.pl` file is not source text; it is a diagram, and the connections *are* the syntax. There is no text form of this entry. |

## Mercury adds the thing that makes it a different language

Mercury is Prolog with a type system, and the type signature is not optional:

```mercury
:- module hello_world.
:- interface.

:- pred main(io::di) is det.

:- implementation.

:- import_module io.

main(IO) :-
    io.write_string("Hello World!", !, IO),
    io.nl(IO).
```

Three things a Prolog program does not have: a `module` declaration, a `pred`
declaration with mode annotations (`io::di` — deterministic, writes and doesn't
fail), and a `:- module` at all. A Mercury file without those compiles as
nothing.

**Curry is not Prolog at all.** It is functional programming with logic
variables, so its output is a function application, not a predicate call. Copying
a Prolog template into a Curry file produces something that parses.

## The two that cannot greet

**Gödel** and **Mercury** can print. **Visual Prolog** can print. But there are
logic languages in this repository whose whole point is to be a theorem and not
a program: `HORN`, `ALLPROO`, `Logtalk` in its logic-programming mode. Those get
an admission, not a fabricated predicate.

## Before you write one

- Is the entry a dialect of Prolog or a different language that shares Prolog's
  syntax? Curry, MiniKanren and LogicBlox are the latter.
- Does the language have an initialisation directive, or is the entry point a
  convention? Prolog has both; Mercury's is declared.
- Does it need a type signature? Mercury does, and omitting it means the file is
  a fragment rather than a program.
- Is it a language or a *diagram language*? Visual Prolog's `.pl` is a diagram,
  and no amount of careful text produces one.