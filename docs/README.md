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
| [Frequently asked questions](FAQ.md) | Why the bar looks grey, why COBOL is missing, which of 694 and 631 is right, and whether all the files actually run. |
| [Contributing](../CONTRIBUTING.md) | How to add a language or a Hello World template, and what CI silently reverts. |
| [Changelog](../CHANGELOG.md) | Every notable change and every defect found, with the reason each was hard to see. |
| [Security](../SECURITY.md) | What in this repository is inert data rather than code. Most of it. |
| [Code of conduct](../CODE_OF_CONDUCT.md) | Contributor Covenant 2.1. |
| [Defect ledger](../logs/ERRORS.log) | Twenty-nine defects, each with the symptom, the cause, and why nothing caught it. The most useful document here. |
| [Decisions](../logs/DECISIONS.md) | Choices made and the reasoning behind them, including the ones that were later reversed. |
| [Working notes](../logs/AGENT_STATE.md) | Current numbers, the commands that matter, and the environment hazards that have actually cost time. |
<!-- DOCS_INDEX_END -->
