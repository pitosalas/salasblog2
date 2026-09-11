# Makefile — dev commands for Salasblog2
#
# fmt/lint only touch files changed in the working tree (staged, unstaged, or
# new/untracked) -- never the whole repo. Introducing or tightening a linter
# partway through a project's life should never force a mass reformat of code
# nobody asked to touch; scope it to what you're actually working on.

CHANGED_PY := $(shell { \
	git diff --name-only --diff-filter=ACMR -- '*.py'; \
	git diff --cached --name-only --diff-filter=ACMR -- '*.py'; \
	git ls-files --others --exclude-standard -- '*.py'; \
} | sort -u)

.PHONY: help setup fmt lint test check generate run local deploy
.DEFAULT_GOAL := setup

help:
	@echo "Targets:"
	@echo "  setup    - install/sync dependencies"
	@echo "  fmt      - format changed .py files"
	@echo "  lint     - lint changed .py files"
	@echo "  test     - run the test suite"
	@echo "  check    - fmt + lint + test"
	@echo "  generate - regenerate the static site into output/"
	@echo "  run      - run the server"
	@echo "  local    - regenerate the static site, then run the server with --reload"
	@echo "  deploy   - build and deploy to fly.io"

setup:
	uv sync

fmt:
	@if [ -z "$(CHANGED_PY)" ]; then \
		echo "fmt: no changed .py files"; \
	else \
		uv run ruff format $(CHANGED_PY); \
	fi

lint:
	@if [ -z "$(CHANGED_PY)" ]; then \
		echo "lint: no changed .py files"; \
	else \
		uv run ruff check $(CHANGED_PY); \
	fi

test:
	uv run pytest

check: fmt lint test

generate:
	uv run bg generate

run:
	uv run bg server

local: generate
	uv run bg server --reload

deploy:
	uv run bg deploy
