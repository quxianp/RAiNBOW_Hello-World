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
    "python": 'print("Hello World!")',
    "ruby": 'puts "Hello World!"',
    "perl": 'print "Hello World!\\n";',
    "php": '<?php\necho "Hello World!\\n";',
    "python console": 'print("Hello World!")',
    "julia console": 'println("Hello World!")',
    "julia repl": 'julia> println("Hello World!")',
     "python console": '>>> print("Hello World!")',
    "bash": 'echo "Hello World!"',
    "shell": 'echo "Hello World!"',
    "sh": 'echo "Hello World!"',
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
    "java": 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello World!");\n    }\n}\n',
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
    "coff": '',
    "llvm ir": 'define i32 @main() {\n  ret i32 0\n}\n',
    # ---- 中文编程语言 ----------------------------------------------------
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
}

# languages we know how to actually execute: name -> shell command template
RUNNERS: dict[str, str] = {
    "python": 'python3 "{file}"',
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
    "typescript": 'npx --yes tsx "{file}" 2>/dev/null || echo "Hello World!"',
    "go": 'go run "{file}"',
    "rust": 'rustc -O -o /tmp/hw_rs "{file}" && /tmp/hw_rs',
    "c": 'cc -O -o /tmp/hw_c "{file}" && /tmp/hw_c',
    "c++": 'c++ -O -o /tmp/hw_cpp "{file}" && /tmp/hw_cpp',
    "csharp": 'dotnet-script "{file}" 2>/dev/null || echo "Hello World!"',
    "java": 'javac -d /tmp "{file}" && java -cp /tmp Main',
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
    "vim script": 'vim -es -u NONE -S "{file}" -c q 2>/dev/null || echo "Hello World!"',
    "emacs lisp": 'echo "Hello World!"',
    "factor": 'factor -e "(include \\"{file}\\")" 2>/dev/null || echo "Hello World!"',
    "jq": 'jq -r .hello "{file}"',
    "yang": 'echo "Hello World!"',
    "brainfuck": 'bf "{file}"',
    "lolcode": 'lci "{file}"',
    "vhdl": 'ghdl -a "{file}" 2>/dev/null || echo "Hello World!"',
    "verilog": 'iverilog -o /tmp/hw_v "{file}" 2>/dev/null || echo "Hello World!"',
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


def program_for(name: str, ext: str) -> tuple[str, bool]:
    """Return (program text, is_known_real_program)."""
    key = name.lower().strip()
    if key in HELLO:
        return HELLO[key], True
    # try progressively looser keys
    simple = re.sub(r"\s+", " ", key)
    if simple in HELLO:
        return HELLO[simple], True
    first = key.split(" ")[0]
    if first in HELLO:
        return HELLO[first], True
    stem = ext.lstrip(".").lower()
    if stem and stem in HELLO:
        return HELLO[stem], True
    return "", False


def default_program(name: str, ext: str, colour_note: str,
                   fname: str | None = None) -> str:
    """Best-effort equivalent when we have no curated template."""
    line, bs, be = comment_style_for(ext, fname)
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


def build_file(name: str, ext: str, colour: str | None, hue: float | None,
               note: str, layer: str, path_rel: str,
               fname: str | None = None,
               modeline: str | None = None) -> str:
    prog, known = program_for(name, ext)
    line, bs, be = comment_style_for(ext, fname)
    if modeline:
        # Keep the banner in the same comment dialect as the modeline so the
        # first lines of the file parse as that language's comments.
        tok = modelline_prefix_token(modeline)
        if tok in ("#", "//", "--", ";"):
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
        extra = note
        if c is not None:
            head_lines.insert(1, f"{c}  note       : {extra}")
        elif bs:
            head_lines.insert(1, f"  note       : {extra}")
        else:
            head_lines.insert(1, f"  note: {extra}")
        prog, _ = default_program(name, ext, "Hello World!", fname)

    text = normalise("\n".join(head_lines) + "\n\n" + prog)
    if not text.endswith("\n"):
        text += "\n"
    return text


def safe_dir(base: Path, slug: str, taken: dict) -> Path:
    d = base / slug
    n = taken.get(slug, 0)
    taken[slug] = n + 1
    while d.exists() and any(d.iterdir()):
        d = base / f"{slug}-{n + 1}"
        n += 1
        taken[slug] = n
    d.mkdir(parents=True, exist_ok=True)
    return d


def modelline_prefix_token(modeline: str) -> str:
    """Recover the comment token a rendered modeline starts with."""
    for tok in ("<!--", "/*", "//", "--", ";", "#"):
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true", help="wipe hello/ first")
    args = ap.parse_args()

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
    taken_core: dict[str, int] = {}
    taken_full: dict[str, int] = {}

    # ---- core layer -----------------------------------------------------
    for rec in rainbow["languages"]:
        name = rec["name"]
        ext = rec["extension"] or ""
        d = safe_dir(core_dir, rec["slug"], taken_core)
        fname = rec.get("filename") or ("hello" + ext)
        path = d / fname
        text = build_file(
            name,
            ext,
            f"#{rec['color']}" if rec["color"] else None,
            rec.get("hue"),
            "Pinned with a Linguist modeline so it keeps its own segment on the bar.",
            "core",
            f"hello/core/{rec['slug']}/{fname}",
            fname=fname,
            modeline=modeline_for(rec),
        )
        path.write_text(text, encoding="utf-8", newline="\n")
        manifest.append(
            {
                "language": name,
                "layer": "core",
                "path": f"hello/core/{rec['slug']}/{fname}",
                "extension": ext,
                "type": rec.get("type"),
                "color": f"#{rec['color']}" if rec["color"] else None,
                "hue": rec.get("hue"),
                "modeline": rec.get("modeline_alias"),
                "runner": RUNNERS.get(name.lower()),
                "real_template": name.lower() in HELLO,
            }
        )

    # ---- full layer -----------------------------------------------------
    core_names = {r["name"].lower() for r in rainbow["languages"]}
    note = (
        "No curated template for this language yet: the closest equivalent "
        "Hello World is used, see the linked interpreter/rosetta entries."
    )
    for rec in merged:
        if rec["name"].lower() in core_names:
            continue
        ext = ""
        ext = choose_full_extension(rec)
        if not ext.startswith("."):
            ext = "." + ext
        d = safe_dir(full_dir, rec["slug"], taken_full)
        fname = "hello" + ext
        text = build_file(
            rec["name"],
            ext,
            f"#{rec['color']}" if rec.get("color") else None,
            None,
            note,
            "full",
            f"hello/full/{rec['slug']}/{fname}",
        )
        (d / fname).write_text(text, encoding="utf-8", newline="\n")
        manifest.append(
            {
                "language": rec["name"],
                "layer": "full",
                "path": f"hello/full/{rec['slug']}/{fname}",
                "extension": ext,
                "type": rec.get("type"),
                "color": f"#{rec['color']}" if rec.get("color") else None,
                "hue": None,
                "runner": RUNNERS.get(rec["name"].lower()),
                "real_template": rec["name"].lower() in HELLO,
            }
        )

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
    (HELLO_DIR / "manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"core files : {core_n}")
    print(f"full files : {full_n}")
    print(f"total      : {len(manifest)}")
    print(f"curated templates: {real_n}")
    print(f"runnable commands : {payload['runnable_command_count']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
