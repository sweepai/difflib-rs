import pytest
import difflib
import random
import string
from difflib_rs import unified_diff as rust_unified_diff


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


def test_output_identical_to_python():
    """Test that output is exactly identical to Python's difflib."""
    test_cases = [
        # Simple addition
        (['line1', 'line3'], ['line1', 'line2', 'line3']),
        # Simple deletion  
        (['line1', 'line2', 'line3'], ['line1', 'line3']),
        # Simple replacement
        (['line1', 'old', 'line3'], ['line1', 'new', 'line3']),
        # Empty to non-empty
        ([], ['line1', 'line2']),
        # Non-empty to empty
        (['line1', 'line2'], []),
        # Identical sequences
        (['line1', 'line2'], ['line1', 'line2']),
        # Complex changes
        (['a', 'b', 'c', 'd', 'e'], ['a', 'x', 'c', 'y', 'e']),
        # Large unchanged context
        (['1', '2', '3', '4', '5', 'change_me', '7', '8', '9', '10'],
         ['1', '2', '3', '4', '5', 'changed', '7', '8', '9', '10']),
    ]
    
    for a, b in test_cases:
        # Test with various parameter combinations
        param_combinations = [
            ('file_a', 'file_b', '', '', 3, '\n'),
            ('original.txt', 'modified.txt', '2023-01-01', '2023-01-02', 3, '\n'),
            ('a', 'b', '', '', 0, '\n'),
            ('a', 'b', '', '', 5, '\n'),
            ('test', 'test', '', '', 3, ''),
        ]
        
        for fromfile, tofile, fromdate, todate, n, lineterm in param_combinations:
            python_result = list(difflib.unified_diff(
                a, b, fromfile, tofile, fromdate, todate, n, lineterm
            ))
            
            rust_result = rust_unified_diff(
                a, b, fromfile, tofile, fromdate, todate, n, lineterm
            )
            
            # Check that outputs are EXACTLY identical
            assert python_result == rust_result, (
                f"Output mismatch for a={a}, b={b}, params=({fromfile}, {tofile}, {fromdate}, {todate}, {n}, {lineterm!r})\n"
                f"Python: {python_result}\n"
                f"Rust: {rust_result}"
            )


@pytest.mark.parametrize("seed", range(20))
def test_against_python_builtin_random(seed):
    """Test against Python's built-in difflib with random data - exact match."""
    random.seed(seed)
    
    # Generate random sequences
    a_len = random.randint(0, 30)
    b_len = random.randint(0, 30)
    
    a = generate_random_lines(a_len) if a_len > 0 else []
    b = generate_random_lines(b_len) if b_len > 0 else []
    
    # Test with different context sizes
    for n in [0, 1, 3, 5, 10]:
        # Get results from both implementations
        python_result = list(difflib.unified_diff(
            a, b, 'file_a', 'file_b', 
            '2023-01-01', '2023-01-02', 
            n=n, lineterm='\n'
        ))
        
        rust_result = rust_unified_diff(
            a, b, 'file_a', 'file_b',
            '2023-01-01', '2023-01-02',
            n=n, lineterm='\n'
        )
        
        # They should be EXACTLY identical
        assert python_result == rust_result, (
            f"Output mismatch for seed={seed}, n={n}\n"
            f"a={a}\n"
            f"b={b}\n"
            f"Python result ({len(python_result)} lines): {python_result}\n"
            f"Rust result ({len(rust_result)} lines): {rust_result}"
        )


