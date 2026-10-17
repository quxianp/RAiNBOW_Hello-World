# Adding a template: the BASIC family

Ten entries on this repository's language bar and about six genuinely different
languages wearing the same word.

## The trap

```basic
PRINT "Hello World!"
```

works in perhaps four of them and fails in the rest, and the failures are of
three different kinds. Which one you hit depends on the entry, so the entries
cannot share a template.

## The families

| entry | dialect | its actual Hello World |
|---|---|---|
| BASIC | ANSI Minimal BASIC | `10 PRINT "HELLO WORLD"`, line numbers required |
| QuickBASIC | Microsoft's dialect | `PRINT "Hello World!"` |
| BASIC (MSX, GW-BASIC style) | line numbers still required | `10 PRINT "Hello World!"` |
| BBC BASIC | Acorn's dialect | `PRINT "Hello World!"`, and it has `PRINT TAB(x,y)` |
| Locomotive BASIC | on the Amstrad CPC | `PRINT "Hello World!"` |
| VBA / VBScript | Microsoft's host, not a compiler | `MsgBox "Hello World!"` in VBA, `WScript.Echo` in VBScript |
| B4X | a modern BASIC that compiles to native | `Msgbox("Hello World!")` — its own function, not BASIC's `PRINT` |
| BlitzBasic | Blitz3D's BASIC | `Print "Hello World!"` |
| FreeBASIC | a modern free BASIC | `Print "Hello World!"` |

## The three differences that matter

**Line numbers.** ANSI Minimal BASIC requires them, and it is *not* a dated
curiosity: the standard's whole control-flow mechanism is `GOTO 10`. A program
without line numbers is not a Minimal BASIC program at all.

**Output is not `PRINT`.** This is the one that gets forgotten. VBA does not
compile BASIC — it is a host language, and `PRINT` in a VBA module writes to the
Immediate window, which nobody is looking at. `MsgBox` is what a VBA program
does. VBScript is the same idea with `WScript.Echo`. B4X is not BASIC at all in
this respect: its output is `Msgbox`, and the case is capitalised, because it is
a Java-callable API rather than a keyword.

**Case sensitivity is undefined.** The ANSI standard says identifiers are
insensitive; QuickBASIC upper-cases them; BBC BASIC is case-sensitive. So
`print` and `PRINT` are the same program in one and two different programs in
the third.

## What a "Hello World" is in a language with no console

**VBA, VBScript and B4X run inside a host.** There is no stdout. A greeting is a
dialog box, a log write, or a return value — and which one is the right answer
depends on the host, so the file should say which host it is for.

**PostScript** and **Forth** have a console, but a stack-shaped one. PostScript'
answer is `show`, and `Hello World!` has to be a *string on the stack* before
`show` will print it, which is not the same thing as a program that has the
words in it.

## Before you write one

- Does this dialect need line numbers? Two of the ten do and they are the two
  people are most likely to copy from each other.
- Is `PRINT` the output operation at all, or is it `MsgBox`, `WScript.Echo`,
  `Msgbox`, `show` or `emit`? Check the host.
- Is the language running on a machine, or inside something?
- Is the case of the keywords part of the language? If it is, pick one and be
  consistent — the repository's `.gitattributes` will not save you.