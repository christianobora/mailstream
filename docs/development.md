# Development Guide

## Setup Development Environment

1. Clone the repository
2. Create a virtual environment
3. Install development dependencies

```bash
# Clone
git clone https://github.com/christianobora/mailstream.git
cd mailstream

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install development dependencies
pip install -e .[dev]
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test module
pytest tests/test_client.py

# Run with verbose output
pytest -v
```

## Code Formatting

```bash
# Use Black for formatting
black src/ tests/

# Use Flake8 for linting
flake8 src/ tests/
```

## Type Checking

```bash
# Run mypy for type checking
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Ensure all tests pass
6. Submit a pull request

### Commit Message Guidelines

- Use descriptive commit messages
- Follow conventional commits format
- Include scope of changes

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag
4. Push to PyPI

```bash
# Example release process
python -m build
twine upload dist/*
```