"""Main entry point for ingesting a source and processing its contents."""

from __future__ import annotations

import asyncio
import shutil
import sys
import warnings
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from gitingest.clone import clone_repo
from gitingest.config import MAX_FILE_SIZE
from gitingest.ingestion import ingest_query
from gitingest.query_parser import IngestionQuery, parse_query
from gitingest.utils.auth import resolve_token
from gitingest.utils.ignore_patterns import load_ignore_patterns


async def ingest_async(
    source: str,
    *,
    max_file_size: int = MAX_FILE_SIZE,
    include_patterns: str | set[str] | None = None,
    exclude_patterns: str | set[str] | None = None,
    branch: str | None = None,
    tag: str | None = None,
    include_gitignored: bool = False,
    include_submodules: bool = False,
    token: str | None = None,
    output: str | None = None,
    remove_comments: bool = False,
    comment_types: set | None = None,
) -> tuple[str, str, str]:
    """Ingest a source and process its contents.

    This function analyzes a source (URL or local path), clones the corresponding repository (if applicable),
    and processes its files according to the specified query parameters. It returns a summary, a tree-like
    structure of the files, and the content of the files. The results can optionally be written to an output file.

    Parameters
    ----------
    source : str
        The source to analyze, which can be a URL (for a Git repository) or a local directory path.
    max_file_size : int
        Maximum allowed file size for file ingestion. Files larger than this size are ignored (default: 10 MB).
    include_patterns : str | set[str] | None
        Pattern or set of patterns specifying which files to include. If ``None``, all files are included.
    exclude_patterns : str | set[str] | None
        Pattern or set of patterns specifying which files to exclude. If ``None``, no files are excluded.
    branch : str | None
        The branch to clone and ingest (default: the default branch).
    tag : str | None
        The tag to clone and ingest. If ``None``, no tag is used.
    include_gitignored : bool
        If ``True``, include files ignored by ``.gitignore`` and ``.gitingestignore`` (default: ``False``).
    include_submodules : bool
        If ``True``, recursively include all Git submodules within the repository (default: ``False``).
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.
        Can also be set via the ``GITHUB_TOKEN`` environment variable.
    output : str | None
        File path where the summary and content should be written.
        If ``"-"`` (dash), the results are written to ``stdout``.
        If ``None``, the results are not written to a file.
    remove_comments : bool
        Whether to remove comments from processed files to reduce token count (default: ``False``).
    comment_types : set | None
        Set of comment types to remove (default: ``None``).

    Returns
    -------
    tuple[str, str, str]
        A tuple containing:
        - A summary string of the analyzed repository or directory.
        - A tree-like string representation of the file structure.
        - The content of the files in the repository or directory.

    """
    token = resolve_token(token)

    query: IngestionQuery = await parse_query(
        source=source,
        max_file_size=max_file_size,
        from_web=False,
        include_patterns=include_patterns,
        ignore_patterns=exclude_patterns,
        token=token,
    )

    if not include_gitignored:
        _apply_gitignores(query)

    if query.url:
        _override_branch_and_tag(query, branch=branch, tag=tag)

    query.include_submodules = include_submodules
    query.remove_comments = remove_comments
    if comment_types is not None:
        query.comment_types = comment_types

    async with _clone_repo_if_remote(query, token=token):
        summary, tree, content = ingest_query(query)
        await _write_output(tree, content=content, target=output)
        return summary, tree, content


