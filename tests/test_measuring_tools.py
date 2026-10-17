#!/usr/bin/env python3
"""The measuring tools must measure something.

Four tools were added today whose only purpose is to produce a number:
`coverage_figure.py`, `classify_placeholders.py`, `language_table.py` and
`hue_uniformity.py`. Each is worth having and none of them is worth much if it
silently reports zero, which is exactly what `hue_uniformity.py` did on its first
run -- it read `colour` where the manifest says `color`, found nothing, and
printed "0 chromatic of 694" with a straight face and a zero exit status.

A measurement that reports nothing and exits zero is the most dangerous kind of
broken tool, because it is indistinguishable from a clean result to anything that
looks at the exit code. So each one is asserted to return a non-degenerate
answer, and the sanity checks that would have caught it are written down:

  * the figure must be a plausible number, not zero;
  * the tool must name the field it reads, so a rename in the manifest is a
    visible failure rather than an empty table;
  * the counts must add up to the number of files, because a classifier that
    drops files is worse than one that mislabels them.

Skipped when the manifest is missing.
"""

import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"


def _module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ready():
    return MANIFEST.exists()


def test_coverage_figure_is_not_zero():
    if not _ready():
        return
    mod = _module("coverage_figure", ROOT / "scripts" / "coverage_figure.py")
    f = mod.figures()
    assert f["files"] == 7326, f"the manifest has {f['files']} files, not 7326"
    assert f["core"] == 694, f"the core layer has {f['core']} files, not 694"
    assert f["curated"] > 1000, (
        f"only {f['curated']} curated templates were found; the HELLO table has "
        f"about 1 600. A field rename in the generator would produce this.")
    assert f["programs"] == f["curated"] + f["inherit"], (
        "programs must be curated plus the inherit allowlist")
    assert f["core_pct"] > 90.0, (
        f"core coverage reads {f['core_pct']:.1f} %; it is 99.7 % and has been "
        f"for weeks. A tool reporting 0 % is reading the wrong field.")


def test_classification_accounts_for_every_file():
    if not _ready():
        return
    mod = _module("classify", ROOT / "scripts" / "classify_placeholders.py")
    data = mod.build()
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    total = len(man["files"])
    classified = data["without_program"]

    assert classified + (total - classified) == total, "arithmetic error"
    assert classified < total, (
        "every file is classified as having no program, which means the "
        "template table was read as empty")
    # The five kinds the generator has an admission sentence for, written out
    # here rather than imported. `KINDS` in the classifier maps Linguist's
    # *types* onto these, so importing it would compare the wrong namespace --
    # which is what the first version of this assertion did.
    EXPECTED_KINDS = {"esolang", "program", "document", "binary", "unknown"}

    assert set(data["counts"]) <= EXPECTED_KINDS, (
        f"the classifier produced kinds the generator has no sentence for: "
        f"{set(data['counts']) - EXPECTED_KINDS}")
    assert sum(data["counts"].values()) == classified, (
        "the per-kind counts do not sum to the number of classified files")


def test_classifier_reads_the_field_the_manifest_actually_uses():
    """The `colour`/`color` mistake, named so it cannot recur silently.

    The manifest key is `color`. A tool reading `colour` finds nothing, returns
    an empty result, and exits 0.
    """
    if not _ready():
        return
    mod = _module("classify", ROOT / "scripts" / "classify_placeholders.py")
    data = mod.build()
    kinds = set(data["counts"])
    assert len(kinds) >= 3, (
        f"only {len(kinds)} kind(s) produced: {kinds}. The classifier is "
        f"probably reading a field the manifest does not have.")


def test_hue_uniformity_reads_colour_and_finds_colours():
    if not _ready():
        return
    mod = _module("hue_uniformity", ROOT / "scripts" / "hue_uniformity.py")
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    core = [f for f in man["files"] if f["path"].startswith("hello/core/")]

    chromatic = 0
    for f in core:
        hsv = mod.parse_colour(f.get("color") or f.get("colour"))
        if hsv is not None and not mod.is_grey(hsv):
            chromatic += 1

    assert chromatic > 600, (
        f"only {chromatic} of {len(core)} core languages parsed as chromatic. "
        f"The manifest key is `color`, not `colour`; reading the wrong one "
        f"gives zero and still exits 0.")


