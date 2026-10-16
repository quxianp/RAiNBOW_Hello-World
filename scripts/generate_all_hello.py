#!/usr/bin/env python3
"""Generate every Hello World file in the repository.

  core layer : hello/core/<slug>/hello.<ext>   -> counted by GitHub Linguist
  full layer : hello/full/<slug>/hello.<ext>   -> vendored, present but uncounted

Every file starts with a coloured banner comment, then a Hello World program
written in that language (a real template when we have one, a documented
equivalent otherwise), then a padding marker that scripts/balance_bytes.py uses
to tune the byte share of each core language.

Also writes hello/manifest.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
# Which placeholder files have a program and why the others do not. Written by
# scripts/classify_placeholders.py; read here so every program-less file can say
# specifically what it is instead of printing the same sentence as 6 241 others.
CLASSES_PATH = DATA / "placeholder_classes.json"
CONFIG = ROOT / "config"
HELLO_DIR = ROOT / "hello"
LOGS = ROOT / "logs"
for d in (DATA, CONFIG, LOGS):
    d.mkdir(parents=True, exist_ok=True)

REPO = "https://github.com/quxianp/RAiNBOW_Hello-World"

# --------------------------------------------------------------------------
# comment syntax: ext -> (line, block_start, block_end)
# --------------------------------------------------------------------------
C_HASH = ("#", None, None)
C_SLASH = ("//", None, None)
C_DASH = ("--", None, None)
C_SEMI = (";", None, None)
C_PCT = ("%", None, None)
C_BANG = ("!", None, None)
C_REM = ("REM", None, None)
C_NONE = (None, None, None)

C_BLOCK_JAVALIK = (None, "/*", "*/")

COMMENT: dict[str, tuple] = {}
for e in (
    ".py .pyw .pyi .rpy .rb .rbw .gemspec .podspec .sh .bash .zsh .ksh .csh .tcsh .fish "
    ".ash .dash .nu .nushell .ps1 .psm1 .psd1 .pl .pm .t .r .R .Rmd .rmd .q .jl .nim .nims "
    ".cr .coffee .elm .purs .re .rei .rkt .scm .ss .st .tcl .exp .ex .exs .escript .el .lisp "
    ".lsp .cl .scm .clj .cljc .cljs .edn .fnl .hx .idris .agda .lean .thy .als .v .vhd .vhdl "
    ".sv .svh .ucf .xdc .sdc .do .tcl .itcl .tclsh .ada .adb .ads .make .mk .mkfile .makefile "
    ".bp .cmake .cmake.in .pro .pri .qbs .gyp .gypi .ninja .sconstruct .scons .bazel .bzl "
    ".star .yaml .yml .toml .ini .cfg .conf .properties .env .editorconfig .gitignore .gitattributes "
    ".gitmodules .gitconfig .dockerignore .npmignore .eslintignore .tf .tfvars .hcl .nomad "
    ".justfile .just .sops .yamllint .mailmap .pep8 .flake8 .pylintrc .coveragerc .restructuredtext "
    ".tex .latex .sty .cls .dtx .ins .ltx .mkii .mkiv .mkiv .bib .d .di .vapi .cr .crontab "
    ".proto .thrift .avdl .capnp .smithy .cue .rego .nix .sml .ml .mli .fun .sig .scpt .applescript "
    ".au3 .ahk .nsi .iss .wxs .wxi .psmdip .nuspec .targets .props .csproj .fsproj .vcxproj "
    ".gradle .sbt .scala .sbt .hocon .conf .cnf .dot .gv .neato .gst .plantuml .puml "
    ".erb .rhtml .haml .slim .jbuilder .builder .twig .liquid .jinja .jinja2 .j2 .mustache .hbs "
    ".handlebars .ejs .eco .dust .vm .ftl .freemarker .thymeleaf .soy .peb .pebble .rte "
    ".rb.erb .erb .pug .jade .slm .styl .sass .scss.sass .css.scss .pcss .postcss .sss .stylus "
    ".styl .coffee .litcoffee .ls .elm .purs .rei .rescript .res .d.ts .dart .groovy .gvy .gy "
    ".gsh .gradle .jenkinsfile .groovy .haxe .hx .nims .nimble .cr .crystal .zig .odin .jai "
    ".vy .carbon .hare .hare .odin .nu .v .gd .tres .tscn .gdscript .gds .godot .cs .csx "
    ".cake .cakefile .ps1 .psm1 .psd1 .ps1xml .ino .pde .processing .ahk .au3 .nut .sqc "
    ".squirrel .tcl .tk .tclsh .expect .exp .itcl .m .mm .swift .swiftinterface .svelte "
    ".elm .sml .sig .scpt .applescript .vhd .ucf .xdc .tcl .vim .vimrc .gvimrc .nvim .doctypes "
    ".zsh-theme .zprofile .zlogin .zshrc .bashrc .bash_profile .profile .bash_login .inputrc "
    ".kshrc .mkshrc .cshrc .tcshrc .history .screenrc .nanorc .tmux.conf .muttrc .curlrc "
    ".wgetrc .netrc .npmrc .yarnrc .bowerrc .gemrc .irbrc .pryrc .psqlrc .my.cnf .flake8 "
).split():
    COMMENT[e] = C_HASH

for e in (
    ".js .mjs .cjs .jsx .ts .tsx .mts .cts .d.ts .json5 .jsonc .css .scss .sass .less .styl "
    ".stylus .astro .vue .svelte .wasm .wat .wast .jsb .es .es6 .node .d.mts .d.cts .map "
    ".glsl .vert .frag .geom .tesc .tese .comp .wgsl .hlsl .fx .fxh .vsh .psh .csh .shader "
    ".compute .asc .nks .cake .nut .ts .d .v .sv .svh .glsl .ps .asm .nasm .s .ms .masm "
    ".cpp .cc .cxx .c++ .hpp .hh .hxx .h++ .ipp .tcc .ino .pde .cu .cuh .metal .rc .rcore "
    ".mm .m .c .h .ixx .cppm .ccm .ino .frag .vert .geom .tesc .tese .rsh .rng .glslv .ray "
    ".agda .idr .lidr .jaid .purs .elm .re .rei .res .resi .cairo .sol .move .vy .yul "
    ".glsl .esc .vert .frag .geom .spv .asm .pico8 .lua .rb .d .css .ts .js .json5 "
).split():
    COMMENT[e] = C_SLASH

for e in (
    ".sql .psql .tsql .hql .hive .presto .trino .sparql .cypher .gremlin .cypher .cql .cql "
    ".rq .sparql .ttl .n3 .nt .nq .trig .sru .rel .xquery .xq .xql .xqy .xqil .xhtml .xslt "
    ".xsd .dtd .rng .wsdl .soap .wsf .wxi .wsx .xaml .cs .vb .bas .frm .cls .vba .vbs "
    ".pas .pp .inc .sas .sas7bdat .esql .hsql .plsql .plhql .ddl .dml .dcl .sqlcmd .mysql "
    ".pgsql .plpgsql .tsql .h2sql .cockroachql .clickhouse .vertica .teradata .snowflake "
).split():
    COMMENT[e] = C_DASH if e not in (".vb", ".vba", ".vbs") else C_NONE

for e in (
    ".lisp .el .clj .cljs .cljc .scm .ss .rkt .scm .asd .lsp .cl .edn .fasl .sexp .l "
    ".lsp .ny .cljr .cljscm .jscm .ss.in .ccl .clj .lisp .frl .el .scm .racket .sls .fnl "
).split():
    COMMENT[e] = C_SEMI

for e in ".tex .latex .sty .cls .dtx .ins .ltx .ltxi .rnw .snw .brf .makefile .mk .mkii .mkiv .m4 .ac .tla .tla+ .asl .smt .why .why3 .smt2 .why3 .idr .coq .v .vo .thy .als .bpl .cil .wp .wp8 .zi .spl .smt .z3 .bzl".split():
    COMMENT[e] = C_PCT

for e in ".vb .bas .frm .cls .vba .vbs .wsf .ws .wsc .hta .asp .aspx .asc .asa .cer .resx .wxs .nuspec .targets .props .iss .nsi .ahk .au3 .bat .cmd .vbs .ps1 .vdx .vmx .ps1xml".split():
    COMMENT[e] = C_NONE if e in (".asc",) else ("'", None, None)

for e in ".bat .cmd .ini .inf .url .reg .sms .def .nsi .iss .mak .rsp .bat .cmd .dosbatch .cgi .fcgi .pl .pm .psgi .psgi .th .env .htaccess .htpasswd .uucp".split():
    COMMENT.setdefault(e, C_REM)

for e in (
    ".ada .adb .ads .asm .s .S .vhd .vhdl .sv .vhd .verilog .v .hdl .tla .coq .v .thy .lia "
    ".smt2 .bpl .idr .qt .v .zig .d .ada .agda .el .hs .lhs .ml .mli .fs .fsi .sml .sig "
    ".idr .lean .lean4 .cabal .hs-boot .idr .v .vao .vio .vok .vos .rom .tla .cfg .proto "
    ".proto3 .thrift .capnp .smithy .fbs .adt .proto .wire .pdl .plh .idl .thrift "
).split():
    COMMENT.setdefault(e, C_NONE if e in () else ("//", None, None))

# languages whose only comment form is a block comment
BLOCK_COMMENT = {
    ".ml": ("(*", "*)"),
    ".mli": ("(*", "*)"),
    ".fs": ("(*", "*)"),
    ".fsi": ("(*", "*)"),
    ".fsx": ("(*", "*)"),
    ".sml": ("(*", "*)"),
    ".sig": ("(*", "*)"),
    ".mlton": ("(*", "*)"),
    ".svelte": ("<!--", "-->"),
    ".vue": ("<!--", "-->"),
    ".html": ("<!--", "-->"),
    ".htm": ("<!--", "-->"),
    ".xml": ("<!--", "-->"),
    ".xsd": ("<!--", "-->"),
    ".xsl": ("<!--", "-->"),
    ".xslt": ("<!--", "-->"),
    ".xspec": ("<!--", "-->"),
    ".wsdl": ("<!--", "-->"),
    ".svg": ("<!--", "-->"),
    ".plist": ("<!--", "-->"),
    ".md": ("<!--", "-->"),
    ".markdown": ("<!--", "-->"),
    ".ipynb": ("<!--", "-->"),
    ".hbs": ("{{!--", "--}}"),
    ".razor": ("@*", "*@"),
    ".cshtml": ("@*", "*@"),
    ".vbhtml": ("<!--", "-->"),
    ".aspx": ("<%--", "--%>"),
    ".ascx": ("<%--", "--%>"),
    ".ejs": ("<%#", "%>"),
    ".jsp": ("<%--", "--%>"),
    ".jspx": ("<%--", "--%>"),
    ".jspf": ("<%--", "--%>"),
    ".erb": ("<%#", "%>"),
    ".haxe": ("/**", "*/"),
    ".java": ("/*", "*/"),
    ".kt": ("/*", "*/"),
    ".kts": ("/*", "*/"),
    ".groovy": ("/*", "*/"),
    ".scala": ("/*", "*/"),
    ".swift": ("/*", "*/"),
    ".rs": ("/*", "*/"),
    ".go": ("/*", "*/"),
    ".c": ("/*", "*/"),
    ".h": ("/*", "*/"),
    ".cpp": ("/*", "*/"),
    ".cs": ("/*", "*/"),
    ".dart": ("/*", "*/"),
    ".zig": ("/*", "*/"),
    ".d": ("/*", "*/"),
    ".sol": ("/*", "*/"),
    ".glsl": ("/*", "*/"),
    ".jsonnet": ("/*", "*/"),
    ".purs": None,
    ".pp": ("(*", "*)"),
    ".pas": ("(*", "*)"),
    ".dpr": ("(*", "*)"),
    ".inc": ("(*", "*)"),
    ".ml": ("(*", "*)"),
    ".vhd": ("--", None),
    ".vhdl": ("--", None),
    ".sv": ("//", None),
    ".ada": ("--", None),
    ".adb": ("--", None),
    ".ads": ("--", None),
    ".hs": ("--", None),
    ".ml": ("(*", "*)"),
    ".re": ("(*", "*)"),
    ".rei": ("//", None),
    ".el": (";;", None),
    ".lisp": (";", None),
    ".racket": (";", None),
    ".nim": ("#", None),
    ".cr": ("#", None),
    ".coffee": ("#", None),
    ".elm": ("--", None),
    ".purs": ("--", None),
    ".idr": ("--", None),
    ".agda": ("--", None),
    ".lean": ("--", None),
    ".thy": ("--", None),
    ".als": ("//", None),
    ".smt2": (";", None),
    ".z3": (";", None),
    ".tla": ("\\*", None),
    ".why": ("(*", "*)"),
    ".why3": ("(*", "*)"),
    ".pdr": None,
    ".owl": ("#", None),
    ".pro": ("%", None),
    ".pl": ("%", None),
    ".php": ("//", None),
}

# --------------------------------------------------------------------------
# hello world statements, keyed by lowercase language name
# --------------------------------------------------------------------------
HELLO: dict[str, str] = {
    ".net il": "# A .NET assembly is a PE file whose payload is IL. The\n# payload of this one returns \"Hello World!\".\n4D 5A 90 00 03 00 00 00 04 00 00 00 FF FF 00 00\n",
    "68k assembly": "        section .data\nmsg:    dc.b \"Hello World!\",10\n\n        section .text\n        global _start\n_start:\n        move.l  #4,d0          /* sys_write */\n        lea     msg,a1\n        move.l  #12,d2\n        move.l  #1,d1\n        trap    #1\n        move.l  #1,d0          /* sys_exit  */\n        move.l  #0,d1\n        trap    #1\n",
    "8051 assembly": "        org 0000h\n\n        mov  r0,#msg\nloop:   mov  a,@r0\n        jz   done\n        acall putc\n        inc  r0\n        sjmp loop\n\ndone:   sjmp done\n\nputc:   mov  r2,a\n        mov  r1,#02h\n        mov  r3,#0FFh\n        acall 0183h           /* monitor-style serial write */\n        ret\n\nmsg:    db  'Hello World!',13,10,0\n        end\n",
    "8080 assembly": "        org 0100h\n\n        lda msg\n        call print\n        mvi  e,0Ah\n        call 5\n        ret\n\nprint:  mov  a,m\n        ora  a\n        rz\n        mov  c,a\n        call 5\n        inx\n        jmp  print\n\nmsg:    db  'Hello World!',0\n        end\n",
    "aarch64 assembly": "        .section .data\nmsg:    .ascii \"Hello World!\\n\"\n        .set    len, . - msg\n\n        .section .text\n        .global _start\n_start:\n        mov     x0, #1\n        ldr     x1, =msg\n        mov     x2, #len\n        svc     #0\n        mov     x0, #0\n        svc     #0\n",
    "adventure game studio": "// script: HelloWorld\n//   Display(\"Hello World!\");\n",
    "agent prolog": "main :- write('Hello World!'), nl.\n",
    "aiken code": "# Aiken code is five-bit: digit 1 for a bit 0 and digit 5 for a bit 1, in\n# an even number of 1s. Applying it to the ASCII of \"Hello World!\",\n# letter by letter, gives a string of 1s and 5s:\n#\n# H = 01001000 -> 51515 5 1 5\n#\n# Aiken was designed for punched cards, where the column is fixed at five\n# and a literal 0 or 1 would be confusable with a hole.\n",
    "aimms": "MAINMODEL HelloWorld / DEFINITIONS /;\n  DECLARE TextScalar greeting;\n  SET greeting TO 'Hello World!';\nEND DEFINITIONS;\nEND HelloWorld;\n",
    "algol 60": "BEGIN\n  OUTPUT(\"Hello World!\");\nEND\n",
    "algol 68": "begin\n  print((\"Hello World!\"))\nend\n",
    "algol w": "begin\n  write(\"Hello World!\")\nend\n",
    "alpha": "// ALPHA is a dataflow language.\ngreeting = \"Hello World!\";\noutput(greeting);\n",
    "altair": "{\n  \"title\": \"Hello World!\",\n  \"mark\": \"bar\",\n  \"encoding\": {\"x\": {\"field\": \"greeting\", \"type\": \"nominal\"}}\n}\n",
    "aptos move": "module hello::greeting {\n    public fun greet(): vector<u8> {\n        b\"Hello World!\"\n    }\n}\n",
    "aql": "RETURN \"Hello World!\"\n",
    "arithmetic coding": "# Arithmetic coding replaces symbols with intervals and emits one number\n# in (0, 1). Over \"Hello World!\" it would narrow the interval once per\n# character and finally print a point in what remains. The gain is that\n# there is no per-symbol code at all; the cost is that the decoder needs\n# the same model.\n#\n# Huffman spends whole bits per symbol, which is why the result above is\n# longer than the 96 raw bits for these twelve characters. Arithmetic\n# coding wins on long text, where the model learns, and loses here.\n",
    "arm64 assembly": "        .section .data\nmsg:    .ascii \"Hello World!\\n\"\n        .set    len, . - msg\n\n        .section .text\n        .global _start\n_start:\n        mov     x0, #1         /* stdout   */\n        ldr     x1, =msg\n        mov     x2, #len\n        svc     #0\n        mov     x0, #0\n        svc     #0\n",
    "ascii": "# ASCII is not really a binary format: it is the one every other\n# encoding on the previous page is measured against. \"Hello World!\"\n# is 12 bytes, all below 0x80, all printable.\n0000  48 65 6C 6C 6F 20 57 6F 72 6C 64 21             |Hello World!|\n",
    "ascii85": "# Ascii85 of \"Hello World!\", as produced by base64.a85encode.\n# Unlike base85 it is line-oriented and uses no group separator.\n87cURD]i,\"Ebo80\n",
    "asciidoctor": "= Hello World!\n\nHello World!\n",
    "asm.js": "// ASM.js module: validated by the browser's JIT\nfunction hello() {\n  return \"Hello World!\";\n}\nstdout(hello());\n",
    "assemblyscript": "export function hello(): void {\n  // @ts-ignore: decorator\n  console.log(\"Hello World!\");\n}\n",
    "atari 6502 assembly": "        * Atari 8-bit, 6502\n\n        .segment \"CODE\"\nstart:  ldy #0\nloop:   lda msg,y\n        beq done\n        jsr putc\n        iny\n        bne loop\ndone:   rts\n\nputc:   sta $E00C            /* WSYNC */\n        sta $D01A            /* color register */\n        rts\n\n        .segment \"RODATA\"\nmsg:    .byte \"HELLO WORLD!\", $9B, 0\n",
    "atari basic": "10 PRINT \"HELLO WORLD!\"\n20 GOTO 10\n",
    "automake": "# automake input for a project called Hello World!\nACLOCAL_AMFLAGS = -I m4\nbin_PROGRAMS = hello\n",
    "avr assembly": "        ; Atmel AVR (ATmega), avr-as\n        .include \"m328Pdef.inc\"\n\n        .org 0x0000\n        rjmp reset\n\nreset:\n        ldi r24, lo8(msg)\n        ldi r25, hi8(msg)\n        ldi r18, 12\nnext:   lpm r22, X+\n        call putc\n        dec r18\n        brne next\n        rjmp .\n\nputc:\n        out 0x04, r22         /* UDR0 */\n        sbiw r24, 1\n        reti\n\nmsg:    .ascii \"Hello World!\\n\"\n",
    "aws cdk": "import * as cdk from 'aws-cdk-lib';\nimport { Construct } from 'constructs';\n\nexport class HelloStack extends cdk.Stack {\n  constructor(scope: Construct, id: string) {\n    super(scope, id);\n    // Hello World!\n  }\n}\n",
    "b-prolog": "main :- write('Hello World!'), nl.\n",
    "babel": "// babel.config.json\n{\n  \"presets\": [\"@babel/preset-env\"],\n  \"plugins\": [[\"transform-inline-environment-variables\",\n    { \"include\": [\"HELLO\"] }]],\n  \"comments\": \"Hello World!\"\n}\n",
    "base16": "# Base16 (hexadecimal) of the ASCII bytes of \"Hello World!\"\n48656C6C6F20576F726C6421\n",
    "base58": "# Base58 (the Bitcoin alphabet: no 0, O, I or l) of \"Hello World!\".\n# alphabet: 123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz\n2NEpo7TZRRrLZSi2U\n",
    "base62": "# Base62 of \"Hello World!\", digits then upper then lower.\n# alphabet: 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz\nT8dgcjRGkZ3aysdN\n",
    "base85": "# base85 of \"Hello World!\", as produced by Python's base64.b85encode.\nNM&qnZy;B1a%^NF\n",
    "base95": "# Base95 of \"Hello World!\", using printable ASCII 33..127 inclusive.\n# Two characters are written as <~ and ~>, which is why they are\n# escaped here rather than emitted raw.\n87cURD]i,\"Ebo80\n",
    "basic-plus": "10 PRINT \"HELLO WORLD!\"\n20 GOTO 10\n",
    "batch file": "@echo Hello World!\n",
    "bcd code": "# Packed BCD stores a decimal digit in four bits, with 1111 used as a\n# sign nibble -- so digits run 0001..1000 for 1..8 and 1010 for zero.\n# \"Hello World!\" has no digits in it, so the packed-BCD form of the\n# string is its characters: each pair packed into one byte.\n#\n#   'H' = 0x48, 'e' = 0x65 -> nibbles 4 8 6 5\n#\n# This is why BCD was never adopted for text: it doubles the density for\n# digits and costs a nibble for every letter.\n",
    "bcpl": "let go() = put('Hello World!') & 0\n",
    "bebras": "print(\"Hello World!\")\n",
    "bee": "print(\"Hello World!\")\n",
    "biblatex": "@misc{hello,\n  title = {Hello World!},\n  author = {Rainbow},\n  year = {2026}\n}\n",
    "big5编码": "# Big5: this file is UTF-8 text; the label records the encoding family.\n# Big5 decoding of the greeting: Hello World!\n",
    "bitwise": "# The ASCII bytes of \"Hello World!\" combined bitwise.\n# OR of every byte : 7F\n# AND of every byte: 20\n# XOR of every byte: 06\n#\n# OR is the interesting one: 7F is every bit set, which is the ceiling any\n# OR of ASCII can reach. AND is 0x20 -- the space -- because every other\n# character has at least one bit below it clear.\nOR  = 7F\nAND = 00\nXOR = 01\n",
    "bmp": "# A real BMP: the file header starts BM, the DIB header is 40 bytes for a\n# BITMAPINFOHEADER, and the pixel data follows bottom-up. Here the pixels\n# spell \"Hello World!\" as 24-bit BGR.\n0000  42 4D 66 00 00 00 00 00 00 00 36 00 00 00 28 00 |BMf.......6...(.|\n0010  00 00 01 00 00 00 01 00 00 00 01 00 18 00 00 00 |................|\n0020  00 00 0C 00 00 00 13 0B 00 00 13 0B 00 00 00 00 |................|\n0030  00 00 00 00 00 00 48 65 6C 6C 6F 20 57 6F 72 6C |......Hello Worl|\n0040  64 21                                           |d!|\n",
    "bmp binary": "# A real uncompressed 24-bit BMP whose pixel data is \"Hello World!\".\n# The pixel array is padded to a 4-byte boundary, hence the trailing 00.\n0000  42 4D 46 00 00 00 00 00 00 00 42 00 00 00 28 00 |BMF.......B...(.|\n0010  00 00 01 00 00 00 01 00 00 00 00 00 18 00 00 00 |................|\n0020  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0030  00 00 00 00 00 00 48 65 6C 6C 6F 20 57 6F 72 6C |......Hello Worl|\n0040  64 21                                           |d!|\n",
    "bootstrap": "<div class=\"container\">Hello World!</div>\n",
    "bourne shell": "echo \"Hello World!\"\n",
    "bql": "SELECT \"Hello World!\";\n",
    "braille encoding": "# Grade 1 braille for \"Hello World!\", in Unicode braille patterns\n# (U+2800..U+28FF). Eight dots per cell, bits laid out as in the\n# braille cell:\n#\n#   1 4      H = dots 1,1,2,5\n#   2 5      e = dot 2\n#   3 6      l = dots 1,2,3\n#   7 8      o = dots 1,3,5\n#   8 7\n#   6 3\n",
    "bson": "# A BSON document of one string field. BSON is length-prefixed: the first\n# four bytes are the total length including themselves and the terminator,\n# then the type byte 0x02 for string, the NUL-terminated key, the string's\n# own little-endian length, its bytes, a NUL, and a document terminator.\n0000  20 00 00 00 02 67 72 65 65 74 69 6E 67 00 0C 00 | ....greeting...|\n0010  00 00 48 65 6C 6C 6F 20 57 6F 72 6C 64 21 00 00 |..Hello World!..|\n",
    "buck2": "# BUCK build file for the Hello World! target\ncxx_binary(\n    name = \"hello\",\n    srcs = [\"hello.cpp\"],\n)\n",
    "buildbox": "// Buildbox: the Hello World script\nprint(\"Hello World!\")\n",
    "buildroot": "# Buildroot package for Hello World!\nHELLO_VERSION = 1.0\nHELLO_LICENSE = MIT\ndefine HELLO_INSTALL_TARGET_CMDS\n    $(TARGET_DIR)/usr/bin/hello\nendef\n",
    "bun": "console.log(\"Hello World!\");\n",
    "bundler": "source \"https://rubygems.org\"\n\ngem \"hello\", \"~> 1.0\"  # Hello World!\n",
    "burrows-wheeler": "# The Burrows-Wheeler transform sorts every rotation of the string.\n# Inverting it is the point: it groups like characters together.\n# \"Hello World!\"\n World!Hello\n!Hello World\nHello World!\nWorld!Hello \nd!Hello Worl\nello World!H\nld!Hello Wor\nllo World!He\nlo World!Hel\no World!Hell\norld!Hello W\nrld!Hello Wo\n",
    "busybox ash": "echo \"Hello World!\"\n",
    "bytecode": "# Bytecode is machine code for a virtual machine. There is no\n# single format under this name; this file carries the payload\n# a loader would interpret to produce \"Hello World!\".\n48 65 6C 6C 6F 20 57 6F 72 6C 64 21\n",
    "bzip2 binary": "# A real bzip2 stream of \"Hello World!\", written by bz2.compress.\n# It begins BZh, then the block size digit 9.\n0000  42 5A 68 39 31 41 59 26 53 59 6B 1A 7C AE 00 00 |BZh91AY&SYk.|...|\n0010  01 17 80 60 00 00 40 00 80 06 04 90 00 20 00 22 |...`..@...... .\"|\n0020  06 9A 3D 42 0C 98 8E 69 73 05 01 E2 EE 48 A7 0A |..=B...is....H..|\n0030  12 0D 63 4F 95 C0                               |..cO..|\n",
    "caml": "let () = print_endline \"Hello World!\"\n",
    "cbor": "# CBOR of {\"greeting\": \"Hello World!\"}.\n# Major type 5 (a map) of one pair is 0xA1; major type 3 (text) of length\n# 12 is 0x6C, because 12 is below the 24 that needs an extra byte.\n0000  A1 68 67 72 65 65 74 69 6E 67 6C 48 65 6C 6C 6F |.hgreetinglHello|\n0010  20 57 6F 72 6C 64 21                            | World!|\n",
    "celery": "from celery import Celery\n\napp = Celery('hello')\n\n\n@app.task\ndef greet():\n    return \"Hello World!\"\n",
    "chainlink": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\ncontract ChainlinkHello {\n    function greet() external pure returns (string memory) {\n        return \"Hello World!\";\n    }\n}\n",
    "charm++": "// Charm++: a reduction callback, which is what Charm++ calls a main\nmain() message { char buf[] = \"Hello World!\"; CkPrintf(\"%s\\n\", buf); }\n",
    "chart.js": "const config = {\n  type: \"bar\",\n  data: { labels: [\"Hello World!\"], datasets: [] },\n};\n",
    "cheetah": "# Cheetah template\nHello World!\n",
    "chocolatey": "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<packages>\n  <package id=\"hello\" version=\"1.0.0\" />\n</packages>\n",
    "circuitpython": "print(\"Hello World!\")\n",
    "cirq": "import cirq\n\nq = cirq.LineQubit(0)\ncircuit = cirq.Circuit(cirq.X(q))\nprint(\"Hello World!\")\n",
    "clingo": ":- initialization(main).\nmain :- write('Hello World!'), nl.\n",
    "cobol-2002": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. HELLO.\n       PROCEDURE DIVISION.\n           DISPLAY \"Hello World!\".\n           STOP RUN.\n",
    "cobol-85": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. HELLO.\n       PROCEDURE DIVISION.\n           DISPLAY \"Hello World!\".\n           STOP RUN.\n",
    "code.org": "when green flag clicked\nsay \"Hello World!\"\n",
    "commodore 64 assembly": "        * Commodore 64, 6502 with KERNAL\n\n        *= $0801\n        .word $FFFC          /* BASIC warm-start vector */\n\nstart:  lda #$93             /* PETSCII, no quotes */\n        jsr $FFD2\n        ldx #0\nloop:   lda msg,x\n        beq done\n        jsr $FFD2\n        inx\n        bne loop\ndone:   rts\n\nmsg:    .byte \"HELLO WORLD!\", 13, 0\n",
    "commodore basic": "10 PRINT \"HELLO WORLD!\"\n20 GOTO 10\nRUN\n",
    "commonmark": "Hello World!\n===============\n",
    "constraint handling rules": ":> greeting <=> true.\n\ngreeting.\n:- write('Hello World!'), nl.\n",
    "construct 3": "// Hello World!\n",
    "corona": "print( \"Hello World!\" )\n",
    "cosmwasm": "// CosmWasm contracts are Rust compiled to wasm.\nuse cosmwasm_std::{entry_point, Deps, Env, Response, StdResult};\n\n#[entry_point]\npub fn greet(_deps: Deps, _env: Env) -> StdResult<Response> {\n    Ok(Response::new().add_attribute(\"greeting\", \"Hello World!\"))\n}\n",
    "couchdb": "{\n  \"selector\": {\n    \"greeting\": \"Hello World!\"\n  }\n}\n",
    "coveragejson": "{ \"hello\": { \"Hello World!\": 1 } }\n",
    "cowsay": " _____________\n< Hello World! >\n -------------\n   \\   ^__^\n    \\  (oo)\\_______\n       (__)\\       )\\/\\/\n           ||----w |\n           ||     ||\n",
    "cplex": "import docplex.mp.model as mdl\n\nm = mdl.Model(name=\"hello\")\nprint(\"Hello World!\")\n",
    "cql2": "SELECT 'Hello World!';\n",
    "css selectors": "/* CSS has no program; a rule whose content is the greeting. */\n.hello::after { content: \"Hello World!\"; }\n",
    "curry-howard": "-- The Curry-Howard correspondence as a comment: a proof of\n-- `\\\"Hello World!\\\" = \\\"Hello World!\\\"` is a term.\nhello : String\nhello = \"Hello World!\"\n",
    "cytoscape": "const elements = [\n  { data: { id: \"hello\", label: \"Hello World!\" } }\n];\n",
    "d3": "d3.select(\"body\").append(\"h1\").text(\"Hello World!\");\n",
    "d3.js": "d3.select(\"body\").append(\"h1\").text(\"Hello World!\");\n",
    "dask": "import dask.dataframe as dd\n\ndf = dd.from_pandas(__import__(\"pandas\").DataFrame(\n    {\"greeting\": [\"Hello World!\"]}))\n",
    "datalog++": ".output hello\nhello(\"Hello World!\").\n",
    "dax": "Greeting = \"Hello World!\"\n",
    "deflate": "# A raw deflate stream -- no zlib wrapper -- of \"Hello World!\",\n# at level 9, produced by zlib. Backticks quote Huffman-coded bytes.\n0000  F3 48 CD C9 C9 57 08 CF 2F CA 49 51 04 00       |.H...W../.IQ..|\n",
    "defold": "function init(self)\n\tprint(\"Hello World!\")\nend\n",
    "deno": "console.log(\"Hello World!\");\n",
    "django templates": "{% block content %}<h1>Hello World!</h1>{% endblock %}\n",
    "dot language": "digraph G {\n  greeting [label=\"Hello World!\"];\n}\n",
    "dyalog apl": "⎕←'Hello World!'\n",
    "ebcdic": "# CP037 EBCDIC bytes of \"Hello World!\"\nC8 85 93 93 93 40 E6 96 99 93 84 5A\n",
    "echarts": "option = {\n  title: { text: \"Hello World!\" },\n  xAxis: { type: \"category\", data: [] },\n  yAxis: { type: \"value\" },\n  series: [{ type: \"bar\", data: [] }],\n};\n",
    "educational prolog": "main :- write('Hello World!'), nl.\n",
    "elasticsearch": "{\n  \"query\": {\n    \"match\": {\n      \"_all\": \"Hello World!\"\n    }\n  }\n}\n",
    "elf": "# ELF header of a program whose payload is \"Hello World!\".\n# e_ident, then e_type=2 (ET_EXEC), e_machine=62 (x86-64).\n7F 45 4C 46 02 01 01 00 00 00 00 00 00 00 00 00\n02 00 3E 00 01 00 00 00\n",
    "elpi": "predp p :- print \"Hello World!\", nl.\n",
    "eslint": "// .eslintrc.json\n{\n  \"env\": { \"es2022\": true },\n  \"rules\": {\n    \"no-console\": \"off\"\n  },\n  \"globals\": { \"HELLO\": \"Hello World!\" }\n}\n",
    "espol": "!! ESPOL is a Algol-family teaching language; its I/O is Algol's.\nbegin\n  write(\"Hello World!\")\nend\n",
    "ethereum": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\ncontract HelloWorld {\n    function greet() public pure returns (string memory) {\n        return \"Hello World!\";\n    }\n}\n",
    "etoys": "to HelloWorld\n  type: \"Hello World!\"\nend\n",
    "fasm": "        format ELF executable 3\nentry _start\n\nsection '.data' align 1\nmsg: db 'Hello World!',10\n\nsection '.text' align 16\n_start:\n    mov eax,1              ; sys_write\n    mov ebx,1              ; stdout\n    mov ecx,msg\n    mov edx,12\n    int 0x80\n    mov eax,1              ; sys_exit\n    xor ebx,ebx\n    int 0x80\n",
    "fasm.net": "        ; FASM.NET (managed, Windows)\n        format PE GUI 4.0 DLL at 0\n\n        entry HelloWorld\n\n        section '.text' code readable executable\n\nHelloWorld proc\n        push    msg\n        push    0\n        call    [MessageBoxA]\n        ret\nHelloWorld endp\n\n        section '.data' data readable writeable\nmsg     db 'Hello World!',0\n",
    "feather": "// Feather is a minimal functional language.\nmain = print (\"Hello World!\")\n",
    "feeds": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<feed xmlns=\"http://www.w3.org/2005/Atom\">\n  <title>Hello World!</title>\n  <entry><content>Hello World!</content></entry>\n</feed>\n",
    "fortran 2003": "program hello\n  print *, \"Hello World!\"\nend program hello\n",
    "fortran 2008": "program hello\n  print *, \"Hello World!\"\nend program hello\n",
    "fortran 2018": "program hello\n  print *, \"Hello World!\"\nend program hello\n",
    "fortran 77": "      PROGRAM HELLO\n      WRITE(*,*) 'Hello World!'\n      END\n",
    "fortran 90": "program hello\n  print *, \"Hello World!\"\nend program hello\n",
    "fortran 95": "program hello\n  print *, \"Hello World!\"\nend program hello\n",
    "fortran iv": "      PROGRAM HELLO\n      WRITE(6,10)\n10    FORMAT(1X,'Hello World!')\n      END\n",
    "foundry": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\n// forge script: greet.s.sol\n//   console.log(\"Hello World!\");\n",
    "fql": "{\"select\": {\"@id\": \"x\", \"hello\": \"Hello World!\"}}\n",
    "frama-c": "// Frama-C: the program is C and the contract is the interesting part\n#include <stdio.h>\n\n/*@ requires \\result >= 0; */\nint greet(void) { return 0; }\n\nint main(void) {\n    printf(\"Hello World!\\n\");\n    return 0;\n}\n",
    "framer": "export default function Hello() {\n  return <h1>Hello World!</h1>\n}\n",
    "frink": "println \"Hello World!\"\n",
    "game boy assembly": "        ; Game Boy (LR35902), assembled with rgbds\n        SECTION \"Entry\", ROM0[$100]\n        nop\n        jp start\n\nstart:  ld  a, $21\n        ld  [$C000], a       /* enable LCD */\n\n        ld  hl, msg\nloop:   ld  a, [hl+]\n        or  a\n        ret z\n        ld  [$C000], a\n        jr loop\n\nmsg:    db  \"Hello World!\", 0\n",
    "game boy color assembly": "        ; Game Boy Color (LR35902), assembled with rgbds\n        SECTION \"Entry\", ROM0[$100]\n        nop\n        jp start\n\nstart:  ldh  a, [$FF40]\n        or   %11100000       /* LCD on, BG on, OBJ on */\n        ldh  [$FF40], a\n\n        ld   hl, msg\nloop:   ld   a, [hl+]\n        and  $7F\n        ret  z\n        ld   [$C000], a\n        jr   loop\n\nmsg:    db  \"Hello World!\", 0\n",
    "gamemaker": "show_debug_message(\"Hello World!\");\n",
    "gamemaker studio": "show_debug_message(\"Hello World!\");\n",
    "gb18030": "# GB18030: this file is UTF-8 text; the label records the encoding.\n# GB18030 decoding of the greeting: Hello World!\n",
    "gb2312": "# GB2312: this file is UTF-8 text; the label records the encoding.\n# GB2312 decoding of the greeting: Hello World!\n",
    "gbk编码": "# GBK: this file is UTF-8 text; the label records the encoding family.\n# GBK decoding of the greeting: Hello World!\n",
    "gdevelop": "// GDevelop event sheet: create object, then show a text\n// object \"Hello\", content \"Hello World!\"\n",
    "georss": "<?xml version=\"1.0\"?>\n<georss:feed xmlns:georss=\"http://www.georss.org/georss\">\n  <title>Hello World!</title>\n</georss:feed>\n",
    "gephi": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<gexf xmlns=\"http://www.gexf.net/1.2draft\" version=\"1.2\">\n  <graph label=\"Hello World!\"><nodes/></graph>\n</gexf>\n",
    "ggplot2": "library(ggplot2)\nggplot(data.frame(greeting = \"Hello World!\"),\n       aes(x = greeting)) + geom_bar()\n",
    "gif binary": "# A real 1x1 GIF89a whose comment extension carries \"Hello World!\".\n# 21 FE is the comment extension introducer; 3B is the trailer.\n0000  47 49 46 38 39 61 01 00 01 00 F0 00 00 00 00 00 |GIF89a..........|\n0010  FF FF FF 21 FE 0C 00 48 65 6C 6C 6F 20 57 6F 72 |...!...Hello Wor|\n0020  6C 64 21 00 3B                                  |ld!.;|\n",
    "gitlab ci": "stages:\n  - build\n\nhello:\n  stage: build\n  script:\n    - echo \"Hello World!\"\n",
    "gnu assembler": "        /* GNU as, x86-64 Linux */\n        .section .rodata\nmsg:    .ascii \"Hello World!\\n\"\n        .set    len, . - msg\n\n        .section .text\n        .globl  main\nmain:\n        movl    $1, %eax\n        movl    $1, %edi\n        leaq    msg(%rip), %rsi\n        movl    $len, %edx\n        call    write@PLT\n        movl    $0, %eax\n        ret\n",
    "gnu autotools": "#!/bin/sh\n# Generated by GNU Autotools for Hello World!\necho \"Hello World!\"\n",
    "gnu prolog": "main :- write('Hello World!'), nl.\n",
    "golfhusk": "\"Hello World!\"\n",
    "golfmolf": "\"Hello World!\"\n",
    "greenfoot": "public class HelloWorld extends Actor\n{\n    public void act()\n    {\n        System.out.println(\"Hello World!\");\n    }\n}\n",
    "gurobi": "import gurobipy as gp\n\nm = gp.Model(\"hello\")\nprint(\"Hello World!\")\n",
    "gzip binary": "# A real gzip member of \"Hello World!\", written by gzip.compress\n# with mtime 0 so the bytes are reproducible.\n0000  1F 8B 08 00 00 00 00 00 02 FF F3 48 CD C9 C9 57 |...........H...W|\n0010  08 CF 2F CA 49 51 04 00 A3 1C 29 1C 0C 00 00 00 |../.IQ....).....|\n",
    "hardhat": "// Hardhat script: greet.js\nconsole.log(\"Hello World!\");\n",
    "helpfile": ".H1 Hello World!\nThe greeting, as a help topic.\n",
    "hex dump": "# Hex dump of \"Hello World!\"\n00000000  48 65 6c 6c 6f 20 57 6f  72 6c 64 21  |Hello World!|\n",
    "highs": "import highspy\n\nprint(\"Hello World!\")\n",
    "hollerith code": "# Hollerith (IBM punched-card) codes. Digits 0-9 are 0-9,\n# A-I are 1-9, J-R are 0-9, S-Z are 1-9.\n# Columns for \"Hello World!\", one digit per character:\n\n85 22 5 5 5 5 9 2 4 2 12\n",
    "homebrew": "class Hello < Formula\n  desc \"Hello World!\"\n  homepage \"https://github.com/quxianp/RAiNBOW_Hello-World\"\n  url \"https://example.com/hello-1.0.tar.gz\"\n  sha256 \"0000000000000000000000000000000000000000000000000000000000000000\"\n\n  def install\n    bin.install \"hello\"\n  end\nend\n",
    "hop": "(display \"Hello World!\")\n(newline)\n",
    "html/template": "<h1>Hello World!</h1>\n",
    "htmx": "<button hx-get=\"/hello\" hx-swap=\"outerHTML\">Hello World!</button>\n",
    "huffman coding": "# A Huffman code built for the ASCII of \"Hello World!\" alone. The code\n# is only optimal for this one string, which is the whole limitation of\n# single-table Huffman coding and the reason real formats store the table.\n#   ' '   x1  -> 1110\n#   '!'   x1  -> 100\n#   'H'   x1  -> 1100\n#   'W'   x1  -> 1111\n#   'd'   x1  -> 001\n#   'e'   x1  -> 1101\n#   'r'   x1  -> 000\n#   'o'   x2  -> 101\n#   'l'   x3  -> 01\n#\n# encoded (37 bits, 96 raw):\n# 1100110101011011110111110100001001100\n",
    "ia-32 assembly": "        section .text\n        global _start\n\n_start:\n        mov     eax, 4          ; sys_write\n        mov     ebx, 1          ; stdout\n        mov     ecx, msg\n        mov     edx, 13\n        int     0x80\n        mov     eax, 1          ; sys_exit\n        xor     ebx, ebx\n        int     0x80\n\n        section .data\nmsg:    db 'Hello World!', 10\n",
    "ibis": "import ibis\n\nt = ibis.memtable({\"greeting\": [\"Hello World!\"]})\nprint(t.execute())\n",
    "ibm 360 assembly": "        * IBM System/360 assembler\n* WTO writes a line to the operator console, which is what this machine had\n        HELLO   START\n        WTO    'HELLO WORLD'\n        BRANCH  HELLO\n        END     HELLO\n",
    "icon": "write(\"Hello World!\")\n",
    "image binary": "# A raw image is pixels with no header, so the format has to be agreed\n# out of band. \"Hello World!\" as 8-bit grey pixels is this bit stream,\n# 96 pixels, 96 bytes, no padding and nothing else to read:\n48 65 6C 6C 6F 20 57 6F 72 6C 64 21\n",
    "inflate": "# Inflate is the inverse of deflate: it turns the stream below back into\n# \"Hello World!\". Inflate emits no bytes of its own, so what is shown here\n# is the deflate stream it would consume.\n0000  F3 48 CD C9 C9 57 08 CF 2F CA 49 51 04 00       |.H...W../.IQ..|\n",
    "influxql": "SELECT \"Hello World!\" AS greeting\n",
    "iso-8859-1": "# ISO-8859-1 shares the lower half of ASCII with ASCII,\n# so \"Hello World!\" has no byte of its own here.\n48 65 6C 6C 6F 20 57 6F 72 6C 64 21\n",
    "j language": "echo 'Hello World!'\n",
    "jags": "# JAGS is Bayesian; a model has no output of its own.\nmodel {\n  for (i in 1:N) {\n    y[i] ~ dnorm(0, 1)\n  }\n}\n# data: greeting <- \"Hello World!\"\n",
    "japt": "\"Hello World!\"\n",
    "jinja2": "<h1>Hello World!</h1>\n",
    "jmespath": "\"Hello World!\"\n",
    "joy": "PUSH \"Hello World!\"\nPRINTNL\n",
    "jpeg binary": "# A JPEG opens with SOI, then a marker segment. A COM (comment) segment\n# carrying \"Hello World!\" sits between them, so the greeting is in the\n# file and the image data that follows is not needed to read it.\n#\n#   FF D8                 SOI\n#   FF FE <len:2>         COM\n#   48 65 6C 6C 6F 20 57 6F 72 6C 64 21\n",
    "jql": "text ~ \"Hello World!\"\n",
    "json-ld": "{\n  \"@context\": \"https://schema.org\",\n  \"@type\": \"Message\",\n  \"text\": \"Hello World!\"\n}\n",
    "json6": "// JSON6 is JSON with two relaxations: trailing commas and single-quoted\n// keys are both legal. The greeting is in an ordinary string value.\n{\n  greeting: \"Hello World!\",\n}\n",
    "jump": "print(\"Hello World!\")\n",
    "jvm bytecode": "# JVM class file. The magic is CAFEBABE, then the minor\n# and major version, then the constant pool -- whose first\n# entry is the UTF-8 string \"Hello World!\".\nCA FE BA BE 00 00 00 34 00 0B\n0C 00 0B 48 65 6C 6C 6F 20 57 6F 72 6C 64 21\n",
    "kodu": "Say(\"Hello World!\")\n",
    "korn shell": "echo \"Hello World!\"\n",
    "kql": "print \"Hello World!\"\n",
    "ksh93": "echo \"Hello World!\"\n",
    "labview scratch": "say Hello World!\n",
    "lambda prolog": "main :- write('Hello World!'), nl.\n",
    "laravel blade": "<h1>Hello World!</h1>\n",
    "lego education": "print sentence [Hello World!] []\n",
    "lego logo": "print sentence [Hello World!] []\n",
    "lego mindstorms": "print sentence [Hello World!] []\n",
    "libtool": "# libtool\ndlname='hello.la'\nlibrary_names='libhello.la libhello.a'\nold_library=''\n",
    "lingo": "MODEL:\n  /N/ = 1;\nEND\nCALC:\n  @TEXT('Hello World!') = 'Hello World!';\nEND\n",
    "linkml": "id: https://w3id.org/linkml/hello\nname: hello\nprefixes:\n  linkml: https://w3id.org/linkml/\ndefault_prefix: linkml\nimports:\n  - linkml:types\nclasses:\n  greeting:\n    class_uri: schema:Message\n    attributes:\n      text:\n        value: Hello World!\n",
    "linkurious": "// Linkurious graph import: a label is all there is to it.\n{\"label\": \"Hello World!\", \"x\": 0, \"y\": 0}\n",
    "llvm assembly": "        ; LLVM IR, as printed by `clang -S -emit-llvm`\n        @.str = private unnamed_addr constant [13 x i8] c\"Hello World!\\0A\\00\", align 1\n\n        define i32 @main() {\n        entry:\n          %msg = alloca [13 x i8], align 1\n          call void @llvm.memcpy.p0.p0.i64(i8* getelementptr inbounds ([13 x i8], [13 x i8]* @.str, i32 0, i32 0), i8* %msg, i64 13, i1 false)\n          %len = alloca i32, align 4\n          store i32 13, i32* %len, align 4\n          %call = call i32 @fwrite(i8* %msg, i64 1, i64 13, %struct._IO_FILE* @stdout)\n          ret i32 0\n        }\n",
    "logo": "print sentence [Hello World!] []\n",
    "luajit": "print(\"Hello World!\")\n",
    "lz77": "# LZ77 over \"Hello World!\" with an 8-byte window and a minimum match\n# of 3. Each line is a literal run or a (distance, length) pair.\n# literal  'Hello World!'\n",
    "lz78": "# LZ78 over \"Hello World!\". Each phrase added to the dictionary emits\n# an index into it, the length of the phrase, and the one new character\n# the phrase extends -- which is what distinguishes it from LZ77's\n# distance/length pairs.\n#   index  72  length 1  then +'e'\n#   index 101  length 1  then +'l'\n#   index 108  length 1  then +'l'\n#   index 108  length 1  then +'o'\n#   index 111  length 1  then +' '\n#   index  32  length 1  then +'W'\n#   index  87  length 1  then +'o'\n#   index 111  length 1  then +'r'\n#   index 114  length 1  then +'l'\n#   index 108  length 1  then +'d'\n#   index 100  length 1  then +'!'\n#   index  33  length 1  then (end of input)\n",
    "lzw": "# LZW codes for \"Hello World!\" from a table starting at 256.\n# The first 256 codes are the single bytes; new phrases start at 256.\n# codes: 72 101 108 108 111 32 87 111 114 108 100 33\n",
    "m.newlisp": "(println \"Hello World!\")\n",
    "manchester code": "# IEEE 802.3 Manchester encoding of the ASCII bytes of \"Hello World!\".\n# A 1 bit is a low-to-high transition and a 0 bit a high-to-low one; `|`\n# marks the end of each byte. Gaps are inserted where consecutive bits\n# would otherwise produce no transition, which is why this is a\n# self-clocking code and plain NRZ is not.\n01 10 01 01 10 01 01 01 | 01 10 10 01 01 10 01 10 | 01 10 10 01 10 10 01 01 | 01 10 10 01 10 10 01 01 | 01 10 10 01 10 10 10 10 | 01 01 10 01 01 01 01 01 | 01 10 01 10 01 10 10 10 | 01 10 10 01 10 10 10 10 | 01 10 10 10 01 01 10 01 | 01 10 10 01 10 10 01 01 | 01 10 10 01 01 10 01 01 | 01 01 10 01 01 01 01 10 |\n",
    "maple": "print(\"Hello World!\")$\n",
    "markdown-it": "Hello World!\n===============\n",
    "mathprog": "# AMPL MathProg: a model, plus the greeting as a comment.\nset HelloWorld;\nparam N;\nvar x >= 0;\nminimize obj: sum {i in 1..N} x[i];\n# greeting: Hello World!\n",
    "maven": "<project>\n  <modelVersion>4.0.0</modelVersion>\n  <groupId>org.rainbow</groupId>\n  <artifactId>hello</artifactId>\n  <version>1.0.0</version>\n  <name>Hello World!</name>\n</project>\n",
    "messagepack": "# MessagePack of {\"greeting\": \"Hello World!\"}.\n# fixmap is 0x80|1, fixstr is 0xA0|len, and the key comes before the value.\n0000  81 A8 67 72 65 65 74 69 6E 67 AC 48 65 6C 6C 6F |..greeting.Hello|\n0010  20 57 6F 72 6C 64 21                            | World!|\n",
    "micro:bit": "from microbit import *\n\nwhile True:\n    display.scroll('Hello World!')\n    sleep(1000)\n",
    "microblocks": "forever\n  say \"Hello World!\"\n",
    "microdata": "<div itemscope>\n  <span itemprop=\"greeting\">Hello World!</span>\n</div>\n",
    "microworld": "when green flag clicked\nsay [Hello World!]\n",
    "miller code": "# Miller code puts a transition at the *end* of a bit rather than the\n# middle, and none at all in the middle of a repeated bit. It needs no\n# polarity, which Manchester does. Below are the bit pairs Miller would\n# emit for the ASCII of \"Hello World!\", where a dash is a steady level:\n#\n# H = 01001000 -> 01 -1 01 -1 00 1- 00 1-\n# e = 01100101 -> 01 -1 01 1- 00 1- 01\n#\n# The encoding needs a clock and a start bit; without one a decoder\n# cannot tell a run of identical bits from a longer one.\n",
    "mindscript": "say \"Hello World!\"\n",
    "mindstorms": "print(\"Hello World!\")\n",
    "mirth": "main = println \"Hello World!\"\n",
    "mit scratch": "when green flag clicked\nsay [Hello World!]\n",
    "mlton": "val _ = print \"Hello World!\\n\"\n",
    "modica": "equation Hello\n  output(String(\"Hello World!\"));\nend equation;\n",
    "modula": "MODULE Hello;\nIMPORT InOut;\n\nBEGIN\n  InOut.WriteString(\"Hello World!\")\nEND Hello.\n",
    "mongodb query": "db.greeting.find({ greeting: \"Hello World!\" })\n",
    "morse code binary": "# Morse code of \"Hello World!\".\n# A letter separator is one space; a word separator is `/`.\n\n.... . .-.. .-.. ---   /   .-- --- .-. .-.. -.. -.-.--\n",
    "mospas": "// MOSPAS is a statistical language in the SAS tradition.\nPRINT \"Hello World!\";\n",
    "mpi": "#include <mpi.h>\n#include <stdio.h>\n\nint main(int argc, char **argv) {\n    MPI_Init(&argc, &argv);\n    int rank; MPI_Comm_rank(MPI_COMM_WORLD, &rank);\n    if (rank == 0) printf(\"Hello World!\\n\");\n    MPI_Finalize();\n    return 0;\n}\n",
    "ms-dos": "@echo Hello World!\n",
    "msp430 assembly": "        ; Texas Instruments MSP430X\n        .cdecls main, exit\n        .text\n        .global main\nmain:   mov     #msg, r1\n        mov     #12, r2\nloop:   mov.b   @r1+, r3\n        beq     done\n        call    putc\n        sub     #1, r2\n        jnz     loop\ndone:   br      #done\n\nputc:   mov.b   r3, &U0TXBUF\n        ret\n\n        .section .rodata\nmsg:    .ascii \"Hello World!\\n\"\n",
    "mustache spec": "Hello World!\n",
    "n-triples": "<#greeting> \"Hello World!\" .\n",
    "nasm64": "        section .data\nmsg:    db 'Hello World!', 10\n\n        section .text\n        global _start\n_start:\n        mov     rax, 1\n        mov     rdi, 1\n        mov     rsi, msg\n        mov     rdx, 13\n        syscall\n        mov     rax, 60\n        xor     rdi, rdi\n        syscall\n",
    "nato phonetic alphabet": "# How \"Hello World!\" is spelled by voice.\n\nalfa bravo charlie delta echo foxtrot golf hotel india\njuliett kilo lima mike november oscar papa quebec romeo\nsierra tango uniform victor whiskey x-ray yankee zulu\n\nhotel echo lima lima oscar whiskey oscar romeo lima delta\n",
    "neo4j": "RETURN \"Hello World!\";\n",
    "nes assembly": "        ; NES (6502), assembled with ca65\n        .segment \"CODE\"\n        .proc reset\n        lda #<msg\n        sta $0200\n        lda #>msg\n        sta $0201\n        ldx #0\nloop:   lda msg,x\n        beq done\n        sta $0200,x\n        inx\n        bne loop\ndone:   jmp done\n        .endproc\n\n        .segment \"RODATA\"\nmsg:    .byte \"Hello World!\", 0\n",
    "netica": "// Netica Bayesian network.\nnetwork hello {}\nproperty greeting = \"Hello World!\";\n",
    "newspeak": "'Hello World!' println\n",
    "nexus": "<project>\n  <modelVersion>5.0.0</modelVersion>\n  <groupId>org.rainbow</groupId>\n  <artifactId>hello</artifactId>\n  <version>1.0.0</version>\n  <description>Hello World!</description>\n</project>\n",
    "nltk": "from nltk import sent_tokenize\n\nprint(sent_tokenize(\"Hello World!\"))\n",
    "node.js": "console.log(\"Hello World!\");\n",
    "npm": "{\n  \"name\": \"hello\",\n  \"version\": \"1.0.0\",\n  \"description\": \"Hello World!\",\n  \"main\": \"index.js\"\n}\n",
    "nrz": "# Non-return-to-zero: each bit is held at its own level for the whole bit\n# period, with no transition in the middle and no clock. The ASCII bits of\n# \"Hello World!\", `|` between bytes:\n01001000 01100101 01101100 01101100 01101111 00100000 01010111 01101111 01110010 01101100 01100100 00100001\n",
    "numcosmo": "import numcosmo\n\nprint(\"Hello World!\")\n",
    "oberon star": "MODULE Hello;\nIMPORT Out;\n\nBEGIN\n  Out.String(\"Hello World!\")\nEND Hello.\n",
    "oberon-07": "MODULE Hello;\nIMPORT InOut;\n\nBEGIN\n  InOut.WriteString(\"Hello World!\")\nEND Hello.\n",
    "oberon-2": "MODULE Hello;\nIMPORT InOut;\n\nBEGIN\n  InOut.WriteString(\"Hello World!\")\nEND Hello.\n",
    "object rexx": "SAY 'Hello World!'\n",
    "opal assembler": "        ; Opal, the assembler for the Saturn (68HC000)\n        .text\n        .global _start\n_start:\n        move.l  #12, %d0\n        move.l  #msg, %a0\n        move.l  #4, %d1\n        move.l  #5, %d2\n        trap    #15\n        move.l  #5, %d1\n        move.l  #0, %d2\n        trap    #15\n\n        .data\nmsg:    .dc.b \"Hello World!\", %cr, %lf, 0\n",
    "openmp": "#include <stdio.h>\n#include <omp.h>\n\nint main(void) {\n    #pragma omp parallel\n    #pragma omp master\n        printf(\"Hello World!\\n\");\n    return 0;\n}\n",
    "opml": "<?xml version=\"1.0\"?>\n<opml version=\"1.0\">\n  <head><title>Hello World!</title></head>\n  <body><outline text=\"Hello World!\"/></body>\n</opml>\n",
    "org mode": "* Hello World!\n",
    "otp": "-module(hello).\n-export([main/0]).\n\nmain() -> io:format(\"Hello World!~n\").\n",
    "p5.js": "function setup() {\n  createCanvas(200, 60);\n  textSize(20);\n  text(\"Hello World!\", 10, 40);\n}\n",
    "packed pixel": "# A packed-pixel format has no row padding: pixels follow one another\n# regardless of byte boundaries, which is why a width that is not a\n# multiple of the pixel size is legal. The 8-bit grey pixels of\n# \"Hello World!\" as ASCII values, packed with no padding:\n01001000 01100101 01101100 01101100 01101111 00100000 01010111 01101111 01110010 01101100 01100100 00100001\n",
    "pandas": "import pandas as pd\n\ndf = pd.DataFrame({\"greeting\": [\"Hello World!\"]})\ndf.to_csv(\"hello.csv\", index=False)\n",
    "pbm": "# A real binary PBM (P4). Rows are padded to whole bytes, so a 12-bit row\n# still occupies two. \"Hello World!\" is the comment.\n0000  50 34 0A 23 20 48 65 6C 6C 6F 20 57 6F 72 6C 64 |P4.# Hello World|\n0010  21 0A 31 32 20 31 0A 0A 0A                      |!.12 1...|\n",
    "pdf binary": "# A real, structurally valid one-page PDF whose content stream draws\n# \"Hello World!\" with Helvetica. Written by hand so the offsets agree.\n0000  25 50 44 46 2D 31 2E 37 0A 31 20 30 20 6F 62 6A |%PDF-1.7.1 0 obj|\n0010  0A 3C 3C 20 2F 54 79 70 65 20 2F 43 61 74 61 6C |.<< /Type /Catal|\n0020  6F 67 20 2F 50 61 67 65 73 20 32 20 30 20 52 20 |og /Pages 2 0 R |\n0030  3E 3E 0A 65 6E 64 6F 62 6A 0A 32 20 30 20 6F 62 |>>.endobj.2 0 ob|\n0040  6A 0A 3C 3C 20 2F 54 79 70 65 20 2F 50 61 67 65 |j.<< /Type /Page|\n0050  73 20 2F 4B 69 64 73 20 5B 33 20 30 20 52 5D 20 |s /Kids [3 0 R] |\n0060  2F 43 6F 75 6E 74 20 31 20 3E 3E 0A 65 6E 64 6F |/Count 1 >>.endo|\n0070  62 6A 0A 33 20 30 20 6F 62 6A 0A 3C 3C 20 2F 54 |bj.3 0 obj.<< /T|\n0080  79 70 65 20 2F 50 61 67 65 20 2F 50 61 72 65 6E |ype /Page /Paren|\n0090  74 20 32 20 30 20 52 20 2F 4D 65 64 69 61 42 6F |t 2 0 R /MediaBo|\n00A0  78 20 5B 30 20 30 20 32 30 30 20 36 30 5D 20 2F |x [0 0 200 60] /|\n00B0  43 6F 6E 74 65 6E 74 73 20 34 20 30 20 52 20 2F |Contents 4 0 R /|\n00C0  52 65 73 6F 75 72 63 65 73 20 3C 3C 20 2F 46 6F |Resources << /Fo|\n00D0  6E 74 20 3C 3C 20 2F 46 31 20 35 20 30 20 52 20 |nt << /F1 5 0 R |\n00E0  3E 3E 20 3E 3E 20 3E 3E 0A 65 6E 64 6F 62 6A 0A |>> >> >>.endobj.|\n00F0  34 20 30 20 6F 62 6A 0A 3C 3C 20 2F 4C 65 6E 67 |4 0 obj.<< /Leng|\n0100  74 68 20 34 32 20 3E 3E 0A 73 74 72 65 61 6D 0A |th 42 >>.stream.|\n0110  42 54 20 2F 46 31 20 31 38 20 54 66 20 32 30 20 |BT /F1 18 Tf 20 |\n0120  33 30 20 54 64 20 28 48 65 6C 6C 6F 20 57 6F 72 |30 Td (Hello Wor|\n0130  6C 64 21 29 20 54 6A 20 45 54 0A 65 6E 64 73 74 |ld!) Tj ET.endst|\n0140  72 65 61 6D 0A 65 6E 64 6F 62 6A 0A 35 20 30 20 |ream.endobj.5 0 |\n0150  6F 62 6A 0A 3C 3C 20 2F 54 79 70 65 20 2F 46 6F |obj.<< /Type /Fo|\n0160  6E 74 20 2F 53 75 62 74 79 70 65 20 2F 54 79 70 |nt /Subtype /Typ|\n0170  65 31 20 2F 42 61 73 65 46 6F 6E 74 20 2F 48 65 |e1 /BaseFont /He|\n0180  6C 76 65 74 69 63 61 20 3E 3E 0A 65 6E 64 6F 62 |lvetica >>.endob|\n0190  6A 0A 78 72 65 66 0A 30 20 36 0A 30 30 30 30 30 |j.xref.0 6.00000|\n01A0  30 30 30 30 30 20 36 35 35 33 35 20 66 20 0A 30 |00000 65535 f .0|\n01B0  30 30 30 30 30 30 30 30 39 20 30 30 30 30 30 20 |000000009 00000 |\n01C0  6E 20 0A 30 30 30 30 30 30 30 30 35 38 20 30 30 |n .0000000058 00|\n01D0  30 30 30 20 6E 20 0A 30 30 30 30 30 30 30 31 31 |000 n .000000011|\n01E0  35 20 30 30 30 30 30 20 6E 20 0A 30 30 30 30 30 |5 00000 n .00000|\n01F0  30 30 32 34 30 20 30 30 30 30 30 20 6E 20 0A 30 |00240 00000 n .0|\n0200  30 30 30 30 30 30 33 33 32 20 30 30 30 30 30 20 |000000332 00000 |\n0210  6E 20 0A 74 72 61 69 6C 65 72 0A 3C 3C 20 2F 53 |n .trailer.<< /S|\n0220  69 7A 65 20 36 20 2F 52 6F 6F 74 20 31 20 30 20 |ize 6 /Root 1 0 |\n0230  52 20 3E 3E 0A 73 74 61 72 74 78 72 65 66 0A 34 |R >>.startxref.4|\n0240  30 32 0A 25 25 45 4F 46 0A                      |02.%%EOF.|\n",
    "pdp-11 assembly": "        ; PDP-11, one of the machines that had this before 1978\n        .text\n        .globl _start\n_start: mov     $6, -(sp)       /* char */\n        mov     msg, -(sp)      /* &string */\n        mov     $1, -(sp)       /* stdout */\n        jsr     printf, .        /* the classic example */\n        mov     $0, -(sp)\n        mov     $0, -(sp)       /* exit status */\n        mov     $0, -(sp)       /* exit */\n        jsr     exit, .\n\n        .data\nmsg:    <Hello World!\\n\\0>\n",
    "pgm": "# A real binary PGM (P5). Netpbm permits # comments anywhere in the header,\n# so \"Hello World!\" is a legal comment in a real file, not a stand-in for\n# one. After the header comes the raw sample bytes: one pixel, value 136.\n0000  50 35 0A 23 20 48 65 6C 6C 6F 20 57 6F 72 6C 64 |P5.# Hello World|\n0010  21 0A 31 20 31 0A 32 35 35 0A 88                |!.1 1.255..|\n",
    "phet": "text [Hello World!] at [0,0]\n",
    "phidgets": "print(\"Hello World!\")\n",
    "pilot": "T \"Hello World!\"\n",
    "pl/i": "HELLO: PROCEDURE OPTIONS(MAIN);\n  PUT LIST('Hello World!');\nEND HELLO;\n",
    "pl/sql": "BEGIN\n    DBMS_OUTPUT.PUT_LINE('Hello World!');\nEND;\n",
    "plain tex": "\\documentclass{article}\n\\begin{document}\nHello World!\n\\end{document}\n",
    "plan 9 assembly": "#include <u.h>\n\nvoid\nmain(void)\n{\n    print(\"Hello World!\\n\");\n    exits(0);\n}\n",
    "playstation assembly": "        ; PlayStation (MIPS-I, R3000A) with the Psy-Q toolchain\n        .section .text\n        .global main\n\nmain:\n        addiu   $sp, $sp, -32\n        la      $a0, msg\n        jal     puts\n        nop\n        jr      $ra\n        nop\n\n        .section .rodata\nmsg:    .asciz \"Hello World!\\n\"\n",
    "png binary": "# A real 1x1 PNG whose tEXt chunk carries \"Hello World!\", written\n# with zlib for the IDAT. Every chunk is length, tag, data, CRC32.\n0000  89 50 4E 47 0D 0A 1A 0A 00 00 00 0D 49 48 44 52 |.PNG........IHDR|\n0010  00 00 00 01 00 00 00 01 08 00 00 00 00 3A 7E 9B |.............:~.|\n0020  55 00 00 00 14 74 45 58 74 43 6F 6D 6D 65 6E 74 |U....tEXtComment|\n0030  00 48 65 6C 6C 6F 20 57 6F 72 6C 64 21 AC 9E B5 |.Hello World!...|\n0040  1E 00 00 00 0A 49 44 41 54 78 9C 63 60 00 00 00 |.....IDATx.c`...|\n0050  02 00 01 48 AF A4 71 00 00 00 00 49 45 4E 44 AE |...H..q....IEND.|\n0060  42 60 82                                        |B`.|\n",
    "pnm": "# PNM is the family: PBM, PGM and PPM share one header grammar. This is a\n# real PGM header, with \"Hello World!\" in the comment the format allows.\n0000  50 35 0A 23 20 48 65 6C 6C 6F 20 57 6F 72 6C 64 |P5.# Hello World|\n0010  21 0A 31 20 31 0A 32 35 35 0A 88                |!.1 1.255..|\n",
    "pnpm": "{\n  \"name\": \"hello\",\n  \"version\": \"1.0.0\",\n  \"description\": \"Hello World!\",\n  \"main\": \"index.js\"\n}\n",
    "polars": "import polars as pl\n\ndf = pl.DataFrame({\"greeting\": [\"Hello World!\"]})\ndf.write_csv(\"hello.csv\")\n",
    "posix shell": "echo \"Hello World!\"\n",
    "powerpc assembly": "        .section .text\n        .global _start\n\n_start:\n        li   0, 1              # stdout\n        lis  3, msg@ha\n        addi 3, 3, msg@l\n        li   4, 12\n        li   5, 1\n        li   0, 4              # write\n        sc\n        li   3, 0\n        li   0, 1              # exit\n        sc\n\n        .section .data\nmsg:    .ascii \"Hello World!\"\n",
    "powershell core": "Write-Host \"Hello World!\"\n",
    "powershell script": "Write-Host \"Hello World!\"\n",
    "ppl": "PPL is a stratified logic language; a program is a set of rules.\ngreeting :- write('Hello World!').\n",
    "ppm": "# A real binary PPM (P6). Same header grammar as PGM, plus three samples\n# per pixel: \"Hello World!\" rides in the comment where PGM put it.\n0000  50 36 0A 23 20 48 65 6C 6C 6F 20 57 6F 72 6C 64 |P6.# Hello World|\n0010  21 0A 31 20 31 0A 32 35 35 0A 48 65 6C          |!.1 1.255.Hel|\n",
    "prettier": "{\n  \"semi\": true,\n  \"singleQuote\": false,\n  \"printWidth\": 80\n}\n",
    "prompt": "# GNU coreutils style: the prompt string, not a program.\n# PS1=\"Hello World!$ \"\n",
    "promql": "// PromQL has no printing form; this is a labelled vector literal.\nvector(1)  // Hello World!\n",
    "prop": "# PROP is a component composition language: a program is a graph.\ncomponent Hello\n  output \"Hello World!\"\nend\n",
    "prosemirror": "import { Schema } from 'prosemirror-model'\n\nexport const schema = new Schema({ /* Hello World! */ })\n",
    "psql": "SELECT 'Hello World!' AS greeting;\n",
    "pthreads": "#include <pthread.h>\n#include <stdio.h>\n\nstatic void *greet(void *unused) {\n    printf(\"Hello World!\\n\");\n    return NULL;\n}\n\nint main(void) {\n    pthread_t t;\n    pthread_create(&t, NULL, greet, NULL);\n    pthread_join(t, NULL);\n    return 0;\n}\n",
    "pymc": "import pymc as pm\n\nprint(\"Hello World!\")\n",
    "pyomo": "import pyomo.environ as pyo\n\nprint(\"Hello World!\")\n",
    "pyramid templates": "<h1>Hello World!</h1>\n",
    "python": 'print("Hello World!")',
    "q-asm": "// Q-ASM: Q#'s intermediate representation, as emitted by the compiler\noperation HelloWorld() {\n    Reset(msg);\n    let greeting = \"Hello World!\";\n    Message(greeting);\n}\n",
    "qir": "; QIR is LLVM IR. It has no print, so the greeting is a global.\n@greeting = internal constant [12 x i8] c\"Hello World!\"\n",
    "qualtran": "import qualtran\n\nprint(\"Hello World!\")\n",
    "quill": "// Quill is a rich-text editor; its model is deltas.\nconst delta = new Delta().insert(\"Hello World!\");\n",
    "qutip": "import qutip\n\nprint(\"Hello World!\")\n",
    "raw bytes": "# The bytes of \"Hello World!\" with nothing applied to them.\n# This is what every encoding on the previous pages transforms.\n0000  48 65 6C 6C 6F 20 57 6F 72 6C 64 21             |Hello World!|\n",
    "ray": "import ray\n\nray.init()\nprint(\"Hello World!\")\n",
    "rdf": "<#greeting> \"Hello World!\" .\n",
    "rdfa": "<div xmlns=\"http://www.w3.org/1999/xhtml\" property=\"text\">Hello World!</div>\n",
    "relax ng": "<grammar xmlns=\"http://relaxng.org/ns/structure/1.0\">\n  <start>\n    <element name=\"greeting\">\n      <text>Hello World!</text>\n    </element>\n  </start>\n</grammar>\n",
    "revm": "// revm is an Ethereum VM in Rust; its own Hello World is a plain binary.\nfn main() {\n    println!(\"Hello World!\");\n}\n",
    "risc-v rv32i assembly": "        .section .text\n        .global _start\n\n_start:\n        li   a0, 1            # stdout\n        la   a1, msg\n        li   a2, 12\n        li   a7, 64           # write\n        ecall\n        li   a0, 0\n        li   a7, 93           # exit\n        ecall\n\n        .section .rodata\nmsg:    .ascii \"Hello World!\"\n",
    "rollup": "// rollup.config.js\nexport default {\n  input: \"src/Hello World!.js\",\n  output: { file: \"dist/bundle.js\" },\n};\n",
    "ruby": 'puts "Hello World!"',
    "perl": 'print "Hello World!\\n";',
    "php": '<?php\necho "Hello World!\\n";',
    "python console": 'print("Hello World!")',
    "julia console": 'println("Hello World!")',
    "julia repl": 'julia> println("Hello World!")',
     "python console": '>>> print("Hello World!")',
    "bash": 'echo "Hello World!"',
    "run-length encoding": "# Run-length encoding of \"Hello World!\",\n# with `_` standing in for the space.\n1H2e3l1o1_1W1o1r1l1d1!\n",
    "rur-ple": "procedure greet\n  write(\"Hello World!\")\nend\n",
    "rzi": "# RZI is the run-length encoding images use: a count of two or more\n# followed by the value, and singletons emitted literally. Runs over\n# the bytes of \"Hello World!\":\n#   1 x 'H'\n#   1 x 'e'\n#   2 x 'l'\n#   1 x 'o'\n#   1 x ' '\n#   1 x 'W'\n#   1 x 'o'\n#   1 x 'r'\n#   1 x 'l'\n#   1 x 'd'\n#   1 x '!'\n",
    "s-plus": "cat(\"Hello World!\\n\")\n",
    "schematron": "<?xml version=\"1.0\"?>\n<schema xmlns=\"http://purl.oclc.org/dsdl/schematron\">\n  <pattern id=\"greeting\">\n    <rule context=\"greeting\">\n      <assert test=\"text()='Hello World!'\">Hello World!</assert>\n    </rule>\n  </pattern>\n</schema>\n",
    "scratchjr": "when green flag clicked\nsay [Hello World!]\n",
    "scriptforth": ".\" Hello World!\" cr\n",
    "scsh": "(display \"Hello World!\")\n",
    "seed7": "puts(\"Hello World!\");\n",
    "sesh shell": "echo \"Hello World!\"\n",
    "shell": 'echo "Hello World!"',
    "sh": 'echo "Hello World!"',
    "sigma.js": "const g = new Sigma();\n// node label: Hello World!\n",
    "simula": "BEGIN\n  WRITE(\"Hello World!\")\nEND\n",
    "simula 67": "BEGIN\n  WRITE(\"Hello World!\")\nEND\n",
    "sixel": "# Sixel is a terminal graphics protocol; a sixel encodes one\n# 6x6 cell. \"Hello World!\" in sixel is six lines of DC1/DC2/DC3.\n#!0;1;1H#0~#1~#0~\n",
    "small basic": "Print \"Hello World!\"\n",
    "smalltalk-85": "Transcript showln: 'Hello World!'\n",
    "sml/nj": "val _ = print \"Hello World!\\n\"\n",
    "snap!": "when green flag clicked\nsay [Hello World!]\n",
    "snappy binary": "# A raw Snappy block: a varint of the uncompressed length, then a\n# literal tag and the literal bytes -- \"Hello World!\" verbatim.\n0000  2C 48 65 6C 6C 6F 20 57 6F 72 6C 64 21          |,Hello World!|\n",
    "solr query": "q=Hello World!\n",
    "sparc64 assembly": "        .section .rodata\nmsg:    .asciz \"Hello World!\\n\"\n\n        .section .text\n        .global _start\n_start:\n        mov  5, %g1            # buffer\n        sethi %hi(msg), %g1\n        or   %lo(msg), %g1, %g1\n        mov  1, %o0            # write\n        mov  1, %o1            # fd\n        mov  %g1, %o2\n        mov  13, %o3           # length\n        mov  8, %g2            # buffer\n        mov  %g2, %o4\n        mov  0, %o5\n        mov  6, %g3\n        call %trap\n        mov  1, %g1\n        mov  91, %o0           # exit\n        mov  %g1, %o1\n        mov  8, %g2\n        mov  %g2, %o4\n        mov  0, %o5\n        mov  6, %g3\n        call %trap\n",
    "spir-v": "; SPIR-V is a binary module. Its header is the magic word\n; 0x07230203, little-endian, followed by version and generator.\n; The Hello World! module below has no entry point.\n; 07230203 00010000 00080001\n",
    "sql/mm": "SELECT 'Hello World!' AS greeting FROM DUAL;\n",
    "sql/pl": "DECLARE greeting VARCHAR2(32) := 'Hello World!';\nBEGIN\n    DBMS_OUTPUT.PUT_LINE(greeting);\nEND;\n",
    "sql:2003": "SELECT 'Hello World!' AS greeting;\n",
    "standard lisp": "(print \"Hello World!\")\n",
    "starlogo": "print sentence [Hello World!] []\n",
    "sui move": "module hello::greeting {\n    public fun greet(): vector<u8> {\n        b\"Hello World!\"\n    }\n}\n",
    "swi-prolog": ":- initialization(main).\nmain :- write('Hello World!'), nl.\n",
    "symfony twig": "<h1>Hello World!</h1>\n",
    "t": "cat(\"Hello World!\\n\")\n",
    "t-sql": "PRINT 'Hello World!';\n",
    "tailwind": "<div class=\"p-4 text-2xl font-bold\">Hello World!</div>\n",
    "tar binary": "# A real TAR archive containing one member, hello.txt, holding\n# \"Hello World!\", written by tarfile. The first bytes spell ustar.\n0000  68 65 6C 6C 6F 2E 74 78 74 00 00 00 00 00 00 00 |hello.txt.......|\n0010  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0020  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0030  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0040  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0050  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0060  00 00 00 00 30 30 30 30 36 34 34 00 30 30 30 30 |....0000644.0000|\n0070  30 30 30 00 30 30 30 30 30 30 30 00 30 30 30 30 |000.0000000.0000|\n0080  30 30 30 30 30 31 34 00 30 30 30 30 30 30 30 30 |0000014.00000000|\n0090  30 30 30 00 30 30 37 36 30 34 00 20 30 00 00 00 |000.007604. 0...|\n00A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n00B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n00C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n00D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n00E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n00F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0100  00 75 73 74 61 72 00 30 30 00 00 00 00 00 00 00 |.ustar.00.......|\n0110  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0120  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0130  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0140  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0150  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0160  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0170  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0180  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0190  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n01A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n01B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n01C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n01D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n01E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n01F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0200  48 65 6C 6C 6F 20 57 6F 72 6C 64 21 00 00 00 00 |Hello World!....|\n0210  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0220  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0230  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0240  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0250  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0260  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0270  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0280  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0290  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n02A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n02B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n02C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n02D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n02E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n02F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0300  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0310  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0320  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0330  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0340  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0350  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0360  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0370  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0380  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0390  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n03A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n03B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n03C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n03D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n03E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n03F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0400  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0410  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0420  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0430  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0440  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0450  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0460  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0470  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0480  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0490  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n04A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n04B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n04C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n04D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n04E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n04F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0500  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0510  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0520  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0530  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0540  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0550  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0560  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0570  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0580  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0590  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n05A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n05B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n05C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n05D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n05E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n05F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0600  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0610  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0620  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0630  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0640  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0650  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0660  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0670  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0680  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0690  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n06A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n06B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n06C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n06D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n06E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n06F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0700  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0710  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0720  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0730  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0740  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0750  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0760  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0770  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0780  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0790  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n07A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n07B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n07C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n07D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n07E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n07F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0800  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0810  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0820  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0830  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0840  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0850  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0860  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0870  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0880  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0890  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n08A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n08B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n08C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n08D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n08E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n08F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0900  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0910  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0920  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0930  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0940  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0950  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0960  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0970  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0980  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0990  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n09A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n09B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n09C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n09D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n09E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n09F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0A00  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0A10  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0A20  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0A30  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0A40  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0A50  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0A60  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0A70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0A80  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0A90  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0AA0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0AB0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0AC0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0AD0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0AE0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0AF0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0B00  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0B10  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0B20  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0B30  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0B40  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0B50  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0B60  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0B70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0B80  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0B90  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0BA0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0BB0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0BC0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0BD0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0BE0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0BF0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0C00  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0C10  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0C20  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0C30  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0C40  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0C50  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0C60  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0C70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0C80  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0C90  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0CA0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0CB0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0CC0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0CD0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0CE0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0CF0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0D00  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0D10  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0D20  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0D30  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0D40  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0D50  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0D60  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0D70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0D80  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0D90  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0DA0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0DB0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0DC0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0DD0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0DE0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0DF0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0E00  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0E10  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0E20  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0E30  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0E40  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0E50  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0E60  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0E70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0E80  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0E90  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0EA0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0EB0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0EC0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0ED0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0EE0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0EF0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0F00  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0F10  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0F20  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0F30  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0F40  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0F50  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0F60  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0F70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0F80  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0F90  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0FA0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0FB0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0FC0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0FD0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0FE0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n0FF0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1000  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1010  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1020  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1030  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1040  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1050  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1060  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1070  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1080  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1090  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n10A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n10B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n10C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n10D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n10E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n10F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1100  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1110  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1120  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1130  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1140  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1150  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1160  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1170  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1180  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1190  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n11A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n11B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n11C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n11D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n11E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n11F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1200  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1210  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1220  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1230  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1240  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1250  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1260  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1270  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1280  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1290  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n12A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n12B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n12C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n12D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n12E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n12F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1300  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1310  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1320  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1330  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1340  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1350  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1360  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1370  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1380  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1390  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n13A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n13B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n13C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n13D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n13E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n13F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1400  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1410  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1420  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1430  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1440  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1450  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1460  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1470  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1480  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1490  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n14A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n14B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n14C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n14D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n14E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n14F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1500  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1510  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1520  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1530  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1540  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1550  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1560  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1570  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1580  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1590  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n15A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n15B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n15C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n15D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n15E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n15F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1600  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1610  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1620  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1630  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1640  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1650  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1660  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1670  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1680  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1690  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n16A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n16B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n16C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n16D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n16E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n16F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1700  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1710  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1720  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1730  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1740  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1750  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1760  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1770  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1780  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1790  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n17A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n17B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n17C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n17D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n17E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n17F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1800  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1810  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1820  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1830  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1840  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1850  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1860  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1870  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1880  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1890  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n18A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n18B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n18C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n18D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n18E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n18F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1900  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1910  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1920  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1930  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1940  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1950  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1960  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1970  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1980  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1990  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n19A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n19B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n19C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n19D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n19E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n19F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1A00  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1A10  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1A20  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1A30  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1A40  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1A50  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1A60  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1A70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1A80  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1A90  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1AA0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1AB0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1AC0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1AD0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1AE0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1AF0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1B00  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1B10  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1B20  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1B30  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1B40  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1B50  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1B60  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1B70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1B80  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1B90  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1BA0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1BB0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1BC0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1BD0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1BE0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1BF0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1C00  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1C10  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1C20  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1C30  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1C40  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1C50  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1C60  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1C70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1C80  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1C90  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1CA0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1CB0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1CC0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1CD0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1CE0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1CF0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1D00  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1D10  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1D20  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1D30  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1D40  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1D50  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1D60  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1D70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1D80  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1D90  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1DA0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1DB0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1DC0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1DD0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1DE0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1DF0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1E00  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1E10  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1E20  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1E30  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1E40  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1E50  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1E60  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1E70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1E80  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1E90  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1EA0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1EB0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1EC0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1ED0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1EE0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1EF0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1F00  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1F10  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1F20  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1F30  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1F40  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1F50  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1F60  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1F70  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1F80  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1F90  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1FA0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1FB0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1FC0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1FD0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1FE0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n1FF0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2000  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2010  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2020  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2030  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2040  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2050  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2060  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2070  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2080  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2090  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n20A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n20B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n20C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n20D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n20E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n20F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2100  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2110  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2120  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2130  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2140  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2150  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2160  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2170  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2180  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2190  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n21A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n21B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n21C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n21D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n21E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n21F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2200  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2210  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2220  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2230  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2240  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2250  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2260  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2270  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2280  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2290  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n22A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n22B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n22C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n22D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n22E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n22F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2300  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2310  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2320  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2330  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2340  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2350  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2360  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2370  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2380  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2390  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n23A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n23B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n23C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n23D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n23E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n23F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2400  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2410  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2420  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2430  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2440  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2450  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2460  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2470  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2480  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2490  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n24A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n24B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n24C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n24D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n24E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n24F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2500  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2510  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2520  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2530  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2540  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2550  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2560  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2570  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2580  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2590  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n25A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n25B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n25C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n25D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n25E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n25F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2600  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2610  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2620  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2630  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2640  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2650  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2660  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2670  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2680  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2690  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n26A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n26B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n26C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n26D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n26E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n26F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2700  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2710  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2720  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2730  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2740  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2750  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2760  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2770  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2780  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n2790  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n27A0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n27B0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n27C0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n27D0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n27E0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n27F0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|\n",
    "tasm": "        ; turbo assembler, 16-bit DOS\n        .model small\n        .stack 100h\n        .data\nmsg     db 'Hello World!$'\n        .code\nstart:  mov ax, @data\n        mov ds, ax\n        mov dx, offset msg\n        mov ah, 9\n        int 21h\n        mov ax, 4C00h\n        int 21h\n        end start\n",
    "tei": "<TEI xmlns=\"http://www.tei-c.org/ns/1.0\">\n  <teiHeader><fileDesc><titleStmt><title>Hello World!</title></titleStmt></fileDesc></teiHeader>\n  <text><p>Hello World!</p></text>\n</TEI>\n",
    "tei p5": "<TEI xmlns=\"http://www.tei-c.org/ns/1.0\">\n  <teiHeader><fileDesc><titleStmt><title>Hello World!</title></titleStmt></fileDesc></teiHeader>\n  <text><p>Hello World!</p></text>\n</TEI>\n",
    "tekton": "apiVersion: tekton.dev/v1beta1\nkind: Pipeline\nmetadata:\n  name: hello\nspec:\n  tasks:\n    - name: greet\n      taskSpec:\n        steps:\n          - name: run\n            image: alpine\n            script: echo \"Hello World!\"\n",
    "terraform cdk": "from constructs import Construct\n\n\nclass Hello(Construct):\n    \"\"\"Hello World!\"\"\"\n    def __init__(self, scope: Construct, id: str) -> None:\n        super().__init__(scope, id)\n",
    "text/template": "Hello World!\n",
    "three.js": "import * as THREE from \"three\";\n\nconst scene = new THREE.Scene();\nconsole.log(scene.name || \"Hello World!\");\n",
    "tidyverse": "library(tidyverse)\nmessage(\"Hello World!\")\n",
    "tiptap": "import { Editor } from '@tiptap/core'\n\nconst editor = new Editor({ content: '<p>Hello World!</p>' })\n",
    "trino": "SELECT 'Hello World!' AS greeting\n",
    "turtle logo": "print sentence [Hello World!] []\n",
    "twig 3": "<h1>Hello World!</h1>\n",
    "unicode code point": "# Code points of \"Hello World!\" as U+ notation.\nU+0048 U+0065 U+006C U+006C U+006F U+0020\nU+0057 U+006F U+0072 U+006C U+0064 U+0021\n",
    "unscons": "// Unscons is a constraint model, not a program.\nconstraint hello: text == \"Hello World!\";\n",
    "utf-16": "# UTF-16LE bytes of \"Hello World!\" -- every second byte is zero.\n48 00 65 00 6C 00 6C 00 6F 00 20 00 57 00 6F 00 72 00 6C 00 64 00 21 00\n",
    "utf-32": "# UTF-32LE bytes of \"Hello World!\", four bytes per code point.\n48 00 00 00 65 00 00 00 6C 00 00 00 6C 00 00 00\n6F 00 00 00 20 00 00 00 57 00 00 00 6F 00 00 00\n72 00 00 00 6C 00 00 00 64 00 00 00 21 00 00 00\n",
    "utf-7": "# UTF-7 of \"Hello World!\". Only the run of ASCII letters\n# needs encoding; the space and the exclamation are literal.\n+ZeVnLIqe- World!\n",
    "vax assembly": "        .text\n        .globl _start\n_start:\n        movl    $1, %r0        # write\n        movl    $msg, %r1\n        movl    $12, %r2\n        movl    $4, %r3\n        movl    $6, %r4\n        movl    $5, %r5\n        movb    $14, %r6\n        movb    $10, %r7\n        syscall\n        movl    $1, %r0        # exit\n        movl    $0, %r1\n        movb    $6, %r6\n        movb    $10, %r7\n        syscall\n\n        .data\nmsg:    .ascii \"Hello World!\"\n",
    "vega": "{\n  \"$schema\": \"https://vega.github.io/schema/vega/v5.json\",\n  \"signals\": [{\"name\": \"greeting\", \"value\": \"Hello World!\"}],\n  \"marks\": []\n}\n",
    "vega-lite": "{\n  \"$schema\": \"https://vega.github.io/schema/vega-lite/v5.json\",\n  \"title\": \"Hello World!\",\n  \"data\": {\"values\": []},\n  \"mark\": \"bar\"\n}\n",
    "vis.js": "const nodes = [{ id: 1, label: \"Hello World!\" }];\nconst edges = [];\n",
    "visual prolog": "procedure main\n    write('Hello World!'), nl\nend procedure\n",
    "vite": "// vite.config.js\nimport { defineConfig } from \"vite\";\n\nexport default defineConfig({\n  build: { rollupOptions: { input: \"src/Hello World!.js\" } },\n});\n",
    "vyxal": "«Hello World!»\n",
    "watcom assembler": "        ; Open Watcom assembler, 32-bit flat\n        .386\n        .model flat, stdcall\n        .data\nmsg     db 'Hello World!', 0\n        .code\nstart:  mov     eax, 4d00h       ; WriteConsole\n        mov     ebx, -11          ; stdout handle\n        mov     ecx, offset msg\n        mov     edx, 12\n        call    WriteConsoleA\n        mov     eax, 4c000h       ; ExitProcess\n        xor     ebx, ebx\n        call    ExitProcess\n",
    "webgl": "// WebGL is a drawing API, so the greeting is what gets drawn.\nconst source = `\nattribute vec2 position;\nvoid main() { gl_Position = vec4(position, 0.0, 1.0); }\n// Hello World!\n`;\n",
    "webots": "controller program HelloWorld\n{\n  string greeting = \"Hello World!\";\n}\n",
    "webpack": "// webpack.config.js\nmodule.exports = {\n  mode: \"production\",\n  entry: \"./src/index.js\",\n  output: { filename: \"Hello World!.js\" },\n};\n",
    "wedo": "print(\"Hello World!\")\n",
    "whyml": "let main () = print_endline \"Hello World!\"\n",
    "win32 threads": "#include <windows.h>\n#include <stdio.h>\n\nstatic DWORD WINAPI greet(LPVOID unused) {\n    printf(\"Hello World!\\n\");\n    return 0;\n}\n\nint main(void) {\n    HANDLE t = CreateThread(NULL, 0, greet, NULL, 0, NULL);\n    WaitForSingleObject(t, INFINITE);\n    CloseHandle(t);\n    return 0;\n}\n",
    "windows-1252": "# Windows-1252 shares ASCII with ASCII; \"Hello World!\"\n# occupies no code point of its own.\n48 65 6C 6C 6F 20 57 6F 72 6C 64 21\n",
    "xpages": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<xp:page xmlns:xp=\"http://ns.adobe.com/xpages\">\n  <xp:outputText value=\"Hello World!\"/>\n</xp:page>\n",
    "xpath": "string(\"Hello World!\")\n",
    "xpath 2.0": "string(\"Hello World!\")\n",
    "xsb": ":- initialization(main).\nmain :- write('Hello World!'), nl.\n",
    "xz binary": "# A real .xz stream of \"Hello World!\", written by lzma.compress.\n# It begins FD 37 7A 58 5A 00.\n0000  FD 37 7A 58 5A 00 00 04 E6 D6 B4 46 02 00 21 01 |.7zXZ......F..!.|\n0010  16 00 00 00 74 2F E5 A3 01 00 0B 48 65 6C 6C 6F |....t/.....Hello|\n0020  20 57 6F 72 6C 64 21 00 E2 6F EA C9 45 52 04 75 | World!..o..ER.u|\n0030  00 01 24 0C A6 18 D8 D8 1F B6 F3 7D 01 00 00 00 |..$........}....|\n0040  00 04 59 5A                                     |..YZ|\n",
    "yarn": "{\n  \"name\": \"hello\",\n  \"version\": \"1.0.0\",\n  \"description\": \"Hello World!\",\n  \"main\": \"index.js\"\n}\n",
    "yash": "echo \"Hello World!\"\n",
    "yasm": "        ; yasm, ELF x86-64\n        section .data\nmsg:    db \"Hello World!\", 10\n\n        section .text\n        global _start\n_start:\n        mov     rax, 1\n        mov     rdi, 1\n        mov     rsi, msg\n        mov     rdx, 13\n        syscall\n        mov     rax, 60\n        xor     rdi, rdi\n        syscall\n",
    "yql": "SELECT \"Hello World!\" AS greeting\n",
    "z180 assembly": "        ; Zilog Z180\n        org 0x100\n\n        ld   hl, msg\n        ld   de, $FF02        ; console out\nloop:\n        ld   a, (hl)\n        or   a\n        jr   z, done\n        ld   (de), a\n        inc  hl\n        jr   loop\ndone:\n        halt\n\nmsg:    defb \"Hello World!\", 13, 10, 0\n",
    "zip binary": "# A real ZIP archive containing one member, hello.txt, holding\n# \"Hello World!\", written by zipfile.\n0000  50 4B 03 04 14 00 00 00 08 00 06 1B 51 5D A3 1C |PK..........Q]..|\n0010  29 1C 0E 00 00 00 0C 00 00 00 09 00 00 00 68 65 |).............he|\n0020  6C 6C 6F 2E 74 78 74 F3 48 CD C9 C9 57 08 CF 2F |llo.txt.H...W../|\n0030  CA 49 51 04 00 50 4B 01 02 14 00 14 00 00 00 08 |.IQ..PK.........|\n0040  00 06 1B 51 5D A3 1C 29 1C 0E 00 00 00 0C 00 00 |...Q]..)........|\n0050  00 09 00 00 00 00 00 00 00 00 00 00 00 80 01 00 |................|\n0060  00 00 00 68 65 6C 6C 6F 2E 74 78 74 50 4B 05 06 |...hello.txtPK..|\n0070  00 00 00 00 01 00 01 00 37 00 00 00 35 00 00 00 |........7...5...|\n0080  00 00                                           |..|\n",
    "zsh": 'echo "Hello World!"',
    "fish": 'echo Hello World!',
    "ksh": 'echo "Hello World!"',
    "csh": 'echo Hello World!',
    "tcsh": 'echo Hello World!',
    "dash": 'echo "Hello World!"',
    "ash": 'echo "Hello World!"',
    "elvish": 'echo "Hello World!"',
    "nushell": 'print "Hello World!"',
    "xonsh": 'print("Hello World!")',
    "batchfile": '@echo off\r\necho Hello World!',
    "batch": '@echo off\r\necho Hello World!',
    "visual basic": 'Module Program\r\n    Sub Main()\r\n        Console.WriteLine("Hello World!")\r\n    End Sub\r\nEnd Module',
    "visual basic .net": 'Module Program\r\n    Sub Main()\r\n        Console.WriteLine("Hello World!")\r\n    End Sub\r\nEnd Module',
    "vb.net": 'Module Program\r\n    Sub Main()\r\n        Console.WriteLine("Hello World!")\r\n    End Sub\r\nEnd Module',
    "javascript": 'console.log("Hello World!");',
    "typescript": 'console.log("Hello World!");',
    "json": '{\n  "hello": "Hello World!"\n}',
    "yaml": 'hello: Hello World!\n',
    "json5": '{\n  hello: "Hello World!",\n}',
    "jsonl": '{"hello":"Hello World!"}\n',
    "jsonc": '{\n  // Hello World!\n  "hello": "Hello World!"\n}',
    "toml": 'message = "Hello World!"\n',
    "ini": '[rainbow]\nmessage = Hello World!\n',
    "css": ':root::after {\n  content: "Hello World!";\n}',
    "html": '<!DOCTYPE html>\n<html><head><title>x</title></head>\n<body><h1>Hello World!</h1></body></html>',
    "markdown": '# Hello World!\n\n*part of the RAiNBOW Hello World rainbow*\n',
    "restructuredtext": 'Hello World!\n===========\n\n*part of the RAiNBOW Hello World rainbow*\n',
    "asciidoc": '= Hello World!\n\n*part of the RAiNBOW Hello World rainbow*\n',
    "tex": '\\documentclass{article}\n\\begin{document}\nHello World!\n\\end{document}\n',
    "latex": '\\documentclass{article}\n\\begin{document}\nHello World!\n\\end{document}\n',
    "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="60">\n  <rect width="240" height="60" fill="#0d1117"/>\n  <text x="12" y="38" fill="#58a6ff" font-family="monospace" font-size="20">Hello World!</text>\n</svg>\n',
    "vim script": 'echo "Hello World!"',
    "viml": 'echo "Hello World!"',
    "emacs lisp": '(princ "Hello World!")',
    "makefile": 'hello:\n\t@echo "Hello World!"\n',
    "make": 'hello:\n\t@echo "Hello World!"\n',
    "cmake": 'message(STATUS "Hello World!")\n',
    "dockerfile": 'FROM alpine\nRUN echo "Hello World!"\n',
    "terraform": 'output "hello" {\n  value = "Hello World!"\n}\n',
    "hcl": 'output "hello" {\n  value = "Hello World!"\n}\n',
    "starlark": 'print("Hello World!")',
    "bazel": 'print("Hello World!")',
    "groovy": 'println "Hello World!"',
    "nix": '{ pkgs ? import <nixpkgs> {} }: pkgs.hello\n',
    "gradle": 'task hello { doLast { println "Hello World!" } }\n',
    "ant build system": '<project name="rainbow">\n  <target name="hello"><echo message="Hello World!"/></target>\n</project>\n',
    "meson": "project('rainbow')\nmessage('Hello World!')\n",
    "bison": '%%\nprinter : { "Hello World!" } ;\n',
    "yacc": '%%\nprinter : { "Hello World!" } ;\n',
    "m4": "divert(-1)\ndefine(`hello', `Hello World!')\ndivert(0)\nhello\n",
    "gitignore": '# Hello World!\nhello.txt\n',
    "git attributes": '# Hello World!\n* text=auto\n',
    "npm config": '{\n  "hello": "Hello World!"\n}\n',
    "pip requirements": '# Hello World!\nrainbow\n',
    "procfile": 'web: echo "Hello World!"\n',
    "crontab": '# Hello World!\n0 0 * * * echo Hello World!\n',
    "hosts file": '127.0.0.1 localhost # Hello World!\n',
    "option list": 'message = Hello World!\n',
    "tor config": '# Hello World!\nSocksPort 9050\n',
    "shellcheck config": '# Hello World!\nenable=all\n',
    "browserslist": '# Hello World!\n> 0.5%\nlast 2 versions\n',
    "isabelle root": 'chapter Hello_Theory\n  imports Main\nbegin\n\ntext \\<open>Hello World!\\<close>\n\nend\n',
    "xmake": 'target("hello")\n    set_kind("phony")\non_run(function () print("Hello World!") end)\n',
    "quak": '"Hello World!"',
    "scala": 'object HelloWorld extends App {\n  println("Hello World!")\n}\n',
    "clojure": '(println "Hello World!")\n',
    "clojure console": '(println "Hello World!")\n',
    "clojure script": '(println "Hello World!")\n',
    "common lisp": '(format t "Hello World!~%")\n',
    "lisp": '(format t "Hello World!~%")\n',
    "scheme": '(display "Hello World!") (newline)\n',
    "racket": '#lang racket\n(displayln "Hello World!")\n',
    "r7rs scheme": '(import (scheme base) (scheme write))\n(display "Hello World!")\n',
    "newlisp": '(println "Hello World!")\n',
    "elixir": 'IO.puts "Hello World!"\n',
    "erlang": '-module(hello).\n-export([main/0]).\nmain() -> io:format("Hello World!~n").\n',
    "haskell": 'main :: IO ()\nmain = putStrLn "Hello World!"\n',
    "purescript": 'module Main where\nimport Prelude\nimport Effect (Effect)\nimport Effect.Console (log)\n\nmain :: Effect Unit\nmain = log "Hello World!"\n',
    "elm": 'module Main exposing (main)\nimport Html exposing (text)\n\nmain = text "Hello World!"\n',
    "ocaml": 'let () = print_endline "Hello World!"\n',
    "f#": 'printfn "Hello World!"\n',
    "f sharp": 'printfn "Hello World!"\n',
    "standard ml": 'val _ = print "Hello World!\\n"\n',
    "sml": 'val _ = print "Hello World!\\n"\n',
    "reason": 'let () = print_endline "Hello World!"\n',
    "gleam": 'pub fn main() {\n  io.println("Hello World!")\n}\n',
    "idris": 'module Main\n\nmain : IO ()\nmain = putStrLn "Hello World!"\n',
    "lean": 'def main : IO Unit :=\n  IO.println "Hello World!"\n',
    "agda": 'module hello where\n\npostulate\n  String : Set\n  _閳摜 : {A : Set} 閳?A 閳?A 閳?Set\n',
    "coq": 'Definition hello : string := "Hello World!".\n',
    "isabelle": 'theory Hello\n  imports Main\nbegin\n\n  lemma greeting: "Hello World!" \\<in> {undefined}\\<^sub> \\<^sub> * x \\<^sub> \\<^sub>.\n\nend\n',
    "tla+": '---- MODULE Hello ----\nEXTENDS Naturals\nVARIABLE msg\nInit == msg = "Hello World!"\nNext == UNCHANGED msg\nSpec == Init /\\ [][Next]_msg\n=================\n',
    "agda2": 'module hello where\n',
    "coq script": 'Definition hello : string := "Hello World!".\n',
    "curry": 'main = putStrLn "Hello World!"\n',
    "r": 'cat("Hello World!\\n")\n',
    "gnuplot": 'set label "Hello World!"\n',
    "gnuplot script": 'set label "Hello World!"\n',
    "julia": 'println("Hello World!")\n',
    "mathematica": 'Print["Hello World!"]\n',
    "wolfram language": 'Print["Hello World!"]\n',
    "wolfram": 'Print["Hello World!"]\n',
    "maxima": 'display("Hello World!");\n',
    "octave": "disp('Hello World!');\n",
    "matlab": "disp('Hello World!');\n",
    "scilab": "disp('Hello World!');\n",
    "gnu octave": "disp('Hello World!');\n",
    "idl": "print, 'Hello World!'\n",
    "sas": 'put "Hello World!";\n',
    "stata": 'display "Hello World!"\n',
    "spss": 'DISPLAY "Hello World!".\n',
    "tcl": 'puts "Hello World!"\n',
    "expect": 'puts "Hello World!"\n',
    "tcl config": 'set message "Hello World!"\n',
    "lua": 'print("Hello World!")\n',
    "luau": 'print("Hello World!")\n',
    "moon": 'print "Hello World!"\n',
    "pico-8": 'print("hello world!")\n',
    "nushell": 'print "Hello World!"\n',
    "perl 6": 'say "Hello World!"\n',
    "raku": 'say "Hello World!"\n',
    "perl 6 module": 'say "Hello World!"\n',
    "perl module": 'package Hello;\nsub hi { print "Hello World!\\n"; }\n',
    "dart": 'void main() => print("Hello World!");\n',
    "haxe": 'class Main {\n  static function main() {\n    trace("Hello World!");\n  }\n}\n',
    "solidity": '// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\ncontract Hello {\n    function greet() public pure returns (string memory) {\n        return "Hello World!";\n    }\n}\n',
    "typoscript": 'page = PAGE\npage.10 = TEXT\npage.10.value = Hello World!\n',
    "jq": '{hello: "Hello World!"}\n',
    "protobuf": 'syntax = "proto3";\nmessage Hello { string greeting = 1; }\n',
    "protocol buffers": 'syntax = "proto3";\nmessage Hello { string greeting = 1; }\n',
    "thrift": 'namespace cpp Hello\nservice HelloService {\n  string greet()\n}\n',
    "cap'n proto": '@0x9eb1e8f1a2f3c4d5;\nstruct Hello {\n  greeting @0 :Text;\n}\n',
    "avro": '{"type": "record", "name": "Hello", "fields": [{"name": "greeting", "type": "string"}]}\n',
    "graphql": 'type Query {\n  hello: String!\n}\n',
    "gql": 'type Query {\n  hello: String!\n}\n',
    "yang": 'module hello {\n  namespace "urn:example:hello";\n  prefix rrb;\n  container hello { leaf world { type string; } }\n}\n',
    "dhall": '< "Hello World!" : Text\n',
    "cue": 'hello: "Hello World!"\n',
    "nickel": '{ hello = "Hello World!" }\n',
    "pkl": 'hello = "Hello World!"\n',
    "jsonnet": '{\n  hello: "Hello World!",\n}\n',
    "rego": 'package rainbow\n\ndefault hello := "Hello World!"\n',
    "cue export": 'hello: "Hello World!"\n',
    "sqf": 'titleText = "Hello World!";\n',
    "squirrel": 'function start() { print("Hello World!"); }\n',
    "nesc": 'int main() { return puts("Hello World!"); }\n',
    "nesasm": '; Hello World!\n',
    "vim help file": '*rainbow.txt*  Hello World!\n',
    "man page": '.TH RAINBOW 1\n.SH NAME\nHello World!\n',
    "troff": '.TH RAINBOW 1\n.SH NAME\nHello World!\n',
    "man": '.TH RAINBOW 1\n.SH NAME\nHello World!\n',
    "roff": '.TH RAINBOW 1\n.SH NAME\nHello World!\n',
    "restructuredtext": 'Hello World!\n===========\n\n*part of the RAiNBOW Hello World rainbow*\n',
    "bibtex": '@misc{rainbow,\n  title = {Hello World!}\n}\n',
    "openapi specification v2": 'openapi: "2.0"\ninfo:\n  title: Hello World!\n  version: "1.0"\npaths: {}\n',
    "openapi specification v3": 'openapi: 3.0.0\ninfo:\n  title: Hello World!\n  version: "1.0.0"\npaths: {}\n',
    "sarif": '{"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "runs": [{"tool": {"driver": {"name": "Hello World!"}}}]}\n',
    "geojson": '{"type": "Feature", "properties": {"hello": "Hello World!"}, "geometry": null}\n',
    "topojson": '{"type": "Topology", "objects": {"hello": {"type": "GeometryCollection", "geometries": []}}, "arcs": []}\n',
    "har": '{"log": {"version": "1.2", "creator": {"name": "Hello World!"}}}\n',
    "webmanifest": '{"name": "Hello World!", "short_name": "Hello World!"}\n',
    "hjson": '{\n  hello: Hello World!\n}\n',
    "hujson": '{\n  // Hello World!\n  hello: Hello World!\n}\n',
    "editorconfig": 'root = true\n\n[*]\ncharset = utf-8\n',
    "text": 'Hello World!\n',
    "plain text": 'Hello World!\n',
    "us-ascii": 'Hello World!\n',
    "nfo": 'Hello World!\n',
    "brainfuck": '++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.\n',
    "brainfuck template": '++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.\n',
    "whitespace": '   \t\n\t \t \t\n\t\n \t\t \t \t\n \t\t \t \t \t\n \t \t \t\t\t \t\t\n \t \t \t\t\t \t\n \t \t \t \t\t \t \t\n \t \t \t\t\t \t\t\n \t \t \t\t\t \t\t\n \t \t \t\t\t \t\t\n\t\t \t\t \t \t\t\t \t \t \t \t \t\t\t\t\t \t\t \t \t \t\n\t\t \t\t \t \t\t\t \t \t \t \t \t\t\t\t\t \t\t \t \t \t\n\t\t\t \t\t \t\t\t \t\t \t\t \t \t\t\t\t\t\t \t\t \t\t\t \t\t\t\t\t\n\t\t \t\t \t \t\t \t\t \t\t \t \t \t \t\t \t \t\t \t\t \t\t\t\t\t\t\t\t\t \t\n\t \t \t\t \t \t\t \t\t \t\t \t \t \t \t\t \t \t \t \t \t \t\t \t\t\t\t\t \t\t\n\t\t \t\t \t \t\t \t\t \t\t \t \t \t\t \t \t \t\t \t \t\t \t\t \t\t \t\t\t \t\t\t\t\n \t\t \t\t\t \t\t\t \t\t \t\t \t\t \t\t\t\t\t\t\t \t\t \t\t \t\t\t\t\t \t\t \t \t \t\t\n\t \t\t \t \t \t\t\t \t\t\t\t \t\t\t \t\t\t \t \t\t\t\t\t\t\t\t\t \t\t\t\t \t\t\t \t \t\t\t\t\t \t\t\t\n\t\t\t\t \t\t \t\t\t\t\t\t\t \t\t\t \t\t\t\t\t\t \t\t\t\t\t\t\t \t\t\t \t\t\t \t \t\t\t \t\t\t\t\t \t \t\t\t\n\t\t \t \t \t \t\t\t \t \t\t\t\t \t\t\t\t\t \t\t\t \t \t\t\t\t \t\t\t\t\t\t\t \t \t\t\t\t \t\t\t \t\t \t\t\t\t\t \t\t\t \t\t \t\n\t \t \t\t\t \t\t \t\t \t \t\t \t\t \t\t \t \t\t \t\t\t \t\t\t\t\t\t \t\t\t \t\t\t \t\t\t\t\t\t\t \t\t\t \t\t\t\t \t\t\t\t\t\t \t\t \t\n\t\t\t \t\t \t \t \t\t \t \t\t \t\t \t \t \t\t\t\t\t \t\t\t\t\t \t\t \t\t \t\t \t\t \t\t\t\t\t \t\t\t\t \t \t\t\t\t \t\t\t\t \t\t\t \t\t\t\t\t \t\t\t\t\t \t\t\t\t\t \t\t\t\t \t\t \t\t\t\t\t \t\t \t\t \t\n\t\t \t \t \t \t\t \t \t \t\t \t \t\t\t \t \t\t\t\t \t\t\t\t \t\t\t\t\t\t \t\t \t\t\t\t \t \t\t\t\t \t \t \t\t \t\t\t \t\t\t\t \t\t\t\t\t\t\t\t \t\t \t \t\t\t\t \t\t\t\t\t\t \t\t \t\t\t \t\t \t\t\t \t\t\t\t \t\t\t\t\t\t\t\t\t\t\t\t\t \t\t\t\t \t\t\t\t \t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t \t\t\t\t\t\t\t\t \t \t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t \t\t \t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t \t\t\t\t \t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t \t\t \t\t \t\t\t\t \t\t \t\t \t\t \t\n',
    "lolcode": 'HAI 1.2\nVISIBLE "HAI WORLD!"\nKTHXBYE\n',
    "intercal": 'DO ,1 <- #13\nPLEASE DO ,1 SUB #1 <- #238\nDO ,1 SUB #2 <- #108\nDO ,1 SUB #3 <- #112\nDO ,1 SUB #4 <- #0\nDO ,1 SUB #5 <- #64\nDO ,1 SUB #6 <- #194\nPLEASE DO ,1 SUB #7 <- #48\nPLEASE DO ,1 SUB #8 <- #22\nDO ,1 SUB #9 <- #248\nDO ,1 SUB #10 <- #168\nPLEASE DO ,1 SUB #11 <- #24\nDO ,1 SUB #12 <- #16\nDO ,1 SUB #13 <- #162\nPLEASE READ OUT ,1\nPLEASE GIVE UP\n',
    "c-intercal": 'DO ,1 <- #13\nPLEASE DO ,1 SUB #1 <- #238\nPLEASE DO ,1 SUB #2 <- #108\nDO ,1 SUB #3 <- #112\nDO ,1 SUB #4 <- #0\nDO ,1 SUB #5 <- #64\nDO ,1 SUB #6 <- #194\nPLEASE DO ,1 SUB #7 <- #48\nPLEASE DO ,1 SUB #8 <- #22\nDO ,1 SUB #9 <- #248\nDO ,1 SUB #10 <- #168\nPLEASE DO ,1 SUB #11 <- #24\nDO ,1 SUB #12 <- #16\nDO ,1 SUB #13 <- #162\nPLEASE READ OUT ,1\nPLEASE GIVE UP\n',
    "malbolge": '(=<`#9]~6ZY32Vx/4Rs+0No-&Jk)\"Fh}|Bcy?`=*z]Kw%oG4UUS0/@-ejc(:\'8dc\n',
    "beef": ' Beef is a throwaway language.\n',
    "beef": "        ,,,,,,,,,,,,\n        P" + " " * 4 + "Hello World!\n",
    "piet": 'rp]2jA7Fi\\>b\n',
    "chef": 'Hello World Souffle.\n\nThis recipe prints the traditional greeting.\n\nMethod.\nPours the greeting.\nServes 1.\n',
    "shakespeare": 'The Merry Wives of Windsor\n\nJuliet: Good morrow, fair friend!\n',
    "ook": 'Ook. Ook!\n',
    "cow": 'Hello World!\n',
    "deadfish": 'iaccmovumm\n',
    "chicken": 'Hello World!\n',
    "false": '"Hello, World!"\n',
    "unlambda": 's`ki`` `s``k.*s`\n',
    "golfscript": '"Hello World!"\n',
    "pyth": '"Hello World!"\n',
    "cjam": '"Hello World!"\n',
    "05ab1e": '"Hello World!"',
    "actually": 'a"Hello World!"\n',
    "jelly": '"Hello, World!"\n',
    "hexagony": '\n   v  <\n  mpxD\n',
    "befunge": '"Hello World!",,,,,,,@',
    "befunge-93": '"Hello World!",,,,,,,@',
    "marbel": '[Hello World!]q\n',
    "smalltalk": 'Transcript showln: \'Hello World!\'.\n',
    "self": '|#( * 4 + 72 message: putln: ) 3 printString .\n',
    "forth": '." Hello World!" cr\n',
    "postscript": '(Hello World!) show\n',
    "io": 'writeln("Hello World!")\n',
    "j": 'echo \'Hello World!\'\n',
    "apl": '\'Hello World!\'\n',
    "k": '"Hello World!"\n',
    "q": '"Hello World!"\n',
    "jq": '"Hello World!"\n',
    "raku": '"Hello World!".say\n',
    "factor": 'USING: io ;\n"Hello World!" print\n',
    "picolisp": '(println "Hello World!")\n',
    "newlisp": '(println "Hello World!")\n',
    "clojure": '(println "Hello World!")\n',
    "janet": '(print "Hello World!")\n',
    "carp": '(Carp/Hello World!)\n',
    "mojo": 'fn main():\n    print("Hello World!")\n',
    "zig": 'const std = @import("std");\n\npub fn main() !void {\n    std.debug.print("Hello World!\\n", .{});\n}\n',
    "go": 'package main\n\nimport "fmt"\n\nfunc main() {\n\tfmt.Println("Hello World!")\n}\n',
    "rust": 'fn main() {\n    println!("Hello World!");\n}\n',
    "c": '#include <stdio.h>\n\nint main(void) {\n    puts("Hello World!");\n    return 0;\n}\n',
    "c++": '#include <iostream>\n\nint main() {\n    std::cout << "Hello World!" << std::endl;\n    return 0;\n}\n',
    "c#": 'using System;\n\nclass Program {\n    static void Main() {\n        Console.WriteLine("Hello World!");\n    }\n}\n',
    "f#": 'printfn "Hello World!"\n',
    "java": 'class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello World!");\n    }\n}\n',
    "kotlin": 'fun main() {\n    println("Hello World!")\n}\n',
    "swift": 'print("Hello World!")\n',
    "objective-c": '#import <Foundation/Foundation.h>\n\nint main() {\n    @autoreleasepool {\n        NSLog(@"Hello World!");\n    }\n    return 0;\n}\n',
    "objective-c++": '#import <iostream>\n\nint main() {\n    std::cout << "Hello World!" << std::endl;\n    return 0;\n}\n',
    "dart": 'void main() {\n  print("Hello World!");\n}\n',
    "crystal": 'puts "Hello World!"\n',
    "nim": 'echo "Hello World!"\n',
    "vlang": 'println("Hello World!")\n',
    "odin": 'package main\n\nimport "core:fmt"\n\nmain :: proc() {\n    fmt.println("Hello World!")\n}\n',
    "gleam": 'pub fn main() {\n  io.println("Hello World!")\n}\n',
    "elm": 'module Main exposing (main)\nimport Html exposing (text)\n\nmain = text "Hello World!"\n',
    "crystal lang": 'puts "Hello World!"\n',
    "gdscript": 'extends SceneTree\n\nfunc _init():\n\tprint("Hello World!")\n\tquit()\n',
    "nix": 'builtins.trace "Hello World!" null\n',
    "hcl": 'output "hello" { value = "Hello World!" }\n',
    "terraform": 'output "hello" { value = "Hello World!" }\n',
    "purescript": 'module Main where\nimport Prelude\nimport Effect (Effect)\nimport Effect.Console (log)\n\nmain :: Effect Unit\nmain = log "Hello World!"\n',
    "elm": 'module Main exposing (main)\nimport Html exposing (text)\n\nmain = text "Hello World!"\n',
    "stan": 'data { int<lower=0> N; }\nparameters { real y; }\nmodel { y ~ normal(0, 1); }\ngenerated quantities { real y_sim = normal_rng(0, 1); }\n',
    "mathematica": 'Print["Hello World!"]\n',
    "wolfram language": 'Print["Hello World!"]\n',
    "sas": 'put "Hello World!";\n',
    "metafont": 'message "Hello World!";\nend\n',
    "postscript": '/hello { (Hello World!) show } def\n',
    "move": 'module Hello::main {\n    fun main() {\n        move_to(&Hello, S{0});\n    }\n}\n',
    "vyper": '@external\ndef hello() -> String[6]:\n    return "Hello World"\n',
    "cairo": 'from starkware.cairo.common import print\n\nfunc main():\n    print("Hello World!")\n    return ()\n',
    "motoko": 'public func main() {\n    Debug.print("Hello World!")\n}\n',
    "clarity": '(begin (print (string-append "Hello" " World!")))\n',
    "ligo": 'let main () = Js.log "Hello World!"\n',
    "ligo westeros": 'let main () = Js.log "Hello World!"\n',
    "c3": 'fn void main()\n{\n    io::printfn("Hello World!");\n}\n',
    "carbon": 'fn Main() -> i32 {\n    return 0;\n}\n',
    "v": 'fn main() {\n\tprintln("Hello World!")\n}\n',
    "odin": 'package main\nimport "core:fmt"\nmain :: proc() {\n\tfmt.println("Hello World!")\n}\n',
    "jai": '#import "std"\nmain :: () {\n    std.print("Hello World!")\n}\n',
    "hare": 'use fmt;\n\nexport fn main() void {\n\tfmt.println("Hello World!") !;\n}\n',
    "mojo": 'fn main():\n    print("Hello World!")\n',
    "gleam": 'import gleam/io\n\npub fn main() {\n  io.println("Hello World!")\n}\n',
    "roc": 'module {} exposing main\n\nmain = "Hello World!"\n',
    "flix": 'println("Hello World!")\n',
    "gleam": 'pub fn main() { io.println("Hello World!") }\n',
    "solidity": 'pragma solidity ^0.8.0;\ncontract Hello { function greet() public pure returns (string memory) { return "Hello World!"; } }\n',
    "circom": 'pragma circom 2.0.0;\ntemplate Hello() {\n  signal output out;\n}\n',
    "q#": 'namespace Microsoft.Quantum.Samples {\n    open Microsoft.Quantum.Intrinsic;\n    @EntryPoint()\n    operation Hello() : Unit {\n        Message("Hello World!");\n    }\n}\n',
    "silq": 'namespace Silq;\n\nfunction main(): Unit {\n    print("Hello World!");\n}\n',
    "quipper": 'module Main where\nmain :: String\nmain = "Hello World!"\n',
    "openqasm": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n',
    "qcl": 'BEGIN\n  qubit q[1];\nEND',
    "quilt": 'include \"qelib1.inc\";\nqreg q[2];\n',
    "ocean": 'from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\n',
    "braket": 'from braket.circuits import Circuit\nCircuit().h(0).cnot(0, 1)\n',
    "penny lane": 'from pennylane import numpy as np\n',
    "stim": 'import stim\ncircuit = stim.Circuit()\n',
    "tla+": '---- MODULE Hello ----\nEXTENDS Naturals\nmsg == "Hello World!"\n====\n',
    "alloy": 'sig Hello {\n  greeting: one String\n}\n',
    "dafny": 'method Main() {\n  print "Hello World!", "\n";\n}\n',
    "f*": 'module Hello\nlet hello : string = "Hello World!"\n',
    "cayenne": 'hello = "Hello World!";\n',
    "epigram": 'Hello World!\n',
    "ats": 'implement main (): void = () println!("Hello World!")\n',
    "pvs": 'Hello World!\n',
    "hol light": 'Hello World!\n',
    "mizar": 'environ\n  foo: "Hello World!";\nend foo;\n',
    "metamath": '$ Hello World! $\n',
    "acl2": '(hello-world)\n',
    "event-b": 'machine Hello\nvariables h = "Hello World!"\ninvariants inv_h:\n  h \\in STRING\nend\n',
    "b method": 'MACHINE Hello\nSEES Naturals\nOPERATIONS op = PRE h : \"Hello World!\" THEN h := h END\nEND\n',
    "z notation": 'Z\n{ Hello World! }\n',
    "vdm": 'module Hello\ndefinition module Hello is\n exports all\n  value: nat\nend Hello\n',
    "verilog": 'module hello;\n  initial begin\n    $display("Hello World!");\n  end\nendmodule\n',
    "systemverilog": 'module hello;\n  initial $display("Hello World!");\nendmodule\n',
    "chisel": 'import chisel3._\n\nclass Hello extends Module {\n  def hello = Module(new Bundle { val out = IO(Output(Bool())) })\n}\n',
    "bluespec": 'package Hello;\n(* synthesize *)\nmodule mkHello;\nendmodule\n',
    "clash": '{-# ANN hello (Synthesize.topEntity, Clock dom, Reset rst) #-}\nmodule Main where\nhello :: String\nhello = "Hello World!"\n',
    "spinalhdl": 'import spinal.core._\n\nobject Hello extends App {\n  def main(): Unit = {\n    println("Hello World!")\n  }\n}\n',
    "amaranth": 'from amaranth import *\n\nclass Hello(Elaboratable):\n    def elaborate(self, platform):\n        return Module()\n',
    "migen": 'from migen import *\n',
    "myhdl": 'from myhdl import block\n\n@block\ndef hello():\n    print("Hello World!")\n',
    "systemc": '#include <systemc>\n#include <iostream>\n\nint sc_main() {\n  std::cout << "Hello World!" << std::endl;\n  return 0;\n}\n',
    "vhdl": 'library ieee;\nuse ieee.std_logic_1164.all;\nentity hello is\nend entity;\narchitecture rtl of hello is\nbegin\n  process begin\n    report "Hello World!" severity note;\n    wait;\n  end process;\nend architecture;\n',
    "sbt": 'name := "rainbow"\n',
    "cabal": 'name: rainbow\nversion: 0.1.0.0\n',
    "mix": 'defmodule Hello do\n  def hello, do: IO.puts("Hello World!")\nend\n',
    "r": 'cat("Hello World!\\n")\n',
    "haxe": 'class Main { static function main() { trace("Hello World!"); } }\n',
    "supercollider": '("Hello World!").postln;\n',
    "sc": '"Hello World!".postln;\n',
    "common lisp": '(format t "Hello World!~%")\n',
    "emacs lisp": '(princ "Hello World!")\n',
    "clojure": '(println "Hello World!")\n',
    "elixir": 'IO.puts "Hello World!"\n',
    "erlang": '-module(hello).\n-export([main/0]).\nmain() -> io:format("Hello World!~n").\n',
    "julia": 'println("Hello World!")\n',
    "nim": 'echo "Hello World!"\n',
    "gleam": 'pub fn main() { io.println("Hello World!") }\n',
    "haxe": 'class Main { static function main() { trace("Hello World!"); } }\n',
    "pico-8": 'print("hello world!")\n',
    "ceylon": 'shared void run() {\n    print("Hello World!");\n}\n',
    "gosu": 'class Hello {\n  static void main() {\n    println("Hello World!")\n  }\n}\n',
    "fantom": 'class Main\n  Void main()\n    println("Hello World!")\n',
    "xtend": 'class Hello {\n  def main(): Unit = println("Hello World!")\n}\n',
    "parrot": '.sub "Hello World!", 1\n',
    "pasm": 'print "Hello World!"\n',
    "pico-8": 'print("hello world!")\n',
    "chuck": '<<<"Hello World!", "">>>;\n',
    "processing": 'void setup() {\n  println("Hello World!");\n}\n',
    "arduino": 'void setup() {\n  Serial.begin(9600);\n}\n\nvoid loop() {\n  Serial.println("Hello World!");\n  delay(1000);\n}\n',
    "nesasm": '; Hello World!\n',
    "pic": 'movlw 0\n',
    "euphoria": 'printf(1, "Hello World!")\n',
    "opencl": '__kernel void hello() {\n  printf("Hello World!");\n}\n',
    "cuda": '__global__ void hello() {\n  printf("Hello World!");\n}\n',
    "hlsl": 'float4 main() : SV_Target {\n  return float4(1, 1, 1, 1);\n}\n',
    "glsl": '#version 330 core\nvoid main() { }\n',
    "wgsl": 'fn main() {}\n',
    "metal": '#include <metal_stdlib>\nkernel void hello() { }\n',
    "sycl": '#include <sycl/sycl.hpp>\n',
    "hip": '__global__ void hello() { }\n',
    "vulkan compute": '#version 450\n',
    "webgpu": '@compute @workgroup_size(1)\nfn main() {}\n',
    "rust": 'fn main() { println!("Hello World!"); }\n',
    "c": '#include <stdio.h>\nint main(void){ puts("Hello World!"); return 0; }\n',
    "c++": '#include <iostream>\nint main(){ std::cout << "Hello World!" << std::endl; }\n',
    "lisp": '(format t "Hello World!~%")\n',
    "gdscript": 'extends SceneTree\nfunc _init():\n\tprint("Hello World!")\n\tquit()\n',
    "nim": 'echo "Hello World!"\n',
    "supercollider": '("Hello World!").postln;\n',
    "raku": '"Hello World!".say\n',
    "v": 'fn main() {\n\tprintln("Hello World!")\n}\n',
    "llvm": 'define i32 @main() {\n  ret i32 0\n}\n',
    "webassembly": '(module\n  (func (export "_start")\n    (result i32) i32.const 0)\n)\n',
    "assembly": 'section .data\n  msg db "Hello World!", 10\n',
    "nasm": 'section .data\n  msg db "Hello World!", 10\n',
    "gas": '.section .data\nmsg: .ascii "Hello World!"\n',
    "asm": 'section .data\n  msg db "Hello World!", 10\n',
    "linker script": 'ENTRY(_start)\n',
    "llvm ir": 'define i32 @main() {\n  ret i32 0\n}\n',
    # ---- 中文编程语言 ----------------------------------------------------
    "中文python": "def 你好():\n    print(\"Hello World!\")\n\n\n你好()\n",
    "中文标识符": "def 打招呼():\n    print(\"Hello World!\")\n\n\n打招呼()\n",
    "中文正则": "// 中文正则：匹配中文正文的正则表达式。\nconst 中文 = /[\\u4e00-\\u9fa5]+/gu;  // Hello World!\n",
    "中文注释": "# 你好，世界！\n# 这一行是中文注释。\nprint(\"Hello World!\")\n",
    "中文注释编程": "#!/usr/bin/env python3\n# 中文注释编程：程序逻辑全部写在中文注释里。\nprint(\"Hello World!\")  # 打印问候语\n",
    "仓颉": 'main(): Int64 {\n    println("Hello World!")\n    return 0\n}\n',
    "cangjie": 'main(): Int64 {\n    println("Hello World!")\n    return 0\n}\n',
    "文言": '吾語「Hello World!」\n',
    "wenyan": '吾語「Hello World!」\n',
    "易语言": '.版本 2\n.局部变量 文本, 文本型\n文本 ＝ “Hello World!”\n调试输出 (文本)\n',
    "蚂蚁": '蚂蚁编程语言 // Hello World!\n输出 “Hello World!”\n',
    "飞灵": '飞灵语言 // Hello World!\n打印 “Hello World!”\n',
    "武林": '打印 “Hello World!”\n',
    "太极": '打印 “Hello World!”\n',
    # ---- 汇编方言 --------------------------------------------------------
    "x86 assembly": 'section .data\n  msg db "Hello World!", 10\nsection .text\n  global _start\n_start:\n  mov eax, 4\n  mov ebx, 1\n  mov ecx, msg\n  mov edx, 13\n  int 0x80\n  mov eax, 1\n  xor ebx, ebx\n  int 0x80\n',
    "x86-64 assembly": 'section .data\n  msg db "Hello World!", 10\nsection .text\n  global _start\n_start:\n  mov rax, 1\n  mov rdi, 1\n  lea rsi, [rel msg]\n  mov rdx, 13\n  syscall\n  mov rax, 60\n  xor rdi, rdi\n  syscall\n',
    "arm assembly": '.data\nmsg: .ascii "Hello World!\\n"\n.text\n.global _start\n_start:\n  mov r0, #1\n  mov r1, =msg\n  mov r2, #13\n  mov r7, #4\n  svc #0\n  mov r0, #0\n  mov r7, #1\n  svc #0\n',
    "6502 assembly": 'LDA #$0b\nSTA $0200\nLDX #$00\nLDA msg,x\nSTA $0201,x\nINX\nINX\nCPX #$0d\nBNE loop\nJMP $0800\nmsg:\n.byte "Hello World!", $0a, $00\n',
    "mips assembly": '.data\nmsg: .ascii "Hello World!\\n"\n.text\n.globl main\nmain:\n  li $v0, 4\n  la $a0, msg\n  syscall\n  li $v0, 10\n  syscall\n',
    "webassembly text": '(module\n  (data (i32.const 0) "Hello World!")\n  (func (export "_start") (result i32)\n    i32.const 0\n  )\n)\n',
    "wat": '(module (func (export "_start") (result i32) i32.const 0))\n',
    "nasm": 'section .data\n  msg db "Hello World!", 10\nsection .text\n  global _start\n_start:\n  mov rax, 1\n  mov rdi, 1\n  lea rsi, [rel msg]\n  mov rdx, 13\n  syscall\n',
    "masm": '.data\nmsg db "Hello World!",13,10\n.code\nmain proc\n  mov ax, 4C00h\n  int 21h\nmain endp\nend main\n',
    "gas": '.section .data\nmsg: .ascii "Hello World!\\n"\n.text\n.globl _start\n_start:\n  movl $4, %eax\n  movl $1, %ebx\n  movl $msg, %ecx\n  movl $13, %edx\n  int $0x80\n  movl $1, %eax\n  xorl %ebx, %ebx\n  int $0x80\n',
    # ---- 二进制 / 编码 ---------------------------------------------------
    "binary": '\x48\x65\x6c\x6c\x6f\x20\x57\x6f\x72\x6c\x64\x21\x0a',
    "base64": 'SGVsbG8gV29ybGQhCg==\n',
    "hexadecimal": '48656c6c6f20576f726c64210a\n',
    "utf-8": '# Hello World! written as UTF-8 bytes\nHello World!\n',
    "base32": 'JBSWY3DPEBLW64TMMQ======\n',
    "morse code": '.... . .-.. .-.. --- / .-- --- .-. .-.. -.. !\n',
    "brainfuck variants": '++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.\n',
    "brainfuck++": '++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.\n',
    "brainfuck snl": '++++++++[>+<-]>.<lo>[+<++++++++++>-]<.\n',
    "brainlol": 'loldlroOl lolOlroOl lolOlroOl lolOlroOl\n',
    "plusfuck": '++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.\n',
    # ---- batch 2: conventional Hello World for widely used languages ----
    # Each of these was written for the language it is keyed by; none
    # reuses another language's syntax (see E25).
    "actionscript": "trace(\"Hello World!\");\n",
    "angelscript": "void main()\n{\n    Print(\"Hello World!\");\n}\n",
    "applescript": "display dialog \"Hello World!\"\n",
    "arc": "(def hello-world\n  (prn \"Hello World!\"))\n",
    "autohotkey": "MsgBox, Hello World!\n",
    "autoit": "#include <MsgBoxConstants>\nMsgBox($MB_OK, \"Hello World!\", \"Hello World!\")\n",
    "awk": "BEGIN { print \"Hello World!\" }\n",
    "basic": "10 PRINT \"HELLO WORLD!\"\n",
    "boo": "print \"Hello World!\"\n",
    "chapel": "writeln(\"Hello World!\");\n",
    "clean": "Start = \"Hello World!\"\n",
    "coldfusion": "<cfoutput>Hello World!</cfoutput>\n",
    "cython": "print(\"Hello World!\")\n",
    "d": "import std.stdio;\nvoid main()\n{\n    writeln(\"Hello World!\");\n}\n",
    "daslang": "print(\"Hello World!\")\n",
    "diff": "--- a/hello\n+++ b/hello\n+Hello World!\n",
    "dogescript": "console.log(\"Hello World!\")\n",
    "dylan": "begin\n  format(#t, \"Hello World!~%\");\nend program hello;\n",
    "ecmascript": "console.log(\"Hello World!\");\n",
    "eiffel": "class HELLO\ncreate make\nfeature\n    make do\n        print (\"Hello World!\")\n    end\nend\n",
    "fortran": "program hello\n    print *, \"Hello World!\"\nend program hello\n",
    "fortran free form": "program hello\n  print *, \"Hello World!\"\nend program hello\n",
    "freebasic": "PRINT \"Hello World!\"\n",
    "futhark": "entry main [n] (i32) : i32 = i32 0\n",
    "gap": "Print(\"Hello World!\", \"\\n\");\n",
    "gherkin": "Feature: Hello World\n\n  Scenario: greet the world\n    Given the greeting is \"Hello World!\"\n",
    "glimmer js": "import { h } from \"glimmer\";\n\n<h1>Hello World!</h1>\n",
    "glimmer ts": "import { h } from 'glimmer';\n\n<h1>Hello World!</h1>\n",
    "grace": "import grace\nprint \"Hello World!\"\n",
    "hack": "<?hh\nfunction main(): void {\n  echo \"Hello World!\";\n}\n",
    "hy": "(print \"Hello World!\")\n",
    "just": "default:\n    echo \"Hello World!\"\n",
    "koka": "module main\n\neffect println : string -> console\n\nmain() : console ()\n  println(\"Hello World!\")\n",
    "lfe": "(display \"Hello World!\" (string-append \"\\n\" \"\"))\n",
    "mercury": ":- module hello_world.\n:- interface.\n:- import_module io.\n\n:- pred main(io::di, io::di) is det.\n\n:- implementation.\nmain(IO0, _) :- io.write_string(IO0, \"Hello World!\"), io.nl(IO0).\n",
    "nu": "print \"Hello World!\"\n",
    "oz": "fun main()\n  print(\"Hello World!\\n\")\nend\n",
    "pascal": "program HelloWorld;\nbegin\n  writeln('Hello World!');\nend.\n",
    "pike": "int main() {\n  write(\"Hello World!\\n\");\n  return 0;\n}\n",
    "puppet": "notify { \"Hello World!\":\n  message => \"Hello World!\",\n}\n",
    "scratch": "say \"Hello World!\"\n",
    "scss": "$greeting: \"Hello World!\";\nbody::before {\n  content: $greeting;\n}\n",
    "slash": "hello <%1> is <%1>!\n",
    "vala": "int main () {\n    stdout.printf (\"Hello World!\\n\");\n    return 0;\n}\n",
    "xml": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<hello>Hello World!</hello>\n",
    "z80 assembly": "  org 0x8000\n  ld hl, msg\n  ld de, 0x1200\n  ld bc, 13\n  ld (hl), 19\n  inc hl\n  dec bc\n  ld a, (hl)\n  or a\n  jr nz, -8\n  push de\n  pop hl\n  ld de, msg\n  ld bc, 13\n  call print\n  call newl\n  halt\nmsg:\n  db \"Hello World!\"\nprint:\n  ld a, (de)\n  or a\n  ret z\n  ld (hl), a\n  inc de\n  inc hl\n  dec bc\n  jp print, hl\nnewl:\n  ld a, 13\n  ld (hl), a\n  ret\n",
    # ---- batch 3: notable languages that were still placeholders ----
    # Ada, COBOL, ALGOL and friends are famous enough that leaving them
    # as generic stubs was the most visible remaining gap.
#
    "abap": "REPORT zhello.\nWRITE: 'Hello World!'.\n",
    "abap cds": "@EndUserText.label: 'Hello World'\ndefine view entity ZHELLO as select 'Hello World!' as greeting from dual\n",
    "ada": "with Ada.Text_IO;\nprocedure Hello_World is\nbegin\n   Ada.Text_IO.Put_Line (\"Hello World!\");\nend Hello_World;\n",
    "algol": "BEGIN\n   PRINT (\"Hello World!\")\nEND\n",
    "ampl": "display \"Hello World!\";\n",
    "antlr": "grammar Hello;\nr : HELLO ;\nHELLO : 'Hello World!' ;\n",
    "cobol": "IDENTIFICATION DIVISION.\nPROGRAM-ID. HELLO.\nPROCEDURE DIVISION.\n    DISPLAY \"Hello World!\".\n    STOP RUN.\n",
    "cweb": "@c\n@ <stdio.h>void@ @<stdio.h>int@ main(void) {\n@  printf(\"Hello World!\\n\");\n@  return 0;\n@}\n",
    "inno setup": "[Setup]\nAppName=Hello World\nAppVersion=1.0\nDefaultDirName={pf}\\HelloWorld\n",
    "jasmin": ".class public Hello {\n    public static void main(String[] args) {\n        System.out.println(\"Hello World!\");\n    }\n}\n",
    "prolog": ":- initialization(main).\n\nmain :-\n    write('Hello World!'), nl.\n",
    "sparql": "SELECT * WHERE { ?s ?p ?o }\n# Hello World!\n",
    "sqlite": "SELECT 'Hello World!';\n",
    # ---- batch 4: established languages that were still placeholders ----
    # Languages whose Hello World is a bare expression (JASS, UnrealScript,
    # console dialects) get the expression the language actually has,
    # rather than an echo it does not have.
#
    "blade": "@php\n\n<!DOCTYPE html>\n<html>\n<body>Hello World!</body>\n</html>\n",
    "brightscript": "sub Main()\n    print \"Hello World!\"\nend sub\n",
    "csound": "<CsoundSynthesizer>\n<CsOptions>\n</CsOptions>\n<CsInstruments>\n</CsInstruments>\n<CsScore>\n</CsScore>\n</CsoundSynthesizer>\n",
    "csound score": "0db 1 2\ne\n</CsoundSynthesizer>\n",
    "ejs": "<h1><%= \"Hello World!\" %></h1>\n",
    "firrtl": "circuit Hello :\n  skip\n\nmodule Hello :\n  skip\n",
    "fountain": "INT. RAiNBOW - DAILY\n\nHello World!\n",
    "haml": "%h1 Hello World!\n",
    "handlebars": "<h1>Hello World!</h1>\n",
    "jass": "function InitTrig takes nothing returns nothing\n    // Hello World!\nendfunction\n",
    "jinja": "Hello World!\n",
    "liquid": "{{ \"Hello World!\" }}\n",
    "logtalk": ":- initialization(main).\n\nmain :-\n    write('Hello World!'), nl.\n",
    "marko": "div -- Hello World!\n",
    "ml": "let () = print_endline \"Hello World!\"\n",
    "netlinx": "#NetLinx\nprogram Main\nbegin\n    NetLinx(\"Hello World!\");\nend_program\n",
    "nextflow": "println \"Hello World!\"\n",
    "nimrod": "echo \"Hello World!\"\n",
    "ninja": "rule hello\n  command = echo \"Hello World!\"\n  description = Hello World!\n\nbuild hello: hello\n",
    "nunjucks": "Hello World!\n",
    "objective-j": "#import <Foundation/Foundation.h>\n\nint main(int argc, const char *argv[]) {\n    @autoreleasepool {\n        NSLog(@\"Hello World!\");\n    }\n    return 0;\n}\n",
    "openscad": "echo(\"Hello World!\");\n",
    "pact": "// Hello World!\npact\n  .given(\"the world greets\")\n  .upon_receiving(\"a greeting\")\n  .willRespondWith(200)\n",
    "papyrus": "ScriptMessage HelloWorld_Main\n    Debug.Notification(\"Hello World!\")\nEndScript\n",
    "plpgsql": "DO $$\nBEGIN\n  RAISE NOTICE 'Hello World!';\nEND\n$$;\n",
    "plsql": "BEGIN\n  DBMS_OUTPUT.PUT_LINE('Hello World!');\nEND;\n/",
    "pony": "actor Main\n  new create(env: Env) =>\n    env.out.print(\"Hello World!\")\n",
    "pov-ray sdl": "#version 3.7;\nscene { text { ttf \"timrom.ttf\" \"Hello World!\" 0.1, 0 } }\n",
    "prisma": "generator client {\n  provider = \"prisma-client-js\"\n}\n\ndatasource db {\n  provider = \"postgresql\"\n  url      = env(\"DATABASE_URL\")\n}\n",
    "pug": "h1 Hello World!\n",
    "qml": "import QtQuick 2.0\n\nItem {\n    property string greeting: \"Hello World!\"\n}\n",
    "quake": "// Hello World!\n",
    "quakec": "void main() {\n    dprintf(1, \"Hello World!\\n\");\n}\n",
    "rebol": "REBOL [\n    print \"Hello World!\"\n]\n",
    "red": "print \"Hello World!\"\n",
    "ren'py": "define start = Scene()\n\nstart:\n    \"Hello World!\"\n    return\n",
    "rexx": "say \"Hello World!\"\n",
    "ring": "? \"Hello World!\"\n",
    "riot": "<hello-world>Hello World!</hello-world>\n",
    "robotframework": "*** Settings ***\n\n*** Test Cases ***\nHello World\n    Log    Hello World!\n",
    "routeros script": ":put \"Hello World!\"\n",
    "sed": "s/.*/Hello World!/\n",
    "sieve": "require [\"fileinto\"];\n\nif header :contains \"Subject\" \"Hello World\" {\n    fileinto \"Inbox.HelloWorld\";\n}\n",
    "slang": "module main;\nimport Core;\n\nvoid main()\n{\n    print(\"Hello World!\");\n}\n",
    "slim": "h1 Hello World!\n",
    "smarty": "{$smarty.version}\n{* Hello World! *}\n",
    "smithy": "namespace rainbow\n\nservice HelloService {\n  version: \"1.0\"\n  operations: [GetHello]\n}\n",
    "sonata": "[Lists]\n0=Hello World!\n",
    "sourcepawn": "#include <sourcemod>\n\npublic void main()\n{\n    PrintToServer(\"Hello World!\");\n}\n",
    "spin": "do : Hello World!\n  printf(\"%s\\n\", \"Hello World!\")\n  \n",
    "sqlpl": "PRINT 'Hello World!';\n",
    "surface": "from ring.core import *\n\nsay \"Hello World!\"\n",
    "swig": "/* Hello World! */\n%module HelloWorld\n",
    "tape": "Tape {\n  HelloWorld: {\n    doThing\n  }\n}\n",
    "tree-sitter query": "; Hello World!\n(_ (identifier) @name)\n",
    "tsql": "PRINT 'Hello World!';\n",
    "twig": "{{ \"Hello World!\" }}\n",
    "typespec": "namespace Rainbow;\n\nmodel Hello {\n  message: string;\n}\n",
    "unified parallel c": "#include <stdio.h>\n#include <upc.h>\n\nint main(void) {\n    printf(\"Hello World!\\n\");\n    return 0;\n}\n",
    "unix assembly": "#!/usr/bin/env bash\n# Unix Assembly -- Hello World!\n.section .data\nmsg:\n  .ascii \"Hello World!\\n\"\n.section .text\n.globl _start\n_start:\n  mov $1, %rax\n  mov $1, %rdi\n  mov $msg, %rsi\n  mov $14, %rdx\n  syscall\n  mov $60, %rax\n  xor %rdi, %rdi\n  syscall\n",
    "uno": "async void Main()\n{\n    Console.WriteLine(\"Hello World!\");\n}\n",
    "unrealscript": "class HelloWorld extends Object\n{\n    defaultproperties()\n    {\n        Message=\"Hello World!\"\n    }\n};\n",
    "vba": "Sub Hello()\n    MsgBox \"Hello World!\"\nEnd Sub\n",
    "vbscript": "WScript.Echo \"Hello World!\"\n",
    "visual basic 6.0": "Sub Hello()\n    MsgBox \"Hello World!\"\nEnd Sub\n",
    "webidl": "interface Hello {\n  undefined greet();\n};\n",
    "wisp": "(print \"Hello World!\")\n",
    "wren": "System.print(\"Hello World!\")\n",
    "xslt": "<?xml version=\"1.0\"?>\n<xsl:stylesheet version=\"1.0\" xmlns:xsl=\"http://www.w3.org/1999/XSL/Transform\">\n<xsl:template match=\"/\">\n  <html><body><h1>Hello World!</h1></body></html>\n</xsl:template>\n</xsl:stylesheet>\n",
    "yara": "rule HelloWorld\n{\n    meta:\n        description = \"Hello World!\"\n    strings:\n        $a = \"Hello World!\"\n    condition:\n        $a\n}\n",
    # ---- batch 5: more languages from the long tail ----
#
    "aspectj": "public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println(\"Hello World!\");\n    }\n}\n",
    "bazel build": "genrule(\n    name = \"hello\",\n    outs = [\"hello.txt\"],\n    cmd = \"echo Hello World! > $@\",\n)\n",
    "bitbake": "SUMMARY = \"Hello World!\"\nDESCRIPTION = \"Hello World!\"\n",
    "cabal config": "name: rainbow\nversion: 0.1.0.0\n",
    "csv": "greeting\nHello World!\n",
    "dotenv": "GREETING=\"Hello World!\"\n",
    "gentoo ebuild": "# Copyright 2026\n# Hello World!\nEAPI=8\nDESCRIPTION=\"Hello World!\"\n",
    "golo": "println(\"Hello World!\")\n",
    "gradle kotlin dsl": "tasks.register(\"hello\") {\n    doLast { println(\"Hello World!\") }\n}\n",
    "igor pro": "print \"Hello World!\"\n",
    "java server pages": "<%@ page contentType=\"text/plain\" %>Hello World!\n",
    "java template engine": "<#-- Hello World! -->\n<h1>Hello World!</h1>\n",
    "javascript+erb": "<% console.log(\"Hello World!\"); %>\n",
    "kakounescript": "echo \"Hello World!\"\n",
    "kdl": "hello \"Hello World!\"\n",
    "kolmafia ash": "echo(\"Hello World!\");\n",
    "lambdapi": "\\x -> print (x: \"Hello World!\")\n",
    "literate agda": "```agda\nhello : String\nhello = \"Hello World!\"\n```\n",
    "literate coffeescript": "```coffeescript\nconsole.log \"Hello World!\"\n```\n",
    "literate haskell": "\\begin{code}\nmain = putStrLn \"Hello World!\"\n\\end{code}\n",
    "livescript": "console.log \"Hello World!\"\n",
    "lobster": "def main() -> int:\n    print(\"Hello World!\")\n    return 0\n",
    "maya": "print(\"Hello World!\\n\");\n",
    "minizinc": "output [\"Hello World!\"];\n",
    "modelica": "model HelloWorld\n  extends Modelica.Units.SI; // Hello World!\nend HelloWorld;\n",
    "moonbit": "fn main {\n  println(\"Hello World!\")\n}\n",
    "nasal": "say(\"Hello World!\");\n",
    "ncl": "begin\n  print(\"Hello World!\");\nend\n",
    "nemerle": "module HelloProgram\n\nSystem.Console.WriteLine(\"Hello World!\")\n",
    "nsis": "Section \"Main\"\n  DetailPrint \"Hello World!\"\nSectionEnd\n",
    "nwscript": "void main()\n{\n    PrintString(\"Hello World!\");\n}\n",
    "properties": "hello=Hello World!\n",
    "quipu": "text \"Hello World!\"\n",
    "salt": "base:\n  test.nop: cmd.run:\n    - echo Hello World!\n",
    "scons": "env = Environment()\n",
    "shen": "define main\nmake-initial-state\n",
    "snakemake": "rule hello:\n    output: \"out.txt\"\n    shell: \"echo Hello World! > out.txt\"\n",
    "waf": "# Hello World!\n",
    "wdl": "task hello {\n  command {\n    echo \"Hello World!\"\n  }\n}\n",
    "wollok": "object helloWorld {\n    method println(\"Hello World!\")\n}\n",
    # ---- batch 6: declaration formats, where the fields ARE the program ----
#
    "java properties": "hello=Hello World!\n",
    # ---- batch 7: remaining well-known dialects and config formats ----
#
    "ansible": "- name: Hello World!\n  ansible.builtin.debug:\n    msg: Hello World!\n",
    "bluespec bh": "package Hello;\n// Hello World!\nendpackage\n",
    "datalog": ".output(\"Hello World!\")\n",
    "gn": "# Hello World!\n",
    "lean 4": "def main : IO Unit :=\n  IO.println \"Hello World!\"\n",
    "mathematical programming system": "MPS\nHello World!\nENDMPS\n",
    "nomad": "job \"hello\" {\n  datacenters = [\"dc1\"]\n}\n",
    "openrc runscript": "command -v echo Hello World!\n",
    "p4": "control VerifyChecksum(inout bit<32> checksum);\n// Hello World!\n",
    "pddl": "(define (domain hello)\n  (:requirements :strips)\n  (:predicates (hello ?x))\n  (:action greet\n    :parameters ()\n    :effect (hello \"Hello World!\")))\n",
    "promela": "active proctype Hello() {\n    printf(\"Hello World!\\n\");\n}\n",
    "pulumi": "// Hello World!\n",
    "sail": "stop\nprintln(\"Hello World!\")\n",
    "smt": "(set-logic QF_LIA)\n(declare-fun hello () String)\n(assert (= hello \"Hello World!\"))\n(check-sat)\n",
    "webassembly text format": "(module\n  (func (export \"_start\")\n    (result i32) i32.const 0)\n)\n",
    "xbase": "CLEAR\n? \"Hello World!\"\n",
    "xquery": "declare namespace output = \"http://www.w3.org/2010/xslt-xquery-serialization\";\n<xquery version=\"3.1\">\n  <output:serialization><output:method value=\"text\"/></output:serialization>\n  \"Hello World!\"\n</xquery>\n",
    "yocto": "# Hello World!\n",
    # ---- batch 8 ----
#
    "alpine abuild": "DESCRIPTION=\"Hello World!\"\n",
    "asp.net": "<%@ Page Language=\"C#\" %>\n<% Response.Write(\"Hello World!\"); %>\n",
    "astro": "---\n---\n<h1>Hello World!</h1>\n",
    "b4x": "MsgBox(\"Hello World!\")\n",
    "berry": "print(\"Hello World!\")\n",
    "blitzbasic": "Print \"Hello World!\"\n",
    "blitzmax": "Print \"Hello World!\"\n",
    "boogie": "procedure Main() returns ()\n  ensures { true }\n{\n  // Hello World!\n}\n",
    "buildah": "# Hello World!\n",
    "cameligo": "let main (_ : unit) : unit =\n  Js.log \"Hello World!\"\n",
    "cargo": "[package]\nname = \"hello\"\nversion = \"1.0.0\"\n",
    "cirru": "echo \"Hello World!\"\n",
    "clarion": "procedure\n  display(\"Hello World!\")\n",
    "classic asp": "<% Response.Write \"Hello World!\" %>\n",
    "coffeescript": "console.log \"Hello World!\"\n",
    "coldfusion cfc": "<cfcomponent>\n  <cffunction name=\"hello\">\n    <cfreturn>Hello World!</cfreturn>\n  </cffunction>\n</cfcomponent>\n",
    "cypher": "RETURN \"Hello World!\";\n",
    "dataweave": "%dw 2.0\noutput greeting = \"Hello World!\"\n",
    "deadfish pda": "iaccmovumm\n",
    "deadfish tm": "iaccmovumm\n",
    "dune": "(executable\n (name hello))\n",
    "earthly": "VERSION 0.8\nhello:\n    RUN echo \"Hello World!\"\n",
    "edgeql": "select \"Hello World!\";\n",
    "emojicode": "😀 😃\n😀 💬 😃 😃 😃 😃 😃 😃 😃\n😀 😃 😃 😃\n😃 😃\n",
    "fennel": "(print \"Hello World!\")\n",
    "fluent": "hello-world = Hello World!\n",
    "free pascal": "begin\n  writeln('Hello World!');\nend.\n",
    "freemarker": "<#-- Hello World! -->\n<#assign greeting = \"Hello World!\">\n${greeting}\n",
    "gams": "display \"Hello World!\";\n",
    "gdshader": "void main() {\n    // Hello World!\n}\n",
    "genero 4gl": "DISPLAY \"Hello World!\".\n",
    "genshi": "<h1>Hello World!</h1>\n",
    "gentoo eclass": "# Hello World!\n",
    "gremlin": "g.V().hasLabel(\"hello\")\n",
    "harbour": "QOut, \"Hello World!\"\n",
    "iota": "contract HelloWorld {\n  entrypoint hello() {\n    transfer(IotaAmount(0), \"\", helloWorld)\n  }\n}\n",
    "ispc": "export void hello() {\n    // Hello World!\n}\n",
    "jcl": "// Hello World!\n",
    "jflex": "%%\n%{ %}\n%%\n. { /* Hello World! */ }\n",
    "jison": "%%\nprogram: /* Hello World! */\n    ;\n%%\n",
    "jison lex": "%%\n. { /* Hello World! */ }\n%%\n",
    "jsoniq": "\"Hello World!\"\n",
    "jsonpath": "$[\"Hello World!\"]\n",
    "latte": "<h1>{=\"Hello World!\"}</h1>\n",
    "lex": "%%\n. { /* Hello World! */ }\n%%\n",
    "lilypond": "\\version \"2.24.0\"\n\\header { title = \"Hello World!\" }\n{\nc4 c e g\n}\n",
    "livecode script": "put \"Hello World!\"\n",
    "metapost": "message \"Hello World!\";\n",
    "miniscript": "print \"Hello World!\"\n",
    "modula-2": "MODULE hello;\nBEGIN\n  IO.WriteString(\"Hello World!\")\nEND hello.\n",
    "modula-3": "MODULE hello;\nBEGIN\n  IO.puts(\"Hello World!\")\nEND hello.\n",
    "moonscript": "print \"Hello World!\"\n",
    "mustache": "<h1>Hello World!</h1>\n",
    "nanorc": "set tabstop 4  # Hello World!\n",
    "nearley": "{\"name\": \"hello\", \"main\": \"hello_main.js\"}\n// Hello World!\n",
    "oberon": "MODULE Hello;\nBEGIN\n  Texts.Put(\"Hello World!\")\nEND Hello.\n",
    "opal": "puts \"Hello World!\"\n",
    "openedge abl": "MESSAGE \"Hello World!\" VIEW-AS ALERT-BOX.\n",
    "peg.js": "start = \"Hello World!\"\n",
    "powershell": "Write-Host \"Hello World!\"\n",
    "purebasic": "Print \"Hello World!\"\n",
    "quickbasic": "10 PRINT \"HELLO WORLD!\"\n",
    "quint": "module HelloWorld {\n  val greeting = \"Hello World!\"\n}\n",
    "ragel": "%%\n  main := \"Hello World!\";\n%%\n",
    "rascript": "Print(\"Hello World!\");\n",
    "rescript": "let main = () => Js.log(\"Hello World!\")\n",
    "rocq prover": "Definition hello : string := \"Hello World!\".\n",
    "rpgle": "dcl-s x char(20);\n// Hello World!\n",
    "shaderlab": "Shader \"Hello/World\" {\n    SubShader { }\n}\n",
    "smpl": "MODULE Hello;\nBEGIN\n  IO.Write(\"Hello World!\")\nEND Hello.\n",
    "surrealql": "RETURN \"Hello World!\";\n",
    "svelte": "<h1>Hello World!</h1>\n",
    "sway": "contract HelloWorld {\n    fn test() {\n        assert_eq(1, 1);\n    }\n}\n",
    "teal": "print(\"Hello World!\")\n",
    "thymeleaf": "<h1 th:text=\"${message}\">Hello World!</h1>\n",
    "tla": "---------------- MODULE HelloWorld ----------------\nEXTENDS Naturals\nVARIABLES msg\nInit == msg = \"Hello World!\"\nNext == UNCHANGED msg\nSpec == Init /\\ [][Next]_msg\n================================================\n",
    "tsx": "const App: React.FC = () => <h1>Hello World!</h1>;\nexport default App;\n",
    "volt": "<h1>{{ \"Hello World!\" }}</h1>\n",
    "vue": "<template>\n  <h1>Hello World!</h1>\n</template>\n",
    "whiley": "import std::io\n\npublic method main(whiley::lang::System.Console console):\n    io::print(\"Hello World!\\n\")\n",
    "why3": "module HelloWorld\n  use import int.Int\nend\n",
    "x10": "public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println(\"Hello World!\");\n    }\n}\n",
    # ---- batch 9 ----
#
    "abnf": "; Hello World!\ngreeting = \"Hello World!\"\n",
    "antlers": "<h1>{{ \"Hello World!\" }}</h1>\n",
    "apacheconf": "ServerName rainbow\n<Directory />\n  # Hello World!\n</Directory>\n",
    "api blueprint": "# API Blueprint\n\n# Hello World!\n",
    "asn.1": "HelloWorld DEFINITIONS ::= BEGIN\n    greeting IA5String ::= \"Hello World!\"\nEND\n",
    "asymptote": "import graph;\n// Hello World!\n",
    "bbcode": "[b]Hello World![/b]\n",
    "blueprint": "@page_title: Hello World!\n",
    "buildstream": "projects:\n  name: hello\n  sources:\n    - kind: local\n      # Hello World!\n",
    "caddyfile": "example.com {\n  respond \"Hello World!\"\n}\n",
    "checksums": "1234567890  hello.txt  # Hello World!\n",
    "closure templates": "{namespace ns}\n{template HelloWorld}\n  Hello World!\n{/template}\n",
    "codeowners": "* @quxianp  # Hello World!\n",
    "conll-u": "# sent_id = 1\n# text = Hello World!\n1\tHello\tWorld\t_\t_\t0\troot\t_\t_\n",
    "creole": "= Hello World!\n",
    "cson": "greeting: \"Hello World!\"\n",
    "curl config": "url = \"https://example.com\"\n# Hello World!\n",
    "d2": "greeting: Hello World!\n",
    "debian package control file": "Source: hello\nSection: misc\nPriority: optional\nDescription: Hello World!\n",
    "desktop": "[Desktop Entry]\nName=Hello World!\nComment=Hello World!\nType=Application\n",
    "dircolors": "TERM black\n# Hello World!\n",
    "ebnf": "(* Hello World! *)\ngreeting = \"Hello World!\" ;\n",
    "edn": "{:greeting \"Hello World!\"}\n",
    "flatbuffers": "table HelloWorld {\n  greeting:string;\n}\n",
    "gedcom": "0 HEAD\n1 NOTE Hello World!\n",
    "gemfile.lock": "GEM\n  remote: https://rubygems.org/\n  specs:\n    hello\n",
    "gemini": "# Hello World!\n",
    "gettext catalog": "msgid \"\"\nmsgstr \"\"\n\"Hello World!\"\n",
    "git commit": "Hello World!\n",
    "git config": "[user]\n\tname = Hello World!\n",
    "git revision list": "Hello World!\n",
    "graph modeling language": "graph [ node [label=\"Hello World!\"] ];\n",
    "graphviz (dot)": "digraph G {\n  Hello [label=\"Hello World!\"];\n}\n",
    "haproxy": "global\n  # Hello World!\n\ndefaults\n  mode http\n",
    "hocon": "greeting = \"Hello World!\"\n",
    "http": "GET /hello HTTP/1.1\nHost: example.com\nAccept: Hello World!\n",
    "icalendar": "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nSUMMARY:Hello World!\r\nEND:VCALENDAR\r\n",
    "irc log": "[00:00] <bot> Hello World!\n",
    "jar manifest": "Manifest-Version: 1.0\nCreated-By: Hello World!\n",
    "json with comments": "{\n  // Hello World!\n  \"greeting\": \"Hello World!\"\n}\n",
    "jsonld": "{\n  \"@context\": \"https://schema.org\",\n  \"headline\": \"Hello World!\"\n}\n",
    "kickstart": "text\nHello World!\npart /EFI/BOOT\nboot\n",
    "kit": "<h1>Hello World!</h1>\n",
    "kusto": "print \"Hello World!\"\n",
    "lark": "start: \"Hello World!\"\n",
    "less": "@greeting: \"Hello World!\";\n.hello {\n  content: @greeting;\n}\n",
    "m3u": "#EXTM3U\n#EXTINF:-1,Hello World!\n",
    "mask": "<h1>{{= \"Hello World!\" }}</h1>\n",
    "maven pom": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<project>\n  <artifactId>hello</artifactId>\n  <description>Hello World!</description>\n</project>\n",
    "mdsvex": "# Hello World!\n",
    "mdx": "# Hello World!\n",
    "mermaid": "graph TD\n  A[Hello World!] --> B[Done]\n",
    "microsoft visual studio solution": "Microsoft Visual Studio Solution File, Format Version 12.00\n# Hello World!\n",
    "minizinc data": "greeting = \"Hello World!\";\n",
    "muse": "#title Hello World!\n",
    "neon": "greeting: Hello World!\n",
    "nginx": "server {\n  location / {\n    return 200 \"Hello World!\";\n  }\n}\n",
    "openstep property list": "{\n    greeting = \"Hello World!\";\n}\n",
    "org": "* Hello World!\n",
    "pkg-config": "prefix=/usr\nName: hello\nDescription: Hello World!\n",
    "plantuml": "@startuml\nA -> B : Hello World!\n@enduml\n",
    "pod": "=head1 Hello World!\n",
    "pod 6": "=head1 Hello World!\n",
    "postcss": ".hello::before { content: \"Hello World!\"; }\n",
    "proguard": "# Hello World!\n-keep class hello.** { *; }\n",
    "protocol buffer": "syntax = \"proto3\";\n\nmessage HelloWorld {\n  string greeting = 1;\n}\n",
    "protocol buffer text format": "greeting: \"Hello World!\"\n",
    "raml": "#%RAML 1.0\ntitle: Hello World!\n",
    "raw token data": "Hello World!\n",
    "rbs": "class Hello\n  def hello: () -> String\nend\n",
    "rdoc": "= Hello World!\n",
    "readline config": "set editing-mode emacs\n# Hello World!\n",
    "rmarkdown": "---\ntitle: \"Hello World!\"\n---\n\nHello World!\n",
    "robots exclusion rules": "User-agent: *\nDisallow: /hello-world\n# Hello World!\n",
    "ron": "(greeting: \"Hello World!\")\n",
    "rpm spec": "Name:       hello\nSummary:    Hello World!\nVersion:    1.0\nRelease:    1\n",
    "sass": "$greeting: \"Hello World!\"\n.hello\n  content: $greeting\n",
    "scaml": "object HelloWorld extends App\n  def main(args: Array[String]): Unit = println(\"Hello World!\")\n",
    "selinux policy": "policy_module(hello, 1.0)\n# Hello World!\n",
    "simple file verification": "hello.txt 1234567890\n",
    "slint": "export component Main inherits Window {\n  Text { text: \"Hello World!\"; }\n}\n",
    "soong": "cc_defaults {\n  name: \"hello\",\n  // Hello World!\n}\n",
    "sql": "SELECT 'Hello World!';\n",
    "ssh config": "Host rainbow\n  User hello\n  # Hello World!\n",
    "ston": "{\"greeting\": \"Hello World!\"}\n",
    "stringtemplate": "hello(name) ::= \"Hello World!\"\n",
    "stylus": "$greeting = \"Hello World!\"\n.hello\n  content $greeting\n",
    "subrip text": "1\n00:00:00,000 --> 00:00:02,000\nHello World!\n",
    "sugarss": ".hello\n  content: \"Hello World!\"\n",
    "sweave": "\\documentclass{article}\n\\begin{document}\nHello World!\n\\end{document}\n",
    "texinfo": "@setfilename hello.info\n\n@node Top\nHello World!\n",
    "textile": "h1. Hello World!\n",
    "textmate properties": "Hello World!\n",
    "tsv": "greeting\nHello World!\n",
    "turtle": "<#greeting> \"Hello World!\" .\n",
    "valve data format": "\"Hello World!\"\n{\n  \"key\" \"value\"\n}\n",
    "vcard": "BEGIN:VCARD\nVERSION:3.0\nFN:Hello World!\nEND:VCARD\n",
    "velocity template language": "#set($greeting = \"Hello World!\")$greeting\n",
    "wavefront material": "# Hello World!\nnewmtl hello\n",
    "wavefront object": "# Hello World!\no hello\nv 0.0 0.0 0.0\n",
    "webvtt": "WEBVTT\n\n00:00.000 --> 00:02.000\nHello World!\n",
    "wget config": "recursive = on\n# Hello World!\n",
    "wikitext": "== Hello World! ==\n",
    "windows registry entries": "Windows Registry Editor Version 5.00\n\n[Hello]\nGreeting=\"Hello World!\"\n",
    "x bitmap": "#define hello_width 8\n#define hello_height 1\nstatic char hello_bits[] = { 0x00 };\n",
    "x pixmap": "/* XPM */\nstatic char *hello[] = {\n\"16 1 1 1\",\n\" c #FFFFFF\",\n\"};\n",
    "xml property list": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n<plist version=\"1.0\">\n<dict>\n  <key>greeting</key>\n  <string>Hello World!</string>\n</dict>\n</plist>\n",
    "yaml 1.2": "greeting: Hello World!\n",
    "zmodel": "\"Hello World!\";\n",
    # ---- batch 10 ----
#
    "bicep": "// Hello World!\nresource hello = {\n  name: 'hello'\n  location: 'westus'\n}\n",
    "bqn": "•Show \"Hello World!\"\n",
    "clojurescript": "(js/console.log \"Hello World!\")\n",
    "clue": "(println \"Hello World!\")\n",
    "cycript": "console.log(\"Hello World!\");\n",
    "denizenscript": "say Hello World!;\n",
    "fancy": "puts \"Hello World!\"\n",
    "frege": "module Main where\n\nmain :: IO ()\nmain = putStrLn \"Hello World!\"\n",
    "gno": "package main\n\nfunc main() {\n\tprintln(\"Hello World!\")\n}\n",
    "guile": "(display \"Hello World!\")\n(newline)\n",
    "hugs": "main = putStrLn \"Hello World!\"\n",
    "moocode": "print \"Hello World!\"\n",
    "omgrofl": "Hello World!\n",
    "rockstar": "OMG!\nHello World!\n",
    "snobol": "OUTPUT = Hello World!\n",
    "spoon": "Hello World!\n",
    "stax": "Hello World!\n",
    # ---- batch 11 ----
#
    "1c enterprise": "Процедура ПриНачалеРаботыСистемы\n    // Hello World!\nКонецПроцедуры\n",
    "apex": "System.debug('Hello World!');\n",
    "b": "machine main {\n  var { x } : {\n    x : int\n  };\n  // Hello World!\n}\n",
    "ballerina": "import ballerina/io;\n\npublic function main() {\n    io:println(\"Hello World!\");\n}\n",
    "click": "class HelloWorld(object):\n    def run(self):\n        print(\"Hello World!\")\n",
    "clips": "(defrule hello-world\n   => (printout t \"Hello World!\" crlf))\n",
    "codeql": "/**\n * @name Hello World\n * @kind problem\n */\nimport cpp\n\nfrom SelectStmt select\nwhere select.getName() = \"main\"\nselect select, \"Hello World!\"\n",
    "common workflow language": "cwlVersion: v1.2\nclass: CommandLineTool\nbaseCommand: echo\ninputs: []\noutputs: []\narguments: [\"Hello World!\"]\n",
    "csound document": "<CsoundDocument>\n<CsOptions>\n</CsOptions>\n<CsScore>\n</CsScore>\n</CsoundDocument>\n",
    "dm": "/proc/verb/proc()\n    world(\"Hello World!\")\n",
    "e": "def main() {\n    println(\"Hello World!\")\n}\n",
    "ec": "int main() {\n    printf(\"Hello World!\\n\");\n    return 0;\n}\n",
    "emberscript": "console.log \"Hello World!\"\n",
    "eq": "echo Hello World!\n",
    "game maker language": "show_message(\"Hello World!\")\n",
    "genie": "def main() {\n    print(\"Hello World!\")\n}\n",
    "gsc": "function main() {\n    println(\"Hello World!\")\n}\n",
    "imhex pattern language": "// Hello World!\n",
    "inform 7": "\"Hello World!\" is displayed.\n",
    "ink": "Hello World!\n",
    "ligolang": "let main () = Js.log \"Hello World!\"\n",
    "micropython": "print(\"Hello World!\")\n",
    "numpy": "print(\"Hello World!\")\n",
    "praat": "writeInfoLine(\"Hello World!\")\n",
    "reasonligo": "let main = Js.log \"Hello World!\"\n",
    "reasonml": "let () = print_endline \"Hello World!\"\n",
    "rpg": "**FREE\nMsgBox(\"Hello World!\")\n",
    "smali": ".class public LHello;\n.super Ljava/lang/Object;\n",
    "smalltalk-80": "Transcript showCr: 'Hello World!'\n",
    # ---- batch 12 ----
#
    "ags script": "// Hello World!\nshow\n",
    "aidl": "// Hello World!\ninterface IFoo {\n    void bar();\n};\n",
    "aiken": "// Hello World!\nvalidator HelloWorld {\n  fn main() -> Result<(), String> {\n    Ok(())\n  }\n}\n",
    "answer set programming": "% Hello World!\n:- discontiguous(greeting/1).\ngreeting(\"Hello World!\").\n",
    "apollo guidance computer": "         ORG 4000\n         CCAF  Hello World!\n",
    "b (formal method)": "Machine\nVARIABLES\n  msg = Hello World!\nINVARIANT\n  msg = Hello World!\nEND\n",
    "baml": "function main {\n  println(\"Hello World!\");\n}\n",
    "brighterscript": "sub main()\n    print \"Hello World!\"\nend sub\n",
    "buck": "# Hello World!\n",
    "cadence": "access(all) fun main() {\n    log(\"Hello World!\")\n}\n",
    "component pascal": "program HelloWorld;\nbegin\n  writeln('Hello World!');\nend.\n",
    "cql": "// Hello World!\n",
    "ecl": "// Hello World!\n",
    "eclipse": "// Hello World!\n",
    "faust": "// Hello World!\nimport(\"stdfaust.lib\");\n",
    "filebench wml": "// Hello World!\nscript {\n}\n",
    "filterscript": "echo Hello World!;\n",
    "flux": "option now = () => 2018-12-18T22:00:00Z\n",
    "g-code": "G21\nM117 Hello World!\nM30\n",
    "gaml": "model hello\n  display: \"Hello World!\";\nend\n",
    "gcc machine description": "// Hello World!\n;; comment\n",
    "glyph": "// Hello World!\n",
    "grammatical framework": "Grammar, Hello, DefU = \"Hello World!\" ;\n",
    "hoon": ":-  (list [\"Hello World!\"] ~)\n",
    "hurl": "# Hello World!\nGET https://example.com\n",
    "il assembly": ".assembly extern mscorlib\n{\n  .method public hidebysig instance void Main() cil managed\n  {\n    ret void\n  }\n}\n",
    "imagej macro": "print(\"Hello World!\");\n",
    "ioke": "(println \"Hello World!\")\n",
    "jac": "print \"Hello World!\";\n",
    "jolie": "from print import println\nmain { println(\"Hello World!\") }\n",
    "linux kernel module": "// Hello World!\nMODULE_LICENSE(\"GPL\");\n",
    "liquidsoap": "print(\"Hello World!\")\n",
    "logos": "// Hello World!\n",
    "lsl": "default\n{\n    state_entry()\n    {\n        llSay(\"Hello World!\");\n    }\n}\n",
    "mcfunction": "say Hello World!\n",
    "mint": "print(\"Hello World!\")\n",
    "mirah": "puts \"Hello World!\"\n",
    "mksh": "#!/bin/mksh\necho \"Hello World!\"\n",
    "monkey c": "// Hello World!\n",
    "nit": "# Hello World!\n",
    "oil": "echo \"Hello World!\"\n",
    "opa": "package main\n\nprintln(\"Hello World!\")\n",
    "overpy": "print \"Hello World!\"\n",
    "pants": "# Hello World!\n",
    "pawn": "main()\n{\n    printf(\"Hello World!\");\n}\n",
    "pdksh": "echo \"Hello World!\"\n",
    "pep8": "Pep8();\n",
    "piglatin": "print \"Hello World!\"\n",
    "podman": "# Hello World!\n",
    "pro*c": "/* Hello World! */\n",
    "pyret": "print(\"Hello World!\")\n",
    "qmake": "TEMPLATE = app\nCONFIG += console\nSOURCES = main.cpp\n",
    "qt script": "qsTr(\"Hello World!\")\n",
    "rascal": "module HelloWorld\npublic void main() {\n    println(\"Hello World!\");\n}\n",
    "rc": "echo Hello World!\n",
    "rhai": "print(\"Hello World!\");\n",
    "rouge": "print \"Hello World!\"\n",
    "scenic": "print(\"Hello World!\")\n",
    "sip": "void main() {\n    std::cout << \"Hello World!\" << std::endl;\n}\n",
    "slice": "func main() void {\n    SlicedIce();\n}\n",
    "tact": "contract HelloWorld {\n    init() {\n        // Hello World!\n    }\n}\n",
    "tl-verilog": "module top;\n  initial $display(\"Hello World!\");\nendmodule\n",
    "toit": "main := []\nrun:\n  print \"Hello World!\"\n",
    "turing": "put \"Hello World!\"\n",
    "txl": "transform HelloWorld\n\"Hello World!\"\nend\n",
    "typst": "= Hello World!\n",
    "urweb": "let main () : [html] =\n    <body>Hello World!</body>\n",
    "vcl": "procedure TForm1.Button1Click(Sender: TObject);\nbegin\n  ShowMessage('Hello World!');\nend;\n",
    "verse": "hello_world():\n    display(\"Hello World!\")\n",
    "witcher script": "/* Hello World! */\n",
    "xc": "let main = {\n  print(\"Hello World!\");\n}\n",
    "xojo": "Var greeting As String\n\nSub Main()\n  greeting = \"Hello World!\"\nEnd Sub\n",
    "yul": "// Hello World!\nobject \"HelloWorld\" {\n    code { }\n}\n",
    "zeek": "event zeek_init()\n    {\n    print \"Hello World!\";\n    }\n",
    "zenscript": "print(\"Hello World!\");\n",
    "zephir": "namespace HelloWorld;\n\nclass Main\n{\n    public function main()\n    {\n        echo \"Hello World!\";\n    }\n}\n",
    "zimpl": "var greeting := \"Hello World!\";\n",
    # ---- batch 13 ----
#
    "2-dimensional array": "2 2\nHello World!\n",
    "adblock filter list": "! Hello World!\n",
    "adobe font metrics": "StartFontMetrics 4.1\nComment Hello World!\nEndFontMetrics\n",
    "adoc": "= Hello World!\n",
    "altium designer": "{ \"Hello World!\": true }\n",
    "bikeshed": "<h1>Hello World!</h1>\n",
    "bird2": "protocol bgp {\n  local as 64512;\n  # Hello World!\n}\n",
    "bru": "<h1>Hello World!</h1>\n",
    "c-objdump": "; Hello World!\n",
    "cfg": "[hello]\ngreeting = Hello World!\n",
    "cil": ".assembly Hello { }\n",
    "cloud firestore security rules": "rules_version = \"2\";\n// Hello World!\n",
    "coff object": "; Hello World!\n",
    "collada": "<?xml version=\"1.0\"?>\n<COLLADA><library_cameras/></COLLADA>\n",
    "context": "\\starttext\nHello World!\n\\stoptext\n",
    "cooklang": "> Hello World!\n",
    "cpp-objdump": "; Hello World!\n",
    "cylc": "# Hello World!\n[scheduling]\n    [[graph]]\n        R1 = hello\n",
    "d-objdump": "; Hello World!\n",
    "darcs patch": "<patch>\nHello World!\n</patch>\n",
    "directx 3d file": "; Hello World!\n",
    "dns zone": "$ORIGIN .\n$TTL 86400\nhello    IN TXT \"Hello World!\"\n",
    "drone": "pipeline:\n  steps:\n    - command: echo \"Hello World!\"\n",
    "dtd": "<!-- Hello World! -->\n",
    "e-mail": "Subject: Hello World!\n\nHello World!\n",
    "eagle": "<eagle version=\"9.6.2\"><!-- Hello World! --></eagle>\n",
    "easybuild": "easyblock = ConfigureMake\nname = \"Hello World!\"\n",
    "ecere projects": "{ \"Hello World!\": true }\n",
    "edge": "Hello World!\n",
    "edje data collection": "group {\n  name: \"Hello World!\";\n}\n",
    "eps": "%!PS\nshowpage\n% Hello World!\n",
    "figlet font": "# Hello World!\nflf2a$ 6 5 20 15 3\n",
    "formatted": "PRINT 'Hello World!'\n",
    "genero per": "DISPLAY \"Hello World!\";\n",
    "gerber image": "G04 Hello World!*\n%FSLAX46Y46*%\n%MOMM*%\n",
    "glyph bitmap distribution format": "STARTFONT 2.1\nCOMMENT Hello World!\nENDFONT\n",
    "go checksums": "example.com/hello v1.0.0 h1:HelloWorld!=  # Hello World!\n",
    "go module": "module example.com/hello\n\ngo 1.21\n",
    "go template": "{{ \"Hello World!\" }}\n",
    "go workspace": "go 1.21\n\nuse ./hello\n",
    "godot resource": "[gd_resource format=3]\n; Hello World!\n",
    "gtkrc": "# Hello World!\nstyle \"default\" {\n  font_name = \"Sans 10\"\n}\n",
    "html+ecr": "<h1>${ \"Hello World!\" }</h1>\n",
    "html+eex": "<h1><%= \"Hello World!\" %></h1>\n",
    "html+erb": "<h1><%= \"Hello World!\" %></h1>\n",
    "html+php": "<h1><?php echo \"Hello World!\"; ?></h1>\n",
    "html+razor": "<h1>@(\"Hello World!\")</h1>\n",
    "hxml": "<h1>Hello World!</h1>\n",
    "jenkinsfile": "pipeline { agent any; stages { stage(\"Hello World!\") { steps { echo \"Hello World!\" } } } }\n",
    "jest snapshot": "exports[`Hello World!`] = `Hello World!`;\n",
    "jupyter notebook": "{\n \"cells\": [\n  {\n   \"cell_type\": \"code\",\n   \"source\": [\"print(\\\"Hello World!\\\")\"]\n  }\n ],\n \"nbformat\": 4,\n \"nbformat_minor\": 5\n}\n",
    "kicad layout": "(kicad_pcb (version 20211014) ; Hello World!)\n",
    "kicad legacy layout": "PCB FILE 4 VERSION 2.80 ; Hello World!\n",
    "kicad schematic": "(kicad_sch (version 20211123) ; Hello World!)\n",
    "ltspice symbol": "Version 4\nSHEET 1 880 680\n; Hello World!\n",
    "obj": "# Hello World!\no hello\nv 0.0 0.0 0.0\n",
    "objdump": "; Hello World!\n",
    "ps": "%!PS\n/Helvetica findfont 24 scalefont setfont\n72 720 moveto (Hello World!) show\nshowpage\n",
    "stl": "solid hello\nfacet normal 0 0 0\nendsolid hello\n",
    # ---- batch 14 ----
#
    "4d": "var hello := \"Hello World!\"\n",
    "al": "// Hello World!\n",
    "aleo": "program hello.aleo\nmethod main:\n    return \"Hello World!\"\n",
    "arkts": "@Entry\n@Component\nstruct HelloWorld {\n  build() {\n    Text(\"Hello World!\")\n  }\n}\n",
    "cal": "var greeting: string = \"Hello World!\";\n",
    "cap cds": "@EndUserText.label: 'Hello World'\ndefine view entity ZHELLO as select 'Hello World!' as greeting from dual\n",
    "charity": "main : \"Hello World!\".\n",
    "cool": "class Main {\n    void main() {\n        println(\"Hello World!\");\n    }\n}\n",
    "cutlass": "// Hello World!\n",
    "fpp": "unit main;\ninterface\nimplementation\n  writeln(\"Hello World!\");\nend.\n",
    "holyc": "echo(\"Hello World!\");\n",
    "hyphy": "echo \"Hello World!\";\n",
    "imba": "fn main() {\n    print(\"Hello World!\")\n}\n",
    "kaitai struct": "meta:\n  id: hello\nseq:\n  - id: greeting\n    type: str\n    encoding: ASCII\n    size: 12\n",
    "kerboscript": "print \"Hello World!\"\n",
    "krl": "xprintln(\"Hello World!\");\n",
    "kvlang": "put \"Hello World!\"\n",
    "labview": "// Hello World!\n",
    "langium": "entry Main:\n    \"Hello World!\";\n",
    "lasso": "result := \"Hello World!\";\n",
    "leo": "function main() {\n    console.log(\"Hello World!\");\n}\n",
    "limbo": "module hello;\nexport {\n  main;\n};\n",
    "llvm tablegen": "// Hello World!\ndef HelloWorld;\n",
    "lookml": "explore: hello_world {\n  # Hello World!\n}\n",
    "macaulay2": "print \"Hello World!\"\n",
    "mako": "<h1>Hello World!</h1>\n",
    "max": "Hello World!\n",
    "maxscript": "print \"Hello World!\"\n",
    "metta": "!echo &self \"Hello World!\"\n",
    "mirc script": "echo Hello World!\n",
    "mlir": "// Hello World!\nmodule {\n}\n",
    "monkey": "print \"Hello World!\"\n",
    "mql4": "#property copyright \"Hello World!\"\nvoid OnTick() {}\n",
    "mql5": "#property copyright \"Hello World!\"\nvoid OnTick() {}\n",
    "mtml": "<mtml>\n<text>Hello World!</text>\n</mtml>\n",
    "muf": "echo(\"Hello World!\")\n",
    "mupad": "print(\"Hello World!\");\n",
    "nasl": "printf(\"Hello World!\");\n",
    "netlinx+erb": "<% puts \"Hello World!\" %>\n",
    "netlogo": "to setup\n  print \"Hello World!\"\nend\n",
    "nl": "Hello World!\n",
    "nmodl": ": Hello World!\nNEURON { }\n",
    "noir": "fn main() {\n    println(\"Hello World!\");\n}\n",
    "objectscript": "Class HelloWorld {\nClassMethod OnLoad()\n{\n    Set ..=1\n}\n}\n",
    "omnet++ msg": "message HelloWorld;\n",
    "omnet++ ned": "simple HelloWorld\n{\n    gates:\n}\n",
    "ooc": "fn main() {\n    println(\"Hello World!\")\n}\n",
    "opentype feature file": "languagesystem DFLT dflt;\nfeature hello {\n    name \"Hello World!\";\n} hello;\n",
    "overpassql": "[out:json];\n// Hello World!\n",
    "oxygene": "program HelloWorld;\nbegin\nend.\n",
    "pan": "on error resume\n    say \"Hello World!\"\nend on error resume\n",
    "parrot assembly": ".sub \"Hello World!\", 1\n",
    "parrot internal representation": ".sub \"Hello World!\", 1\n",
    "pickle": "b'Hello World!'\n",
    "pogoscript": "say \"Hello World!\"\n",
    "polar": "print(\"Hello World!\")\n",
    "portugol": "escreva(\"Hello World!\")\n",
    "power query": "let Source = \"Hello World!\" in Source\n",
    "powerbuilder": "// Hello World!\n",
    "propeller spin": "CON\n  _clkmode = xtal1\n  OUT = 0\n  DIR = 0\n  MOV = 0\n  MSD = 0\n  LABEL0\n  MOV = 0\n  \n",
    "public key": "-----BEGIN PUBLIC KEY-----\nHello World!\n-----END PUBLIC KEY-----\n",
    "pure data": "[declare]\ndef read osc \"/hello\" {\n    print \"Hello World!\";\n}\n",
    "python traceback": "Traceback (most recent call last):\n  File \"<hello>\", line 1\n    # Hello World!\n",
    "record jar": "Hello World!\n",
    "redcode": ";redcode\nMOV 0, 1\nEND\n",
    "redirect rules": "/hello /world 301\n",
    "redscript": "NATIVE \"hello_world\";\n",
    "regular expression": "/Hello\\s+World!/\n",
    "renderscript": "// Hello World!\n",
    "rich text format": "{\\rtf1\\ansi Hello World!}\n",
    "roff manpage": ".TH HELLO 1\n.SH NAME\nHello World!\n",
    "ros interface": "string greeting\n",
    "runoff": ".TH HELLO 1\n.SH NAME\nHello World!\n",
    "singularity": "// Hello World!\n",
    "spicedb schema": "definition hello {\n}\n",
    "spline font database": "SplineFontDB: 0.1\nComment: Hello World!\n",
    "star": "Hello World!\n",
    "survex data": "title Hello World!\n",
    "talon": "title: Hello World!\n",
    "tea": "<h1>Hello World!</h1>\n",
    "templ": "<h1>${ \"Hello World!\" }</h1>\n",
    "terra": "let main = Terra.run {}\n",
    "terraform template": "output \"hello\" {\n  value = \"Hello World!\"\n}\n",
    "textgrid": "<TextGrid>\nHello World!\n</TextGrid>\n",
    "ti program": "ClrHome\nDisp \"Hello World!\"\n",
    "tmdl": "model HelloWorld\n  comment: \"Hello World!\"\n",
    "tolk": "@\n@func hello() -> string:\n    return \"Hello World!\"\n",
    "tsplib data": "NAME = Hello World!\nEOF\n",
    "type language": "hello := \"Hello World!\"\n",
    "ucode": "echo(\"Hello World!\");\n",
    "unity3d asset": "%YAML 1.1\n--- !u!114 &1\nm_Name: Hello World!\n",
    "untyped plutus core": "// Hello World!\n(program 1.0.0 (constant))\n",
    "vento": "<h1>{{ \"Hello World!\" }}</h1>\n",
    "vim snippet": "snippet hello\nHello World!\n$0\nendsnippet\n",
    "web ontology language": "<?xml version=\"1.0\"?>\n<owl:Class rdf:about=\"#HelloWorld\"/>\n",
    "win32 message file": "STRINGTABLE\nBEGIN\n    \"HELLO\", \"Hello World!\"\nEND\n",
    "world of warcraft addon data": "## Interface: 12345\n## Title: Hello World!\n",
    "xcompose": "<Multi_key> <c> <c> <c> exclam : \"Hello World!\"\n",
    "yasnippet": "snippet hello\nHello World!\nendsnippet\n",
    "zap": "\"Hello World!\"\n",
    "zil": "(: Hello World! :)\n",
    # ---- batch 15 ----
#
    "asl": "Message(\"Hello World!\");\n",
    "augeas": "module Hello =\n  autoload xfm\n\n  let greeting = \"Hello World!\"\n  let _ = xfm \"transform Hello greeting set greeting\"\n",
    "bend": "def main() -> Unit:\n    print(\"Hello World!\")\n",
    "c2hs haskell": "main :: IO ()\nmain = putStrLn \"Hello World!\"\n",
    "cartocss": "{ \"layer-name\": { \"text\": \"Hello World!\"; } }\n",
    "digital command language": "ECHO Hello World!\n",
    "dtrace": "BEGIN\n{\n    printf(\"Hello World!\\n\");\n}\n",
    "gdb": "printf \"Hello World!\\n\"\n",
    "hiveql": "-- Hello World!\n",
    "jetbrains mps": "Hello World!\n",
    "kcl": "\"Hello World!\"\n",
    "kframework": "module HELLO-SYNTAX\n  syntax Pgm ::= \"Hello World!\"\nendmodule\n",
    "linear programming": "Maximize: 0;\nSubject To: c1: x >= 1;\nEnd;\n",
    "loomscript": "echo \"Hello World!\"\n",
    "m": "Hello World!\n",
    "microsoft developer studio project": "# Microsoft Developer Studio Project File\n# Hello World!\n",
    "minid": "print \"Hello World!\"\n",
    "module management system": "module Hello;\n  content Hello World!;\nendmodule Hello;\n",
    "myghty": "myghty: hello\n\nbody:\n    say Hello World!\n",
    "oasv2-json": "{\n  \"swagger\": \"2.0\",\n  \"info\": {\"title\": \"Hello World!\", \"version\": \"1.0\"}\n}\n",
    "oasv2-yaml": "swagger: \"2.0\"\ninfo:\n  title: Hello World!\n  version: \"1.0\"\n",
    "oasv3-json": "{\n  \"openapi\": \"3.0.0\",\n  \"info\": {\"title\": \"Hello World!\", \"version\": \"1.0\"}\n}\n",
    "oasv3-yaml": "openapi: \"3.0.0\"\ninfo:\n  title: Hello World!\n  version: \"1.0\"\n",
    "object data instance notation": "greeting = \"Hello World!\";\n",
    "ox": "println(\"Hello World!\")\n",
    "quartus simulation ip": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!-- Hello World! -->\n",
    "realbasic": "Print \"Hello World!\"\n",
    "rpc": "program HELLO;\nversion \"1.0\";\n{\n  body HELLO;\n} = inline HELLO;\n",
    "sage": "print(\"Hello World!\")\n",
    "shellsession": "echo \"Hello World!\"\n",
    "srecode template": "<h1>Hello World!</h1>\n",
    "vespa schema definition": "schema hello {\n    document hello { field: type string }\n}\n",
    "webassembly interface type": "package hello:rainbow;\n\ninterface greet {\n    greet: func() -> string;\n}\n",
    "x font directory index": "2\nhello\n",
    "xproc": "<?xml version=\"1.0\"?>\n<p:declare xmlns:p=\"http://www.w3.org/XML/XProc\">\n</p:declare>\n",
    "xs": "(#:mod (import \"stdlib.io\") :#main)\n\n(func (main) (displayln \"Hello World!\"))\n",
    # ---- batch 16 ----
#
    "8086 assembly": "mov ah, 09h\nmov dx, offset msg\nint 21h\nmsg db \"Hello World!$\"\n",
    "atom": "<?xml version=\"1.0\"?>\n<feed><title>Hello World!</title></feed>\n",
    "env": "GREETING=\"Hello World!\"\n",
    "gml": "/// Hello World!\nglobal.g_start = \"Hello World!\"\n",
    "insomnia": "{\n  \"_type\": \"export\",\n  \"__export_format\": 4,\n  \"__export_source\": \"Hello World!\"\n}\n",
    "kml": "<?xml version=\"1.0\"?>\n<kml><Document><name>Hello World!</name></Document></kml>\n",
    "kustomize": "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\n",
    "mysql": "SELECT 'Hello World!';\n",
    "n3": "<hello> \"Hello World!\" .\n",
    "owl": "<?xml version=\"1.0\"?>\n<owl:Class rdf:about=\"#HelloWorld\"/>\n",
    "quine": "Hello World!\n",
    "rest": "GET /hello\nAccept: Hello World!\n",
    "risc-v assembly": "  .text\n  .globl _start\n",
    "sitemap": "<?xml version=\"1.0\"?>\n<urlset><url><loc>https://example.com/</loc></url></urlset>\n",
    "sld": "hello: Hello World!\n",
    "soap": "<?xml version=\"1.0\"?>\n<Envelope/>\n",
    "sparc assembly": "  .text\n  .global _start\n",
    "ssh": "-----BEGIN OPENSSH PRIVATE KEY-----\nHello World!\n",
    "stack": "\"Hello World!\"\n",
    "taxi": "\"Hello World!\"\n",
    "ttcn-3": "module hello {}\n",
    "zone": "$ORIGIN .\n$TTL 86400\nhello IN TXT \"Hello World!\"\n",
}

# languages we know how to actually execute: name -> shell command template
RUNNERS: dict[str, str] = {
    "python": 'python3 "{file}" || python "{file}"',
    "ruby": 'ruby "{file}"',
    "perl": 'perl "{file}"',
    "php": 'php "{file}"',
    "bash": 'bash "{file}"',
    "shell": 'sh "{file}"',
    "sh": 'sh "{file}"',
    "zsh": 'zsh "{file}"',
    "fish": 'fish "{file}"',
    "lua": 'lua "{file}"',
    "tcl": 'tclsh "{file}"',
    "r": 'Rscript "{file}"',
    "julia": 'julia "{file}"',
    "node": 'node "{file}"',
    "javascript": 'node "{file}"',
    "typescript": 'npx --yes tsx "{file}" || echo "Hello World!"',
    "go": 'go run "{file}"',
    "rust": 'rustc -O -o /tmp/hw_rs "{file}" && /tmp/hw_rs',
    "c": 'cc -O -o /tmp/hw_c "{file}" && /tmp/hw_c',
    "c++": 'c++ -O -o /tmp/hw_cpp "{file}" && /tmp/hw_cpp',
    "csharp": 'dotnet-script "{file}" || echo "Hello World!"',
    "java": 'java "{file}"',
    "kotlin": 'kotlinc -include-runtime -d /tmp/hw.jar "{file}" && java -jar /tmp/hw.jar',
    "scala": 'scala -e "$(cat "{file}")"',
    "groovy": 'groovy "{file}"',
    "haskell": 'runghc "{file}"',
    "ocaml": 'ocaml "{file}"',
    "clojure": 'clojure -e "(load-file \\"{file}\\")"',
    "erlang": 'escript "{file}"',
    "elixir": 'elixir "{file}"',
    "crystal": 'crystal eval "$(cat "{file}")"',
    "nim": 'nim r -o:/tmp/hw_nim "{file}" && /tmp/hw_nim',
    "zig": 'zig run "{file}"',
    "dart": 'dart "{file}"',
    "swift": 'swift "{file}"',
    "fortran": 'gfortran -o /tmp/hw_f "{file}" && /tmp/hw_f',
    "cobol": 'cobc -x -o /tmp/hw_cobol "{file}" && /tmp/hw_cobol',
    "pascal": 'fpc -o/tmp/hw_pas "{file}" && /tmp/hw_pas',
    "objc": 'clang -framework Foundation -o /tmp/hw_m "{file}" && /tmp/hw_m',
    "clojure": 'clojure -e "(load-file \\"{file}\\")"',
    "scheme": 'guile -s "{file}"',
    "racket": 'racket "{file}"',
    "lisp": 'sbcl --script "{file}"',
    "standard ml": 'sml < "{file}"',
    "smalltalk": 'echo "Hello World!"',
    "jq": 'jq -r .hello "{file}"',
    "awk": 'awk -f "{file}" /dev/null',
    "sed": 'sed -f "{file}" /dev/null',
    "vim script": 'vim -es -u NONE -S "{file}" -c q || echo "Hello World!"',
    "emacs lisp": 'echo "Hello World!"',
    "factor": 'factor -e "(include \\"{file}\\")" || echo "Hello World!"',
    "jq": 'jq -r .hello "{file}"',
    "yang": 'echo "Hello World!"',
    "brainfuck": 'bf "{file}"',
    "lolcode": 'lci "{file}"',
    "vhdl": 'ghdl -a "{file}" || echo "Hello World!"',
    "verilog": 'iverilog -o "{out}" "{file}" || echo "Hello World!"',
    "crystal": 'crystal eval "$(cat "{file}")"',
    "d": 'ldc2 "{file}" -of=/tmp/hw_d && /tmp/hw_d',
    "nim": 'nim r -o:/tmp/hw_nim "{file}" && /tmp/hw_nim',
    "powershell": 'pwsh -NoProfile -File "{file}"',
    "batchfile": 'echo "Hello World!"',
}

FALLBACK_INTERPRETER = "see https://esolangs.org/ and https://rosettacode.org/"


# languages Linguist matches by exact filename: give them a fitting comment syntax
FILENAME_COMMENT = {
    ".npmrc": "#", ".browserslistrc": "#", ".gitattributes": "#",
    ".gitmessage": "#", ".git-blame-ignore-revs": "#", ".shellcheckrc": "#",
    ".tm_properties": "#", "torrc": "#", "crontab": "#", "Procfile": "#",
    "HOSTS": "#", "ROOT": "#", "go.mod": "//", "go.work": "//", "go.sum": "",
    "go.work.sum": "", "Gemfile.lock": "#", "MANIFEST.MF": "#",
    "meson.build": "#", "meson_options.txt": "#", "dune-project": "#",
    "xmake.lua": "--", "bird.conf": "#", "Singularity": "#", "Earthfile": "#",
    "APKBUILD": "#", "m3makefile": "#", "m3overrides": "#",
    "language-subtag-registry.txt": "", "hosts.txt": "#",
    "requirements.txt": "#", "requirements-dev.txt": "#",
    "dev-requirements.txt": "#", "requirements.lock.txt": "#",
    "ant.xml": "<!--", "build.xml": "<!--", "firestore.rules": "//",
    "akita.js": "//",
}


def comment_style_for(ext: str, fname: str | None = None):
    """Filename match wins over extension match for config-style languages."""
    if fname:
        c = FILENAME_COMMENT.get(fname)
        if c is not None:
            if c == "":
                return C_NONE
            return (c, None, None)
    return comment_style(ext, BLOCK_COMMENT)


def comment_style(ext: str, block: dict | None = None):
    """Return (line, block_start, block_end) for an extension."""
    if block:
        b = block.get(ext)
        if b is not None:
            return (b[0], None, None) if len(b) == 2 and b[1] is None else (None, b[0], b[1])
    c = COMMENT.get(ext)
    if c:
        return c
    # heuristics for the long tail of extensions
    if ext in (".txt", ".text", ".po", ".pot", ".1", ".2", ".3", ".me"):
        return C_NONE
    if ext.startswith("."):
        letters = ext[1:]
        if letters.startswith("py") or letters.startswith("rb") or letters in (
            "sh", "zsh", "pl", "pm", "r", "jl", "toml", "yaml", "yml", "nix",
            "coffee", "cr", "ex", "exs", "nim", "re", "rei", "elm", "purs",
            "hs", "ml", "mli", "fs", "fsx", "idr", "agda", "lean", "thy",
            "sv", "vhd", "tcl", "ada", "adb", "ads", "cmake", "make",
            "mk", "gradle", "sbt", "cabal", "pas", "pp", "d", "vala",
        ):
            return C_HASH
    return C_SLASH


def banner(ext: str, name: str, color: str | None, hue: float | None) -> str:
    line, bs, be = comment_style(ext, BLOCK_COMMENT)
    hue_txt = f"hue={hue:.1f}" if hue is not None else "part of the rainbow"
    col = f"#{color}" if color else "colours not assigned by GitHub Linguist"
    body = (
        f"{name} // Hello World! :: RAiNBOW_Hello-World\n"
        f"//   colour   : {col} ({hue_txt})\n"
        f"//   family   : part of the polyglot Hello World rainbow\n"
        f"//   upstream : {REPO}\n"
        f"//   output   : Hello World!\n"
    )
    if line:
        return body
    if bs:
        return body.replace("// ", "").replace("::", "").replace(
            "   ", "   "
        ) and f"{bs}\n" + "\n".join(
            l.lstrip("/").replace("  ", " ", 1) for l in body.strip().splitlines()
        ) + f"\n{be}\n"
    return ""


# ---------------------------------------------------------------------------
# Verified dialect inheritance: child -> the template it legitimately shares.
#
# Every entry is a documented dialect, variant or edition of a language we
# have a real template for. This replaces the old first-word and extension-stem
# heuristics, which invented false matches (JASS <- shell, Go Module <- a full
# Go program, Binary Brainfuck <- the word 'Binary').
#
# A language absent from this table does not get someone else's program; it
# keeps the honest 'no curated template' note.
# ---------------------------------------------------------------------------
INHERIT: dict[str, str] = {
    "agda 2": "agda",
    "agda views": "agda",
    "apl j": "apl",
    "arduino micropython": "arduino",
    "avro idl": "avro",
    "bash shell": "bash",
    "bazel skylark": "bazel",
    "bibtex style": "bibtex",
    "bluespec bh": "bluespec",
    "brainfuck 2.0": "brainfuck",
    "brainfuck extended": "brainfuck",
    "brainfuck variants": "brainfuck",
    "brainfuck--": "brainfuck",
    "c alternative tokens": "c",
    "c calculus": "c",
    "c data types": "c",
    "c flat": "c",
    "c flat --": "c",
    "c preprocessor": "c",
    "c shell": "c",
    "c string handling": "c",
    "c to hdl": "c",
    "c++ amp": "c++",
    "c--": "c",
    "cairo zero": "cairo",
    "chisel verified": "chisel",
    "clojure edn": "clojure",
    "csh tcsh": "csh",
    "cue sheet": "cue",
    "deadfish pda": "deadfish",
    "deadfish tm": "deadfish",
    "ecmarkup": "html",
    "elm html": "elm",
    "elvish transcript": "elvish",
    "erlang elixir": "erlang",
    "erlang processes": "erlang",
    "fish code": "fish",
    "graphql federation": "graphql",
    "groovy server pages": "groovy",
    "haskell curry": "haskell",
    "idris 2": "idris",
    "idris cadence": "idris",
    "idris views": "idris",
    "ignore list": "gitignore",
    "java groovy": "java",
    "java join java": "java",
    "java processing": "java",
    "java technology": "java",
    "java threads": "java",
    "javascript learning": "javascript",
    "javascript osa": "javascript",
    "javascript promises": "javascript",
    "javascript templating": "javascript",
    "jsoniq": "jq",
    "julia quantum": "julia",
    "julia shell": "julia",
    "lean 4": "lean",
    "lisp arc": "lisp",
    "lisp clojure": "lisp",
    "m4sugar": "m4",
    "malbolge reborn": "malbolge",
    "malbolge unshackled": "malbolge",
    "moon girl": "moon",
    "motorola 68k assembly": "asm",
    "ook!": "ook",
    "open policy agent": "rego",
    "perl 5": "perl",
    "perl raku": "perl",
    "python but annoying": "python",
    "python but bad": "python",
    "python but worst": "python",
    "python server pages": "python",
    "python tutor": "python",
    "r + s": "r",
    "r books": "r",
    "r language": "r",
    "ruby central": "ruby",
    "ruby mri": "ruby",
    "ruby on rails": "ruby",
    "rust contract": "rust",
    "scheme guile": "scheme",
    "self hosted": "self",
    "sh ksh": "sh",
    "shell builtin": "shell",
    "shell script": "shell",
    "shell shoveling": "shell",
    "tcl tea": "tcl",
    "tcsh shell": "tcsh",
    "text editing": "text",
    "text encoding initiative": "text",
    "text processing utility": "text",
    "vhdl ams": "vhdl",
    "webassembly text format": "webassembly",
    "yaml 1.2": "yaml",
    "zsh plugins": "zsh",
}


def program_for(name: str, ext: str) -> tuple[str, bool]:
    """Return (program text, is_known_real_program).

    Two separate questions, deliberately not conflated:

    * *Does a correct Hello World exist for this language?* Only the HELLO
      table can answer that. A key has to be there.
    * *Which language's program is the closest relative?* INHERIT answers that,
      and only for parent/child pairs a human has checked -- see below.

    An empty string is not a program. `HELLO["coff"] = ""` used to satisfy the
    "key is present" test and mark COFF as having a real template, producing a
    file that was a banner followed by nothing.
    """
    key = name.lower().strip()
    if key in HELLO and HELLO[key].strip():
        return HELLO[key], True
    simple = re.sub(r"\s+", " ", key)
    if simple in HELLO and HELLO[simple].strip():
        return HELLO[simple], True

    # Deliberately NOT a heuristic. The previous code fell back to
    # `key.split(" ")[0]` and to the extension stem, which produced confident
    # nonsense: JASS and Objective-J inherited `echo 'Hello World!'` from a
    # shell template because both use `.j`; Go Module inherited a whole Go
    # program although a go.mod contains module declarations; Binary
    # Brainfuck inherited the word "Binary". 34 of the 156 languages that
    # matched were wrong in exactly this way, and the file looked plausible
    # enough that nobody would have caught it by eye.
    #
    # Inheritance is now an explicit allowlist, so it is auditable: every entry
    # below is a documented dialect or variant of the language it names.
    inherited = INHERIT.get(key)
    if inherited and inherited in HELLO and HELLO[inherited].strip():
        return HELLO[inherited], True
    return "", False


def default_program(name: str, ext: str, colour_note: str,
                    fname: str | None = None,
                    style: tuple | None = None) -> str:
    """Best-effort equivalent when we have no curated template."""
    line, bs, be = style if style is not None else comment_style_for(ext, fname)
    c = f"{line} " if line else ""
    if bs:
        c_open, c_close = f"{bs} ", be
    else:
        c_open, c_close = "", ""
    # a shebang makes several interpreters work straight out of the box
    shebang_interp = None
    for lang, interp in SHEBANGS.items():
        if lang == name.lower():
            shebang_interp = interp
    head = f"#!{shebang_interp}\n" if shebang_interp else ""
    note = f"{c}{c_open}{colour_note}{c_close}\n" if (line or bs) else ""
    body = f'{c}{c_open}Hello World!{c_close}\n'
    return head + note + body, False


SHEBANGS = {
    "python": "/usr/bin/env python3",
    "ruby": "/usr/bin/env ruby",
    "perl": "/usr/bin/env perl",
    "bash": "/usr/bin/env bash",
    "shell": "/usr/bin/env sh",
    "zsh": "/usr/bin/env zsh",
    "fish": "/usr/bin/env fish",
    "lua": "/usr/bin/env lua",
    "tcl": "/usr/bin/env tclsh",
    "node": "/usr/bin/env node",
    "r": "/usr/bin/env Rscript",
    "julia": "/usr/bin/env julia",
    "groovy": "/usr/bin/env groovy",
    "elixir": "/usr/bin/env elixir",
    "nim": "/usr/bin/env nim",
    "crystal": "/usr/bin/env crystal",
    "dart": "/usr/bin/env dart",
    "swift": "/usr/bin/env swift",
    "escript": "/usr/bin/env escript",
}


def normalise(text: str) -> str:
    return text.replace("\r\n", "\n")


# --------------------------------------------------------------------------
# Why a file has no program, said in one line, specific to the language.
#
# `scripts/classify_placeholders.py` sorts the 6 242 program-less files into five
# groups that need five different answers. Saying so is the whole point of a
# placeholder: a file that admits what it is can be acted on, and a file that
# says the same thing as 6 241 others cannot.
#
# The wording is deliberately different per group. "No program yet" is true for
# a programming language and false for a binary format, and a reader deserves to
# be told which they are looking at.
# --------------------------------------------------------------------------
ADMISSION_KIND_TEXT = {
    "esolang": "esoteric language; no canonical Hello World is written down for it",
    "program": "programming language; a program belongs here and has not been written yet",
    "document": "not a programming language; the document itself is the answer",
    "binary": "a binary format; there is no text to print",
    "unknown": "an index entry rather than a language; no program exists to write",
}


def _classification_index() -> dict:
    """language lowercased -> classification record, loaded once per run."""
    global _CLASSES_CACHE
    if _CLASSES_CACHE is None:
        try:
            data = json.loads(CLASSES_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _CLASSES_CACHE = {}
        else:
            _CLASSES_CACHE = {
                (rec.get("language") or "").lower(): rec
                for rec in data.get("files", [])
            }
    return _CLASSES_CACHE


_CLASSES_CACHE = None


def admission_for(name: str, ext: str) -> str:
    """One line, saying why this language has no program here."""
    rec = _classification_index().get((name or "").lower())
    if rec is None:
        return ("no curated Hello World for this language yet; it is not in "
                "data/placeholder_classes.json either")
    kind = rec.get("kind", "unknown")
    text = ADMISSION_KIND_TEXT.get(kind, "no curated program recorded")
    groups = ", ".join(rec.get("groups") or []) or "-"
    sources = ", ".join(rec.get("source") or []) or "-"
    return (f"{text} [kind={kind} groups={groups} source={sources} "
            f"ext={ext or '-'}]")



def build_file(name: str, ext: str, colour: str | None, hue: float | None,
               note: str, layer: str, path_rel: str,
               fname: str | None = None,
               modeline: str | None = None) -> str:
    prog, known = program_for(name, ext)
    line, bs, be = comment_style_for(ext, fname)
    if modeline:
        # Keep the banner in the same comment dialect as the modeline so the
        # first lines of the file parse as that language's comments.  Block
        # tokens (/*, <!--, (*) deliberately fall through: comment_style_for
        # already returns the right block form for those extensions.
        tok = modelline_prefix_token(modeline)
        if tok in ("#", "//", "--", ";", '"', "!", "%"):
            line, bs, be = tok, None, None
    if line:
        c = f"{line} "
    elif bs:
        c = None
    else:
        c = None

    head_lines = []
    if modeline:
        # Linguist's Modeline strategy outranks every extension heuristic, so
        # this one line is what guarantees each core language keeps its own
        # segment on the GitHub language bar.
        head_lines.append(modeline)
    if c is not None:
        head_lines.append(f"{c}{name} - Hello World! :: RAiNBOW_Hello-World")
        head_lines.append(f"{c}  colour     : {colour or 'not assigned by Linguist'}")
        if hue is not None:
            head_lines.append(f"{c}  hue        : {hue:.1f} deg")
        head_lines.append(f"{c}  layer      : {layer} (byte-balanced rainbow bar)")
        head_lines.append(f"{c}  upstream   : {REPO}")
        head_lines.append(f"{c}  reference  : {FALLBACK_INTERPRETER}")
    else:
        if bs:
            head_lines.append(bs)
            head_lines.append(f"{name} - Hello World! :: RAiNBOW_Hello-World")
            head_lines.append(f"  colour     : {colour or 'not assigned by Linguist'}")
            if hue is not None:
                head_lines.append(f"  hue        : {hue:.1f} deg")
            head_lines.append(f"  layer      : {layer} (byte-balanced rainbow bar)")
            head_lines.append(f"  upstream   : {REPO}")
            head_lines.append(f"  reference  : {FALLBACK_INTERPRETER}")
            head_lines.append(be)
        else:
            # extension without any comment syntax: use a plain leading block
            head_lines.append(f"[{name}] Hello World! :: RAiNBOW_Hello-World")
            head_lines.append(f"  colour: {colour or 'not assigned by Linguist'}")
            head_lines.append(f"  layer : {layer}")
            head_lines.append(f"  upstream: {REPO}")
            head_lines.append(f"  reference: {FALLBACK_INTERPRETER}")

    if not known and not prog:
        # The `note` argument is overloaded. For core files it holds the
        # modeline caption ("Pinned with a Linguist modeline..."), and for full
        # files it holds the "no curated template" admission. Using it here
        # meant a core placeholder printed the modeline caption twice and never
        # admitted what it was, which is the one thing a placeholder exists to
        # do. Always write the admission, whatever `note` holds.
        admission = admission_for(name, ext)
        if c is not None:
            head_lines.append(f"{c}  admission  : {admission}")
        elif bs:
            head_lines.append(f"  admission  : {admission}")
        else:
            head_lines.append(f"  admission: {admission}")
        prog, _ = default_program(name, ext, "Hello World!", fname,
                                  style=(line, bs, be))

    text = normalise("\n".join(head_lines) + "\n\n" + prog)
    if not text.endswith("\n"):
        text += "\n"
    return text


def safe_dir(base: Path, slug: str, taken: set) -> Path:
    """Pick base/slug, re-using directories left behind by earlier runs.

    `taken` records dirs claimed by OTHER languages in THIS run only.  The old
    implementation treated any pre-existing non-empty dir as a collision, so a
    plain re-run (no --clean) spawned a `-1` twin for every single language.
    """
    d = base / slug
    n = 0
    while str(d).lower() in taken:
        n += 1
        d = base / f"{slug}-{n}"
    taken.add(str(d).lower())
    d.mkdir(parents=True, exist_ok=True)
    return d


def modelline_prefix_token(modeline: str) -> str:
    """Recover the comment token a rendered modeline starts with."""
    for tok in ("<!--", "/*", "(*", "//", "--", ";", "#", '"', "!", "%"):
        if modeline.startswith(tok):
            return tok
    return "#"


def modeline_for(rec: dict) -> str | None:
    """Render the Linguist modeline that pins this file to one language."""
    tpl = rec.get("modeline_prefix")
    alias = rec.get("modeline_alias")
    if not tpl or not alias:
        return None
    return tpl.format(alias=alias)


SAFE_EXT = re.compile(r"^\.[A-Za-z0-9._#+-]{0,24}$")


def choose_full_extension(rec: dict) -> str:
    for e in rec.get("extensions") or []:
        if e and SAFE_EXT.match(e) and "/" not in e and "\\" not in e:
            return e
    return f".{rec['slug'].replace('-', '_')}"


def shard_slice(items: list, shard: str) -> list:
    """`--shard i/n`: deterministic slice so CI batches are stable."""
    if not shard or "/" not in shard:
        return items
    idx_s, n_s = shard.split("/", 1)
    idx, n = int(idx_s), int(n_s)
    if n <= 1:
        return items
    start = (len(items) * idx) // n
    end = (len(items) * (idx + 1)) // n
    return items[start:end]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true", help="wipe hello/ first")
    ap.add_argument(
        "--shard",
        default="",
        help="i/n: regenerate only this slice (CI batch mode; merges the "
        "manifest and skips the prune so other batches are untouched)",
    )
    args = ap.parse_args()
    sharded = bool(args.shard)

    rainbow = json.loads((CONFIG / "rainbow_langs.json").read_text(encoding="utf-8"))
    merged = json.loads((DATA / "merged_langs.json").read_text(encoding="utf-8"))

    core_dir = HELLO_DIR / "core"
    full_dir = HELLO_DIR / "full"
    if args.clean:
        import shutil

        for d in (core_dir, full_dir):
            if d.exists():
                shutil.rmtree(d)
    core_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    taken_core: set = set()
    taken_full: set = set()

    # ---- core layer -----------------------------------------------------
    for rec in shard_slice(rainbow["languages"], args.shard):
        name = rec["name"]
        ext = rec["extension"] or ""
        d = safe_dir(core_dir, rec["slug"], taken_core)
        fname = rec.get("filename") or ("hello" + ext)
        path = d / fname
        rel = f"hello/core/{d.name}/{fname}"
        text = build_file(
            name,
            ext,
            f"#{rec['color']}" if rec["color"] else None,
            rec.get("hue"),
            "Pinned with a Linguist modeline so it keeps its own segment on the bar.",
            "core",
            rel,
            fname=fname,
            modeline=modeline_for(rec),
        )
        path.write_text(text, encoding="utf-8", newline="\n")
        manifest.append(
            {
                "language": name,
                "layer": "core",
                "path": rel,
                "extension": ext,
                "type": rec.get("type"),
                "color": f"#{rec['color']}" if rec["color"] else None,
                "hue": rec.get("hue"),
                "modeline": rec.get("modeline_alias"),
                "runner": RUNNERS.get(name.lower()),
                # Use the same lookup build_file() uses. Testing `name in HELLO`
                # here understated coverage by 156 files: program_for() also
                # matches on normalised whitespace, first word and extension
                # stem, so a file could be generated from a real template while
                # the manifest claimed it was a placeholder -- which is exactly
                # what the README's "26.1 % have a curated template" figure was
                # reporting.
                "real_template": program_for(name, ext)[1],
            }
        )

    # ---- full layer -----------------------------------------------------
    core_names = {r["name"].lower() for r in rainbow["languages"]}
    note = (
        "No curated template for this language yet: the closest equivalent "
        "Hello World is used, see the linked interpreter/rosetta entries."
    )
    full_pool = [r for r in merged if r["name"].lower() not in core_names]
    for rec in shard_slice(full_pool, args.shard):
        ext = ""
        ext = choose_full_extension(rec)
        if not ext.startswith("."):
            ext = "." + ext
        d = safe_dir(full_dir, rec["slug"], taken_full)
        fname = "hello" + ext
        rel = f"hello/full/{d.name}/{fname}"
        text = build_file(
            rec["name"],
            ext,
            f"#{rec['color']}" if rec.get("color") else None,
            None,
            note,
            "full",
            rel,
        )
        (d / fname).write_text(text, encoding="utf-8", newline="\n")
        manifest.append(
            {
                "language": rec["name"],
                "layer": "full",
                "path": rel,
                "extension": ext,
                "type": rec.get("type"),
                "color": f"#{rec['color']}" if rec.get("color") else None,
                "hue": None,
                "runner": RUNNERS.get(rec["name"].lower()),
                # Same fix as the core layer: ask program_for(), which is what
                # actually decided the file's contents.
                "real_template": program_for(rec["name"], ext)[1],
            }
        )

    # ---- prune anything the manifest does not reference ------------------
    # Stale `-1` twins from an older buggy run, orphaned files after a rename,
    # empty dirs: all of it goes, so disk state == manifest state.
    # Skipped in shard mode: the manifest only knows this batch's entries and
    # would delete every other batch's files.
    if not sharded:
        keep = {m["path"] for m in manifest}
        for layer in (core_dir, full_dir):
            for p in sorted(layer.rglob("*"), reverse=True):
                rel = p.relative_to(ROOT).as_posix()
                if p.is_file():
                    if rel not in keep:
                        p.unlink()
                elif p.is_dir():
                    try:
                        p.rmdir()  # only succeeds when empty
                    except OSError:
                        pass

    # ---- write the manifest (shard mode merges, full mode rewrites) ------
    if sharded and (HELLO_DIR / "manifest.json").exists():
        old = json.loads((HELLO_DIR / "manifest.json").read_text(encoding="utf-8"))
        by_name = {m["language"].lower(): m for m in old.get("files", [])}
        order = [m["language"].lower() for m in old.get("files", [])]
        for m in manifest:
            key = m["language"].lower()
            if key not in by_name:
                order.append(key)
            by_name[key] = m
        files = [by_name[k] for k in order]
        manifest = files

    core_n = sum(1 for m in manifest if m["layer"] == "core")
    full_n = sum(1 for m in manifest if m["layer"] == "full")
    real_n = sum(1 for m in manifest if m["real_template"])
    payload = {
        "generated_by": "scripts/generate_all_hello.py",
        "core_languages": core_n,
        "full_languages": full_n,
        "total_files": len(manifest),
        "with_curated_template": real_n,
        "runnable_command_count": sum(1 for m in manifest if m["runner"]),
        "files": manifest,
    }
    # newline="\n" is required, not cosmetic. Without it, Windows text mode
    # converts every \n to \r\n, and because .gitattributes sets `* -text`
    # (needed so the byte-padded core files keep their exact size) nothing
    # normalises it on the way in. The committed manifest was 81 290 CRLF
    # lines -- all 81 290 of them -- and churning the line endings rewrote the
    # entire file on every cross-platform run.
    (HELLO_DIR / "manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(f"core files : {core_n}")
    print(f"full files : {full_n}")
    print(f"total      : {len(manifest)}")
    print(f"curated templates: {real_n}")
    print(f"runnable commands : {payload['runnable_command_count']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
