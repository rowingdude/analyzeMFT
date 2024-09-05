# Contributing to AnalyzeMFT

We welcome all contributions to AnalyzeMFT and appreciate your effort in helping improve this project! Please take a moment to read through the following guidelines before opening an issue, pull request (PR), or making any contributions.

## Code of Conduct

1. **Issues and Pull Requests (PRs)**  
   You are encouraged to open as many issues or PRs as you see necessary. Contributions are always welcome!
   
2. **Commit Guidelines**  
   To maintain a clean and manageable project history:
   - Each commit should represent **ONE** discrete change. Avoid bundling multiple changes into a single commit.
   - PRs will be **squashed** if necessary, but we strongly prefer a clear change-by-change commit history. This is essential for effective debugging and maintaining code quality.

## How to Contribute

### Reporting Bugs

- **Create an issue** for any bug you encounter. Make sure to describe the issue clearly and include any necessary information (e.g., error messages, logs, steps to reproduce).
- Feel free to contribute a fix after reporting!

### Proposing New Features

- **Open an issue** to discuss your proposed feature before opening a PR. It's important to make sure it aligns with the project goals.

### Making Changes

1. **Fork the repository** and create your branch from `main`.
2. **Make your changes**, ensuring that they address one issue at a time.
3. **Test your changes** thoroughly.
4. **Submit a pull request**, referencing the related issue if applicable.

### Commit Messages

- Use concise and descriptive commit messages that explain the context of your change.
- Reference the issue number (if applicable) in your commit message.

Example:
```
   Fix parsing of reparse point attribute (#123)

   Add error handling for incomplete reparse point data
   Update documentation for reparse point parsing
```

## Code Style

We follow a specific code style to maintain consistency throughout the project. Please adhere to the following guidelines:

### Python Code Style

1. Use 4 spaces for indentation (no tabs).
2. Follow PEP 8 guidelines for naming conventions and code layout.
3. Use type hints for function parameters and return values.
4. Keep lines to a maximum of 100 characters.
5. Use descriptive variable names.

Example:

```
from typing import List, Dict

def parse_mft_record(raw_record: bytes) -> Dict[str, Any]:
    record = {}
    return record


class MftAnalyzer:
    def __init__(self, mft_file: str, output_file: str):
        self.mft_file = mft_file
        self.output_file = output_file

    async def analyze(self) -> None:
        pass
```

### Comments

- Though not implemented yet, future updates will include docstrings for modules, classes, and functions.
- Keep inline comments to a minimum unless necessary for complex logic or non-obvious code.
- Keep comments up-to-date with code changes.

Example - Future comment style:

```
def parse_attribute(offset: int, raw_data: bytes) -> Dict[str, Any]:
    """
    Parse an MFT attribute at the given offset.

    Args:
        offset (int): The starting offset of the attribute.
        raw_data (bytes): The raw MFT record data.

    Returns:
        Dict[str, Any]: A dictionary containing the parsed attribute information.
    """
```

### SQL - work in progress

We're working on bringing an SQL engine into this program because (IMO) it's the better way to sort and analyze massive datasets. With that in mind, I'd like to lay out a few SQL specific items:

SQL keywords need to be uppercase.
SQL data columns should be lowercase and use `_` to separate words. 

```
CREATE TABLE mft_record (
    id INTEGER PRIMARY KEY,
    record_number INTEGER NOT NULL,
    parent_record_number INTEGER
)
```

### Pull Requests 

After undering the joy of learning why branches have locks and the issues with trusting people to test fully, we're going to revamp the PR process. 

1. Instituted branch safety on the main branch
2. Built out a test suite (if anyone knows how to make this work on GH, lmk)

PRs will now be required to fit this format:

```
## Description
This PR adds support for parsing reparse point attributes in MFT records. It includes:
- New function `parse_reparse_point` in `mft_record.py`
- Updated `MftRecord` class to handle reparse point attributes
- New tests for reparse point parsing in `test_mft_record.py`
- Updated documentation in README.md

Fixes #123

## Checklist
- [x] Code follows the project's style guidelines
- [x] Tests have been added/updated
- [x] Documentation has been updated
- [x] All tests pass locally
```

# Thank You
#### Your contribution is greatly appreciated, and we look forward to reviewing your work!

