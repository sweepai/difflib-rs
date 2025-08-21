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

### Benchmark Results Summary (After Optimizations)
Based on comprehensive benchmarking (`tests/test_benchmark.py`):

**Rust Now Outperforms Python in ALL Scenarios:**

#### Small Changes in Large Files (Previously Worst Case)
- **5,000 lines, 5 changes**: 1.72x faster (was 0.75x slower)
- **10,000 lines, 5 changes**: 1.81x faster (was 0.54x slower)
- **20,000 lines, 5 changes**: 2.35x faster (was 0.45x slower)

#### Medium Changes in Large Files
- **5,000 lines, 250 changes**: 2.30x faster (was 0.68x slower)
- **10,000 lines, 500 changes**: 2.31x faster (was 0.42x slower)
- **20,000 lines, 1,000 changes**: 2.29x faster (was 0.21x slower)

#### Other Scenarios
- **Identical sequences**: 5.5x faster than Python
- **Small files (100-2000 lines)**: 1.5x-2.7x faster
- **Files with 50% changes**: 2.5x-2.8x faster

### Key Optimizations That Fixed Performance
1. **HashMap-based sparse representation** in `find_longest_match` (eliminated O(n²) memory operations)
2. **Queue-based approach** in `get_matching_blocks` (better cache locality)
3. **Proper memory management** (using move semantics instead of swap for HashMaps)

## Future Improvements
- Fix identical sequence handling to return empty list
- Improve range formatting to exactly match Python's output
- Add benchmarking suite to measure performance gains
- Consider adding more difflib functions (context_diff, etc.)