def test_language_index_is_grouped_and_complete():
    if not _ready():
        return
    mod = _module("language_table", ROOT / "scripts" / "language_table.py")
    text = mod.build()

    for kind, title in mod.SECTION_TITLES.items():
        assert title.split(" (")[0] in text, f"section missing: {title}"

    rows = [l for l in text.splitlines() if l.startswith("| ") and l.count("|") == 4]
    assert len(rows) > 7000, (
        f"the index lists {len(rows)} rows; there are 7 326 files. A classifier "
        f"that drops files would produce a shorter table and still exit 0.")
    assert "**total**" in text


def test_extension_collisions_are_counted_not_guessed():
    """The tool measures how much is at stake; it must not pick a winner.

    Linguist resolves an ambiguous extension by filename, then by path pattern,
    then by heuristics that live in the linguist gem and not in this
    repository. A tool that answered "which language wins" by reading the
    manifest would be answering a different question with a straight face --
    the `colour`/`color` mistake again, one level up.

    So the assertions are about the counting: that collisions exist, that every
    file lands in exactly one row, and that a row's languages are the ones that
    actually claim that extension.
    """
    if not _ready():
        return
    mod = _module("extension_collisions", ROOT / "scripts" / "extension_collisions.py")
    rows = mod.collides()
    f = mod.figures()

    assert len(rows) == f["colliding_extensions"] > 100, (
        f"only {len(rows)} colliding extensions found; Linguist shares the "
        f"extension of about 117 of them with another language")
    assert f["files"] == 7326
    assert f["colliding_pct"] < 10.0, (
        f"{f['colliding_pct']} % of the repository is at stake; that is not an "
        f"ambiguity in a handful of files, it is a systematic overcount")

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_ext: dict[str, set] = {}
    for entry in man["files"]:
        by_ext.setdefault(entry.get("extension") or "", set()).add(entry["language"])
    for r in rows:
        assert r["languages"] == sorted(by_ext[r["extension"]]), (
            f"{r['extension']}: reported {r['languages']}, manifest says "
            f"{sorted(by_ext[r['extension']])}")
        assert len(r["languages"]) > 1, (
            f"{r['extension']} is reported as a collision with one language")

    # Every file counted as colliding must really be in a colliding extension,
    # and the counts must not double up.
    counted = sum(r["files"] for r in rows)
    assert counted == f["colliding_files"] == 281, (
        f"rows sum to {counted}, figures say {f['colliding_files']}")
    expected = sum(1 for e in man["files"]
                   if len(by_ext[e.get("extension") or ""]) > 1)
    assert counted == expected, (
        f"{counted} files counted as colliding, {expected} are in a colliding "
        f"extension")


def test_doc_figures_are_measured_not_typed():
    """The stale-figure check must resolve against a measurement, not a table.

    Typed figures were the most common defect in this repository's history --
    not wrong arithmetic, stale arithmetic. A commit message saying "94 tests"
    when there are 95 is true for exactly as long as nobody adds anything.

    So the assertions here are about provenance: every claimable quantity must
    come out of the tool that measures it, and a round number must be a
    deliberate rounding rather than the only value the tool knows.
    """
    if not _ready():
        return
    mod = _module("check_doc_figures", ROOT / "scripts" / "check_doc_figures.py")
    known = mod.truth()

    assert known["tests"] > 50, "the test count is a definition, not a run"
    assert known["files"] == 7326
    assert known["fps"] == 10, (
        f"record_demo.sh says fps={known['fps']}; the docs quote 10")
    assert known["max_colors"] == 128, (
        f"record_demo.sh encodes {known['max_colors']} colours. It mentions "
        f"max_colors twice -- 96 as a size to compare against, 128 as the "
        f"value passed to ffmpeg -- and taking the first reports a real file "
        f"at the wrong setting")

    # Round numbers must exist as *derivations*, so "about 1 700 curated" can be
    # checked without the phrase "about" having to be trusted.
    assert known["curated_hundred"] == round(known["curated"], -2)
    assert known["curated_hundred"] != known["curated"]

    assert set(mod.UNRESOLVED) <= {"segments", "acceptance"}, (
        f"claims marked unresolvable grew: {mod.UNRESOLVED}")
    for claim in mod.UNRESOLVED:
        assert claim not in known, (
            f"{claim} is both unresolvable and resolved; pick one")


