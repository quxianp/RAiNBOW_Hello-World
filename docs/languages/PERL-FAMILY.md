# Adding a template: the Perl family

Perl, Raku and Perl 6, and the difference between them is not cosmetic: it is
whether a sigil is part of a variable's name.

## The trap

```perl
print "Hello World!\n";
```

is Perl 5 and it is *not* Raku. Raku's `print` is a function, takes parentheses
like any other function, and the string is quoted the same way — so this program
is valid in both by accident, and the same accident makes it a poor Raku program.

The real difference is the sigil, and it is visible in one character:

```perl
my $greeting = "Hello World!";
print "$greeting\n";
```

```raku
my $greeting = "Hello World!";
$greeting.say;
```

In Perl, `$greeting` interpolates into the double-quoted string. In Raku, `$greeting`
is a *container* — the sigil names the container, not the variable — and string
interpolation requires a method: `"$greeting"` gives you the container's name, not
its contents. Raku's idiom is `.say` or `"... $greeting()"` with the parens.

## The entries

| entry | what it is | its Hello World |
|---|---|---|
| Perl | the language | `print "Hello World!\n";` |
| Perl 6 | the old name for Raku | as Raku |
| Raku | Perl 6, renamed | `say "Hello World!";` |
| PerlTidy | a *formatter* | a declaration, not a program |
| Pod | Perl's documentation format | a documentation block |
| Perl Module | `.pm` — a module, with a package statement | `package Hello; … 1;` |

## The three that are not programs

**Pod** is embedded documentation. A `.pod` file is a document, and the greeting
is a paragraph:

```perl
=head1 NAME

Hello World! - the canonical Perl program

=cut
```

That is a valid Pod document and the whole of it.

**PerlTidy** is a code formatter's configuration file. It has options and no
program, so it is a declaration form.

**Perl Module** is a module, and a module has two obligations: a package
statement and a true value at the end.

```perl
package Hello::World;

use strict;
use warnings;

sub hello { return "Hello World!"; }

1;
```

The trailing `1;` is not optional. A `.pm` without it does not load, and Perl
says so at `require` time rather than at compile time, which is the worst
possible place to find out.

## Before you write one

- Is this Perl 5 or Raku? The sigil interpretation changed and it changes what a
  string interpolation means.
- Is it a module or a script? A `.pm` needs a `package` and a true last
  expression.
- Is it Pod? Then the file is a document and the greeting is a paragraph.
- Is it a formatter's configuration? Then there is no program and the fields are
  the answer.