import pytest
import difflib
import random
import string
from difflib_rst import unified_diff as rust_unified_diff


def test_basic_sanity_check():
    """Basic sanity check with simple strings."""
    a = ['one', 'two', 'three', 'four']
    b = ['zero', 'one', 'tree', 'four']
    
    # Test that our function returns a list of strings
    result = rust_unified_diff(a, b, 'Original', 'Current')
    assert isinstance(result, list)
    assert all(isinstance(line, str) for line in result)
    
    # Should have header lines
    assert any('---' in line for line in result)
    assert any('+++' in line for line in result)
    assert any('@@' in line for line in result)


def test_empty_sequences():
    """Test with empty sequences."""
    # Both empty
    result = rust_unified_diff([], [], 'a', 'b')
    assert result == []
    
    # One empty
    result = rust_unified_diff(['line1'], [], 'a', 'b')
    assert len(result) > 0
    
    result = rust_unified_diff([], ['line1'], 'a', 'b')
    assert len(result) > 0


def test_identical_sequences():
    """Test with identical sequences."""
    a = ['line1', 'line2', 'line3']
    result = rust_unified_diff(a, a, 'a', 'b')
    assert result == []


def test_simple_addition():
    """Test simple line addition."""
    a = ['line1', 'line3']
    b = ['line1', 'line2', 'line3']
    
    result = rust_unified_diff(a, b, 'a', 'b')
    assert any('+line2' in line for line in result)


def test_simple_deletion():
    """Test simple line deletion."""
    a = ['line1', 'line2', 'line3']
    b = ['line1', 'line3']
    
    result = rust_unified_diff(a, b, 'a', 'b')
    assert any('-line2' in line for line in result)


def test_simple_replacement():
    """Test simple line replacement."""
    a = ['line1', 'old_line', 'line3']
    b = ['line1', 'new_line', 'line3']
    
    result = rust_unified_diff(a, b, 'a', 'b')
    assert any('-old_line' in line for line in result)
    assert any('+new_line' in line for line in result)


def test_with_dates():
    """Test with file dates."""
    a = ['line1']
    b = ['line2']
    
    result = rust_unified_diff(
        a, b, 'file1.txt', 'file2.txt', 
        '2023-01-01 10:00:00', '2023-01-02 11:00:00'
    )
    
    # Should include dates in header
    header_lines = [line for line in result if line.startswith('---') or line.startswith('+++')]
    assert any('2023-01-01 10:00:00' in line for line in header_lines)
    assert any('2023-01-02 11:00:00' in line for line in header_lines)


def test_custom_lineterm():
    """Test with custom line terminator."""
    a = ['line1']
    b = ['line2']
    
    result = rust_unified_diff(a, b, 'a', 'b', lineterm='')
    # When lineterm is empty, lines shouldn't end with newlines
    for line in result:
        if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
            assert not line.endswith('\n')


def generate_random_lines(n: int, max_length: int = 20) -> list[str]:
    """Generate random lines for testing."""
    lines = []
    for _ in range(n):
        length = random.randint(1, max_length)
        line = ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))
        lines.append(line)
    return lines


def normalize_diff_output(lines: list[str]) -> list[str]:
    """Normalize diff output for comparison by removing trailing whitespace and newlines."""
    normalized = []
    for line in lines:
        # Remove trailing newlines and whitespace for comparison
        normalized.append(line.rstrip('\n').rstrip())
    return normalized


@pytest.mark.parametrize("seed", range(10))
def test_against_python_builtin_random(seed):
    """Test against Python's built-in difflib with random data."""
    random.seed(seed)
    
    # Generate random sequences
    a_len = random.randint(1, 20)
    b_len = random.randint(1, 20)
    
    a = generate_random_lines(a_len)
    b = generate_random_lines(b_len)
    
    # Get results from both implementations
    python_result = list(difflib.unified_diff(
        a, b, 'file_a', 'file_b', 
        '2023-01-01', '2023-01-02', 
        n=3, lineterm='\n'
    ))
    
    rust_result = rust_unified_diff(
        a, b, 'file_a', 'file_b',
        '2023-01-01', '2023-01-02',
        n=3, lineterm='\n'
    )
    
    # Normalize both results for comparison
    python_normalized = normalize_diff_output(python_result)
    rust_normalized = normalize_diff_output(rust_result)
    
    # They should have the same number of lines
    assert len(python_normalized) == len(rust_normalized), f"Length mismatch: Python={len(python_normalized)}, Rust={len(rust_normalized)}"
    
    # Compare line by line (allowing for minor formatting differences)
    for i, (py_line, rust_line) in enumerate(zip(python_normalized, rust_normalized)):
        # For content lines, they should be identical
        if py_line.startswith(('+', '-', ' ')):
            assert py_line == rust_line, f"Line {i} differs: Python='{py_line}', Rust='{rust_line}'"
        # For header lines, check they have the same structure
        elif py_line.startswith(('---', '+++')):
            assert py_line.split('\t')[0] == rust_line.split('\t')[0], f"Header {i} differs: Python='{py_line}', Rust='{rust_line}'"
        # For hunk headers, check they have the same ranges
        elif py_line.startswith('@@'):
            # Extract the ranges from both
            py_ranges = py_line.split('@@')[1].strip()
            rust_ranges = rust_line.split('@@')[1].strip()
            assert py_ranges == rust_ranges, f"Hunk header {i} differs: Python='{py_ranges}', Rust='{rust_ranges}'"


def test_known_examples():
    """Test with known examples from Python documentation."""
    # Example from Python docs
    a = 'one two three four'.split()
    b = 'zero one tree four'.split()
    
    python_result = list(difflib.unified_diff(
        a, b, 'Original', 'Current',
        '2005-01-26 23:30:50', '2010-04-02 10:20:52',
        lineterm=''
    ))
    
    rust_result = rust_unified_diff(
        a, b, 'Original', 'Current',
        '2005-01-26 23:30:50', '2010-04-02 10:20:52',
        lineterm=''
    )
    
    # Normalize and compare
    python_normalized = normalize_diff_output(python_result)
    rust_normalized = normalize_diff_output(rust_result)
    
    assert len(python_normalized) == len(rust_normalized)
    
    # Check that we have the expected changes
    rust_content = '\n'.join(rust_normalized)
    assert '+zero' in rust_content
    assert '-two' in rust_content
    assert '-three' in rust_content
    assert '+tree' in rust_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])