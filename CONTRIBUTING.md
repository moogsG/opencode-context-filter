# Contributing to OpenCode Context Filter Proxy

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with:

- **Clear title** describing the problem
- **Steps to reproduce** the issue
- **Expected behaviour** vs actual behaviour
- **System information** (OS, Python version, OpenCode version)
- **Proxy logs** from `/tmp/ollama_context_filter.log`

### Suggesting Enhancements

Feature requests are welcome! Please create an issue with:

- **Clear description** of the proposed feature
- **Use case** explaining why it's useful
- **Proposed implementation** if you have ideas

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/gunnarnordqvist/opencode-context-filter.git
   cd opencode-context-filter
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add tests if applicable
   - Update documentation

4. **Test your changes**
   ```bash
   python3 tests/test_basic.py
   python3 tests/test_realistic.py
   python3 tests/test_extreme.py
   ```

5. **Commit with clear message**
   ```bash
   git commit -m "Add feature: brief description"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

### Python

- Follow PEP 8 style guide
- Use descriptive variable names
- Add comments for complex logic
- Keep functions focused and small

### Shell Scripts

- Use `bash` for compatibility
- Add error checking (`set -e`)
- Use meaningful function names
- Comment complex sections

### Documentation

- Use British English spelling
- Keep README concise
- Detailed docs go in `docs/`
- Include code examples

## Testing

### Running Tests

```bash
# All tests
python3 tests/test_basic.py
python3 tests/test_realistic.py
python3 tests/test_extreme.py

# Single test
python3 tests/test_basic.py
```

### Adding Tests

When adding features, include tests:

```python
# tests/test_new_feature.py
def test_new_feature():
    """Test description"""
    # Setup
    # Execute
    # Assert
    pass
```

## Documentation

Update documentation when changing:

- **README.md** - For user-facing changes
- **docs/SETUP.md** - For installation changes
- **docs/USAGE.md** - For usage changes
- **docs/TECHNICAL.md** - For implementation changes

## Commit Messages

Use clear, descriptive commit messages:

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **test**: Test changes
- **refactor**: Code refactoring
- **chore**: Maintenance tasks

Examples:
```
feat: Add support for phi-2 model
fix: Handle JSON decode errors gracefully
docs: Update installation instructions
test: Add test for extreme context filtering
```

## Code Review

Pull requests will be reviewed for:

- **Functionality**: Does it work as intended?
- **Tests**: Are there adequate tests?
- **Documentation**: Is it documented?
- **Style**: Does it follow project conventions?
- **Performance**: Any performance implications?

## Release Process

1. Update version in relevant files
2. Update CHANGELOG.md
3. Create git tag
4. Create GitHub release
5. Announce in README

## Questions?

- Open an issue for questions
- Check existing issues first
- Be respectful and constructive

## Licence

By contributing, you agree that your contributions will be licensed under the MIT Licence.

Thank you for contributing! 🎉
