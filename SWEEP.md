# SWEEP.md - difflib-rst Project Knowledge Base

## Project Overview
This is a Rust implementation of Python's `difflib.unified_diff` function with PyO3 bindings, created as a high-performance alternative to the built-in Python implementation.

## Build and Development Commands

### Building the Package
```bash
# Activate virtual environment (required)
source venv/bin/activate

# Clear build cache (important when changes aren't taking effect!)
cargo clean

# Development build (for testing)
maturin develop

# Production build with release optimizations (recommended for benchmarking)
maturin develop --release

# Build wheel for distribution
maturin build --release
```

### Testing Commands
```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_unified_diff.py::test_identical_sequences -v

# Run tests with more verbose output
python -m pytest tests/ -vv

# Run only basic sanity tests
python -m pytest tests/test_unified_diff.py -k "sanity or basic" -v

# Run benchmark tests
python -m pytest tests/test_benchmark.py -s
```

### Package Management
```bash
# Activate virtual environment
source venv/bin/activate

# Install the package in development mode
maturin develop

# Check for Rust compilation errors
cargo check
```

## Project Structure
```
difflib-rst/
├── Cargo.toml              # Rust dependencies and configuration
├── pyproject.toml          # Python packaging with maturin backend
├── src/
│   ├── lib.rs             # Main Rust implementation
│   └── lib_old.rs         # Backup of previous implementation
├── tests/
│   └── test_unified_diff.py # Comprehensive test suite
├── .gitignore             # Git ignore patterns
├── README.md              # Project documentation
└── SWEEP.md               # This file
```

## Implementation Details

### Core Algorithm
- Uses longest common subsequence (LCS) algorithm for diff computation
- Implements sequence matching with grouped opcodes
- Supports context lines (default: 3)
- Handles edge cases like identical sequences and empty inputs

### Known Issues
1. **Identical sequences**: Currently returns diff output instead of empty list
2. **Range formatting**: Some hunk header ranges don't match Python's exactly

### Test Coverage
- Basic functionality tests ✅
- Edge cases (empty, identical sequences) ⚠️ 
- Random data validation against Python's difflib ⚠️
- Known examples from Python documentation ✅
- File date handling ✅
- Custom line terminators ✅

## Debugging Commands
```bash
# Compare outputs between Rust and Python implementations
python3 -c "
from difflib_rst import unified_diff as rust_unified_diff
import difflib

a = ['line1', 'line2', 'line3']
rust_result = rust_unified_diff(a, a, 'a', 'b')
python_result = list(difflib.unified_diff(a, a, 'a', 'b'))

print('Rust result:', rust_result)
print('Python result:', python_result)
"

# Check Rust compilation
cargo check --manifest-path Cargo.toml
```

## Performance Notes

### Benchmark Results Summary
Based on comprehensive benchmarking (`tests/test_benchmark.py`):

**Where Rust Excels:**
- **Identical sequences**: 4.9x faster than Python
- **Completely different files**: 2.6x faster than Python
- **Small files with many changes**: Competitive performance

**Where Python's difflib is Faster:**
- **Small changes in large files**: Python is 20-78x faster (critical performance gap)
- **Medium-sized files with small changes**: Python is 2-4x faster
- **General use cases**: Python's implementation is highly optimized

### Key Findings
- The Rust implementation has O(n²) or worse scaling for small changes in large files
- Python's difflib uses optimizations that the Rust version currently lacks
- PyO3 overhead affects small datasets but is negligible for large ones
- Both implementations produce nearly identical results (within 10 lines difference)

## Future Improvements
- Fix identical sequence handling to return empty list
- Improve range formatting to exactly match Python's output
- Add benchmarking suite to measure performance gains
- Consider adding more difflib functions (context_diff, etc.)