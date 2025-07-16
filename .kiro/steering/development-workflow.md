---
inclusion: always
---

# Development Workflow for Nightswitch

This document outlines the development workflow and best practices for the Nightswitch project.

## Git Workflow

### Commit Guidelines

**IMPORTANT**: After successfully completing each task, you MUST commit your changes to git with a descriptive commit message.

```bash
# Stage all changes
git add .

# Commit with descriptive message
git commit -m "feat: implement [task description]

- Brief description of what was implemented
- Any important technical details
- Reference to requirements if applicable"
```

### Commit Message Format

Use conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/modifications
- `refactor:` for code refactoring
- `style:` for formatting changes
- `chore:` for maintenance tasks

### Examples

```bash
# After completing a task
git add .
git commit -m "feat: set up project structure and development environment

- Created Python 3.13 project with uv dependency management
- Set up pyproject.toml with PyGTK 4 dependencies
- Created modular directory structure for core, plugins, services, UI
- Added comprehensive test structure
- Configured Flatpak distribution support"

# After implementing a feature
git add .
git commit -m "feat: implement theme switching core functionality

- Added ThemeManager class for desktop environment abstraction
- Implemented plugin system for desktop environment support
- Created configuration management system
- Added unit tests for core functionality"
```

## Development Standards

### Python Environment
- **MANDATORY**: All Python operations must use `uv` (see python-uv-requirements.md)
- Never use `pip` or direct `python` commands
- All commands must be prefixed with `uv run`

### Code Quality
- All code must pass type checking with `uv run mypy src`
- Code must be formatted with `uv run black src tests` and `uv run isort src tests`
- All new functionality requires unit tests
- Integration tests for user-facing features

### Testing Requirements
- Minimum 80% code coverage
- All public APIs must have tests
- Mock external dependencies in unit tests
- Integration tests for plugin system
- Run tests with `uv run pytest`

### Documentation
- All modules must have docstrings
- Public APIs require comprehensive documentation
- Update README.md for user-facing changes
- Add inline comments for complex logic

## Task Completion Checklist

For each completed task:

1. ✅ Implement the functionality
2. ✅ Write/update tests
3. ✅ Run test suite (`uv run pytest`)
4. ✅ Format code (`uv run black src tests && uv run isort src tests`)
5. ✅ Type check (`uv run mypy src`)
6. ✅ Update documentation if needed
7. ✅ **Commit changes to git**
8. ✅ Mark task as complete in tasks.md

## Project Structure Guidelines

### Module Organization
- `core/`: Application lifecycle, mode management, configuration
- `plugins/`: Desktop environment-specific implementations
- `services/`: External integrations (location, scheduling, etc.)
- `ui/`: GTK 4 user interface components
- `tests/`: Comprehensive test suite

### File Naming
- Use snake_case for Python files
- Use descriptive names that indicate purpose
- Group related functionality in modules
- Keep individual files focused and cohesive

## Dependencies Management

### Adding Dependencies
- Add to pyproject.toml dependencies section
- Update Flatpak manifest if needed
- Document new dependencies in README
- Consider security and maintenance implications

### Development Dependencies
- Keep development dependencies separate
- Include tools for code quality (black, isort, mypy, flake8)
- Include testing framework and coverage tools
- Document development setup in README