def test_large_files_identical_output():
    """Test that large files produce identical output to Python's difflib."""
    random.seed(42)  # Fixed seed for reproducibility
    
    # Test various sizes that were benchmarked
    test_cases = [
        # (num_lines, num_changes, description)
        (100, 10, "Small file with 10% changes"),
        (500, 50, "Medium file with 10% changes"),
        (1000, 100, "Large file with 10% changes"),
        (2000, 200, "Larger file with 10% changes"),
        (5000, 5, "Large file with few changes"),
        (5000, 250, "Large file with 5% changes"),
        (1000, 500, "File with 50% changes"),
    ]
    
    for num_lines, num_changes, description in test_cases:
        # Generate base file
        base_lines = [f"Line {i:04d} - {'x' * (i % 10)}" for i in range(num_lines)]
        
        # Create modified version with specific number of changes
        modified_lines = base_lines.copy()
        change_indices = random.sample(range(num_lines), min(num_changes, num_lines))
        
        for idx in change_indices:
            if random.random() < 0.33:
                # Delete
                if idx < len(modified_lines):
                    modified_lines[idx] = None
            elif random.random() < 0.66:
                # Replace
                modified_lines[idx] = f"Modified line {idx:04d} - {'y' * (idx % 10)}"
            else:
                # Insert (by duplicating with modification)
                modified_lines[idx] = f"Inserted line {idx:04d} - {'z' * (idx % 10)}"
        
        # Remove None entries (deletions)
        modified_lines = [line for line in modified_lines if line is not None]
        
        # Test with different context sizes
        for n in [0, 3, 5]:
            python_result = list(difflib.unified_diff(
                base_lines, modified_lines,
                'original.txt', 'modified.txt',
                '2024-01-01', '2024-01-02',
                n=n, lineterm='\n'
            ))
            
            rust_result = rust_unified_diff(
                base_lines, modified_lines,
                'original.txt', 'modified.txt',
                '2024-01-01', '2024-01-02',
                n=n, lineterm='\n'
            )
            
            assert python_result == rust_result, (
                f"Output mismatch for {description}, n={n}\n"
                f"File size: {num_lines} lines, {num_changes} changes\n"
                f"Python result: {len(python_result)} lines\n"
                f"Rust result: {len(rust_result)} lines\n"
                f"First difference at line {next((i for i, (p, r) in enumerate(zip(python_result, rust_result)) if p != r), len(python_result))}"
            )


def test_edge_cases_identical_output():
    """Test edge cases to ensure identical output to Python's difflib."""
    test_cases = [
        # Very long identical prefix and suffix with small change in middle
        (
            ['same'] * 100 + ['old'] + ['same'] * 100,
            ['same'] * 100 + ['new'] + ['same'] * 100,
            "Long identical prefix and suffix"
        ),
        # Many small scattered changes
        (
            [f"line{i}" if i % 10 != 0 else f"old{i}" for i in range(100)],
            [f"line{i}" if i % 10 != 0 else f"new{i}" for i in range(100)],
            "Many small scattered changes"
        ),
        # All lines changed
        (
            [f"old{i}" for i in range(50)],
            [f"new{i}" for i in range(50)],
            "All lines changed"
        ),
        # Lines with special characters
        (
            ['normal', 'has\ttab', 'has\nnewline', 'has"quote', "has'quote", 'has\\backslash'],
            ['normal', 'no\ttab', 'no\nnewline', 'no"quote', "no'quote", 'no\\backslash'],
            "Special characters"
        ),
        # Empty lines
        (
            ['line1', '', 'line3', '', '', 'line6'],
            ['line1', '', '', 'line3', '', 'line6'],
            "Empty lines"
        ),
    ]
    
    for a, b, description in test_cases:
        # Test with various parameters
        for n in [0, 3, 5]:
            for lineterm in ['\n', '']:
                python_result = list(difflib.unified_diff(
                    a, b, 'a.txt', 'b.txt', '', '', n, lineterm
                ))
                
                rust_result = rust_unified_diff(
                    a, b, 'a.txt', 'b.txt', '', '', n, lineterm
                )
                
                assert python_result == rust_result, (
                    f"Output mismatch for edge case: {description}\n"
                    f"n={n}, lineterm={lineterm!r}\n"
                    f"Python: {len(python_result)} lines\n"
                    f"Rust: {len(rust_result)} lines"
                )


