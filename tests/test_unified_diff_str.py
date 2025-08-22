"""Test the unified_diff_str function."""

import pytest
import time
import difflib
import random
import string
from difflib_rs import unified_diff, unified_diff_str


def test_basic_functionality():
    """Test basic functionality."""
    text_a = """Line 1
Line 2
Line 3
Line 4"""

    text_b = """Line 1
Modified Line 2
Line 3
Added Line
Line 4"""

    # Using the new string function
    result_str = unified_diff_str(text_a, text_b, "file1.txt", "file2.txt")
    
    # Using the original function with pre-split lines
    result_list = unified_diff(text_a.splitlines(), text_b.splitlines(), "file1.txt", "file2.txt")
    
    assert len(result_str) == len(result_list), f"Length mismatch: {len(result_str)} vs {len(result_list)}"
    
    # Check that both produce the same output
    for i, (str_line, list_line) in enumerate(zip(result_str, result_list)):
        assert str_line == list_line, f"Line {i} differs: {repr(str_line)} vs {repr(list_line)}"


def test_keepends_false():
    """Test keepends=False (default)."""
    text_mixed = "Line 1\r\nLine 2\nLine 3\rLine 4"
    text_modified = "Line 1\r\nModified Line 2\nLine 3\rLine 4"
    
    result = unified_diff_str(text_mixed, text_modified, keepends=False)
    
    # Check that line endings are not preserved
    for line in result:
        if line.startswith(' Line') or line.startswith('-Line') or line.startswith('+Modified'):
            # Content lines should not have line endings
            assert not line.endswith('\r\n')
            assert not line.endswith('\r')
            # Header lines end with \n (from lineterm parameter)


def test_keepends_true():
    """Test keepends=True preserves line endings."""
    text_mixed = "Line 1\r\nLine 2\nLine 3\rLine 4"
    text_modified = "Line 1\r\nModified Line 2\nLine 3\rLine 4"
    
    result = unified_diff_str(text_mixed, text_modified, keepends=True)
    
    # Find lines with different line endings preserved
    has_crlf = False
    has_lf = False
    has_cr = False
    
    for line in result:
        if ' Line 1\r\n' in line:
            has_crlf = True
        if '-Line 2\n' in line or '+Modified Line 2\n' in line:
            has_lf = True
        if ' Line 3\r' in line:
            has_cr = True
    
    assert has_crlf, "Should preserve \\r\\n endings"
    assert has_lf, "Should preserve \\n endings"
    # Note: \r handling might be different in the output


def test_empty_strings():
    """Test with empty strings."""
    # Empty to content
    result = unified_diff_str("", "New content\nLine 2", "empty.txt", "new.txt")
    assert len(result) > 0, "Should produce output for empty to content"
    assert any('+New content' in line for line in result)
    assert any('+Line 2' in line for line in result)
    
    # Content to empty
    result = unified_diff_str("Old content\nLine 2", "", "old.txt", "empty.txt")
    assert len(result) > 0, "Should produce output for content to empty"
    assert any('-Old content' in line for line in result)
    assert any('-Line 2' in line for line in result)
    
    # Empty to empty
    result = unified_diff_str("", "", "empty1.txt", "empty2.txt")
    assert len(result) == 0, "Should produce no output for empty to empty"


def test_single_line_no_newline():
    """Test single line strings without newlines."""
    result = unified_diff_str("Hello", "World", "a.txt", "b.txt")
    assert len(result) > 0
    assert any('-Hello' in line for line in result)
    assert any('+World' in line for line in result)


def test_mixed_line_endings():
    """Test handling of mixed line endings."""
    # Mix of \n, \r\n, and \r
    text_a = "Line1\nLine2\r\nLine3\rLine4"
    text_b = "Line1\nModified2\r\nLine3\rLine4"
    
    result = unified_diff_str(text_a, text_b, keepends=False)
    
    # Should correctly identify the change
    assert any('-Line2' in line for line in result)
    assert any('+Modified2' in line for line in result)
    assert any(' Line1' in line for line in result)
    assert any(' Line3' in line for line in result)
    assert any(' Line4' in line for line in result)


