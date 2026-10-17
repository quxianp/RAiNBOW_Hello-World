# Adding a template: the C family

Nine entries on the bar whose names start with C, and they are more different
from each other than the names suggest.

## The trap

```c
#include <stdio.h>
int main(void) { printf("Hello World!\n"); return 0; }
```

compiles as C, as C++, and — with a `using namespace std;` — as neither without
a change. It is also wrong in three of the nine, and wrong in a way that a
compiler catches only if you happen to compile it with the right standard.

## The nine

| entry | what it actually is | its Hello World |
|---|---|---|
| C | the language | `int main(void) { puts("Hello World!"); return 0; }` |
| C++ | a superset, and a different one | `std::cout << "Hello World!\n";` |
| C-- | a deliberately smaller C, from the same design lineage as Go and D | `proc main() { puts("Hello World!"); }` |
| C#, F#, Visual Basic .NET | **C# is not C.** It is a .NET language | `Console.WriteLine("Hello World!");` |
| Objective-C | C plus message sending | `NSLog(@"Hello World!");` |
| Objective-C++ | both | `NSLog` again, with C++ available |
| Cuda | C plus device qualifiers | the kernel writes to memory; the host reads it back |
| Cirru | a visual syntax that compiles to a tree | not source text |

## The two that get confused with C hardest

**C#** shares a name and nothing else. It has no header files, no `printf`, no
`int main` — it has `static void Main()` and `Console.WriteLine`. A C program in
a `.cs` file does not compile and the compiler's first message is about `using`,
not about `main`.

**C--** is smaller than C by design, and the difference shows in the entry point:
C-- uses `proc main()` rather than `int main(void)`. That is not a stylistic
choice; `proc` is a keyword and the file is not C.

## The three that cannot print

**Cuda** has no output instruction. A kernel writes to device memory and the
host copies the buffer back and prints it — so the program's output is on the
*host* side, in ordinary C++. A Cuda file whose kernel prints is a file that
does not compile, and one that fakes the print is a file that misrepresents
where the output came from.

**Objective-C** can print (`printf` works) but the idiomatic way is `NSLog`,
which is what every Objective-C tutorial opens with and what a reader expects to
see. `NSLog` also appends a newline, which `printf` does not — a difference you
notice when the output has one extra blank line.

**Cirru** is a visual notation. Its source is a diagram of characters; the text
form is generated *from* it. Writing text into a `.cirru` file produces
something that is not a Cirru program.

## Before you write one

- Is it C, or is it a language that starts with the letter C? C#, F#, Visual
  Basic .NET and Cirru are not C.
- Is it a superset or a subset? C++ is a superset and should use `std::cout`;
  C-- is a subset and uses `proc main()`.
- Where does the output come from? For Cuda it is the host, not the device.
- Is the entry text at all? For Cirru it is not.
- Does the output operation add its own newline? `NSLog` does, `printf` does
  not, and `puts` does.