@pytest.mark.parametrize("n", [0, 1, 2, 3, 10])
@pytest.mark.parametrize("operation,a,b,description", [
    # Start insertions
    ("start_insert", ['line2', 'line3', 'line4'], ['NEW', 'line2', 'line3', 'line4'], "Start insertion"),
    ("start_insert_multiple", ['line3', 'line4'], ['NEW1', 'NEW2', 'line3', 'line4'], "Multiple start insertions"),
    
    # End insertions  
    ("end_insert", ['line1', 'line2', 'line3'], ['line1', 'line2', 'line3', 'NEW'], "End insertion"),
    ("end_insert_multiple", ['line1', 'line2'], ['line1', 'line2', 'NEW1', 'NEW2'], "Multiple end insertions"),
    
    # Middle insertions
    ("middle_insert", ['line1', 'line3'], ['line1', 'NEW', 'line3'], "Middle insertion"),
    ("middle_insert_multiple", ['line1', 'line4'], ['line1', 'NEW1', 'NEW2', 'NEW3', 'line4'], "Multiple middle insertions"),
    
    # Start deletions
    ("start_delete", ['OLD', 'line2', 'line3', 'line4'], ['line2', 'line3', 'line4'], "Start deletion"),
    ("start_delete_multiple", ['OLD1', 'OLD2', 'line3', 'line4'], ['line3', 'line4'], "Multiple start deletions"),
    
    # End deletions
    ("end_delete", ['line1', 'line2', 'line3', 'OLD'], ['line1', 'line2', 'line3'], "End deletion"),
    ("end_delete_multiple", ['line1', 'line2', 'OLD1', 'OLD2'], ['line1', 'line2'], "Multiple end deletions"),
    
    # Middle deletions
    ("middle_delete", ['line1', 'OLD', 'line3'], ['line1', 'line3'], "Middle deletion"),
    ("middle_delete_multiple", ['line1', 'OLD1', 'OLD2', 'OLD3', 'line5'], ['line1', 'line5'], "Multiple middle deletions"),
    
    # Complex scenarios
    ("start_and_end", ['OLD_START', 'line2', 'line3', 'OLD_END'], ['NEW_START', 'line2', 'line3', 'NEW_END'], "Start and end changes"),
    ("scattered_changes", ['A', 'OLD1', 'C', 'OLD2', 'E'], ['A', 'NEW1', 'C', 'NEW2', 'E'], "Scattered changes"),
    ("adjacent_changes", ['line1', 'OLD1', 'OLD2', 'line4'], ['line1', 'NEW1', 'NEW2', 'line4'], "Adjacent changes"),
    
    # Edge cases with context
    ("single_line_file", ['OLD'], ['NEW'], "Single line file"),
    ("two_line_file", ['line1', 'OLD'], ['line1', 'NEW'], "Two line file"),
    ("empty_to_content", [], ['line1', 'line2'], "Empty to content"),
    ("content_to_empty", ['line1', 'line2'], [], "Content to empty"),
])
def test_comprehensive_patterns_identical_output(n, operation, a, b, description):
    """Test various insertion/deletion patterns with different context sizes."""
    # Test with different line terminators and file parameters
    test_params = [
        ('a.txt', 'b.txt', '', '', '\n'),
        ('file1', 'file2', '2024-01-01', '2024-01-02', '\n'),
        ('original', 'modified', '', '', ''),
    ]
    
    for fromfile, tofile, fromdate, todate, lineterm in test_params:
        python_result = list(difflib.unified_diff(
            a, b, fromfile, tofile, fromdate, todate, n, lineterm
        ))
        
        rust_result = rust_unified_diff(
            a, b, fromfile, tofile, fromdate, todate, n, lineterm
        )
        
        assert python_result == rust_result, (
            f"Output mismatch for {operation} ({description}), n={n}, lineterm={lineterm!r}\n"
            f"Files: {fromfile} -> {tofile}\n"
            f"Sequences: {a} -> {b}\n"
            f"Python result ({len(python_result)} lines): {python_result}\n"
            f"Rust result ({len(rust_result)} lines): {rust_result}"
        )


