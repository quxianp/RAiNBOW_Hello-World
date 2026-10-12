# DECISIONS — G-RAINBOW-HELLO

## D1. Toolchain location, not installation
`git`, `bash`, `python` were absent from `PATH` but present on disk
(`D:\Git`, `C:\hclaw\python`). Chose to invoke them by absolute path rather than
download PortableGit (60 MB) or re-run installers.
- Options compared: (a) download PortableGit, (b) filesystem search, (c) write a
  pure-Python git via dulwich.
- Search won: zero network, zero supply-chain risk, and it also yielded `bash`,
  which PortableGit-minimal variants omit but `run.sh` requires.

## D2. `python3` on Windows is a stub, not an interpreter
`C:\Users\...\WindowsApps\python3` is the Microsoft Store alias: it exists,
exits 0 and prints nothing. Any `command -v python3` probe passes while nothing
actually executes. `run.sh` therefore probes with `[ "$(python3 -c 'print(1)')" = "1" ]`.
Kept as-is — it is already correct and CI (Linux) needs the same robustness.

## D3. Emit true colour even when stdout is not a TTY  (changed this session)
`scripts/rainbow.py` previously set `plain = args.plain or not is_tty()`, so the
moment output was piped to a file — which is exactly what CI, `logs/run.log` and
the recording step do — it degraded to three plain text lines and the bar and
ASCII art never rendered.
- Considered: leaving it, or forcing a pty.
- Chosen: `plain` is now driven only by `--plain` / `RAINBOW_PLAIN`. Cursor
  tricks (hide cursor, clear screen, animation) stay gated on `is_tty()`.
- Rationale: ANSI in a log file is harmless and is the evidence the acceptance
  criteria ask for; animation without a terminal would just spam the log.

## D4. Fix `rgb()` in run.sh  (correctness bug, this session)
`rgb()` emitted `ESC 38;2;R;G;Bm` — no `[` after ESC. Those are not SGR
sequences, so the per-character rainbow greeting and the roll-call check marks
rendered as literal escape garbage, i.e. *not coloured at all*.
- Considered: rewriting the whole colour layer, or patching the one format string.
- Chosen: patch the format string to `'%s[38;2;%d;%d;%dm'`. Single character,
  no behavioural change elsewhere. Verified: 0 malformed escapes, 12 distinct
  colours in the final greeting.

## D5. Keep Linguist's `include_in_language_stats` pressure handled via `linguist-detectable`
Linguist only counts `programming` and `markup` types by default; 124 of the 694
core languages are `data`/`prose` (Markdown, JSON, SQL, CSV, TOML, AsciiDoc...).
The inherited `.gitattributes` adds `linguist-detectable` on `/hello/core/**`
rather than pretending those languages are something else.
Rejected: dropping those languages (bar gets visibly less dense) or relying on
`include_in_language_stats` per language (needs a Linguist PR upstream).

## D6. Every core file pinned to exactly 2048 bytes
Gives each language 100/694 = 0.144092 % — identical for all, inside the
0.05 %–0.5 % window, summing to exactly 100 %. Confirmed idempotent: running
`balance_bytes.py` again produces zero diffs.
Rejected: proportional-to-natural-size balancing (the inherited first attempt),
because natural sizes ranged 408 B mean with large outliers, which starved the
small languages below the visibility window.

## D7. Workflow gains a separate `assets` job
Acceptance requires GIF/MP4/PNG produced in CI and committed back. The inherited
workflow only verified and regenerated shards, and `.github/` was never even
pushed. Added a dedicated `assets` job (VHS + ffmpeg + Playwright + README
rewrite + `[skip ci]` commit) plus a `schedule` trigger.
- Considered: folding asset generation into the `verify` job.
- Chosen: separate job, because recording is slow and must not be able to
  invalidate the fast acceptance gate.

## D8. Skip push when the triggering commit says `[skip ci]`
Prevents the asset job from committing and thereby re-triggering itself.
Guards both on `github.event.head_commit.message` and on the actor, because a
scheduled run has no head commit and must still publish.

## D9. Fail loudly *after* publishing, not before
`record_demo.sh` and `screenshot_github.py` are `continue-on-error` so a missing
CDN or browser cannot block the local bar, the README refresh and the push.
That is required, but it also let run 37820167736 report success while producing
nothing. Fixed by adding `assert the demo assets exist` **after** the push step:
partial delivery still ships, and the run still turns red. Ordering matters --
putting the assertion before the push would have thrown away good assets.

