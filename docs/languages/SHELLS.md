# Adding a template: the shell family

Fifteen-odd entries, one word "shell" in most of them, and a distinction that
matters more than any other in this guide: **a shell script is not a program in
the shell, and `print` is not a thing any of them have.**

## The trap

```sh
print "Hello World!"
```

is not POSIX shell. It is `print` as a *function* — in ksh it is a builtin, in
zsh it is a builtin, and in bash it does not exist at all. Copying the line
between three entries produces one that works and two that fail, and the two
that fail are the two people are most likely to run.

The answer in every POSIX shell is `echo` or `printf`, and they differ:

| | behaviour |
|---|---|
| `echo "Hello World!"` | POSIX says the behaviour is undefined for `-n`, `-e` and backslash escapes. It works in bash's builtin and in dash, and they disagree about backslashes. |
| `printf 'Hello World!\n'` | defined everywhere, and `\n` is a real newline rather than two characters |

This repository's own `run.sh` uses `printf`, and the reason is not stylistic.

## The families

| entry | what it is | what its Hello World is |
|---|---|---|
| POSIX shell / Bourne shell | the standard | a shebang and `printf` |
| Bash | adds arrays, `[[ ]]`, `$'...'`, process substitution | a Bash script |
| Zsh | adds globbing qualifiers and `=(...)` | a zsh script |
| Ksh | `print` **is** a builtin here, and it is the idiomatic choice | `print "Hello World!"` |
| Tcsh | C shell; the syntax is not Bourne at all | `echo Hello World!` |
| Fish | C shell's descendant, not Bourne's; `echo` takes options as `-s` | `echo Hello World!` |
| Elvish | structured, with `echo` a command and `pprint` the pretty one | `echo 'Hello World!'` |
| Nushell | structured data, no strings as a concept | `print "Hello World!"` |
| Xonsh | Python with shell syntax | `print("Hello World!")` |
| Slurm | a resource manager's batch language, not a shell | a `#SBATCH` header and an `echo` |
| ECL / ECLiPSe | constraint solving; it has no shell | see `PROVERS-AND-SOLVERS.md` |

## The trap inside the trap: shebang or not

The standard says a shell script starts with `#!`, and the repository's
generator puts a comment banner at the top of every file. Those two things fight
for the same first line.

The resolution in this repository is that a shebang is part of the *program* and
the banner goes after it:

```sh
#!/usr/bin/env bash
# RAiNBOW_Hello-World :: Bash :: Hello World!
```

A file that begins with a banner and no shebang is not executable by name, and
a file that begins with a shebang and then a banner is fine. `tests/
test_shell_variables.py` guards the other direction — the demo's `run.sh` used
to read `$FAST` under `set -u` behind a `[ -t 1 ]` test no local run reached,
and that is E31.

## The trap that is really a portability bug

`echo` versus `printf` is a portability bug in both directions:

- `echo -e "a\tb"` — the `-e` is an extension. In POSIX `echo`, `-e` is the
  *string*, so you get `-e a<TAB>b` on a strict shell.
- `printf "Hello World!\n"` — but `printf` is a shell builtin that some minimal
  `sh` builds lack, and it does not accept a bare `\n` in the format the way
  `echo` does.

So a template for a POSIX shell should use `printf`, and a template for ksh
should use `print`, and the commit message for the ksh one should say which is
why — otherwise the next person "fixes" it.

## The batch languages are not shells at all

**Slurm**, **LSF**, **Grid Engine** and **PBS** have `#SBATCH`/`#BSUB`/`#$`
comment markers that are read by a *scheduler*, not by a shell. The comment
marker matters: a `#SBATCH` line in a script that is not submitted through
Slurm is just a comment, and writing one in a POSIX-shell entry would be a
fabrication.

A batch-language template is therefore a scheduler header followed by one
command, and the honest comment is that the scheduler is what runs it.

## Before you write one

- Which shell, specifically? Not "shell".
- Does this shell have `print`? Only ksh and zsh, as a builtin.
- `echo` or `printf`? And if `printf`, does the shebang's interpreter have it?
- Does the file need a shebang, and does the banner go after it?
- Is this actually a batch language, and is the comment marker the scheduler's?