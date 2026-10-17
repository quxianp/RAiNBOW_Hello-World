# Adding a template: web templating languages

About twenty-five entries here are templating languages, and none of them is a
programming language in the way `echo` is. They are string substitution with a
layer of control flow, and the layer is where the syntax is.

## The trap

Every one of these is HTML plus syntax, so it is very tempting to write a file
that is `<h1>Hello World!</h1>` and call it a program. For most of them that is
wrong in an interesting way: a template is not a document, it is a document
*with holes in it*, and a template with no holes in it is a template that does
nothing.

## What a template actually looks like

| entry | syntax | its Hello World |
|---|---|---|
| Twig | `{{ … }}`, `{% … %}` | `<h1>{{ greeting }}</h1>` with `greeting` set to the string |
| Jinja2 | `{{ … }}`, `{% … %}` — same syntax as Twig | same shape |
| Nunjucks | `{{ … }}` plus JS expressions | same shape |
| Handlebars | `{{ … }}`, no logic in the template by design | `<h1>{{greeting}}</h1>` |
| Mustache | `{{ … }}` only; no logic at all | `<h1>{{greeting}}</h1>` |
| Liquid | `{{ … }}` and `{% … %}`, but **only** the Shopify tags | `{{ 'Hello World!' }}` |
| ERB | `<% … %>` in an HTML file | `<h1><%= "Hello World!" %></h1>` |
| EJS | `<% … %>`, two tags | `<h1><%= "Hello World!" %></h1>` |
| Blade | `{{ … }}` and `@…` directives | `<h1>{{ 'Hello World!' }}</h1>` |
| Pug / Jade | indentation; the HTML is *generated* | `h1= "Hello World!"` |
| Haml | indentation, like Pug with different syntax | `%h1= "Hello World!"` |

## The three that are not templating languages at all

- **Twig, Jinja2 and Nunjucks** are Python, JavaScript and JavaScript
  respectively, embedded in markup. Their expressions are real expressions from
  that language, so `{{ 'Hello World!' }}` is a Python string literal, a
  JavaScript string literal and a JavaScript string literal respectively.
- **ERB** is Ruby, not a template language; `<%= expr %>` is Ruby.
- **Blade** is PHP with a `{{ }}` syntax on top; the PHP is escaped behind
  `@php`.

## Pug and Haml are the trap inside the trap

A Pug file does not contain HTML. It *generates* it:

```
h1= "Hello World!"
```

compiles to `<h1>Hello World!</h1>`. Writing HTML into a Pug file produces a file
that Pug parses as text nodes and renders escaped, which is a file that loads and
displays `&lt;h1&gt;Hello World!&lt;/h1&gt;`. Same for Haml. Neither has a comment
syntax that reads naturally in an indented language, so the greeting goes in a
Pug line comment (`//-`) or not at all.

## Liquid cannot do what the others do

Liquid's tag set is fixed and small, by design — a template that can run
arbitrary code is a template that lets a shop owner run code. There is no
`printf`, no function call beyond a handful, and no arithmetic beyond addition.
So `{{ 'Hello World!' }}` is not a simplification; it is the most Liquid can do,
and a Liquid template calling a function would be rejected by Shopify.

## Before you write one

- Is the template's expression language Python, Ruby, PHP or JavaScript? Name
  it, because the difference is the syntax inside the braces.
- Does this language generate HTML (Pug, Haml) or contain it (everything else)?
- Are there logic tags at all? Handlebars and Mustache deliberately have none.
- Is the greeting in the template or in the context that fills it? Both are
  correct; putting it in the template and saying so is what distinguishes the
  two.