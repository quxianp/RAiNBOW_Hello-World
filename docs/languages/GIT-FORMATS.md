# Adding a template: the git formats

Six entries in this repository are not languages and never were. They are file
formats that `git` reads, and Linguist counts them because Linguist counts
everything with an extension.

## The trap

A `.gitattributes` file is a list of attributes and paths. There is no program in
it, no main function, and nowhere to put a greeting except in a comment — and
`#` is git's own comment marker *in this format*, which is convenient, and the
reason a naive `print("Hello World!")` template is both impossible and wrong.

## The six

| entry | what git reads it for | what its content is |
|---|---|---|
| Git Attributes | `.gitattributes` — path/extension attributes | patterns and attribute names |
| Git Config | `.gitconfig` — repository and user configuration | `key = value` |
| Git Commit | `COMMIT_EDITMSG` — the message template | a message |
| Git Revision List | `.gitrevlist` — paths rev-list touches | patterns |
| Ignore List | `.gitignore` — ignored paths | patterns |
| Git Module | `.gitmodules` — submodule declarations | `[submodule "…"]` sections |

## The two that are literally just patterns

**Git Attributes** and **Ignore List** are lists of glob patterns. An attribute
line is `pattern attr1 attr2=value`, and a `.gitignore` line is a pattern with
optional negations. Neither has a body:

```gitattributes
# Git Attributes - Hello World! :: RAiNBOW_Hello-World
*.hello.text diff=hello
# Hello World!
```

The greeting goes in a comment, because that is the only place a `.gitattributes`
file has prose. And `#` is a comment in this format, so it costs nothing.

**Git Revision List** is the same idea with a different purpose: it is the list of
paths `git rev-list` passes to its diff, and it contains patterns and nothing
else.

## The one that has a value

**Git Config** is `key = value` pairs, which makes it a declaration form rather
than a pattern list:

```ini
[hello]
	greeting = Hello World!
```

A `[section]` and a tab-indented key. This is a real `.gitconfig` and it is what
the file should be — a section whose name is the language and one key that holds
the greeting. A `.gitconfig` containing a shell command is a file git will
happily ignore, which is worse than a placeholder because it looks configured.

## The two that are messages

**Git Commit** is a commit message template. The file *is* the message, so its
Hello World is a message:

```
Hello World!

The commit that added this file, in the only form a commit message can take.
```

**Git Module** is `[submodule "name"]` sections with `path`, `url` and `branch`.
The greeting belongs in a key value, and the only free text in one is the
submodule's name or its URL path — so `url` is the honest field.

## Before you write one

- Is this a pattern list, a key/value file, or a message? Three different shapes
  for six entries.
- Is the comment marker available? `#` works in all six, and it is the reason a
  greeting in a comment is not a workaround here — it is the format.
- For Git Config: is it a section git would read? A key outside a section is
  ignored.
- For Git Module: is every key one git knows? An unknown key in `.gitmodules` is
  an error rather than a comment.