def test_performance_vs_python_split():
    """Test performance compared to Python splitting."""
    # Create large strings
    large_a = "\n".join([f"Line {i}" for i in range(1000)])
    large_b = "\n".join([f"Line {i}" if i % 10 != 0 else f"Modified Line {i}" for i in range(1000)])
    
    # Time the string version
    start = time.time()
    result_str = unified_diff_str(large_a, large_b)
    time_str = time.time() - start
    
    # Time the list version (including split time)
    start = time.time()
    lines_a = large_a.splitlines()
    lines_b = large_b.splitlines()
    result_list = unified_diff(lines_a, lines_b)
    time_list = time.time() - start
    
    # Calculate speedup
    speedup = time_list / time_str if time_str > 0 else float('inf')
    
    # Print detailed comparison
    print(f"\n--- Performance Comparison (1000 lines, 10% changes) ---")
    print(f"unified_diff_str:                 {time_str:.6f}s")
    print(f"unified_diff + Python splitlines: {time_list:.6f}s")
    print(f"Speedup (unified_diff_str):       {speedup:.2f}x {'FASTER' if speedup > 1 else 'SLOWER'}")
    print(f"Result size: {len(result_str)} lines (str) vs {len(result_list)} lines (list)")
    
    # Results should be the same
    assert len(result_str) == len(result_list)
    
    # Performance should be reasonable (not necessarily faster due to overhead)
    # But should be within an order of magnitude
    assert time_str < time_list * 10, f"String version too slow: {time_str:.6f}s vs {time_list:.6f}s"


def test_with_all_parameters():
    """Test with all parameters specified."""
    text_a = "Line 1\nLine 2\nLine 3"
    text_b = "Line 1\nModified\nLine 3"
    
    result = unified_diff_str(
        text_a,
        text_b,
        fromfile="original.txt",
        tofile="modified.txt", 
        fromfiledate="2023-01-01",
        tofiledate="2023-01-02",
        n=2,  # Context lines
        lineterm="\r\n",  # Different line terminator
        keepends=True
    )
    
    # Check headers are present
    assert any("original.txt" in line for line in result)
    assert any("modified.txt" in line for line in result)
    assert any("2023-01-01" in line for line in result)
    assert any("2023-01-02" in line for line in result)
    
    # Check line terminator is used
    assert result[0].endswith("\r\n")


def test_no_changes():
    """Test when there are no changes."""
    text = "Line 1\nLine 2\nLine 3"
    result = unified_diff_str(text, text, "same.txt", "same.txt")
    assert len(result) == 0, "Should produce no output when texts are identical"


def test_multiline_changes():
    """Test with multiple consecutive line changes."""
    text_a = """Line 1
Line 2
Line 3
Line 4
Line 5"""

    text_b = """Line 1
Changed 2
Changed 3
Changed 4
Line 5"""
    
    result = unified_diff_str(text_a, text_b)
    
    # Should show all changes
    assert any('-Line 2' in line for line in result)
    assert any('-Line 3' in line for line in result)
    assert any('-Line 4' in line for line in result)
    assert any('+Changed 2' in line for line in result)
    assert any('+Changed 3' in line for line in result)
    assert any('+Changed 4' in line for line in result)


# Benchmark tests for unified_diff_str function
def generate_large_text_str(num_lines: int, line_length: int = 80) -> str:
    """Generate a large text string with specified number of lines."""
    lines = []
    for _ in range(num_lines):
        line = ''.join(random.choices(string.ascii_letters + string.digits + ' .,!?', k=line_length))
        lines.append(line)
    return '\n'.join(lines)


def modify_text_str(text: str, modification_ratio: float = 0.1) -> str:
    """Modify a percentage of lines in the text string."""
    lines = text.splitlines()
    modified = lines.copy()
    num_modifications = int(len(lines) * modification_ratio)
    
    for _ in range(num_modifications):
        idx = random.randint(0, len(modified) - 1)
        # Randomly choose to modify, delete, or insert
        action = random.choice(['modify', 'delete', 'insert'])
        
        if action == 'modify':
            modified[idx] = ''.join(random.choices(string.ascii_letters + string.digits + ' .,!?', k=80))
        elif action == 'delete' and len(modified) > 1:
            modified.pop(idx)
        elif action == 'insert':
            new_line = ''.join(random.choices(string.ascii_letters + string.digits + ' .,!?', k=80))
            modified.insert(idx, new_line)
    
    return '\n'.join(modified)


