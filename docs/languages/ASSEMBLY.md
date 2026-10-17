# Adding a template: the assembly families

Eighty-odd of this repository's entries are assembly for a specific machine, and
almost none of them wants a C program with a different comment character.

## The trap

Writing

```asm
mov eax, 4
mov ebx, 1
; ...
```

into `hello/full/arm64-assembly/` produces a file that is plausible, passes every
check in this repository, and assembles on no machine at all.

Each architecture has **its own syscall convention**, and that convention *is*
the program:

| architecture | syscall |
|---|---|
| 8080 | BDOS trap 5, so `mvi e, 0Ah` / `call 5` |
| 6502 family | no syscall — a screen register (`$E00C`), KERNAL (`$FFD2`), or PPU (`$2007`) |
| ARM / AArch64 | `svc #0`, arguments in `a0`–`a2`, number in `a7` |
| 32-bit ARM | `svc 0`, arguments in `r0`–`r2` |
| RISC-V | `ecall`, number in `a7` |
| SPARC | register-window traps, `%hi`/`%lo` to split an address |
| PowerPC | the shortest of these, four moves and a trap |
| AVR 8-bit | `out` to `UDR0`, and `sbiw` to step the string pointer |
| 8051 | the classic `mov dptr`, `movc a,@a+dptr` pointer walk |
| PIC 16/18/32 | bank switching, and `#define`/`#include` before anything |
| 6502 in an emulator | the vector at `$FFFC` matters |

## The honest exception

**A microcontroller with no display cannot print.** PIC16 is the case that
demonstrated this: the program that blinks an LED never greets, and
`add_templates.py` refuses it, correctly. `docs/HOW-FILES-GET-THEIR-CONTENT.md`
records why a wrong program is worse than an honest admission.

## Object and container formats are not assembly

`.coff`, `.omf`, `.intel-hex`, `.motorola-s-record`, `.llvm-bitcode`, `.dwarf`
and `.tiff` are *file formats*. They have headers, and in three of those cases
they have **checksums**:

```
:0C00000048656C6C6F20576F726C6421B7     Intel HEX
 count 0x0C, offset 0, type 00, 12 data bytes, checksum B7.
 Sum of the bytes is 1097 = 0x449; the checksum is 0x100 - 0x49.

S10F000048656C6C6F20576F726C6421B3     Motorola S-record
 count 0x0F = 2 address bytes + 12 data + 1 checksum.
 Sum is 1100 = 0x44C and S-records use the ones complement: ~0x4C = 0xB3.
```

A checksum recalled from memory is wrong in one byte and reads as correct, which
is why every one of them in this repository was produced by the library that
defines the format and is checked by `scripts/verify_encodings.py`.

## Before you write one

- Find out how the machine *exits*. Most do not just fall off the end.
- Find out how it *prints*. On a 6502 that is the single most important detail
  in the program.
- If it has a memory model, the pointer walk is the program, not the output
  call.
- If it is a format with a checksum, compute it.