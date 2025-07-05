"""Utility module for removing comments from source code files."""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Set

from pygments import highlight
from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
from pygments.token import Comment
from pygments.formatters import NullFormatter


class CommentType(Enum):
    """Types of comments that can be removed."""
    
    SINGLE_LINE = "single_line"
    MULTI_LINE = "multi_line"
    DOCUMENTATION = "documentation"
    ALL = "all"


def get_lexer_for_file(file_path: Path):
    """Get a Pygments lexer for the given file."""
    try:
        # First try to get lexer by filename
        return get_lexer_for_filename(str(file_path))
    except Exception:
        # Fallback to extension-based detection
        extension = file_path.suffix.lstrip('.').lower()
        
        # Map common extensions to lexer names
        extension_map = {
            'py': 'python',
            'js': 'javascript', 
            'ts': 'typescript',
            'jsx': 'jsx',
            'tsx': 'tsx',
            'java': 'java',
            'c': 'c',
            'cpp': 'cpp',
            'cc': 'cpp',
            'cxx': 'cpp',
            'h': 'c',
            'hpp': 'cpp',
            'cs': 'csharp',
            'rb': 'ruby',
            'go': 'go',
            'rs': 'rust',
            'php': 'php',
            'swift': 'swift',
            'kt': 'kotlin',
            'scala': 'scala',
            'sh': 'bash',
            'bash': 'bash',
            'zsh': 'bash',
            'sql': 'sql',
            'html': 'html',
            'xml': 'xml',
            'css': 'css',
            'scss': 'scss',
            'sass': 'sass',
            'yml': 'yaml',
            'yaml': 'yaml',
            'json': 'json',
            'toml': 'toml',
            'ini': 'ini',
            'lua': 'lua',
            'r': 'r',
            'perl': 'perl',
            'pl': 'perl',
            'hs': 'haskell',
            'm': 'matlab',
            'asm': 'nasm',
        }
        
        lexer_name = extension_map.get(extension)
        if lexer_name:
            try:
                return get_lexer_by_name(lexer_name)
            except Exception:
                pass
    
    return None


def remove_comments_from_content(
    content: str,
    file_path: Path,
    comment_types: Set[CommentType] = {CommentType.ALL},
) -> str:
    """Remove comments from source code content using Pygments.
    
    Parameters
    ----------
    content : str
        The source code content to process
    file_path : Path
        The path to the file (used for language detection)
    comment_types : Set[CommentType]
        Types of comments to remove
        
    Returns
    -------
    str
        The content with comments removed
    """
    if not content.strip():
        return content
    
    # Get appropriate lexer
    lexer = get_lexer_for_file(file_path)
    if not lexer:
        return content
    
    # Expand ALL to include all comment types
    if CommentType.ALL in comment_types:
        comment_types = {CommentType.SINGLE_LINE, CommentType.MULTI_LINE, CommentType.DOCUMENTATION}
    
    try:
        # Tokenize the content
        tokens = list(lexer.get_tokens(content))
        
        # Filter out comment tokens based on comment_types
        filtered_tokens = []
        removed_chars = 0
        
        for token_type, token_value in tokens:
            should_remove = False
            
            if token_type in Comment:
                # Determine comment type based on token content and type
                if token_type == Comment.Single:
                    should_remove = CommentType.SINGLE_LINE in comment_types
                    comment_kind = "single-line"
                elif token_type == Comment.Multiline:
                    should_remove = CommentType.MULTI_LINE in comment_types
                    comment_kind = "multi-line"
                elif token_type in (Comment.Doc, Comment.DocTag):
                    should_remove = CommentType.DOCUMENTATION in comment_types
                    comment_kind = "documentation"
                elif token_type == Comment:
                    # Generic comment - check content to determine type
                    if any(marker in token_value for marker in ['"""', "'''", '/**', '///', '##']):
                        should_remove = CommentType.DOCUMENTATION in comment_types
                        comment_kind = "documentation"
                    elif '\n' in token_value or any(marker in token_value for marker in ['/*', '*/']):
                        should_remove = CommentType.MULTI_LINE in comment_types
                        comment_kind = "multi-line"
                    else:
                        should_remove = CommentType.SINGLE_LINE in comment_types
                        comment_kind = "single-line"
                else:
                    # Other comment subtypes - treat as single-line by default
                    should_remove = CommentType.SINGLE_LINE in comment_types
                    comment_kind = "single-line"
                
                if should_remove:
                    removed_chars += len(token_value)
                    # For multi-line comments, preserve line breaks to maintain line structure
                    if '\n' in token_value:
                        filtered_tokens.append((token_type, '\n' * token_value.count('\n')))
                else:
                    filtered_tokens.append((token_type, token_value))
            else:
                # Check if this might be a Python docstring (which Pygments treats as a string)
                if 'String' in str(token_type) and ('"""' in token_value or "'''" in token_value):
                    if CommentType.DOCUMENTATION in comment_types or CommentType.ALL in comment_types:
                        # Check if this looks like a docstring (string at start of function/class/module)
                        should_remove = True
                        comment_kind = "docstring"
                        
                        if should_remove:
                            removed_chars += len(token_value)
                            # Preserve line breaks for docstrings too
                            if '\n' in token_value:
                                filtered_tokens.append((token_type, '\n' * token_value.count('\n')))
                        else:
                            filtered_tokens.append((token_type, token_value))
                    else:
                        filtered_tokens.append((token_type, token_value))
                else:
                    filtered_tokens.append((token_type, token_value))
        
        # Reconstruct content from filtered tokens
        result = ''.join(token_value for _, token_value in filtered_tokens)
        
        return result
        
    except Exception as e:
        return content


def should_remove_comments(file_path: Path) -> bool:
    """Check if comments should be removed from this file type."""
    extension = file_path.suffix.lstrip('.').lower()
    
    # Skip binary files and files without known comment patterns
    binary_extensions = {
        'exe', 'dll', 'so', 'dylib', 'bin', 'img', 'jpg', 'jpeg', 'png', 
        'gif', 'bmp', 'ico', 'svg', 'pdf', 'zip', 'tar', 'gz', 'rar', '7z'
    }
    
    if extension in binary_extensions:
        return False
    
    # Check if we can get a lexer for this file
    lexer = get_lexer_for_file(file_path)
    return lexer is not None 