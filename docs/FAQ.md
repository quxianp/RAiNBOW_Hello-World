# Frequently asked questions

### Why does my clone show a grey bar?

GitHub's language panel is **edge-cached** and is frequently several commits
behind the repository. Hard-reload, then check the API:

```bash
curl -s https://api.github.com/repos/quxianp/RAiNBOW_Hello-World/languages \
  | python -c "import json,sys; d=json.load(sys.stdin); print(len(d),'languages')"
```

That endpoint is authoritative. If it reports 631 and the page shows something
else, the page is stale, not the repository.

### Why is there no C or C++ label on the site?

Because GitHub's legend collapses the tail into a grey **Other** row. At 631
languages, C and C++ — each only marginally larger than 693 neighbours — fall
inside it. The *segments are there*; only the labels are withheld.

Full explanation with the measurements:
[docs/WHY-631-NOT-694.md](WHY-631-NOT-694.md).

### 694 files but 631 segments — which number is right?

Both. 694 is how many languages are **in the repository**. 631 is how many
Linguist keeps **distinct**. It merges dialects into parents: the 7 HTML-family
files become one `HTML` segment of 7 × 2048 bytes, which is exactly why `HTML`
reads 1.0116 %.

### Is COBOL really missing?

Yes, and that is correct. Linguist assigns COBOL **no colour**, and a language
without a colour cannot appear on a colour bar. 142 languages are in this
category. They live in `hello/full/`, which is excluded from the bar.

### Do all 694 files actually run?

No, and the README says so. **7.1 %** have a runner and **26.1 %** have a curated
Hello World template. The rest are byte-balanced stubs containing a modeline, a
banner and comment padding. Their job is to be **detected and coloured**, not to
compile.

Run `python scripts/language_report.py` for the current figures.

### Why exactly 2048 bytes per file?

Because equal size means equal share, and equal share is the only reason the hue
ordering is visible. 2048 is arbitrary; the exactness is not. Every core file is
2048 bytes, so each language gets exactly 1/694 = 0.144092 %, and the shares sum
to precisely 100.000000 %.

### Why do the core files have a modeline in them?

Because Linguist sometimes needs a hint to detect a file. It was worth checking
whether they actually help: `scripts/modeline_ab_test.rb` runs Linguist over the
repository with and without them, and **both report 631 languages**. They are
neutral. They are kept because they make each file self-describing when you open
it.

### Can I run it locally?

Yes:

```bash
./install_deps.sh      # optional — everything degrades gracefully
bash run.sh            # prints a true-colour Hello World!
```

Or use `run.sh --help` for `--max`, `--jobs`, `--motion` and `--fast`.

### `run.sh` says `Permission denied`

```bash
chmod +x run.sh install_deps.sh scripts/record_demo.sh
```

They are committed `100755`. If yours are not, something rewrote the exec bit —
that was a real bug here once, when every recorded demo ended on a permission
error.

### Why does CI regenerate `hello/core/`?

Because it is generated output. Editing it by hand produces a commit CI silently
reverts. Fix the generator instead. `CONTRIBUTING.md` explains the workflow.

### How do I add a language?

Check `config/core-langs.txt` first — it may already be there. If not, add it to
the fallback groups in `scripts/fetch_languages.py` and re-run the pipeline:

```bash
python scripts/fetch_languages.py
python scripts/merge_language_sources.py
python scripts/select_rainbow_langs.py
python scripts/generate_all_hello.py
python scripts/balance_bytes.py
python scripts/verify_languages.py
```

### What is the rainbow bar image, and why is it drawn rather than screenshotted?

Because GitHub will not label the languages. `assets/rainbow-bar-github.png` is
rendered from `GET /repos/.../languages` and names **all 631** languages with
their real colours and shares. A screenshot of the site would show a grey *Other*
row and defeat the point.

### How do I check the repository is healthy?

```bash
python scripts/audit_repo.py          # equal-size invariant, assets, manifest
python scripts/verify_languages.py     # 19 acceptance checks
python scripts/validate_delivery.py    # workflow, layout, generators, exec bits
python scripts/check_readme_links.py   # broken images and dead anchors
```

All four are offline, deterministic and safe to run on a clean checkout.

### Something looks wrong. What now?

Open an issue with the output of `python scripts/audit_repo.py`. It usually
identifies the cause on its own — and it is worth running first, because a large
share of "the bar is broken" reports turn out to be a stale cached page.