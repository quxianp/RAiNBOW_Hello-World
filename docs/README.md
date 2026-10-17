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
