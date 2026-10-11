// Unix Assembly - Hello World! :: RAiNBOW_Hello-World
//   colour     : not assigned by Linguist
//   layer      : full (byte-balanced rainbow bar)
//   upstream   : https://github.com/quxianp/RAiNBOW_Hello-World
//   reference  : see https://esolangs.org/ and https://rosettacode.org/

#!/usr/bin/env bash
# Unix Assembly -- Hello World!
.section .data
msg:
  .ascii "Hello World!\n"
.section .text
.globl _start
_start:
  mov $1, %rax
  mov $1, %rdi
  mov $msg, %rsi
  mov $14, %rdx
  syscall
  mov $60, %rax
  xor %rdi, %rdi
  syscall
