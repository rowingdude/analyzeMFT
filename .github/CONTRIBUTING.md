# Contributing to analyzeMFT

Thank you for your interest in contributing to analyzeMFT! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please treat all community members with respect and create a welcoming environment for everyone.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of NTFS file systems and digital forensics (helpful but not required)

### Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/rowingdude/analyzeMFT.git
   cd analyzeMFT
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate 
   ```

4. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio pytest-cov flake8 mypy bandit
   pip install -e .
   ```

5. Run tests to verify setup:
   ```bash
   pytest tests/
   ```

## Development Workflow

### Branching Strategy

- `main` branch: Stable releases
- `develop` branch: Integration branch for features
- Feature branches: `feature/description-of-feature`
- Bug fix branches: `fix/description-of-fix`

### Making Changes

1. Create a new branch for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards
3. Add or update tests for your changes
4. Update documentation as needed
5. Commit your changes with descriptive messages

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code formatting changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions or modifications
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

Examples:
```
feat(parser): add support for alternate data streams
fix(cli): resolve memory leak in large file processing
docs: update installation instructions for Windows
```

## Coding Standards

### Python Style Guide

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Maximum line length: 120 characters
- Use descriptive variable and function names

### Code Quality

Run these tools before submitting:

```bash
# Linting
flake8 src/ tests/ --max-line-length=120

# Type checking
mypy src/ --ignore-missing-imports

# Security analysis
bandit -r src/

# Run tests with coverage
pytest tests/ --cov=src/analyzeMFT --cov-report=term
```

### Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Update README.md for user-facing changes
- Add comments for complex logic

Example docstring:
```python
def parse_mft_record(data: bytes, offset: int) -> MftRecord:
    """Parse a single MFT record from binary data.
    
    Args:
        data: Raw MFT data as bytes
        offset: Byte offset of the record within the MFT
        
    Returns:
        Parsed MFT record object
        
    Raises:
        ValueError: If the record is malformed or corrupted
    """
```

## Testing

### Test Requirements

- All new features must include tests
- Bug fixes should include regression tests
- Aim for >80% code coverage
- Tests should be fast and reliable

### Test Categories

- Unit tests: Test individual functions and classes
- Integration tests: Test component interactions
- End-to-end tests: Test complete workflows

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_mft_record.py

# Run with coverage
pytest tests/ --cov=src/analyzeMFT --cov-report=html

# Run only fast tests
pytest tests/ -m "not slow"
```

### Test Structure

```python
import pytest
from src.analyzeMFT.module import function_to_test

class TestFunctionName:
    def test_normal_case(self):
        """Test the happy path."""
        result = function_to_test(valid_input)
        assert result == expected_output
    
    def test_edge_case(self):
        """Test boundary conditions."""
        result = function_to_test(edge_case_input)
        assert result == expected_edge_output
    
    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
```

## Pull Request Process

### Before Submitting

1. Ensure all tests pass
2. Update documentation
3. Add entry to CHANGES.md (if applicable)
4. Verify code quality checks pass

### PR Requirements

- Clear description of changes
- Link to related issues
- Screenshots for UI changes (if applicable)
- Confirmation that tests pass

### Review Process

1. Automated checks must pass
2. At least one maintainer review required
3. Address all review feedback
4. Maintain clean commit history

## Performance Considerations

### Guidelines

- Profile code changes that affect performance
- Consider memory usage for large MFT files
- Use generators for processing large datasets
- Implement progress indicators for long operations

### Benchmarking

```bash
# Time command execution
time python analyzeMFT.py -f large_mft.raw -o output.csv

# Memory profiling (if memory_profiler installed)
mprof run python analyzeMFT.py -f large_mft.raw -o output.csv
mprof plot
```

## Security Considerations

- Never commit sensitive data or credentials
- Validate all user inputs
- Use secure file handling practices
- Run security scans on dependencies

## Documentation

### Types of Documentation

- Code comments: Explain complex logic
- Docstrings: API documentation
- README: User guide and quick start
- CHANGES.md: Version history
- Contributing guidelines (this file)

### Documentation Standards

- Keep documentation up-to-date with code changes
- Use clear, concise language
- Include examples where helpful
- Consider non-expert users

## Release Process

Releases are handled by maintainers:

1. Update version numbers
2. Update CHANGES.md
3. Create release tag
4. Automated CI/CD handles publishing

## Getting Help

### Community Resources

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and community support
- Code reviews: Learning opportunity

### Maintainer Contact

For sensitive issues or questions:
- Email: [maintainer email if available]
- Direct message on GitHub

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- GitHub contributor statistics

Thank you for contributing to analyzeMFT and helping improve digital forensics tools!