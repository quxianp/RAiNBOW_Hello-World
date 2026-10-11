# Security Policy

## Supported versions

Only `main` is supported. This repository is a collection of "Hello World"
files plus the tooling that generates and verifies them.

| Version | Supported |
|---|---|
| `main` | yes |
| anything older | no |

## What this repository does and does not execute

This matters more here than in most projects, because the repository contains
thousands of programs in hundreds of languages.

- **Nothing in `hello/` is ever executed by the maintainers locally.** All
  compilation and execution happens inside GitHub Actions, on a throwaway
  runner, via `scripts/run_languages.py` and `run.sh`.
- **The files in `hello/core/` are not functional programs.** They are
  byte-balanced stubs: a modeline, a short banner, and comment padding to reach
  exactly 2048 bytes so each language occupies an identical slice of the
  language bar. Do not execute them expecting a working program.
- `run.sh` does execute whatever interpreters happen to be installed, and it
  runs `scripts/run_languages.py`, which may execute small snippets from
  `hello/full/`. Treat running it on an untrusted checkout as you would running
  any script from a stranger.

## Reporting a vulnerability

If you find a security problem, report it privately by opening a
[security advisory](https://github.com/quxianp/RAiNBOW_Hello-World/security/advisories/new)
rather than a public issue. Please include:

- what you did,
- what you expected,
- what happened instead,
- a minimal reproduction if you have one.

You can expect an acknowledgement within a few days and a fix or an explanation
of why the report is out of scope.

## Scope

In scope:

- the workflow in `.github/workflows/`,
- anything under `scripts/`,
- `run.sh` and `install_deps.sh`.

Out of scope, because these are inert data rather than code we run:

- the contents of `hello/core/` and `hello/full/` as files *on disk*,
- third-party actions referenced by the workflow,
- anything reachable only if you execute a file from `hello/` yourself.