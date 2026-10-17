# Adding a template: golf and concatenative languages

About sixty entries in this repository are golfing languages, and their Hello
Worlds are the shortest programs anyone has written.

## The trap

`print("Hello World!")` is a twenty-character statement in a language whose whole
purpose is to not contain statements. It is also wrong in a way that matters: a
golf language's program is usually *the last expression on the stack*, and
printing is implicit or absent.

## The three shapes

**Stack-dump golf** — the program is a literal and nothing else:

```golfscript
"Hello World!"
```

GolfScript, GolfHusk and GolfMolf are all this. There is no `print`; the stack
is printed when the program ends, and a lone string is a one-character program
once the quotes are implied.

**Explicit output** — a literal plus one instruction:

```vitsy
"Hello World!"o
```

Vitsy needs `o` to output the stack top. Kitten needs `:print`. Thunno and Golfy
dump the stack, so for them the literal alone is right.

**Scaled literals** — the language has no string type at all, only numbers:

```
Huff:  #define HELLO 0x48656C6C6F20576F726C6421
```

Huff is a macro language for EVM bytecode. There are no strings. The greeting is
a hex literal, and adding a `print` would be a file in a language that does not
have one.

## The most counter-intuitive entry in the repository

**Actually** is fifteen `+` characters:

```
+++++++++++++++
```

Each `+` flips the character under the instruction pointer, and the pointer wraps.
That is the entire language, and it is the canonical program. Anything with a
semicolon in it is not Actually.

**Chef** is a recipe, and the trick is the number:

```
Hello World Souffle.

Ingredients with 72 measures of letters
(Hello World)

Serves 1.
```

72 is the character code for `H`. The recipe prints a title, measures are
character codes, and the servings line ends it.

## Golfing languages that are not golfing

**Whitespace** uses only spaces, tabs and newlines — three characters that are
invisible in most editors. Its canonical program exists and is 60-odd characters
of which you cannot see any. That is a genuine reason for caution: a Whitespace
template has to be byte-exact and there is no way to proofread it by eye, so
either copy one that has been run or leave the honest placeholder.

## Before you write one

- Does the language print the stack on exit? If so, a bare literal is the whole
  program.
- Does it have a string type? If not, the greeting is bytes.
- Can you verify it? If not — Whitespace is the case — do not write it from
  memory.