@pytest.mark.parametrize("n", [0, 1, 2, 3, 5, 10])
def test_large_file_patterns_with_context(n):
    """Test large files with different patterns and context sizes."""
    base_size = 50
    base_lines = [f"line_{i:03d}" for i in range(base_size)]
    
    test_cases = [
        # Start region changes
        (base_lines, ['NEW_START'] + base_lines[1:], "Replace first line"),
        (base_lines, ['NEW1', 'NEW2'] + base_lines[2:], "Replace first two lines"),
        
        # End region changes  
        (base_lines, base_lines[:-1] + ['NEW_END'], "Replace last line"),
        (base_lines, base_lines[:-2] + ['NEW1', 'NEW2'], "Replace last two lines"),
        
        # Middle region changes
        (base_lines, base_lines[:25] + ['NEW_MID'] + base_lines[26:], "Replace middle line"),
        (base_lines, base_lines[:20] + ['NEW1', 'NEW2', 'NEW3'] + base_lines[23:], "Replace middle block"),
        
        # Multiple scattered changes
        (base_lines, 
         ['NEW_0'] + base_lines[1:10] + ['NEW_10'] + base_lines[11:20] + ['NEW_20'] + base_lines[21:],
         "Multiple scattered changes"),
        
        # Dense changes in small region
        (base_lines,
         base_lines[:15] + [f"CHANGED_{i}" for i in range(10)] + base_lines[25:],
         "Dense changes in middle"),
    ]
    
    for a, b, description in test_cases:
        python_result = list(difflib.unified_diff(
            a, b, 'original.txt', 'modified.txt', '2024-01-01', '2024-01-02', n, '\n'
        ))
        
        rust_result = rust_unified_diff(
            a, b, 'original.txt', 'modified.txt', '2024-01-01', '2024-01-02', n, '\n'
        )
        
        assert python_result == rust_result, (
            f"Output mismatch for large file test: {description}, n={n}\n"
            f"File size: {len(a)} -> {len(b)} lines\n"
            f"Python result: {len(python_result)} lines\n"
            f"Rust result: {len(rust_result)} lines\n"
            f"First difference at line: {next((i for i, (p, r) in enumerate(zip(python_result, rust_result)) if p != r), 'N/A')}"
        )


