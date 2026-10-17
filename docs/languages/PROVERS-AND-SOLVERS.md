# Adding a template: provers, model checkers and solvers

Three families that look alike on the language bar and behave nothing alike when
you try to make them print.

## The trap

Every one of these has no output statement. `print("Hello World!")` in Agda, in
MiniZinc, or in Michelson is a program in a language that does not exist, and it
looks fine until someone tries to run it.

The honest answer in each case is what the language actually offers.

## Theorem provers

A proof assistant's "program" is a term of a type. That *is* the content.

| language | what its Hello World is |
|---|---|
| Coq, Lean, Idris, Agda | a definition or a theorem statement |
| Agda | a module plus the signature it needs — `postulate putStrLn : String -> IO {()}` |
| Isabelle | `val "Hello World!" = verbatim (Output.output_text)` |
| HOL4 | `val () = print "Hello World!\n";` |
| Nuprl | a Coq definition, because Nuprl is MetaCoq |
| Curry-Howard | a typed value: the correspondence says a proof *is* a term |
| Higher-Rank | a typed value in a type-and-effect system |

The Agda case is the one that trips people. There is no `print` in Agda, so a
real program has to *postulate* one. Writing the postulate is the honest thing,
and it is what Agda's own test suite does.

## Model checkers

A model checker explores a state space and answers a question. There is no
program to write and no result to print.

- **NuSMV** — an `INVARSPEC`. That is the whole output mechanism.
- **Alloy** — a signature and a `fact`. The assertion is the answer.
- **SMT** — `declare-fun`, `assert`, `check-sat`.
- **SMT-LIB** is the syntax, so `Alloy` and `SMT` are close relatives and are
  recorded separately because Linguist counts them separately.

## Constraint solvers

MiniZinc *does* have output, and it is not a print:

```minizinc
include "gecode.mzn";

predicate greet() = true;

solve satisfy;

output ["Hello World!\n"];
```

That is MiniZinc's `output`, which declares the program's result. Gecode and
Chuffed are both library implementations with MiniZinc as their front end, and
both entries are the same shape with a different `include`.

**CSP** (the Constraints-and-Solutions System) is the hardest case: it has no
output statement at all, so its entry is a named condition, and the file says so
in its first line rather than pretending.

## Before you write one

- Does the language have an output operation? Check before assuming.
- If it does not, is there a *value* you can name instead? Usually yes.
- If it has neither, the file should say which, in its first line.
- Never invent a `print` to make a file look finished.