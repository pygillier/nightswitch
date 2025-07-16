---
inclusion: always
---

# Python Development with uv

This document establishes mandatory requirements for Python development in the Nightswitch project.

## Mandatory uv Usage

**CRITICAL REQUIREMENT**: All Python operations MUST be executed through `uv`. Never use `pip`, `python -m pip`, or direct `python` commands for package management or execution.

### Package Management

```bash
# ✅ CORRECT - Use uv for all package operations
uv pip install package-name
uv pip install -e .
uv pip install -e ".[dev]"
uv pip uninstall package-name
uv pip list
uv pip freeze

# ❌ INCORRECT - Never use pip directly
pip install package-name
python -m pip install package-name
```

### Python Execution

```bash
# ✅ CORRECT - Use uv run for Python execution
uv run python script.py
uv run python -m module
uv run pytest
uv run mypy src
uv run black src tests
uv run isort src tests

# ❌ INCORRECT - Never use python directly
python script.py
python -m pytest
python -m mypy src
```

### Development Workflow Commands

Replace all Python commands in development workflow with uv equivalents:

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/nightswitch --cov-report=html

# Code formatting
uv run black src tests
uv run isort src tests

# Type checking
uv run mypy src

# Linting
uv run flake8 src tests

# Complete quality check
uv run pytest && uv run black --check src tests && uv run isort --check src tests && uv run mypy src && uv run flake8 src tests
```

### Project Setup

```bash
# Initial project setup
uv pip install -e ".[dev]"

# Verify installation
uv run python -c "import nightswitch; print('Installation successful')"

# Run application
uv run nightswitch
```

### Testing Commands

```bash
# Run all tests
uv run pytest

# Run specific test files
uv run pytest tests/unit/test_config.py

# Run with verbose output
uv run pytest tests/unit/test_config.py -v

# Run specific test categories
uv run pytest -m unit
uv run pytest -m integration

# Run with coverage
uv run pytest --cov=src/nightswitch --cov-report=term-missing
```

### Git Commit Requirements

When committing changes, ensure all commands in commit messages and documentation use `uv`:

```bash
git commit -m "feat: implement configuration management

- Created FreeDesktop-compliant config system
- Added comprehensive unit tests (run with: uv run pytest tests/unit/test_config.py)
- All dependencies managed through uv
- Code formatted with: uv run black src tests && uv run isort src tests"
```

## Why uv is Mandatory

1. **Consistency**: Ensures all team members use the same package management approach
2. **Performance**: uv is significantly faster than pip for dependency resolution
3. **Reliability**: Better dependency resolution and conflict detection
4. **Modern Python**: Follows current best practices for Python project management
5. **Reproducibility**: Ensures consistent environments across development and deployment

## Environment Setup

Before starting development, ensure uv is installed:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify uv installation
uv --version

# Set up project
uv pip install -e ".[dev]"
```

## Enforcement

- All documentation MUST use uv commands
- All CI/CD scripts MUST use uv
- All development instructions MUST specify uv usage
- Code reviews MUST verify uv usage in any scripts or documentation
- Any use of pip or direct python commands will be rejected

## Exception Handling

The ONLY exception to this rule is when uv is not available in a specific environment (e.g., some CI systems). In such cases:

1. Document the exception clearly
2. Provide both uv and fallback commands
3. Prioritize uv commands in documentation
4. Work to migrate the environment to support uv

Example:
```bash
# Preferred method
uv run pytest

# Fallback only if uv is not available
python -m pytest
```