## D10. Reject degenerate captures rather than committing them
A language-bar capture under 6 KB cannot be a 631-segment bar. `usable()` throws
it away and the selector cascade continues, so the failure mode is "file missing"
(broken image link, obvious) instead of "141-byte image committed and displayed
as if it were the bar" (silently wrong). The same reasoning puts the diagnostic
full-page screenshot in `.tmp/` instead of `assets/`.

## D11. Do not force a cache bypass on the GitHub page
GitHub edge-caches the anonymous repository page, so a screenshot can lag the
newest push. The obvious fix -- cache-busting parameter plus `Cache-Control:
no-cache` -- made GitHub serve an unstyled document and produced a 303 KB
screenshot of nothing. Chosen: accept the lag. A stale-but-correct image is a
cosmetic issue that the daily `schedule` run repairs; an unstyled page is a
capability regression. The locally generated bar is the authoritative image and
is always in sync.

## D12. Verify against the interpreter CI actually uses
A change that passed locally on Python 3.13.12 killed CI on 3.12.15, because
`Path.read_text` only gained `newline` in 3.13. Now every script is both
compiled and (where dependencies allow) executed under a real 3.12.7 before
pushing. Cheap insurance against the single most likely CI-only failure.

## D13. Name templates explicitly; never infer them
The generator originally decided "does this language have a Hello World?" by
matching the first word of the name, then the file extension. Both guesses
produce confident nonsense: JASS and Objective-J inherited a shell `echo` from a
shared `.j`, and `Go Module` inherited an entire Go program though a `go.mod`
contains module declarations. 34 of 156 matches were wrong, and every one was
valid in *some* language, which is what made them hard to see.

Chosen: an explicit `INHERIT` allowlist naming each child and the template it
legitimately shares. More to maintain, and that is the point -- a wrong entry is
now reviewable by reading rather than discovered by inspecting output.

## D14. An honest placeholder beats a plausible wrong program
Where a correct Hello World is not known, the file says so in its own header.
The alternative -- shipping something plausible -- was tried and is what produced
E25.

The boundary is not "can I write something". A `.properties` file is
`hello=Hello World!`, a `.cabal` file is `name: rainbow`, a JASS file has an
`InitTrig` trigger because JASS has no console output at all. Those are answers.
Rez is not: its `.r` extension is shared with R, and the correct program depends
on which language is meant, so it keeps the placeholder.

## D15. Measure the recording; do not watch it
The closing hold printed zero bytes for several releases and nothing failed,
because it exited 0 and `run.sh` guarded it with `|| true`. The last 8.7 s of a
37.4 s recording was a frozen still.

`scripts/measure_motion.py` reports the fraction of the frame changing between
consecutive frames. Watching a terminal recording does not distinguish "a
deliberate hold" from "a phase that never ran"; the number does, immediately.
It is now part of the delivery gate and of the test suite.

The previous fix to the same phase -- moving the hold before `exit 0` -- was
correct and insufficient. Making code reachable is not the same as making it run.

## D16. Write files in Python, never through PowerShell
Editing one number in README.md with `Set-Content -Encoding UTF8` destroyed every
emoji in the file: PowerShell round-trips text through the console's active code
page on the way in. Two headings lost their emoji entirely, which silently broke
three table-of-contents anchors.

Chosen: every file write goes through Python or the edit tool. Where a generated
figure must be updated, a script owns it (`update_readme_coverage.py`), so the
edit never involves a console and cannot be made by hand.

## D17. Tests that run nothing are the failure mode
Several checks here once passed while asserting nothing: a link checker whose
anchor comparison reduced only one side, a template guard that matched its own
explanatory comment, a suite that only ever ran by hand.

A check is only worth having if it can fail. The tests added this week execute
the real commands and assert on the bytes that come back, and `check_templates.py`
was run against deliberately corrupted input to prove it fires.

## D18. Keep the repository's own tooling off its own bar
`scripts/**` is marked `linguist-vendored`. The rainbow is the point; the
scripts are how it is built. Fourteen thousand lines of Python competing with the
694 language files for space would be the wrong trade, and `CODEOWNERS` routes
the paths that can change the bar to a second look.

