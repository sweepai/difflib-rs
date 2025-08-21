import pytest
import difflib
import time
import random
import string
from difflib_rst import unified_diff as rust_unified_diff


def generate_large_text(num_lines: int, line_length: int = 80) -> list[str]:
    """Generate a large text with specified number of lines."""
    lines = []
    for _ in range(num_lines):
        line = ''.join(random.choices(string.ascii_letters + string.digits + ' .,!?', k=line_length))
        lines.append(line)
    return lines


def modify_text(lines: list[str], modification_ratio: float = 0.1) -> list[str]:
    """Modify a percentage of lines in the text."""
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
    
    return modified


def time_function(func, *args, **kwargs):
    """Time a function execution and return (result, elapsed_time)."""
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    return result, end_time - start_time


class TestBenchmark:
    """Benchmark tests comparing Rust vs Python implementations."""
    
    def setup_method(self):
        """Set up test data."""
        random.seed(42)  # For reproducible results
    
    @pytest.mark.parametrize("num_lines", [100, 500, 1000, 2000])
    def test_speed_comparison_small_changes(self, num_lines):
        """Compare speed with small changes (10% modification)."""
        # Generate test data
        original = generate_large_text(num_lines)
        modified = modify_text(original, modification_ratio=0.1)
        
        # Time Python implementation
        python_result, python_time = time_function(
            lambda: list(difflib.unified_diff(original, modified, 'original', 'modified'))
        )
        
        # Time Rust implementation
        rust_result, rust_time = time_function(
            rust_unified_diff, original, modified, 'original', 'modified'
        )
        
        # Calculate speedup
        speedup = python_time / rust_time if rust_time > 0 else float('inf')
        
        print(f"\n--- Benchmark Results ({num_lines} lines, 10% changes) ---")
        print(f"Python time: {python_time:.4f}s")
        print(f"Rust time:   {rust_time:.4f}s")
        print(f"Speedup:     {speedup:.2f}x")
        print(f"Python lines: {len(python_result)}")
        print(f"Rust lines:   {len(rust_result)}")
        
        # Verify results are similar (allow some differences in formatting)
        assert abs(len(python_result) - len(rust_result)) <= 10, "Results should be similar length"
        
        # Performance assertion - Rust should be competitive
        # (Allow Rust to be slower for small datasets due to overhead)
        if num_lines >= 1000:
            assert rust_time <= python_time * 5, f"Rust should be reasonably competitive for large datasets"
    
    @pytest.mark.parametrize("num_lines", [100, 500, 1000])
    def test_speed_comparison_large_changes(self, num_lines):
        """Compare speed with large changes (50% modification)."""
        # Generate test data
        original = generate_large_text(num_lines)
        modified = modify_text(original, modification_ratio=0.5)
        
        # Time Python implementation
        python_result, python_time = time_function(
            lambda: list(difflib.unified_diff(original, modified, 'original', 'modified'))
        )
        
        # Time Rust implementation
        rust_result, rust_time = time_function(
            rust_unified_diff, original, modified, 'original', 'modified'
        )
        
        # Calculate speedup
        speedup = python_time / rust_time if rust_time > 0 else float('inf')
        
        print(f"\n--- Benchmark Results ({num_lines} lines, 50% changes) ---")
        print(f"Python time: {python_time:.4f}s")
        print(f"Rust time:   {rust_time:.4f}s")
        print(f"Speedup:     {speedup:.2f}x")
        print(f"Python lines: {len(python_result)}")
        print(f"Rust lines:   {len(rust_result)}")
        
        # Verify results are similar
        assert abs(len(python_result) - len(rust_result)) <= 10, "Results should be similar length"
    
    def test_speed_identical_sequences(self):
        """Test speed with identical sequences (should be very fast)."""
        # Generate large identical sequences
        lines = generate_large_text(5000)
        
        # Time Python implementation
        python_result, python_time = time_function(
            lambda: list(difflib.unified_diff(lines, lines, 'a', 'b'))
        )
        
        # Time Rust implementation
        rust_result, rust_time = time_function(
            rust_unified_diff, lines, lines, 'a', 'b'
        )
        
        print(f"\n--- Identical Sequences Benchmark (5000 lines) ---")
        print(f"Python time: {python_time:.6f}s")
        print(f"Rust time:   {rust_time:.6f}s")
        print(f"Python result: {len(python_result)} lines")
        print(f"Rust result:   {len(rust_result)} lines")
        
        # Both should return empty results
        assert len(python_result) == 0
        assert len(rust_result) == 0
        
        # Rust should be very fast for identical sequences
        assert rust_time < 0.01, "Rust should handle identical sequences very quickly"
    
    def test_small_changes_large_files(self):
        """Test performance with small changes in very large files."""
        print("\n--- Small Changes in Large Files Benchmark ---")
        
        # Test different file sizes with minimal changes
        for num_lines in [5000, 10000, 20000]:
            # Generate large file
            original = generate_large_text(num_lines)
            modified = original.copy()
            
            # Make only 5 small changes (0.05% - 0.1% modification)
            num_changes = 5
            for i in range(num_changes):
                # Change a random line
                idx = random.randint(0, len(modified) - 1)
                modified[idx] = modified[idx][:40] + " MODIFIED " + modified[idx][40:]
            
            # Time Python implementation
            python_result, python_time = time_function(
                lambda: list(difflib.unified_diff(original, modified, 'original', 'modified'))
            )
            
            # Time Rust implementation
            rust_result, rust_time = time_function(
                rust_unified_diff, original, modified, 'original', 'modified'
            )
            
            # Calculate speedup
            speedup = python_time / rust_time if rust_time > 0 else float('inf')
            
            print(f"\n  {num_lines} lines, {num_changes} changes:")
            print(f"    Python time: {python_time:.4f}s")
            print(f"    Rust time:   {rust_time:.4f}s")
            print(f"    Speedup:     {speedup:.2f}x")
            print(f"    Diff size:   {len(python_result)} lines (Python), {len(rust_result)} lines (Rust)")
            
            # Verify results are similar
            assert abs(len(python_result) - len(rust_result)) <= 10, "Results should be similar length"
    
    def test_medium_changes_large_files(self):
        """Test performance with medium changes in large files."""
        print("\n--- Medium Changes in Large Files Benchmark ---")
        
        # Test different file sizes with medium changes (5% modification)
        for num_lines in [5000, 10000, 20000]:
            # Generate large file
            original = generate_large_text(num_lines)
            modified = original.copy()
            
            # Make medium number of changes (5% of lines)
            num_changes = int(num_lines * 0.05)
            for i in range(num_changes):
                # Change a random line
                idx = random.randint(0, len(modified) - 1)
                modified[idx] = modified[idx][:30] + " CHANGED " + modified[idx][30:]
            
            # Time Python implementation
            python_result, python_time = time_function(
                lambda: list(difflib.unified_diff(original, modified, 'original', 'modified'))
            )
            
            # Time Rust implementation
            rust_result, rust_time = time_function(
                rust_unified_diff, original, modified, 'original', 'modified'
            )
            
            # Calculate speedup
            speedup = python_time / rust_time if rust_time > 0 else float('inf')
            
            print(f"\n  {num_lines} lines, {num_changes} changes (5%):")
            print(f"    Python time: {python_time:.4f}s")
            print(f"    Rust time:   {rust_time:.4f}s")
            print(f"    Speedup:     {speedup:.2f}x")
            print(f"    Diff size:   {len(python_result)} lines (Python), {len(rust_result)} lines (Rust)")
            
            # Verify results are similar
            assert abs(len(python_result) - len(rust_result)) <= 50, "Results should be similar length"
    
    def test_memory_usage_large_diff(self):
        """Test with very large diffs to check memory efficiency."""
        # Generate large sequences
        original = generate_large_text(1000)
        # Create a completely different sequence
        modified = generate_large_text(1000)
        
        # Time both implementations
        python_result, python_time = time_function(
            lambda: list(difflib.unified_diff(original, modified, 'original', 'modified'))
        )
        
        rust_result, rust_time = time_function(
            rust_unified_diff, original, modified, 'original', 'modified'
        )
        
        print(f"\n--- Large Diff Benchmark (1000 vs 1000 completely different lines) ---")
        print(f"Python time: {python_time:.4f}s")
        print(f"Rust time:   {rust_time:.4f}s")
        print(f"Python lines: {len(python_result)}")
        print(f"Rust lines:   {len(rust_result)}")
        
        # Both should complete without errors
        assert len(python_result) > 0
        assert len(rust_result) > 0


if __name__ == "__main__":
    # Run benchmarks directly
    benchmark = TestBenchmark()
    benchmark.setup_method()
    
    print("Running speed benchmarks...")
    
    # Run a few key benchmarks
    benchmark.test_speed_comparison_small_changes(1000)
    benchmark.test_speed_comparison_large_changes(500)
    benchmark.test_speed_identical_sequences()
    benchmark.test_memory_usage_large_diff()
    
    print("\nBenchmarks completed!")