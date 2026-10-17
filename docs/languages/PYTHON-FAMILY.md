# Adding a template: the Python family

Fourteen entries whose names begin with Python or Jython or Iron, and only one of
them is CPython.

## The trap

```python
print("Hello World!")
```

is correct for CPython and for most of the family, and it is *too correct* for
three of them. A file whose whole claim is that it is not CPython should not be a
file that would run unchanged on CPython.

## The entries that really are Python

| entry | what it is |
|---|---|
| Python, Python console, IPython, Jupyter, Sage, RPython, MicroPython, Brython | Python or a dialect of it |
| Cython | compiles to C, and its own Hello World should say so |
| Jython | compiles to the JVM; the source is Python |
| IronPython | compiles to .NET; the source is Python |
| PyPy | a Python *implementation*, not a language |

For the ones that are Python, `print("Hello World!")` is the right answer and
there is nothing to add. For an implementation like PyPy there is nothing to add
either, because PyPy has no file format — the `.py` entry it contributes is
Python's, and that is an honest duplicate rather than a missing one.

## The two that are worth more than a print

**Cython** compiles Python to C. Its own Hello World should show the thing that
makes it Cython rather than Python — and the thing is a typed block:

```cython
def main():
    print("Hello World!")

if __name__ == "__main__":
    main()
```

with a `cdef` block, because that is what Cython adds and what a Python file
with a `.pyx` extension does not demonstrate.

**Sage** is a mathematical programming system built on Python. Its greeting
should evaluate something, because that is the point of the language:

```sage
print(factor(2024))
```

## The three that cannot print at all

**Jython** and **IronPython** can — they have `print`. But they run on a JVM and
a .NET runtime respectively, and neither is on CI here, so what matters for the
*file* is that it is valid Python, which `print` is.

**Magma** is a computer algebra system in the same family and its output
operation is `print` with a different signature. **SageMath** likewise.

The one that genuinely cannot is **NumPy**'s own `.pyi` — no. The real case is
**micropython**, which does have `print`, so all of these are fine and the only
genuine trap in this family is the boring one: a `.pyi` stub file has no body,
because it is a type stub.

## Type stubs, which is the one that is not a program

A `.pyi` file declares interfaces and nothing else. Every statement is an
ellipsis or an annotation:

```python
def main() -> None: ...
```

That is the whole file. It is not a degraded Hello World; it is the format. The
same applies to `.pyi`'s siblings in other languages — `.pyi` is the Python
entry, and the test `tests/test_declaration_forms.py` guards the family.

## Before you write one

- Is this Python, an implementation of Python, or something that compiles to it?
  PyPy is an implementation; Cython and Jython compile.
- Is the file a type stub? `.pyi` has no body and that is correct.
- If the entry is a language that Python compiles to, does the file show what the
  compilation adds? A Python program with a `.pyx` extension demonstrates
  nothing about Cython.
- Is this dialect's `print` Python's? Sage, Magma and Jython all say `print`,
  and only Sage's returns a value worth showing.