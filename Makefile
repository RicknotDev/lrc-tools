# Detect Python interpreter (python3 on Unix, python on Windows)
PYTHON ?= $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)
PIP := $(PYTHON) -m pip
PACKAGE := .
FULL_EXTRAS := .[full]
UNAME := $(shell uname -s)

.PHONY: help install install-minimal reinstall uninstall test build clean verify binary

help:
	@echo "Available targets:"
	@echo "  make install          Install with full dependencies"
	@echo "  make install-minimal  Install base dependencies only"
	@echo "  make reinstall        Reinstall"
	@echo "  make uninstall        Uninstall"
	@echo "  make test             Run test suite"
	@echo "  make build            Build wheel + sdist"
	@echo "  make binary           Build standalone binary (PyInstaller)"
	@echo "  make verify           Post-install verification"
	@echo "  make clean            Remove artifacts"

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

binary:
	$(PIP) install pyinstaller
	$(PYTHON) scripts/build_binary.py

verify:
	$(PYTHON) scripts/verify_install.py

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