def test_doc_figure_scanner_finds_a_planted_claim_and_flags_it(tmp_path=None):
    """A report nobody has ever seen fail is not a report.

    The scanner is exercised on a file written to be stale, so the assertion is
    that it *reports* -- not that the documentation happens to be clean.
    """
    if not _ready():
        return
    mod = _module("check_doc_figures", ROOT / "scripts" / "check_doc_figures.py")
    import tempfile
    known = mod.truth()
    # The correct figure is interpolated, not typed. A first version of this
    # test wrote "about 1704 curated" and then asserted it was exact, which
    # made the test fail the moment a batch added fourteen programs -- a typed
    # figure inside the checker for typed figures, and the last one needed.
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "probe.md"
        p.write_text(
            "The suite has 999 tests.\n"
            "The repository holds 123 tracked files.\n"
            f"It is roughly 5000 files, and about {known['curated']} curated.\n",
            encoding="utf-8")
        rows = mod.scan(p, known)
        by_claim = {r["claim"]: r for r in rows}
        assert by_claim["tests"]["said"] == 999
        assert by_claim["tests"]["actual"] == known["tests"]
        assert not by_claim["tests"]["exact"]
        # The line beginning "It is roughly" must be treated as approximate,
        # and the curated figure on it must be compared rather than skipped.
        assert by_claim["curated"]["approximate"], (
            "'roughly' did not mark the claim approximate")
        assert by_claim["curated"]["exact"], (
            f"{known['curated']} curated is exact and was reported stale")


def test_banner_checker_passes_on_the_repository_and_catches_planted_defects():
    """A report nobody has ever seen fail is not a report.

    `check_banners.py` found no defects on its first clean run, which is the
    opposite of the manifest check's four. That makes it exactly the tool where
    "it passes" proves nothing, so each check is exercised against a banner that
    is wrong in one field -- and the assertion is that the checker says so.
    """
    if not _ready():
        return
    mod = _module("check_banners", ROOT / "scripts" / "check_banners.py")

    # the real thing first, because a checker that cannot pass is useless.
    # The has-a-program rule comes from the tool rather than from here: the
    # first version of this test passed `True` unconditionally and produced
    # fifty false positives on the document-kind files, which have no program
    # and correctly carry an admission line. A test that reinvents the rule is a
    # second opinion on the wrong question.
    kinds = {}
    classes = ROOT / "data" / "placeholder_classes.json"
    if classes.exists():
        kinds = {f["path"]: f.get("kind") for f in
                 json.loads(classes.read_text(encoding="utf-8"))["files"]}
    gen = _generator()
    real = [f for f in json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
            if (ROOT / f["path"]).is_file()][:400]
    assert real, "no manifest entries to check"
    for entry in real:
        gen_ok = mod.check(entry, ROOT / entry["path"], gen,
                           mod.has_program_for(entry, gen, kinds))
        assert not gen_ok, f"{entry['path']}: {gen_ok}"

    # now the same banner with one field wrong at a time
    sample = next((e for e in real
                 if e["path"].endswith("hello.py") and e.get("color")), None)
    if sample is None:
        # The manifest is ordered by hue, so Python is not in the first 400.
        # Take the sample from the whole set rather than from the sample slice.
        all_files = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
        sample = next((e for e in all_files
                       if e["path"].endswith("hello.py") and e.get("color")
                       and (ROOT / e["path"]).is_file()), None)
    if sample is None:
        return
    text = (ROOT / sample["path"]).read_text(encoding="utf-8")

    def problems(body, has_program=None):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "probe.py"
            p.write_text(body, encoding="utf-8")
            return mod.check(
                sample, p, gen,
                mod.has_program_for(sample, gen, kinds)
                if has_program is None else has_program)

    assert not problems(text)
    # The manifest's colour may differ from the banner's in case, so replace
    # whichever form is actually there -- and assert the replacement happened,
    # because a silent no-op makes the next assertion meaningless. That was the
    # first version's bug: `.upper()` on "#3572a5" produced a string the banner
    # never contained, so nothing was planted and the check below was vacuous.
    wrong = text.replace(sample["color"], "#ff0000")
    if wrong == text:
        wrong = text.replace(sample["color"].lower(), "#ff0000")
    assert wrong != text, f"could not plant a wrong colour in {sample['path']}"
    assert problems(wrong), "a wrong colour was not reported"
    assert problems(text.replace(":: RAiNBOW_Hello-World", "", 1)), (
        "a missing title was not reported")
    assert problems(text, has_program=False), (
        "an admission line on a file that has none was not reported")


