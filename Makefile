# Every task this repository has, in one place.
#
# The scripts are the interface; this file is an index of them. Nothing here
# does work that scripts/ does not, because a wrapper that re-implements a
# command is a second place for it to be wrong -- which is E32 all over again.
#
#   make help      list the targets
#   make check     the full gate, in the order CI runs it
#   make fast      the gate without the slow checks
#
# Nothing here needs a dependency beyond Python 3.11 and Bash, which is the
# same constraint the test suite has: standard library only.

PY      ?= python3
.DEFAULT_GOAL := help

# SHELL is deliberately not overridden. The usual `SHELL := /usr/bin/env bash`
# is not valid make syntax -- SHELL must be a path, and make runs it directly
# without a shell in front of it, so `env bash` fails with a bare "system
# cannot find the file specified" before a single recipe line is read.
# Leaving it alone means make uses /bin/sh, which every target here works
# under: no pipelines, no process substitution, no bashisms.

.PHONY: help check fast test generate balance templates encodings figures \
        demo assets clean distclean validate coverage collisions hues \
        language-table object-formats doc-figures lint

## ---------------------------------------------------------------- the gate

# The usual `grep -E '^[a-z-]+:.*?## ' | awk` idiom for a self-documenting
# Makefile is not used here, because it needs grep and awk on PATH and this
# repository is developed on a Windows box where neither is. Ten echo lines
# that run everywhere beat a clever one that does not.
# Help is printed by scripts/make_help.py rather than by a recipe.
#
# Two reasons, both of them found by running it rather than by reading it. The
# usual `SHELL := /usr/bin/env bash` is not valid make syntax -- SHELL must be a
# path -- so the shell was not being chosen at all, and with a shell make
# cannot find, every recipe fails with "system cannot find the file specified"
# before the first line is read. And the usual
# `grep -E '^[a-z-]+:.*?## ' | awk` self-documenting idiom needs grep and awk,
# neither of which is on PATH on the Windows machine this repository is built
# on. A Python script needs neither, and it can parse this file with the same
# rule the targets use.
help:
	$(PY) scripts/make_help.py Makefile

check:                    ## everything CI runs, in CI's order
	$(MAKE) fast
	$(MAKE) validate
	$(PY) scripts/validate_delivery.py

fast:                     ## the gate without the repository audit
	$(PY) scripts/run_tests.py
	$(PY) scripts/check_templates.py
	$(PY) scripts/check_manifest.py
	$(PY) scripts/check_banners.py
	$(PY) scripts/verify_encodings.py
	$(PY) scripts/build_object_formats.py --check

validate:                 ## the repo/workflow audit
	$(PY) scripts/audit_repo.py
	$(PY) scripts/check_docs_links.py
	$(PY) scripts/check_readme_links.py
	$(PY) scripts/check_doc_figures.py

test:                     ## the test suite only
	$(PY) scripts/run_tests.py -v

## ------------------------------------------------------------ regeneration

generate:                 ## rewrite hello/ from the generator's tables
	$(PY) scripts/generate_all_hello.py

balance:                  ## re-tune the core layer's byte shares
	$(PY) scripts/balance_bytes.py

refresh:                  ## every generated file, in dependency order
	$(MAKE) generate
	$(MAKE) balance
	$(PY) scripts/classify_placeholders.py
	$(PY) scripts/language_table.py
	$(PY) scripts/update_docs_index.py
	$(PY) scripts/update_readme_coverage.py
	$(PY) scripts/update_readme_showcase.py

object-formats:           ## rebuild the seven binary formats, byte for byte
	$(PY) scripts/build_object_formats.py --emit .tmp/object_batch.json
	$(PY) scripts/add_templates.py --from .tmp/object_batch.json --replace
	$(PY) scripts/build_object_formats.py --check

## ----------------------------------------------------------------- the bar

coverage:                 ## the figures README quotes
	$(PY) scripts/coverage_figure.py

figures:                  ## every figure in the documentation, checked
	$(PY) scripts/check_doc_figures.py

collisions:               ## extensions more than one language claims
	$(PY) scripts/extension_collisions.py

hues:                     ## how evenly the core layer's hues are spaced
	$(PY) scripts/hue_uniformity.py

language-table:           ## data/LANGUAGES.md
	$(PY) scripts/language_table.py

## ------------------------------------------------------------- the demo

demo:                     ## record assets/ locally (needs ffmpeg and vhs)
	bash scripts/record_demo.sh

assets:                   ## re-render the bar and the hero banner
	$(PY) scripts/render_github_bar.py
	$(PY) scripts/generate_hero_banner.py

## ------------------------------------------------------------------ chores

lint:                     ## the cheap guards, no test suite
	$(PY) scripts/check_templates.py
	$(PY) scripts/check_manifest.py
	$(PY) scripts/check_banners.py
	$(PY) scripts/check_docs_links.py
	$(PY) scripts/check_readme_links.py
	$(PY) scripts/check_doc_figures.py

clean:                    ## caches and scratch files
	rm -rf .tmp/*.json .tmp/batch*.json
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

distclean: clean          ## also the recorded assets
	rm -f assets/hello-world.gif assets/hello-world.mp4