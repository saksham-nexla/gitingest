"""Reusable form type aliases for FastAPI form parameters."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List

from fastapi import Form

from gitingest.utils.compat_typing import Annotated
from gitingest.utils.comment_removal import CommentType

if TYPE_CHECKING:
    from gitingest.utils.compat_typing import TypeAlias

StrForm: TypeAlias = Annotated[str, Form(...)]
IntForm: TypeAlias = Annotated[int, Form(...)]
OptStrForm: TypeAlias = Annotated[Optional[str], Form()]

def QueryForm(
    input_text: str = Form(..., description="Git repository URL or slug"),
    token: Optional[str] = Form(None, description="GitHub PAT for private repos"),
    max_file_size: int = Form(243, description="Maximum file size slider position"),
    pattern_type: str = Form("exclude", description="File filter pattern type"),
    pattern: str = Form("", description="File filter glob pattern"),
    remove_comments: bool = Form(False, description="Remove comments from files"),
    comment_types: List[str] = Form(["all"], description="Comment types to remove"),
):
    # Convert list of string comment types to set of CommentType enums
    try:
        parsed_comment_types = {CommentType(ct) for ct in comment_types}
    except ValueError as e:
        # Re-raise with a more informative message if an invalid type is provided
        raise ValueError(f"Invalid comment_type provided: {e}") from e

    return {
        "input_text": input_text,
        "token": token,
        "max_file_size": max_file_size,
        "pattern_type": pattern_type,
        "pattern": pattern,
        "remove_comments": remove_comments,
        "comment_types": parsed_comment_types,
    }