def ingest(
    source: str,
    *,
    max_file_size: int = MAX_FILE_SIZE,
    include_patterns: str | set[str] | None = None,
    exclude_patterns: str | set[str] | None = None,
    branch: str | None = None,
    tag: str | None = None,
    include_gitignored: bool = False,
    include_submodules: bool = False,
    token: str | None = None,
    output: str | None = None,
    remove_comments: bool = False,
    comment_types: set | None = None,
) -> tuple[str, str, str]:
    """Provide a synchronous wrapper around ``ingest_async``.

    This function analyzes a source (URL or local path), clones the corresponding repository (if applicable),
    and processes its files according to the specified query parameters. It returns a summary, a tree-like
    structure of the files, and the content of the files. The results can optionally be written to an output file.

    Parameters
    ----------
    source : str
        The source to analyze, which can be a URL (for a Git repository) or a local directory path.
    max_file_size : int
        Maximum allowed file size for file ingestion. Files larger than this size are ignored (default: 10 MB).
    include_patterns : str | set[str] | None
        Pattern or set of patterns specifying which files to include. If ``None``, all files are included.
    exclude_patterns : str | set[str] | None
        Pattern or set of patterns specifying which files to exclude. If ``None``, no files are excluded.
    branch : str | None
        The branch to clone and ingest (default: the default branch).
    tag : str | None
        The tag to clone and ingest. If ``None``, no tag is used.
    include_gitignored : bool
        If ``True``, include files ignored by ``.gitignore`` and ``.gitingestignore`` (default: ``False``).
    include_submodules : bool
        If ``True``, recursively include all Git submodules within the repository (default: ``False``).
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.
        Can also be set via the ``GITHUB_TOKEN`` environment variable.
    output : str | None
        File path where the summary and content should be written.
        If ``"-"`` (dash), the results are written to ``stdout``.
        If ``None``, the results are not written to a file.

    Returns
    -------
    tuple[str, str, str]
        A tuple containing:
        - A summary string of the analyzed repository or directory.
        - A tree-like string representation of the file structure.
        - The content of the files in the repository or directory.

    See Also
    --------
    ``ingest_async`` : The asynchronous version of this function.

    """
    return asyncio.run(
        ingest_async(
            source=source,
            max_file_size=max_file_size,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            branch=branch,
            tag=tag,
            include_gitignored=include_gitignored,
            include_submodules=include_submodules,
            token=token,
            output=output,
            remove_comments=remove_comments,
            comment_types=comment_types,
        ),
    )


def _override_branch_and_tag(query: IngestionQuery, branch: str | None, tag: str | None) -> None:
    """Compare the caller-supplied ``branch`` and ``tag`` with the ones already in ``query``.

    If they differ, update ``query`` to the chosen values and issue a warning.
    If both are specified, the tag wins over the branch.

    Parameters
    ----------
    query : IngestionQuery
        The query to update.
    branch : str | None
        The branch to use.
    tag : str | None
        The tag to use.

    """
    if tag and query.tag and tag != query.tag:
        msg = f"Warning: The specified tag '{tag}' overrides the tag found in the URL '{query.tag}'."
        warnings.warn(msg, RuntimeWarning, stacklevel=3)

    query.tag = tag or query.tag

    if branch and query.branch and branch != query.branch:
        msg = f"Warning: The specified branch '{branch}' overrides the branch found in the URL '{query.branch}'."
        warnings.warn(msg, RuntimeWarning, stacklevel=3)

    query.branch = branch or query.branch

    if tag and branch:
        msg = "Warning: Both tag and branch are specified. The tag will be used."
        warnings.warn(msg, RuntimeWarning, stacklevel=3)

    # Tag wins over branch if both supplied
    if query.tag:
        query.branch = None


def _apply_gitignores(query: IngestionQuery) -> None:
    """Update ``query.ignore_patterns`` in-place.

    Parameters
    ----------
    query : IngestionQuery
        The query to update.

    """
    for fname in (".gitignore", ".gitingestignore"):
        query.ignore_patterns.update(load_ignore_patterns(query.local_path, filename=fname))


@asynccontextmanager
async def _clone_repo_if_remote(query: IngestionQuery, *, token: str | None) -> AsyncGenerator[None]:
    """Async context-manager that clones ``query.url`` if present.

    If ``query.url`` is set, the repo is cloned, control is yielded, and the temp directory is removed on exit.
    If no URL is given, the function simply yields immediately.

    Parameters
    ----------
    query : IngestionQuery
        Parsed query describing the source to ingest.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.

    """
    if query.url:
        clone_config = query.extract_clone_config()
        await clone_repo(clone_config, token=token)
        try:
            yield
        finally:
            shutil.rmtree(query.local_path.parent)
    else:
        yield


async def _write_output(tree: str, content: str, target: str | None) -> None:
    """Write combined output to ``target`` (``"-"`` ⇒ stdout).

    Parameters
    ----------
    tree : str
        The tree-like string representation of the file structure.
    content : str
        The content of the files in the repository or directory.
    target : str | None
        The path to the output file. If ``None``, the results are not written to a file.

    """
    data = f"{tree}\n{content}"
    loop = asyncio.get_running_loop()
    if target == "-":
        await loop.run_in_executor(None, sys.stdout.write, data)
        await loop.run_in_executor(None, sys.stdout.flush)
    elif target is not None:
        await loop.run_in_executor(None, Path(target).write_text, data, "utf-8")
