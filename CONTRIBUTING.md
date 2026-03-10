# Contributing to Autonomous CLI

Thank you for your interest in contributing to Autonomous CLI!

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Security](#security)
- [License](#license)

## Code of Conduct

This project adheres to a code of conduct:

- **Be respectful** and inclusive
- **Be collaborative** and constructive
- **Focus on the best** outcome for the community
- **Show empathy** towards others

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher (for MCP servers)
- Git
- Familiarity with async Python
- Basic understanding of Claude Agent SDK

### Finding Issues

Good first issues are labeled:
- `good-first-issue` - Perfect for newcomers
- `help-wanted` - We need assistance
- `bug` - Something isn't working
- `enhancement` - New features or improvements

## Development Setup

### 1. Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/autonomous-cli
cd autonomous-cli

# Add upstream remote
git remote add upstream https://github.com/claude-code-skills-factory/autonomous-cli
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
acli --version
pytest --version
```

### 4. Install Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

## Development Workflow

### 1. Create a Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/my-feature
# or
git checkout -b fix/my-bugfix
```

Branch naming:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `refactor/` - Code refactoring
- `test/` - Test improvements

### 2. Make Changes

Follow these guidelines:
- Write clear, concise code
- Add tests for new functionality
- Update documentation as needed
- Keep commits atomic and focused

### 3. Commit Changes

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add .
git commit -m "feat: add new dashboard panel"
# or
git commit -m "fix: resolve streaming buffer overflow"
# or
git commit -m "docs: update installation guide"
```

Commit types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process or tool changes

### 4. Push Changes

```bash
git push origin feature/my-feature
```

## Testing

### Run All Tests

```bash
# Run full test suite
pytest

# With coverage report
pytest --cov=acli --cov-report=html

# View coverage
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### Run Specific Tests

```bash
# Run specific module
pytest tests/test_security.py

# Run specific test
pytest tests/test_security.py::TestValidatePkill::test_pkill_node

# Run with verbose output
pytest -v

# Run with print output
pytest -s
```

### Test Coverage Requirements

- **Minimum**: 80% overall coverage
- **Security**: 100% coverage for `acli.security`
- **Core**: 90% coverage for `acli.core`
- **New Code**: All new code must have tests

### Writing Tests

Follow these patterns:

```python
"""
Test Description
================

Brief description of what this test module covers.
"""

import pytest

class TestMyFeature:
    """Test MyFeature class."""

    @pytest.fixture
    def my_fixture(self):
        """Create test fixture."""
        return SomeObject()

    def test_basic_functionality(self, my_fixture):
        """Test basic functionality works."""
        result = my_fixture.do_something()
        assert result == expected_value

    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test async functionality."""
        result = await async_function()
        assert result is not None
```

## Code Style

### Python Style Guide

We follow **PEP 8** with these tools:

```bash
# Linting
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
ruff format src/
```

### Type Hints

Use type hints for all functions:

```python
from typing import Optional, List, Dict
from pathlib import Path

def process_file(
    file_path: Path,
    max_size: int = 1000,
    encoding: str = "utf-8",
) -> Dict[str, Any]:
    """Process a file and return results."""
    ...
```

### Type Checking

```bash
# Run mypy
mypy src/acli

# Strict mode (recommended)
mypy --strict src/acli
```

### Docstrings

Use Google-style docstrings:

```python
def validate_command(command: str, allowed: set[str]) -> bool:
    """Validate command against allowlist.

    Args:
        command: The command to validate
        allowed: Set of allowed command names

    Returns:
        True if command is allowed, False otherwise

    Raises:
        ValueError: If command is malformed

    Examples:
        >>> validate_command("ls", {"ls", "cat"})
        True
        >>> validate_command("rm", {"ls", "cat"})
        False
    """
    ...
```

### Import Order

1. Standard library
2. Third-party packages
3. Local modules

```python
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from acli.core.client import create_client
from acli.security.hooks import bash_security_hook
```

## Pull Request Process

### 1. Ensure Quality

Before submitting:

```bash
# Run tests
pytest

# Check coverage
pytest --cov=acli --cov-report=term-missing

# Type check
mypy src/acli

# Lint
ruff check src/

# Format
ruff format src/
```

### 2. Update Documentation

- Update README.md if needed
- Update relevant docs/ files
- Add docstrings to new functions
- Update CHANGELOG.md

### 3. Create Pull Request

1. Go to GitHub
2. Click "New Pull Request"
3. Select your branch
4. Fill out PR template:

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing

- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Coverage maintained/improved

## Checklist

- [ ] Code follows project style guide
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added for new features
- [ ] All tests passing
```

### 4. Code Review

Expect feedback on:
- Code quality and style
- Test coverage
- Documentation clarity
- Security implications
- Performance impact

Address feedback:

```bash
# Make changes
git add .
git commit -m "Address review feedback"
git push origin feature/my-feature
```

### 5. Merge

Once approved:
- Squash commits if requested
- Ensure CI passes
- Maintainer will merge

## Project Structure

Understanding the codebase:

```
autonomous-cli/
├── src/acli/              # Source code
│   ├── core/             # Core orchestration
│   ├── security/         # Security hooks and validators
│   ├── progress/         # Progress tracking
│   ├── browser/          # Browser automation
│   ├── spec/             # Spec enhancement
│   └── ui/               # Dashboard UI
├── tests/                # Test suite
│   ├── test_security.py  # Security tests
│   ├── test_cli.py       # CLI tests
│   └── ...
├── docs/                 # Documentation
├── pyproject.toml        # Project metadata
└── README.md             # Main documentation
```

## Security

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead, email: security@example.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will:
1. Acknowledge within 48 hours
2. Investigate and validate
3. Develop and test a fix
4. Release a security patch
5. Publicly disclose after fix is available

### Security Best Practices

When contributing:
- Never commit API keys or secrets
- Validate all user inputs
- Use shlex for command parsing
- Follow principle of least privilege
- Test security boundaries

## Areas for Contribution

### High Priority

- **Browser Testing**: Enhanced visual testing
- **Error Handling**: Better error messages
- **Performance**: Dashboard optimization
- **Documentation**: More examples and guides

### Medium Priority

- **Features**: Pause/resume functionality
- **Testing**: Integration test coverage
- **UI**: Dashboard customization
- **Config**: Hot-reload support

### Good First Issues

- Documentation improvements
- Test coverage increases
- Code comment additions
- Example projects

## Getting Help

### Questions?

- **GitHub Discussions**: For general questions
- **Issues**: For bug reports and feature requests
- **Pull Requests**: For code contributions

### Resources

- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Quick Start](docs/QUICKSTART.md)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Autonomous CLI! 🚀
