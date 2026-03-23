.DEFAULT_GOAL := help
SHELL := /bin/bash

PYTHON ?= python3
SRC_DIR := src
TEST_DIR := tests
PACKAGE := clawarena

# ─── Installation ────────────────────────────────────────────────────────────

.PHONY: install
install: ## Install package in editable mode
	$(PYTHON) -m pip install -e .

.PHONY: install-dev
install-dev: ## Install with all dev dependencies
	$(PYTHON) -m pip install -e ".[dev,llm-judge]"
	$(PYTHON) -m pip install pylint bandit pre-commit tox

.PHONY: install-hooks
install-hooks: ## Install pre-commit hooks
	pre-commit install

# ─── Linting ─────────────────────────────────────────────────────────────────

.PHONY: lint
lint: lint-ruff lint-pylint ## Run all linters

.PHONY: lint-ruff
lint-ruff: ## Run ruff linter
	ruff check $(SRC_DIR) $(TEST_DIR)

.PHONY: lint-pylint
lint-pylint: ## Run pylint
	pylint $(SRC_DIR)/$(PACKAGE) --output-format=colorized

# ─── Formatting ──────────────────────────────────────────────────────────────

.PHONY: format
format: ## Auto-format code with ruff
	ruff format $(SRC_DIR) $(TEST_DIR)
	ruff check --fix $(SRC_DIR) $(TEST_DIR)

.PHONY: format-check
format-check: ## Check formatting without changes
	ruff format --check $(SRC_DIR) $(TEST_DIR)

# ─── Type Checking ───────────────────────────────────────────────────────────

.PHONY: typecheck
typecheck: ## Run mypy type checker
	mypy $(SRC_DIR)/$(PACKAGE)

# ─── Testing ─────────────────────────────────────────────────────────────────

.PHONY: test
test: ## Run tests
	pytest $(TEST_DIR) -v

.PHONY: test-fast
test-fast: ## Run tests without slow markers
	pytest $(TEST_DIR) -v -m "not slow"

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	pytest $(TEST_DIR) -v --cov=$(SRC_DIR)/$(PACKAGE) --cov-report=term-missing --cov-report=html

.PHONY: test-ci
test-ci: ## Run tests with coverage (CI mode, XML output)
	pytest $(TEST_DIR) -v --cov=$(SRC_DIR)/$(PACKAGE) --cov-report=xml --cov-report=term-missing --junitxml=junit.xml

# ─── Security ────────────────────────────────────────────────────────────────

.PHONY: security
security: ## Run security checks with bandit
	bandit -r $(SRC_DIR)/$(PACKAGE) -c pyproject.toml

# ─── Quality Gate (run all checks) ──────────────────────────────────────────

.PHONY: check
check: format-check lint typecheck test ## Run all quality checks (CI-like)

.PHONY: fix
fix: format lint-ruff ## Auto-fix all fixable issues

# ─── Build & Distribution ───────────────────────────────────────────────────

.PHONY: build
build: clean-build ## Build source and wheel distributions
	$(PYTHON) -m build

.PHONY: publish-test
publish-test: build ## Upload to TestPyPI
	twine upload --repository testpypi dist/*

.PHONY: publish
publish: build ## Upload to PyPI
	twine upload dist/*

# ─── Cleaning ────────────────────────────────────────────────────────────────

.PHONY: clean
clean: clean-build clean-pyc clean-test ## Remove all build/test/cache artifacts

.PHONY: clean-build
clean-build: ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info src/*.egg-info

.PHONY: clean-pyc
clean-pyc: ## Remove Python file artifacts
	find . -type f -name '*.py[cod]' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyo' -delete

.PHONY: clean-test
clean-test: ## Remove test and coverage artifacts
	rm -rf .pytest_cache/ .coverage htmlcov/ coverage.xml junit.xml
	rm -rf .mypy_cache/ .ruff_cache/ .tox/

# ─── Tox ─────────────────────────────────────────────────────────────────────

.PHONY: tox
tox: ## Run full tox suite
	tox

.PHONY: tox-lint
tox-lint: ## Run tox lint environment
	tox -e lint

.PHONY: tox-type
tox-type: ## Run tox type-check environment
	tox -e typecheck

# ─── Help ────────────────────────────────────────────────────────────────────

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
