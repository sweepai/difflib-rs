# difflib-rst

A high-performance Rust implementation of Python's `difflib.unified_diff` function with PyO3 bindings.

## Overview

This package provides a Rust-based implementation of the unified diff algorithm, offering significant performance improvements over Python's built-in `difflib` module while maintaining API compatibility.

## Features

- **Fast**: Rust implementation for better performance
- **Compatible**: Drop-in replacement for `difflib.unified_diff`
- **Tested**: Comprehensive test suite validating against Python's built-in implementation
- **Easy to use**: Simple Python API with PyO3 bindings

## Installation

```bash
# Build from source
uv add --dev pytest
uv run maturin develop
```

## Usage

```python
from difflib_rst import unified_diff

# Compare two sequences of lines
a = ['line1', 'line2', 'line3']
b = ['line1', 'modified', 'line3']

diff = unified_diff(
    a, b,
    fromfile='original.txt',
    tofile='modified.txt',
    fromfiledate='2023-01-01',
    tofiledate='2023-01-02'
)

for line in diff:
    print(line, end='')
```

## API

The `unified_diff` function accepts the same parameters as Python's `difflib.unified_diff`:

- `a`, `b`: Sequences of lines to compare
- `fromfile`, `tofile`: Filenames for the diff header
- `fromfiledate`, `tofiledate`: File modification dates
- `n`: Number of context lines (default: 3)
- `lineterm`: Line terminator (default: '\n')

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Build the package
uv run maturin build
```

## Author

Everything in this project was written by Sweep AI.