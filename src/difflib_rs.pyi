"""Type stubs for difflib_rs - Rust implementation of Python's difflib.unified_diff"""

from typing import List, Optional

def unified_diff(
    a: List[str],
    b: List[str],
    fromfile: str = "",
    tofile: str = "",
    fromfiledate: str = "",
    tofiledate: str = "",
    n: int = 3,
    lineterm: str = "\n"
) -> List[str]:
    """
    Compare two sequences of lines; generate the unified diff.
    
    Args:
        a: First sequence of lines
        b: Second sequence of lines
        fromfile: Name of the first file
        tofile: Name of the second file
        fromfiledate: Timestamp for the first file
        tofiledate: Timestamp for the second file
        n: Number of context lines
        lineterm: Line terminator string
    
    Returns:
        Generator-like list of diff lines
    """
    ...

def unified_diff_str(
    a: str,
    b: str,
    fromfile: str = "",
    tofile: str = "",
    fromfiledate: str = "",
    tofiledate: str = "",
    n: int = 3,
    lineterm: str = "\n",
    keepends: bool = False
) -> List[str]:
    """
    Compare two strings; generate the unified diff.
    
    This is a convenience function that handles string splitting internally,
    providing better performance than splitting in Python.
    
    Args:
        a: First string to compare
        b: Second string to compare
        fromfile: Name of the first file
        tofile: Name of the second file
        fromfiledate: Timestamp for the first file
        tofiledate: Timestamp for the second file
        n: Number of context lines
        lineterm: Line terminator string
        keepends: Whether to keep line endings when splitting
    
    Returns:
        Generator-like list of diff lines
    """
    ...