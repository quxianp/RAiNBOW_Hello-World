# Adding a template: the Ruby and PHP families

Two languages with several dialects each, and in both families the trap is the
same: the dialects are close enough that a template copied between them compiles
and behaves differently.

## Ruby

```ruby
puts "Hello World!"
```

is Ruby, and it is Ruby 1.8 through 3.x. What differs is not the syntax but the
*encoding of the source file*, and that is a real trap here: Ruby 1.9 changed
the default source encoding to UTF-8, and a file with no magic comment in a
repository full of UTF-8 should declare it anyway.

```ruby
# encoding: utf-8
puts "Hello World!"
```

| entry | what it is | note |
|---|---|---|
| Ruby | the language | as above |
| Ruby (irb) | the REPL | a REPL echoes what you type, so the program is a line |
| Gemfile | Bundler's dependency declaration | a declaration form, not a program |
| Ruby Module | `.rb` declared as a module | needs `module` and a value |
| RSpec | a test framework's configuration | a declaration form |

**The `.gem` file** is a Ruby *program* that describes a gem, and it is one of
the nicer declaration forms in this repository because it has a real DSL:

```ruby
Gem::Specification.new do |s|
  s.name        = "hello"
  s.version     = "1.0.0"
  s.summary     = "Hello World!"
  s.authors     = ["quxianp"]
end
```

That is a genuine gemspec and the greeting is the summary, which is the field a
person reads.

## PHP

```php
<?php echo "Hello World!\n";
```

is PHP, and the `<?php` is not optional in the sense people expect — it is the
only thing that tells the file it is PHP rather than HTML. And **the closing `?>`
is optional**, which matters because a file that omits it will emit nothing after
the PHP block.

| entry | what it is | note |
|---|---|---|
| PHP | the language | needs `<?php` first |
| Hack | Facebook's PHP dialect | typed, and `echo` is still `echo` |
| Psalm | a static analyser | its `config.xml` is a declaration form |
| Composer (JSON) | a dependency manifest | a declaration form |
| PHP Config | a `.user.ini` | `greeting = "Hello World!"` |

## The trap in both: the opening tag

The single most common wrong answer in these two families is a template with no
`<?php` or no `require`. A PHP file that is just `echo "Hello World!";` is a file
that outputs its own source when requested over HTTP, and a Ruby file that is
just a method body is a fragment that raises `NameError` at the first call.

Both are *loadable* and both are wrong, which is the failure mode this
repository's whole template policy exists to catch.

## Before you write one

- Is this the language or one of its dialects? Hack is typed and PHP is not.
- Is the file a program or a declaration? `Gemfile`, `.gemspec`, `.user.ini` and
  `composer.json` are declarations, and the template guard knows that by
  extension.
- Is the opening tag present? For PHP it is the entire difference between PHP and
  HTML.
- Does the dialect need a source-encoding comment? Ruby does, and this
  repository's files are UTF-8.