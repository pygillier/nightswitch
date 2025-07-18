"""
Tasks for managing the Nightswitch project.

This module provides tasks for development, testing, and deployment
using the invoke library. It complements the taskfile.yaml for users
who prefer Python-based task runners.
"""

import os
import shutil
import sys
from pathlib import Path

from invoke import task

# Configuration
SRC_DIR = "src/nightswitch"
TEST_DIR = "tests"
PYTHON_CMD = "uv run python"
PIP_CMD = "uv pip"
PYTEST_CMD = "uv run pytest"
BLACK_CMD = "uv run black"
ISORT_CMD = "uv run isort"
MYPY_CMD = "uv run mypy"
FLAKE8_CMD = "uv run flake8"


@task
def install(c):
    """Install the package and development dependencies."""
    c.run(f"{PIP_CMD} install -e '.[dev]'")


@task
def run(c):
    """Run the application."""
    c.run(f"{PYTHON_CMD} -m nightswitch.main")


@task
def test(c, unit=False, integration=False, coverage=False):
    """Run tests."""
    cmd = PYTEST_CMD
    
    if unit:
        cmd += f" {TEST_DIR}/unit"
    elif integration:
        cmd += f" {TEST_DIR}/integration"
    
    if coverage:
        cmd += f" --cov={SRC_DIR} --cov-report=html --cov-report=term"
    
    c.run(cmd)


@task
def format(c):
    """Format code with black and isort."""
    c.run(f"{BLACK_CMD} {SRC_DIR} {TEST_DIR}")
    c.run(f"{ISORT_CMD} {SRC_DIR} {TEST_DIR}")


@task
def lint(c):
    """Run linting checks."""
    c.run(f"{FLAKE8_CMD} {SRC_DIR} {TEST_DIR}")


@task
def typecheck(c):
    """Run type checking with mypy."""
    c.run(f"{MYPY_CMD} {SRC_DIR}")


@task
def quality(c):
    """Run all code quality checks."""
    format(c)
    lint(c)
    typecheck(c)
    test(c)


@task
def clean(c):
    """Clean up build artifacts and cache files."""
    patterns = [
        "build/",
        "dist/",
        "*.egg-info/",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        "coverage.xml",
        "**/__pycache__",
        "**/*.pyc",
    ]
    
    for pattern in patterns:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)


@task
def build(c):
    """Build the package."""
    c.run(f"{PYTHON_CMD} -m build")


@task
def autostart_enable(c):
    """Enable autostart for the application."""
    c.run("./enable-autostart.sh")


@task
def autostart_disable(c):
    """Disable autostart for the application."""
    home = os.path.expanduser("~")
    autostart_dir = os.path.join(home, ".config", "autostart")
    
    # Create autostart directory if it doesn't exist
    if not os.path.exists(autostart_dir):
        os.makedirs(autostart_dir)
    
    # Remove desktop file if it exists
    desktop_file = os.path.join(autostart_dir, "me.pygillier.Nightswitch.desktop")
    if os.path.exists(desktop_file):
        os.remove(desktop_file)


@task
def install_system(c):
    """Install the application system-wide."""
    c.run("sudo ./install.sh")