def _generator():
    """The generator module, loaded the way check_banners.py loads it."""
    import sys as _sys
    key = "gen_hello_banner_test"
    if key in _sys.modules:
        return _sys.modules[key]
    spec = importlib.util.spec_from_file_location(
        key, ROOT / "scripts" / "generate_all_hello.py")
    mod = importlib.util.module_from_spec(spec)
    _sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def test_check_banners_passes_over_the_whole_repository():
    if not _ready():
        return
    mod = _module("check_banners", ROOT / "scripts" / "check_banners.py")
    files = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
    gen = mod.load_generator()
    kinds = {}
    classes = ROOT / "data" / "placeholder_classes.json"
    if classes.exists():
        kinds = {f["path"]: f.get("kind") for f in
                 json.loads(classes.read_text(encoding="utf-8"))["files"]}
    bad = []
    for entry in files:
        p = ROOT / entry["path"]
        if not p.is_file():
            continue
        _prog, real = gen.program_for(entry["language"],
                                      entry.get("extension") or "")
        has = bool(real) and kinds.get(entry["path"]) is None
        bad.extend(mod.check(entry, p, gen, has))
    assert not bad, f"{len(bad)} banner problem(s), first: {bad[:3]}"


def test_workflow_gate_audit_matches_what_github_actually_ran():
    """A green pull request is not evidence about twenty-four jobs.

    The first Dependabot pull request in this repository was green and
    mergeable, and it bumped three actions across three major versions. The
    job that would have found out is `demo assets`, and it is gated away from
    pull_request events -- as are all 24 batch shards. That was worked out by
    reading the API, and it should not have to be worked out again by reading
    it.

    So the tool has to agree with what GitHub actually did, and the test asserts
    against the workflow file rather than against the tool's own parser.
    """
    workflow = ROOT / ".github" / "workflows" / "rainbow.yml"
    if not workflow.exists():
        return
    mod = _module("audit_workflow_gates", ROOT / "scripts" / "audit_workflow_gates.py")
    jobs = {name: cond for name, _needs, cond in mod.parse(workflow)}

    # The `on:` block's four event names are indented keys, not jobs. The
    # first parser reported all four as jobs.
    for event in ("push", "pull_request", "workflow_dispatch", "schedule"):
        assert event not in jobs, f"{event} is an `on:` key, not a job"

    assert "verify" in jobs, "the verification job was not found"
    gated = {n for n, c in jobs.items()
             if mod.runs_on(c, "pull_request") is False}
    assert "batches" in gated, "the batch shards do run on a pull request?"
    assert "assets" in gated, "the demo-assets job does run on a pull request?"
    assert "verify" not in gated, "the verification job is gated off pull requests"

    # Every gated job must print its condition verbatim, because that string is
    # the whole value of the table.
    for name in gated:
        cond = " ".join(jobs[name].split())
        assert "github.event_name" in cond, f"{name}: {cond!r}"
        assert "||" in cond or "!=" in cond, f"{name}: {cond!r}"


def test_the_expression_evaluator_distinguishes_false_from_unknown():
    """A checker that returns False for what it cannot read is the worst kind,
    because every cell it gets wrong looks right.

    `if: always()` is a status-check function rather than a condition. An
    earlier version reported it as "does not run on a pull request", which is
    the opposite of the truth, and the table said so with a straight face.
    """
    mod = _module("audit_workflow_gates", ROOT / "scripts" / "audit_workflow_gates.py")

    assert mod.runs_on("always()", "pull_request") is True
    assert mod.runs_on("", "pull_request") is True
    assert mod.runs_on("always() && failure()", "pull_request") is None, (
        "`always() && failure()` depends on how the run went, which this tool "
        "does not model, so the answer is unknown rather than a guess. GitHub "
        "would say False for a green run and True for a red one, and a tool "
        "that picks one is wrong half the time and never says so")
    assert mod.runs_on("github.event_name != 'pull_request'", "pull_request") is False
    assert mod.runs_on("github.event_name != 'pull_request'", "push") is True
    chain = ("github.event_name == 'workflow_dispatch' || "
             "github.event_name == 'schedule' || "
             "(github.event_name == 'push' && "
             "!contains(github.event.head_commit.message, '[skip ci]'))")
    assert mod.runs_on(chain, "push") is True
    assert mod.runs_on(chain, "schedule") is True
    assert mod.runs_on(chain, "pull_request") is False
    # A form this does not understand must be None, never False.
    assert mod.runs_on("needs.verify.result == 'success'", "push") is None


