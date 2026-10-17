# Adding a template: visual and block languages

Roughly seventy entries here have no text syntax at all. They are languages whose
programs are made by dragging blocks, and their on-disk form is a JSON document.

## The trap

They are the easiest entries in this repository to get wrong, because the
"program" looks like nothing and it is very tempting to write something that
looks like code.

Neither is right. A Scratch `.sb3` project is a ZIP of JSON; writing Python into
it produces a file Scratch cannot open, and the damage is worse than a
placeholder because the file is plausible.

## What they actually store

| family | on-disk form | where the greeting goes |
|---|---|---|
| Scratch, Snap!, MicroWorld, Code.org | project JSON, with a scripts array | the `say` block's literal |
| ScratchJr | project JSON | the `sayForever` literal |
| App Inventor, Thunkable, MIT App Inventor | `.aia`, which is JSON | the component's `Text` property |
| Blockly | the workspace is XML; the *generated* JS is the program | a generated-variable definition |
| Kodu, Cubetto | a world file | the `Say` action, or the robot's `hello` action |
| MicroBlocks, Mindscript | block code, text | the `say` literal |
| MakeCode | TypeScript-ish source | `basic.showString("Hello World!")` |
| Kodable | a command stream | `hi` |

## The two exceptions worth knowing

**MakeCode** is genuinely a language — its blocks compile to TypeScript, and the
source form is text. `basic.showString("Hello World!")` is a real program and is
recorded as one.

**Code.org** and **MIT Scratch** are also text in this repository, because those
entries are the *block-language* text forms, which are two lines of block syntax
and nothing else. That is not a degraded placeholder; it is the whole format.

## The display case

**Micro:bit** and **MicroBlocks** have no screen. The Micro:bit's display is a
5×5 LED matrix and its honest Hello World is `display.scroll('Hello World!')`,
which scrolls. That is the right answer — a device that cannot print a line is
not a shortfall, it is a fact about the device.

## Before you write one

- Find out what the project file actually is. It is usually JSON, and the program
  is one field of it.
- Find out whether the language has a text source form at all. MakeCode does;
  Scratch does not.
- Does the target have a display? If not, scrolling is the answer and saying so
  is better than faking a `print`.