@pytest.mark.parametrize("num_changes", [1, 2, 3, 5, 10, 15, 20, 25, 30, 40, 50])
@pytest.mark.parametrize("n", [0, 3, 5])
def test_small_changes_in_1000_line_files(num_changes, n):
    """Test small numbers of changes (1-50) in 1000 line files with different context sizes."""
    file_size = 1000
    base_lines = [f"line_{i:04d}_content_here" for i in range(file_size)]
    
    # Test different change patterns
    change_patterns = [
        ("scattered", "Scattered changes throughout file"),
        ("clustered_start", "Changes clustered at start"),
        ("clustered_middle", "Changes clustered in middle"),
        ("clustered_end", "Changes clustered at end"),
        ("mixed_operations", "Mix of insertions, deletions, and replacements"),
    ]
    
    for pattern, description in change_patterns:
        modified_lines = base_lines.copy()
        
        if pattern == "scattered":
            # Evenly distribute changes throughout the file
            indices = [i * (file_size // (num_changes + 1)) for i in range(1, num_changes + 1)]
            for i, idx in enumerate(indices):
                if idx < len(modified_lines):
                    modified_lines[idx] = f"CHANGED_scattered_{i:02d}"
                    
        elif pattern == "clustered_start":
            # All changes in first part of file
            for i in range(min(num_changes, len(modified_lines))):
                modified_lines[i] = f"CHANGED_start_{i:02d}"
                
        elif pattern == "clustered_middle":
            # All changes in middle of file
            start_idx = file_size // 2 - num_changes // 2
            for i in range(num_changes):
                idx = start_idx + i
                if 0 <= idx < len(modified_lines):
                    modified_lines[idx] = f"CHANGED_middle_{i:02d}"
                    
        elif pattern == "clustered_end":
            # All changes at end of file
            start_idx = max(0, file_size - num_changes)
            for i in range(num_changes):
                idx = start_idx + i
                if idx < len(modified_lines):
                    modified_lines[idx] = f"CHANGED_end_{i:02d}"
                    
        elif pattern == "mixed_operations":
            # Mix of insertions, deletions, and replacements
            indices = [i * (file_size // (num_changes + 1)) for i in range(1, num_changes + 1)]
            for i, idx in enumerate(indices):
                if idx >= len(modified_lines):
                    continue
                    
                op_type = i % 3
                if op_type == 0:  # Replace
                    modified_lines[idx] = f"REPLACED_{i:02d}"
                elif op_type == 1:  # Delete (mark for deletion)
                    modified_lines[idx] = None
                else:  # Insert (duplicate and modify)
                    modified_lines[idx] = f"INSERTED_{i:02d}"
            
            # Remove None entries (deletions)
            modified_lines = [line for line in modified_lines if line is not None]
        
        # Test the pattern
        python_result = list(difflib.unified_diff(
            base_lines, modified_lines,
            'original_1000.txt', 'modified_1000.txt',
            '2024-01-01', '2024-01-02',
            n=n, lineterm='\n'
        ))
        
        rust_result = rust_unified_diff(
            base_lines, modified_lines,
            'original_1000.txt', 'modified_1000.txt',
            '2024-01-01', '2024-01-02',
            n=n, lineterm='\n'
        )
        
        assert python_result == rust_result, (
            f"Output mismatch for {description} in 1000-line file\n"
            f"Pattern: {pattern}, Changes: {num_changes}, Context: n={n}\n"
            f"File size: {len(base_lines)} -> {len(modified_lines)} lines\n"
            f"Python result: {len(python_result)} diff lines\n"
            f"Rust result: {len(rust_result)} diff lines\n"
            f"First difference at: {next((i for i, (p, r) in enumerate(zip(python_result, rust_result)) if p != r), 'N/A')}"
        )


@pytest.mark.parametrize("n", [0, 1, 2, 3, 10])  
def test_context_boundary_behavior(n):
    """Test behavior at context boundaries with different n values."""
    # Create a file where changes are exactly n lines apart
    lines = [f"line_{i:02d}" for i in range(20)]
    
    test_cases = [
        # Changes separated by exactly 2*n lines (should create separate hunks when n > 0)
        (lambda n: max(2, 2*n + 2), "Changes separated by 2*n+2 lines"),
        
        # Changes separated by exactly 2*n-1 lines (should merge hunks)  
        (lambda n: max(1, 2*n - 1) if n > 0 else 1, "Changes separated by 2*n-1 lines"),
        
        # Changes separated by exactly 2*n lines (boundary case)
        (lambda n: max(1, 2*n) if n > 0 else 1, "Changes separated by 2*n lines"),
    ]
    
    for gap_func, description in test_cases:
        gap = gap_func(n)
        if gap >= len(lines) - 2:
            continue  # Skip if gap is too large for our test data
            
        # Create two changes separated by 'gap' lines
        modified_lines = lines.copy()
        modified_lines[5] = "CHANGED_1"
        if 5 + gap + 1 < len(modified_lines):
            modified_lines[5 + gap + 1] = "CHANGED_2"
        
        python_result = list(difflib.unified_diff(
            lines, modified_lines, 'a.txt', 'b.txt', '', '', n, '\n'
        ))
        
        rust_result = rust_unified_diff(
            lines, modified_lines, 'a.txt', 'b.txt', '', '', n, '\n'
        )
        
        assert python_result == rust_result, (
            f"Context boundary test failed: {description}, n={n}, gap={gap}\n"
            f"Python result ({len(python_result)} lines): {python_result}\n"
            f"Rust result ({len(rust_result)} lines): {rust_result}"
        )


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
    
    # Check for exact match
    assert python_result == rust_result, (
        f"Output mismatch for Python docs example\n"
        f"Python result ({len(python_result)} lines): {python_result}\n"
        f"Rust result ({len(rust_result)} lines): {rust_result}"
    )
    
    # Also check that we have the expected changes
    rust_content = '\n'.join(rust_result)
    assert '+zero' in rust_content
    assert '-two' in rust_content
    assert '-three' in rust_content
    assert '+tree' in rust_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])