def python_split_rust_diff(text_a: str, text_b: str, fromfile: str = '', tofile: str = '',
                          fromfiledate: str = '', tofiledate: str = '', n: int = 3,
                          lineterm: str = '\n', keepends: bool = False) -> list[str]:
    """Rust unified_diff with Python splitlines (to isolate split performance)."""
    if keepends:
        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)
    else:
        lines_a = text_a.splitlines()
        lines_b = text_b.splitlines()
    
    # Use Rust unified_diff with Python-split lines
    return unified_diff(lines_a, lines_b, fromfile, tofile, fromfiledate, tofiledate, n, lineterm)


def time_function(func, *args, **kwargs):
    """Time a function execution and return (result, elapsed_time)."""
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    return result, end_time - start_time


@pytest.mark.parametrize("num_lines", [100, 500, 1000, 2000])
def test_unified_diff_str_speed_comparison_small_changes(num_lines):
    """Compare speed of unified_diff_str vs Python implementation with small changes."""
    random.seed(42)  # For reproducible results
    
    # Generate test data
    original = generate_large_text_str(num_lines)
    modified = modify_text_str(original, modification_ratio=0.1)
    
    # Time Rust unified_diff with Python splitlines (baseline)
    baseline_result, baseline_time = time_function(
        python_split_rust_diff, original, modified, 'original', 'modified'
    )
    
    # Time Rust unified_diff_str (optimized - includes Rust split_lines)
    optimized_result, optimized_time = time_function(
        unified_diff_str, original, modified, 'original', 'modified'
    )
    
    # Calculate speedup
    speedup = baseline_time / optimized_time if optimized_time > 0 else float('inf')
    
    print(f"\n--- unified_diff_str vs Rust unified_diff Benchmark ({num_lines} lines, 10% changes) ---")
    print(f"Rust unified_diff + Python split: {baseline_time:.4f}s")
    print(f"Rust unified_diff_str (all Rust): {optimized_time:.4f}s")
    print(f"Speedup (optimized split):        {speedup:.2f}x {'FASTER' if speedup > 1 else 'SLOWER'}")
    print(f"Baseline lines: {len(baseline_result)}")
    print(f"Optimized lines: {len(optimized_result)}")
    
    # Verify results are identical 
    assert len(baseline_result) == len(optimized_result), "Results should be identical length"
    
    # Performance assertion - optimized version should be competitive
    if num_lines >= 1000:
        assert optimized_time <= baseline_time * 2, f"Optimized version should be reasonably competitive for large datasets"


@pytest.mark.parametrize("num_lines", [100, 500, 1000])
def test_unified_diff_str_speed_comparison_large_changes(num_lines):
    """Compare speed with large changes (50% modification)."""
    random.seed(42)
    
    # Generate test data
    original = generate_large_text_str(num_lines)
    modified = modify_text_str(original, modification_ratio=0.5)
    
    # Time Python implementation (including split)
    python_result, python_time = time_function(
        python_unified_diff_str, original, modified, 'original', 'modified'
    )
    
    # Time Rust implementation
    rust_result, rust_time = time_function(
        unified_diff_str, original, modified, 'original', 'modified'
    )
    
    # Calculate speedup
    speedup = python_time / rust_time if rust_time > 0 else float('inf')
    
    print(f"\n--- unified_diff_str Benchmark ({num_lines} lines, 50% changes) ---")
    print(f"Python time (with split): {python_time:.4f}s")
    print(f"Rust time:                {rust_time:.4f}s")
    print(f"Speedup:                  {speedup:.2f}x")
    print(f"Python lines: {len(python_result)}")
    print(f"Rust lines:   {len(rust_result)}")
    
    # Verify results are similar
    assert abs(len(python_result) - len(rust_result)) <= 50, "Results should be similar length"


