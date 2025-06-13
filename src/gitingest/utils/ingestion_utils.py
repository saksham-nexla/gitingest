"""Utility functions for the ingestion process."""

from fnmatch import fnmatch
from pathlib import Path
from typing import Set


def _should_include(path: Path, base_path: Path, include_patterns: Set[str]) -> bool:
    """
    Determine if the given file or directory path matches any of the include patterns.

    This function checks whether the relative path of a file or directory matches any of the specified patterns. If a
    match is found, it returns `True`, indicating that the file or directory should be included in further processing.

    The function handles both recursive (**) and non-recursive patterns differently:
    - For non-recursive patterns (e.g. "src/*.py"), files must match the exact pattern depth
    - For recursive patterns (e.g. "src/**/*.py"), files can match at any depth under the pattern prefix

    Directory matching has special handling:
    - For directories, we check if they could contain matching files based on the pattern
    - Patterns ending in /* are treated as matching any files in that directory
    - For non-recursive patterns, directories must match the exact pattern depth
    - For recursive patterns with **, directories are checked against the pattern prefix

    Parameters
    ----------
    path : Path
        The absolute path of the file or directory to check.
    base_path : Path
        The base directory from which the relative path is calculated.
    include_patterns : Set[str]
        A set of patterns to check against the relative path. Patterns can include:
        - * to match any characters except /
        - ** to match any characters including /
        - /* at the end to match any files in a directory

    Returns
    -------
    bool
        `True` if the path matches any of the include patterns, `False` otherwise.

    Raises
    ------
    ValueError
        If a non-recursive pattern is used and the directory depth exceeds the pattern depth.
        This indicates a traversal error since parent directories should have been filtered.

    Examples
    --------
    >>> _should_include(Path("/root/src/file.py"), Path("/root"), include_patterns={"src/*.py"})
    True
    >>> _should_include(Path("/root/src/nested/file.py"), Path("/root"), include_patterns={"src/**/*.py"})
    True
    >>> _should_include(Path("/root/src"), Path("/root"), include_patterns={"src/*"})
    True  # Directory matches as it could contain matching files

    # TODO: Fix bug where directories are included in the directory structure output when they should not be,
    #       e.g. atomics/**/Indexes-Markdown/*.md should not include atomics/Indexes/Attack-Navigator-Layers/
    #       or atomics/T1003.003/src/ for the repository https://github.com/redcanaryco/atomic-red-team.
    """
    try:
        rel_path = path.relative_to(base_path)
    except ValueError:
        # If path is not under base_path at all
        return False

    rel_str = str(rel_path)

    for pattern in include_patterns - {""}:  # ignore empty pattern
        if path.is_dir():
            # For directory traversal, check if the directory is part of the path that leads to matching files
            if pattern.endswith("/*"):
                # If the pattern ends with *, add a trailing * to the pattern to match any files in the directory
                pattern += "*"

            pattern_parts = pattern.split("/")
            dir_parts = rel_str.split("/")

            # For non-recursive patterns (no **), validate directory depth matches pattern depth
            # Recursive patterns can match directories at any depth
            if all(["**" not in pattern, len(pattern_parts) > 1, len(dir_parts) > len(pattern_parts)]):
                raise ValueError(
                    f"Directory '{rel_str}' has {len(dir_parts)} path segments but pattern '{pattern}' "
                    f"only has {len(pattern_parts)} segments. This indicates a traversal error since "
                    f"parent directories should have been filtered out by pattern matching."
                )

            relevant_pattern_length = (
                min(len(dir_parts), pattern_parts.index("**")) if "**" in pattern_parts else len(dir_parts)
            )
            pattern_prefix = "/".join(pattern_parts[:relevant_pattern_length])

            if "**" in pattern_parts:
                pattern_prefix += "*"

            if fnmatch(rel_str, pattern_prefix):
                return True
        else:
            if fnmatch(rel_str, pattern):
                return True

    return False


def _should_exclude(path: Path, base_path: Path, ignore_patterns: Set[str]) -> bool:
    """
    Determine if the given file or directory path matches any of the ignore patterns.

    This function checks whether the relative path of a file or directory matches
    any of the specified ignore patterns. If a match is found, it returns `True`, indicating
    that the file or directory should be excluded from further processing.

    TODO: Check if we need to handle exclude patterns with **, and if so, how.

    Parameters
    ----------
    path : Path
        The absolute path of the file or directory to check.
    base_path : Path
        The base directory from which the relative path is calculated.
    ignore_patterns : Set[str]
        A set of patterns to check against the relative path.

    Returns
    -------
    bool
        `True` if the path matches any of the ignore patterns, `False` otherwise.
    """
    try:
        rel_path = path.relative_to(base_path)
    except ValueError:
        # If path is not under base_path at all
        return True

    rel_str = str(rel_path)
    for pattern in ignore_patterns:
        if pattern and fnmatch(rel_str, pattern):
            return True
    return False
