# Adding a template: the Pascal and Ada families

Eleven entries, two languages, and the traps are the same two: `program` versus
`procedure`, and a semicolon that is mandatory in one and illegal in the other.

## The trap

```pascal
program HelloWorld;
begin
  writeln('Hello World!');
end.
```

This is Pascal, and it is wrong in Ada — Ada has no `program`, and its entry
point is a `procedure`. And in Object Pascal it is incomplete, because
Object Pascal's console unit is not implicitly available.

## The Pascal side

| entry | what it is | its Hello World |
|---|---|---|
| Pascal | the original, ISO 7185 | `program … begin writeln(…) end.` |
| Object Pascal | Free Pascal and Delphi's dialect | `program … begin writeln(…) end.` — plus `uses SysUtils` for some I/O |
| Delphi | Object Pascal plus the VCL | `program … begin writeln(…) end.` |
| Free Pascal | the compiler and its dialect | as Object Pascal |
| PascalABC | a compiler with its own dialect | as Pascal, and its unit is `uses`d |
| Turbo Pascal | the 1980s compiler | as Pascal, and the file is `.pas` with a header |

All six want the same shape, which is why they can share a program:

```pascal
program HelloWorld;
begin
  writeln('Hello World!');
end.
```

Two details. The program block is `begin … end.` — a semicolon *after* `end`,
not before, which is the one that catches everyone. And `writeln` is Pascal's
line-writing procedure; `write` does not add a newline.

## The Ada side

Ada's entry point is a procedure, and the language is strongly typed so the
signature is not optional:

```ada
with Ada.Text_IO;

procedure Hello_World is
begin
   Ada.Text_IO.Put_Line ("Hello World!");
end Hello_World;
```

Four differences from Pascal, and each one is a compile error if you miss it:

**No `program` keyword.** Ada has `package`, `procedure` and `function`. The
procedure is the program's main.

**The name is repeated at the end.** `end Hello_World;` — and the semicolon is
*inside*, after the name. This is the only place in either language where the
semicolon goes after the end, and it is Ada's rule rather than Pascal's.

**The unit is named.** `Ada.Text_IO`, not `Text_IO`, unless there is a `with`
and a `use`. The `with` makes it visible; `use` makes it unqualified.

**Ada 2012's `pragma Ada.Text_IO.Put_Line`** is the modern form, and GNAT accepts
both.

## The dialects worth knowing about

**GNAT** is the name of the compiler, not the language — and Linguist's entry
`Ada` covers both. **GNATprove** is a verification tool whose `.gpr` file is a
*project* declaration, which is a different kind of file entirely:

```ada
project Hello is
   for Source_Dirs use ("src");
   for Object_Dir use "obj";
end Hello;
```

A `.gpr` file is a declaration form. The greeting goes in the project name or a
comment, and there is no program in it.

## Before you write one

- Is this Pascal or Ada? The entry point is the tell: `program` or `procedure`.
- Where does the semicolon go at the end? Pascal: after `end`. Ada: after the
  name, inside.
- Is the unit qualified? Ada says `Ada.Text_IO.Put_Line` unless you `use`d it.
- Is the entry point really a type declaration? Delphi's `.dpk` and GNAT's `.gpr`
  are declarations, not programs.