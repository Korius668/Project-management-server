from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from pydantic import ValidationError

from app.domain.exceptions import (
    DomainError,
    DatabaseError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserDeletionForbiddenError,
    AuthenticationError,
    ProjectNotFoundError,
    ProjectAlreadyExistsError,
    DocumentAlreadyExistsError,
    DocumentNotFoundError,
    DocumentAlreadyExistsError,
    PermissionDeniedError,
    UserAlreadyMemberError,
    ProjectMembershipNotFoundError,
    InsufficientPermissionsError,
)

from app.logger.logger import logger


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        status_code = status.HTTP_400_BAD_REQUEST
        log_level = "warning"
        public_message = str(exc) or "Unknown domain error"

        if isinstance(
            exc,
            (
                UserAlreadyExistsError,
                UserAlreadyMemberError,
            ),
        ):
            status_code = status.HTTP_409_CONFLICT
        elif isinstance(exc, AuthenticationError):
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(
            exc,
            (
                UserNotFoundError,
                ProjectNotFoundError,
                DocumentNotFoundError,
                ProjectMembershipNotFoundError,
                PermissionDeniedError,
            ),
        ):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(
            exc,
            (
                UserDeletionForbiddenError,
                ProjectAlreadyExistsError,
                DocumentAlreadyExistsError,
            ),
        ):
            status_code = status.HTTP_409_CONFLICT
        elif isinstance(exc, InsufficientPermissionsError):
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, DatabaseError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.error(msg=f"{status_code} , {public_message}")

        return JSONResponse(status_code=status_code, content={"detail": public_message})

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        log_msg = f"[{request.method}] {request.url.path} → {exc.status_code} | HTTPException: {exc.detail}"
        logger.warning(log_msg)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        log_msg = f"[{request.method}] {request.url.path} → 422 | ValidationError: {exc.errors()}"
        logger.warning(log_msg)
        return JSONResponse(
            status_code=422,
            content={"detail": "Validation error", "errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        log_msg = f"[{request.method}] {request.url.path} → 500 | {type(exc).__name__}: {str(exc)}"
        logger.error(log_msg, exc_info=True)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )

    @app.exception_handler(ValidationError)
    async def pydantic_error(request: Request, exc: Exception):
        return JSONResponse(
            status_code=400, content={"detail": "Internal server error"}
        )
