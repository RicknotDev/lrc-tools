PYTHON ?= python3
PIP := $(PYTHON) -m pip
PACKAGE := .
FULL_EXTRAS := .[full,timing]

.PHONY: help install install-minimal reinstall uninstall test build clean

help:
	@echo "Available targets:"
	@echo "  make install          Install editable package with full default dependencies"
	@echo "  make install-minimal  Install editable package with base dependencies only"
	@echo "  make reinstall        Reinstall editable package with full dependencies"
	@echo "  make uninstall        Uninstall lrc-tools"
	@echo "  make test             Run test suite"
	@echo "  make build            Build wheel and sdist"
	@echo "  make clean            Remove build artifacts"

install:
	$(PIP) install --user -e '$(FULL_EXTRAS)'

install-minimal:
	$(PIP) install --user -e '$(PACKAGE)'

reinstall:
	$(PIP) uninstall -y lrc-tools || true
	$(PIP) install --user -e '$(FULL_EXTRAS)'

uninstall:
	$(PIP) uninstall lrc-tools

test:
	bash scripts/run_tests.sh

build:
	$(PIP) install --upgrade build
	$(PYTHON) -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
