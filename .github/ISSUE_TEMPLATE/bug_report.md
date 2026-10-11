---
name: Bug report
about: Something in the pipeline or the bar is wrong
title: ""
labels: bug
assignees: ""
---

## What happened

<!-- A clear, short description of the problem. -->

## What I expected

<!-- What you expected instead. -->

## Reproduction

```bash
# the exact commands you ran
```

<!-- If this is about the language bar, paste the output of: -->

```
python scripts/audit_repo.py
```

## Environment

- OS:
- Python version (`python --version`):
- Branch / commit (`git rev-parse --short HEAD`):

## Extra context

<!-- Anything else: screenshots, logs, partial API responses. -->

> A note before you file: GitHub's own language panel is served from an edge
> cache and can show an **older** breakdown than the repository actually has.
> Hard-reload first. If the panel says `HTML 27.6 %` while
> `GET /repos/quxianp/RAiNBOW_Hello-World/languages` reports HTML at 1.0116 %,
> the cached page is stale rather than the bar being wrong. See the README
> section "Why you cannot see C and C++ named on the site".