def test_every_runner_mentions_the_file_it_runs():
    """A runner that does not mention {file} does not run anything.

    Four entries in the generator's RUNNERS table were the bare string
    `echo "Hello World!"`. Nothing was executed, `language_report.py` counted
    them among the runnable languages, and the manifest carried a runner for
    four languages that were never run. It is the same shape as E31 and E30: a
    claim that is checkable and nobody checked it. See E34.
    """
    if not _ready():
        return
    spec = importlib.util.spec_from_file_location(
        "gen_hello", ROOT / "scripts" / "generate_all_hello.py")
    gen = importlib.util.module_from_spec(spec)
    sys.modules["gen_hello"] = gen
    spec.loader.exec_module(gen)

    assert len(gen.RUNNERS) > 40, f"only {len(gen.RUNNERS)} runners"
    bare = {k: v for k, v in gen.RUNNERS.items() if "{file}" not in v}
    assert not bare, f"runners that never mention the file: {bare}"

    # And the fallback is a fallback: a command that ends in
    # `|| echo "Hello World!"` must have something before it.
    for name, cmd in gen.RUNNERS.items():
        if '|| echo "Hello World!"' in cmd:
            attempt = cmd.split("||", 1)[0].strip()
            assert attempt and "{file}" in attempt, (
                f"{name}: the fallback is the whole command")


def test_make_help_documents_every_phony_target():
    """`make help` is the only documentation a new contributor will find.

    So it has to run everywhere, and it has to be complete. Both were false:
    the Makefile's `SHELL := /usr/bin/env bash` is not valid make syntax (SHELL
    must be a path), so every recipe failed on a machine without a findable
    shell, and the usual grep-and-awk self-documenting idiom needs two programs
    that are not on PATH here either.
    """
    makefile = ROOT / "Makefile"
    if not makefile.exists():
        return
    mod = _module("make_help", ROOT / "scripts" / "make_help.py")
    text = makefile.read_text(encoding="utf-8")

    documented = {n for n, _ in mod.targets(text)}
    phony = set(mod.declared_phony(text))
    assert documented, "no target in the Makefile has a ## comment"
    # `help` documents itself by printing the list, so it is the one target
    # allowed to be in .PHONY without a comment of its own.
    missing = phony - documented - {"help"}
    assert not missing, f"in .PHONY but undocumented: {sorted(missing)}"

    # A comment on the wrong side of the recipe -- `# not a target` -- must not
    # be picked up as one, and neither may a recipe line that begins with a
    # tab and happens to contain a colon.
    assert "SHELL   := /usr/bin/env bash" not in text, (
        "SHELL must be a path; make runs it directly, so `env bash` fails "
        "before the first recipe line is read")

    # Only recipe lines count. The Makefile's own comment *describes* the
    # grep-and-awk idiom it refused to use, and a test that failed on the word
    # would be failing on the explanation.
    recipes = "\n".join(l for l in text.splitlines() if l.startswith("\t"))
    for tool in ("grep ", "awk ", "sed "):
        assert tool not in recipes, (
            f"a recipe uses {tool.strip()}, which is not on PATH on the "
            f"machine this is built on")


def test_extension_collisions_measures_bytes_off_disk():
    """The manifest has no byte field, and this tool must not invent one.

    It records a language's byte *share*, which is a tuning number from
    balance_bytes.py. Summing it here would report a plausible total for
    something the manifest does not contain.
    """
    if not _ready():
        return
    mod = _module("extension_collisions", ROOT / "scripts" / "extension_collisions.py")
    sizes = mod.byte_totals()
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(sizes) == len(man["files"])
    assert all(isinstance(v, int) and v >= 0 for v in sizes.values())
    f = mod.figures()
    assert f["colliding_bytes"] > 100_000, (
        f"only {f['colliding_bytes']} bytes at stake; 281 files cannot fit in "
        f"that")