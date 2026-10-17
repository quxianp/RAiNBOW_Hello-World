# Adding a template: build, package and CI configuration

Thirty-odd entries in this repository are not languages at all. They are files
whose entire content is a declaration about a project.

## The trap

`add_templates.py` used to reject every one of them with *"never says Hello
World"*, which was the wrong question. A Maven POM, a webpack config and a
GitLab CI file have nowhere to put a greeting, and demanding one is the same
mistake as asking a `.properties` file to have a main function.

The fix was not to loosen the rule but to name the category properly:
**declaration forms**, in `scripts/add_templates.py`'s `DECLARATION_FORMS`, with
`tests/test_declaration_forms.py` guarding them.

## What counts

- **Package manifests** — `package.json`, `pyproject`, `Gemfile`, `composer`,
  `Cargo.toml`, `go.mod`, `pom.xml`
- **Build systems** — `Makefile`, `CMakeLists.txt`, `BUILD`, `meson.build`,
  `justfile`
- **CI definitions** — `.gitlab-ci.yml`, Tekton, Jenkins
- **Infrastructure** — `Dockerfile`, `Terraform`, Kubernetes manifests
- **Lockfiles and generated metadata** — `package-lock.json`, `Cargo.lock`

The exemption keys on the **extension**, not on the language, so it cannot be
used to excuse an actual program.

## The trap in the other direction

The exemption is not a licence to write a program in a config file. The test
enforces the other half: no `function main`, no `def main`, no `int main`, no
`printf(`, no `#!/` in any declaration form.

A `go.mod` containing a Go program passes every other check in this repository —
it is the right byte count, carries the right modeline, and is 19/19 on the
acceptance checks — and is rejected by every Go tool in existence. That is the
whole reason the guard exists.

## Worked examples in this repository

```xml
<!-- Maven -->
<project>
  <modelVersion>4.0.0</modelVersion>
  <artifactId>hello</artifactId>
  <name>Hello World!</name>
</project>
```

```yaml
# GitLab CI
stages: [build]
hello:
  stage: build
  script: [echo "Hello World!"]
```

```javascript
// webpack.config.js
module.exports = { mode: "production", entry: "./src/index.js",
                   output: { filename: "Hello World!.js" } };
```

## The honest placeholder

The Homebrew formula is the interesting one. It has every field a formula
requires, and its SHA-256 is 64 zeros — obviously not a real digest, and
deliberately so. A fabricated checksum in a file that people copy would be worse
than an obviously-placeholder one.

## Before you write one

- Is the extension a declaration form? If not, the greeting is required.
- Does the format have a field that is *meant* to hold prose? Use it.
- Does it have a checksum, a version pin, or a digest? Never invent one.
- Will the tool that reads it still read it? That is the test that matters.