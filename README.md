# difflib-rst

A high-performance Rust implementation of Python's `difflib.unified_diff` function with PyO3 bindings.

## Overview

This package provides a Rust-based implementation of the unified diff algorithm, offering significant performance improvements over Python's built-in `difflib` module while maintaining API compatibility.

## Features

- **Fast**: Rust implementation for better performance
- **Compatible**: Drop-in replacement for `difflib.unified_diff`
- **Tested**: Comprehensive test suite validating against Python's built-in implementation
- **Easy to use**: Simple Python API with PyO3 bindings

## Performance

The Rust implementation consistently outperforms Python's built-in `difflib` module across all scenarios:

### Benchmark Results

#### Small Changes in Large Files
- **5,000 lines, 5 changes**: 1.72x faster
- **10,000 lines, 5 changes**: 1.81x faster  
- **20,000 lines, 5 changes**: 2.35x faster

#### Medium Changes in Large Files (5% changed)
- **5,000 lines, 250 changes**: 2.30x faster
- **10,000 lines, 500 changes**: 2.31x faster
- **20,000 lines, 1,000 changes**: 2.29x faster

#### General Performance
- **Small files (100-2000 lines)**: 1.5x-2.7x faster
- **Identical sequences**: 5.5x faster
- **Files with 50% changes**: 2.5x-2.8x faster

### Key Optimizations

The performance improvements come from:
- **Sparse HashMap representation** for tracking matches (instead of dense vectors)
- **Queue-based matching algorithm** for better cache locality
- **Optimized string operations** leveraging Rust's zero-cost abstractions

## Installation

```bash
# Build from source
source venv/bin/activate
pip install maturin pytest
maturin develop --release
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
# Activate virtual environment
source venv/bin/activate

# Run tests
python -m pytest tests/ -v

# Run benchmarks
python -m pytest tests/test_benchmark.py -s

# Build the package with optimizations
maturin develop --release
```

## Author

Everything in this project was written by Sweep AI.