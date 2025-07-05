"""Pydantic models for the query form."""

from __future__ import annotations

from enum import Enum
from typing import Union, List

from pydantic import BaseModel, Field, field_validator

# needed for type checking (pydantic)
from server.form_types import IntForm, OptStrForm, StrForm  # noqa: TC001 (typing-only-first-party-import)


class PatternType(str, Enum):
    """Enumeration for pattern types used in file filtering."""

    INCLUDE = "include"
    EXCLUDE = "exclude"


class IngestRequest(BaseModel):
    """Request model for the /api/ingest endpoint.

    Attributes
    ----------
    input_text : str
        The Git repository URL or slug to ingest.
    max_file_size : int
        Maximum file size slider position (0-500) for filtering files.
    pattern_type : PatternType
        Type of pattern to use for file filtering (include or exclude).
    pattern : str
        Glob/regex pattern string for file filtering.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.
    remove_comments : bool
        Whether to remove comments from the processed files.
    comment_types : List[str]
        List of comment types to remove (single_line, multi_line, documentation, all).

    """

    input_text: str = Field(..., description="Git repository URL or slug to ingest")
    max_file_size: int = Field(..., ge=0, le=500, description="File size slider position (0-500)")
    pattern_type: PatternType = Field(default=PatternType.EXCLUDE, description="Pattern type for file filtering")
    pattern: str = Field(default="", description="Glob/regex pattern for file filtering")
    token: str | None = Field(default=None, description="GitHub PAT for private repositories")
    remove_comments: bool = Field(default=False, description="Whether to remove comments from processed files")
    comment_types: List[str] = Field(default=["all"], description="Types of comments to remove")

    @field_validator("input_text")
    @classmethod
    def validate_input_text(cls, v: str) -> str:
        """Validate that input_text is not empty."""
        if not v.strip():
            err = "input_text cannot be empty"
            raise ValueError(err)
        return v.strip()

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        """Validate pattern field."""
        return v.strip()


class IngestSuccessResponse(BaseModel):
    """Success response model for the /api/ingest endpoint.

    Attributes
    ----------
    repo_url : str
        The original repository URL that was processed.
    short_repo_url : str
        Short form of repository URL (user/repo).
    summary : str
        Summary of the ingestion process including token estimates.
    tree : str
        File tree structure of the repository.
    content : str
        Processed content from the repository files.
    default_max_file_size : int
        The file size slider position used.
    pattern_type : str
        The pattern type used for filtering.
    pattern : str
        The pattern used for filtering.
    remove_comments : bool
        Whether comments were removed from processed files.
    comment_types : List[str]
        Types of comments that were removed.

    """

    repo_url: str = Field(..., description="Original repository URL")
    short_repo_url: str = Field(..., description="Short repository URL (user/repo)")
    summary: str = Field(..., description="Ingestion summary with token estimates")
    tree: str = Field(..., description="File tree structure")
    content: str = Field(..., description="Processed file content")
    default_max_file_size: int = Field(..., description="File size slider position used")
    pattern_type: str = Field(..., description="Pattern type used")
    pattern: str = Field(..., description="Pattern used")
    remove_comments: bool = Field(..., description="Whether comments were removed")
    comment_types: List[str] = Field(..., description="Types of comments that were removed")


class IngestErrorResponse(BaseModel):
    """Error response model for the /api/ingest endpoint.

    Attributes
    ----------
    error : str
        Error message describing what went wrong.
    repo_url : str
        The repository URL that failed to process.

    """

    error: str = Field(..., description="Error message")
    repo_url: str = Field(..., description="Repository URL that failed")


# Union type for API responses
IngestResponse = Union[IngestSuccessResponse, IngestErrorResponse]
