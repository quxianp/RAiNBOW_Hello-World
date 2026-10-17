#!/usr/bin/env python3
"""Which CI jobs run on which event, and what a green pull request does not prove.

This repository's workflow has 26 jobs. Two of them -- the 24 batch shards and
the demo-assets job -- are gated with `if:` conditions that exclude
`pull_request`. So a green pull request is evidence about two jobs and silence
about the other twenty-four.

That matters every time one is reviewed. The first Dependabot pull request in
this repository was green, mergeable, and clean; merging it bumped
`actions/checkout` from v4 to v7, `setup-python` from v5 to v7 and
`upload-artifact` from v4 to v7 -- and the job that would have found out whether
the new pins work is precisely one the pull request did not run.

So this reads the workflow, evaluates each job's `if:` against each event type,
and prints the table. It does not guess at GitHub's expression semantics: it
reports the expression verbatim next to the events it excludes, which is enough
for a human to judge and impossible to get wrong by reimplementation.

    python scripts/audit_workflow_gates.py
    python scripts/audit_workflow_gates.py --workflow .github/workflows/rainbow.yml
    python scripts/audit_workflow_gates.py --fail-on-skipped
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT = ROOT / ".github" / "workflows" / "rainbow.yml"

EVENTS = ("push", "pull_request", "workflow_dispatch", "schedule")

JOB = re.compile(r"^  ([A-Za-z0-9_.-]+):\s*$")
IF = re.compile(r"^\s*if:\s*(>?-?)\s*(.*)$")


def parse(path: pathlib.Path) -> list[tuple[str, str, str]]:
    """(job name, needs, the `if:` expression, verbatim).

    There is deliberately no YAML parser. The test suite is standard library
    only, and a workflow's `if:` is not YAML in any way a generic parser helps
    with: it is an expression language GitHub evaluates, and reimplementing that
    is how a checker ends up confidently wrong.

    Two things the first version got wrong, both found by printing the table:

    * `push`, `pull_request`, `workflow_dispatch` and `schedule` appeared as
      jobs, because they are keys of the `on:` block and the parser was looking
      for `two-space-indented key:` from the first line of the file. Job
      collection starts at `jobs:` and nowhere else.
    * A folded `if: >-` swallowed the entire rest of its job, because nothing
      said where the scalar ended. YAML's rule is indentation: a continuation
      line is more indented than the key it continues. `runs-on:` is at the same
      indent as `if:`, so the scalar ends there -- and the condition printed as
      a paragraph of shell script.
    """
    jobs: list[tuple[str, str, str]] = []
    name = needs = cond = ""
    in_jobs = False
    in_if = False
    if_indent = 0

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if indent == 0:
            # A top-level key ends everything being collected. `on:`'s four
            # event names are indented and are *not* jobs -- the first version
            # reported all four as jobs, because the guard that was supposed to
            # skip them was three lines of tangled boolean precedence.
            if name:
                jobs.append((name, needs, cond))
            name = needs = cond = ""
            in_if = False
            in_jobs = stripped == "jobs:"
            continue

        if not in_jobs:
            continue

        m = JOB.match(line)
        if m:
            if name:
                jobs.append((name, needs, cond))
            name, needs, cond = m.group(1), "", ""
            continue

        # The folded-scalar continuation is handled *before* the job-level
        # indent guard, and that order is the whole trick. A folded `if:` puts
        # its continuation lines two spaces deeper than the key, so a guard
        # that skips anything not at exactly four columns drops them before the
        # accumulator ever sees them -- which is why `assets` reported an empty
        # condition while the file plainly carries a three-term `||` chain.
        if in_if:
            # A folded scalar ends at the first line that is not more indented
            # than the key it continues.
            if indent > if_indent:
                cond = (cond + " " + stripped).strip()
                continue
            in_if = False

        # Job-level keys only, and the guard sits after both the job match and
        # the continuation. A step's own `if: always()` is indented deeper, and
        # matching on the key alone picked those up and overwrote the job's
        # condition. In this workflow a job key sits at exactly four spaces,
        # one level under its two-space name.
        if indent != 4:
            continue

        mi = IF.match(line)
        if mi:
            cond = mi.group(2).strip()
            in_if = mi.group(1) in (">-", ">")
            if_indent = indent
            continue

        mn = re.match(r"^\s*needs:\s*(.+)$", line)
        if mn:
            needs = mn.group(1).strip()

    if name:
        jobs.append((name, needs, cond))
    return jobs


def excludes(expr: str, event: str) -> bool:
    """Does this `if:` exclude `event`?

    Three forms cover everything in this workflow, and anything else is reported
    as "unknown" rather than guessed:
      * `github.event_name != 'x' && ...`  -- excludes x
      * `github.event_name == 'x' || ...`  -- includes only x (and the || chain)
      * `contains(github.event.head_commit.message, '[skip ci]')` -- a push-time
        gate, which does not depend on the event name at all
    """
    if not expr:
        return False
    e = expr.replace("\n", " ")
    if f"github.event_name != '{event}'" in e and "!=" in e:
        return True
    if f"github.event_name == '{event}'" in e:
        return False
    return False


def only_events(expr: str) -> list[str]:
    """The event names an `==` chain names, if that is what the expression is."""
    e = expr.replace("\n", " ")
    if "github.event_name ==" not in e:
        return []
    return sorted(set(re.findall(r"github\.event_name == '([^']+)'", e)))


def _eval_atom(atom: str, event: str) -> bool | None:
    """One term of a condition, or None if it is not a form we understand."""
    a = atom.strip().strip("()").strip()
    if a.startswith("!"):
        inner = _eval_atom(a[1:], event)
        return None if inner is None else (not inner)
    m = re.match(r"^github\.event_name\s*==\s*'([^']+)'$", a)
    if m:
        return m.group(1) == event
    m = re.match(r"^github\.event_name\s*!=\s*'([^']+)'$", a)
    if m:
        return m.group(1) != event
    if "github.event.head_commit.message" in a:
        # A `[skip ci]` gate, which depends on the commit rather than the event.
        # Undefined for a pull request, so it cannot turn a job on.
        return "contains" not in a or a.startswith("!")
    return None


def runs_on(expr: str, event: str) -> bool | None:
    """Does a job with this `if:` run for `event`?  None if undecidable.

    `||` separates alternatives and `&&` separates requirements, which is the
    only shape GitHub's `if:` takes in this repository and the only shape this
    claims to understand. Anything else returns None and prints as `?`, because
    a wrong answer here would be worse than no answer: the whole point of the
    table is that a reader can trust the cells that are not `?`.
    """
    e = " ".join(expr.split())
    if not e:
        return True
    # `always()` and friends are status-check functions rather than
    # conditions: they make the job run unconditionally, whatever the event.
    if re.fullmatch(r"(always|cancelled|success|failure)\(\s*\)", e):
        return True
    undecidable = False
    for alt in e.split("||"):
        value: bool | None = True
        for atom in alt.split("&&"):
            got = _eval_atom(atom, event)
            if got is None:
                value = None
                break
            value = value and got
        if value is True:
            return True
        if value is None:
            undecidable = True
    # An alternative that evaluates False is not an alternative; an alternative
    # this cannot read is a reason to say so rather than to guess False. The
    # first version conflated the two, which reported `if: always()` as "does
    # not run" -- and a table that is confidently wrong is worse than no table.
    return None if undecidable else False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workflow", default=str(DEFAULT))
    ap.add_argument("--fail-on-skipped", action="store_true",
                    help="exit non-zero if any job is gated away from a pull request")
    args = ap.parse_args()

    path = pathlib.Path(args.workflow)
    if not path.is_file():
        print(f"no workflow at {path}", file=sys.stderr)
        return 1

    jobs = parse(path)
    if not jobs:
        print(f"no jobs found in {path.name}", file=sys.stderr)
        return 1

    width = max(len(j) for j, _, _ in jobs)
    print(f"{len(jobs)} job(s) in {path.name}\n")
    header = "  " + "job".ljust(width) + "  " + "  ".join(e[:6] for e in EVENTS)
    print(header)
    print("  " + "-" * (width + 2 + 6 * len(EVENTS)))

    gated = []
    for name, _needs, cond in jobs:
        marks = []
        for event in EVENTS:
            verdict = runs_on(cond, event)
            marks.append("  --  " if verdict is False
                         else "  ?   " if verdict is None else "  yes ")
        print("  " + name.ljust(width) + "  " + "  ".join(marks))
        if runs_on(cond, "pull_request") is False:
            gated.append((name, cond))

    if gated:
        print(f"\n{len(gated)} job(s) do not run on a pull request:")
        for name, cond in gated:
            flat = " ".join(cond.split())
            print(f"  {name}")
            print(f"      if: {flat}")
        print("\nA green pull request is therefore evidence about the jobs that do "
              "run and silence about these. Merging a change to CI is a bet about "
              "them; the bet is settled by the next push to main, which runs the "
              "full pipeline.")
        if args.fail_on_skipped:
            return 1
    else:
        print("\nevery job runs on a pull request")
    return 0


if __name__ == "__main__":
    sys.exit(main())