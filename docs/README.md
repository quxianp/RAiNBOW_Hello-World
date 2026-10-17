# Documentation

Every document in this repository, and what it is for. The deep-dive pages
answer questions that the README raises but cannot fit; the ledgers record what
went wrong, which is usually more instructive than what went right.

<!-- DOCS_INDEX_START -->
| Document | What it answers |
|---|---|
| [The project page](../README.md) | The rainbow bar, the demo, and how to read everything else. |
| [Architecture](ARCHITECTURE.md) | The bar is controlled by byte count: equal file size means equal share, and hue ordering makes that visible. Also the 694-to-631 gap and the known limits. |
| [Why 631 segments, not 694](WHY-631-NOT-694.md) | The single most asked question, with the measurements that settle it. Linguist merges dialects into parents; the 7 HTML-family files become one `HTML` segment of 7 x 2048 bytes, which is why it reads 1.0116 %. |
| [How a file in hello/ gets its content](HOW-FILES-GET-THEIR-CONTENT.md) | The five kinds of file in `hello/` and why each needs different content — a program, an esoteric admission, an index admission, a document, a binary header — plus how to add one, and what "real" means here. |
| [The demo](DEMO.md) | How `assets/hello-world.gif` is recorded, why a gate refuses to publish a static take, and the three tools to reach for when a recording looks wrong. |
| [The files that are not programs](ENCODINGS.md) | The seventy files holding encodings of the greeting rather than a program: checksummed records, real archives, image formats, and why each is not a `print`. |
| [Language index](../data/LANGUAGES.md) | All 7 326 files, grouped by what they contain rather than by directory. Generated; `scripts/language_table.py --check` fails if it is stale. |
| [Fortran and COBOL families](../docs/languages/FORTRAN-AND-COBOL.md) | Nine Fortran entries, five of which a single inherited program would get wrong: fixed form puts the statement number in columns 1-6 and the verb in column 7, and free form dropped all of it. |
| [Assembly families](../docs/languages/ASSEMBLY.md) | Eighty-odd entries, each with its own syscall convention -- and that convention is the program. Plus the object formats, three of which carry checksums. |
| [Provers, model checkers and solvers](../docs/languages/PROVERS-AND-SOLVERS.md) | Three families that look alike on the language bar and none of which can print. Coq gets a definition, NuSMV an INVARSPEC, MiniZinc an output declaration, and CSP a file that says it has neither. |
| [SQL and query languages](../docs/languages/SQL-AND-QUERIES.md) | Fourteen entries where the keyword is sometimes SELECT, sometimes RETURN and sometimes PRINT, and two of which cannot print at all. |
| [Build, package and CI configuration](../docs/languages/CONFIG-FILES.md) | The declaration-form exemption, why it keys on the extension, and why the guard has to run in both directions. |
| [Visual and block languages](../docs/languages/BLOCK-LANGUAGES.md) | Seventy entries whose programs are dragged and whose project files are JSON. Writing Python into a Scratch project passes every check here and Scratch cannot open it. |
| [The Lisp families](../docs/languages/LISP.md) | Ten entries whose entire difference is whether the language appends the newline itself. |
| [Golf and concatenative languages](../docs/languages/GOLF.md) | Sixty entries whose canonical program is one to fifteen characters, in three shapes -- and Actually, whose whole program is fifteen + characters. |
| [The editor languages](../docs/languages/EDITOR-LANGUAGES.md) | Half a dozen entries that do not run in a terminal. Emacs Lisp says it with `message`, Vim script with `echom`, and the two that are not programs at all -- a derived mode and a vimdoc tag line -- have a required header rather than an output operation. |
| [APL, J and their descendants](../docs/languages/APL-FAMILY.md) | Six array languages that all read right to left, so a Hello World written left to right does nothing at all. APL's output is the quad assignment, J's is `echo`, K has none and gets a comment that says so. |
| [Stack and concatenative languages](../docs/languages/STACK-LANGUAGES.md) | Forth, PostScript, Factor: the question is how a value gets from the stack to the screen, and the answer is different in each. Why a Forth Hello World is longer than a C one, and why that is correct. |
| [The BASIC family](../docs/languages/BASIC-FAMILY.md) | Ten entries and about six languages. Two require line numbers because the ANSI standard's control flow is GOTO; and output is not PRINT in half of them -- VBA is a host language where MsgBox is the answer and VBScript's is WScript.Echo. |
| [Web templating languages](../docs/languages/WEB-TEMPLATING.md) | Twenty-five entries that are string substitution with a layer of control flow. A template with no holes in it does nothing, so the greeting goes in an expression. Liquid's tag set is fixed by design, which is why {{ 'Hello World!' }} is the most it can do. |
| [The TeX and troff families](../docs/languages/TEX-AND-TROFF.md) | Eight entries that typeset rather than print, and not one of them has an output operation. Three shapes -- a full document, a man page whose greeting belongs under .SH NAME, and an M4 macro that prints its own definition unless you write dnl. |
| [The logic-programming family](../docs/languages/LOGIC-PROGRAMMING.md) | Prolog has no print in its language proper -- write/1 is a library predicate and the program is a set of rules. Mercury adds type signatures that are not optional, Curry is not Prolog at all despite the syntax, and Visual Prolog's .pl file is a diagram. |
| [The JavaScript family](../docs/languages/JAVASCRIPT-FAMILY.md) | Sixteen entries on a JavaScript engine, differing in three places: the module system, the type system, and whether the unit is a program or a component. CoffeeScript calls without parentheses, Dart has void main(), ActionScript's only output was trace(), and JSX renders rather than runs. |
| [The C family](../docs/languages/C-FAMILY.md) | Nine entries whose names start with C and which have less in common than the names suggest. C# shares a name and nothing else; C-- is a subset whose entry point is proc main(); Cuda cannot print because the output is on the host side of the copy. |
| [Glossary](GLOSSARY.md) | This repository uses four senses of 'kind' and two of 'layer', and none of them is a classification of languages. Reconciles Linguist's types, our five placeholder kinds, the two layers, and what a *segment* is -- which is GitHub's word, not ours, and is the reason 694 files is 631 slices. |
| [hello/manifest.json](MANIFEST.md) | The most load-bearing file in the repository and the one with the fewest readers: one entry per file, what each field means, and which three are allowed to be empty and why -- plus why `extension` is Linguist's and not pathlib's. |
| [Terminal output and control languages](../docs/languages/TERMINALS.md) | Twenty-odd entries that do not print characters -- they move the cursor and set attributes. Worked out: the SGR codes are additive bit flags, 38;2;r;g;b is the whole of truecolour, and that is the escape run.sh draws the rainbow with. |
| [The shell family](../docs/languages/SHELLS.md) | Fifteen entries, one word 'shell' in most of them, and the distinction that matters most: a shell script is not a program in the shell. print is a ksh and zsh builtin and does not exist in bash, so copying one line between three entries produces one that works and two that fail. |
| [Markup, prose and documents](../docs/languages/MARKUP-AND-DOCUMENTS.md) | Four shapes of document, and the one that is not what it looks like: a binary format gains a greeting by putting it in the field the format itself accepts. |
| [Frequently asked questions](FAQ.md) | Why the bar looks grey, why COBOL is missing, which of 694 and 631 is right, and whether all the files actually run. |
| [Contributing](../CONTRIBUTING.md) | How to add a language or a Hello World template, and what CI silently reverts. |
| [Changelog](../CHANGELOG.md) | Every notable change and every defect found, with the reason each was hard to see. |
| [Security](../SECURITY.md) | What in this repository is inert data rather than code. Most of it. |
| [Code of conduct](../CODE_OF_CONDUCT.md) | Contributor Covenant 2.1. |
| [Defect ledger](../logs/ERRORS.log) | Thirty-two defects, each with the symptom, the cause, and why nothing caught it. The most useful document here. |
| [Decisions](../logs/DECISIONS.md) | Choices made and the reasoning behind them, including the ones that were later reversed. |
| [Working notes](../logs/AGENT_STATE.md) | Current numbers, the commands that matter, and the environment hazards that have actually cost time. |
<!-- DOCS_INDEX_END -->
