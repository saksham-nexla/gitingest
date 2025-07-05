"""Ingest endpoint for the API."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from server.form_types import QueryForm
from server.models import IngestErrorResponse, IngestRequest, IngestSuccessResponse, PatternType
from server.query_processor import process_query
from server.server_utils import limiter

router = APIRouter()


@router.post(
    "/api/ingest",
    responses={
        status.HTTP_200_OK: {"model": IngestSuccessResponse, "description": "Successful ingestion"},
        status.HTTP_400_BAD_REQUEST: {"model": IngestErrorResponse, "description": "Bad request or processing error"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": IngestErrorResponse, "description": "Internal server error"},
    },
)
@limiter.limit("10/minute")
async def api_ingest(
    request: Request, form_data: dict = Depends(QueryForm)
) -> JSONResponse:
    """Ingest a Git repository and return processed content.

    This endpoint processes a Git repository by cloning it, analyzing its structure,
    and returning a summary with the repository's content. The response includes
    file tree structure, processed content, and metadata about the ingestion.

    Parameters
    ----------
    request : Request
        FastAPI request object
    form_data : dict
        Form data containing input parameters

    Returns
    -------
    JSONResponse
        Success response with ingestion results or error response with appropriate HTTP status code

    """
    repo_url = form_data.get("input_text", "Unknown")
    try:
        # Validate input using Pydantic model
        ingest_request = IngestRequest(
            input_text=repo_url,
            max_file_size=form_data["max_file_size"],
            pattern_type=PatternType(form_data["pattern_type"]),
            pattern=form_data["pattern"],
            token=form_data["token"],
            remove_comments=form_data["remove_comments"],
            comment_types=form_data["comment_types"],
        )

        result = await process_query(
            input_text=ingest_request.input_text,
            slider_position=ingest_request.max_file_size,
            pattern_type=ingest_request.pattern_type,
            pattern=ingest_request.pattern,
            token=ingest_request.token,
            remove_comments=ingest_request.remove_comments,
            comment_types=ingest_request.comment_types,
        )

        if isinstance(result, IngestErrorResponse):
            # Return structured error response with 400 status code
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=result.model_dump(),
            )

        # Return structured success response with 200 status code
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.model_dump(),
        )

    except ValueError as ve:
        # Handle validation errors with 400 status code
        error_response = IngestErrorResponse(
            error=f"Validation error: {ve!s}",
            repo_url=repo_url,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump(),
        )

    except Exception as exc:
        # Handle unexpected errors with 500 status code
        error_response = IngestErrorResponse(
            error=f"Internal server error: {exc!s}",
            repo_url=repo_url,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )
