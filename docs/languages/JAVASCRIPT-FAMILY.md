# Adding a template: the JavaScript family

Sixteen entries that all run on a JavaScript engine, and the differences are
almost entirely in three places: the module system, the type system, and
whether the program is a *file* or a *component*.

## The trap

```js
console.log("Hello World!");
```

is JavaScript. It is also the answer for Node.js, and for most of the family as a
*default export*. But it is wrong in the three entries where the module system
matters, wrong in the four where the type system matters, and simply not
applicable to the entries that are components rather than programs.

## The three axes

**Module system.**

| entry | module | its Hello World |
|---|---|---|
| JavaScript | none | `console.log("Hello World!");` |
| Node.js | CommonJS | `console.log("Hello World!");` — same program |
| ECMAScript | ES modules | `console.log("Hello World!");` — same program |
| TypeScript | ES modules, compiled | `const greeting: string = "Hello World!";` |
| JSX | JS with JSX syntax | a function returning `<h1>Hello World!</h1>` |
| TSX | TypeScript with JSX | the same, typed |
| CoffeeScript | compiles to JS | `console.log "Hello World!"` — **no** parentheses |
| Dart | its own runtime | `void main() { print("Hello World!"); }` |
| ActionScript | Flash, gone | `trace("Hello World!");` — `trace`, not `console.log` |

## The four that are genuinely not JavaScript

**CoffeeScript** compiles to JavaScript and its call syntax is bare:

```coffee
console.log "Hello World!"
```

No parentheses. An English-word JavaScript template in a CoffeeScript file is a
file that reads as a property access.

**TypeScript** is a superset, so the program is the same — but the *point* of
the entry is the type, so a TypeScript template that adds no annotation is a
JavaScript file with a `.ts` extension:

```ts
const greeting: string = "Hello World!";
console.log(greeting);
```

**Dart** is a different language with a different runtime. `main` is a top-level
function with `void`, and `print` is Dart's:

```dart
void main() {
  print("Hello World!");
}
```

**ActionScript** was Flash's. Its output is `trace()`, which went to the Flash
debugger and nowhere else — so a Flash program has no console, and `trace` is
the only thing that resembles one.

## JSX and TSX are components, not programs

A JSX file's unit is a component, and a component returns markup:

```jsx
export default function HelloWorld() {
  return <h1>Hello World!</h1>;
}
```

That renders. It does not run on its own and it prints nothing. The honest
comment is that JSX describes something a renderer displays, and that the
greeting is in the rendered output rather than on a terminal.

## The two that are extensions of another file

**Vue** and **Svelte** are `.vue` and `.svelte` files that contain three things
in one: a `<template>` block, a `<script>` block, and a `<style>` block. The
greeting belongs in the template, because that is what gets rendered:

```vue
<template>
  <h1>Hello World!</h1>
</template>

<script>
export default { name: "HelloWorld" }
</script>
```

**Astro** is the same idea with a frontmatter fence instead of a `<script>`
block. Getting this wrong produces a `.vue` file with a `<script>` in it, which
the Vue compiler accepts and renders nothing.

## Before you write one

- Is this JavaScript, or a language that compiles to it? CoffeeScript is not
  JavaScript and neither are Dart and ActionScript.
- Does it have a module system that the entry point must satisfy?
- Is a type annotation part of what makes the entry worth having? For TypeScript
  it is.
- Is the unit a program or a component? JSX, TSX, Vue and Svelte render; they
  do not run.