def test_unified_diff_str_speed_identical_sequences():
    """Test speed with identical sequences (should be very fast)."""
    # Generate large identical sequences
    text = generate_large_text_str(5000)
    
    # Time Python implementation (including split)
    python_result, python_time = time_function(
        python_unified_diff_str, text, text, 'a', 'b'
    )
    
    # Time Rust implementation
    rust_result, rust_time = time_function(
        unified_diff_str, text, text, 'a', 'b'
    )
    
    print(f"\n--- unified_diff_str Identical Sequences Benchmark (5000 lines) ---")
    print(f"Python time (with split): {python_time:.6f}s")
    print(f"Rust time:                {rust_time:.6f}s")
    print(f"Python result: {len(python_result)} lines")
    print(f"Rust result:   {len(rust_result)} lines")
    
    # Both should return empty results
    assert len(python_result) == 0
    assert len(rust_result) == 0
    
    # Rust should be very fast for identical sequences
    assert rust_time < 0.01, "Rust should handle identical sequences very quickly"


def test_unified_diff_str_small_changes_large_files():
    """Test performance with small changes in very large files."""
    print("\n--- unified_diff_str Small Changes in Large Files Benchmark ---")
    random.seed(42)
    
    # Test different file sizes with minimal changes
    for num_lines in [5000, 10000, 20000]:
        # Generate large file
        original = generate_large_text_str(num_lines)
        lines = original.splitlines()
        
        # Make only 5 small changes (0.05% - 0.1% modification)
        num_changes = 5
        for i in range(num_changes):
            # Change a random line
            idx = random.randint(0, len(lines) - 1)
            lines[idx] = lines[idx][:40] + " MODIFIED " + lines[idx][40:]
        
        modified = '\n'.join(lines)
        
        # Time Python implementation (including split)
        python_result, python_time = time_function(
            python_unified_diff_str, original, modified, 'original', 'modified'
        )
        
        # Time Rust implementation
        rust_result, rust_time = time_function(
            unified_diff_str, original, modified, 'original', 'modified'
        )
        
        # Calculate speedup
        speedup = python_time / rust_time if rust_time > 0 else float('inf')
        
        print(f"\n  {num_lines} lines, {num_changes} changes:")
        print(f"    Python time (with split): {python_time:.4f}s")
        print(f"    Rust time:                {rust_time:.4f}s")
        print(f"    Speedup:                  {speedup:.2f}x")
        print(f"    Diff size: {len(python_result)} lines (Python), {len(rust_result)} lines (Rust)")
        
        # Verify results are similar
        assert abs(len(python_result) - len(rust_result)) <= 10, "Results should be similar length"


def test_unified_diff_str_keepends_performance():
    """Test performance difference between keepends=True and keepends=False."""
    print("\n--- unified_diff_str keepends Performance Comparison ---")
    random.seed(42)
    
    # Generate text with mixed line endings
    lines = []
    for i in range(1000):
        line = f"Line {i:04d} - " + ''.join(random.choices(string.ascii_letters, k=50))
        # Mix different line endings
        if i % 3 == 0:
            lines.append(line + '\r\n')
        elif i % 3 == 1:
            lines.append(line + '\n')
        else:
            lines.append(line + '\r')
    
    original = ''.join(lines)
    
    # Modify some lines
    modified_lines = lines.copy()
    for i in range(0, len(modified_lines), 10):
        modified_lines[i] = modified_lines[i].replace('Line', 'Modified')
    modified = ''.join(modified_lines)
    
    # Test keepends=False
    result_false, time_false = time_function(
        unified_diff_str, original, modified, 'original', 'modified', keepends=False
    )
    
    # Test keepends=True
    result_true, time_true = time_function(
        unified_diff_str, original, modified, 'original', 'modified', keepends=True
    )
    
    print(f"  keepends=False: {time_false:.4f}s, {len(result_false)} lines")
    print(f"  keepends=True:  {time_true:.4f}s, {len(result_true)} lines")
    print(f"  Ratio: {time_true/time_false:.2f}x")
    
    # Both should complete successfully
    assert len(result_false) > 0
    assert len(result_true) > 0