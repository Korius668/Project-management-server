from fastapi import (
    FastAPI,
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
    Security,
    UploadFile,
    status,
)
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4



auth=APIRouter(prefix="/auth", tags=["auth"])
projects=APIRouter(prefix="/projects", tags=["projects"])
documents=APIRouter(prefix="/documents", tags=["documents"])


from fastapi.responses import StreamingResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

app = FastAPI(
    title="Project Documents API",
    version="1.0.0",
    description="API for user authentication, project management, and document handling.",
)

# Security (JWT Bearer)
bearer_scheme = HTTPBearer(auto_error=True)


class AuthenticatedUser(BaseModel):
    user_id: UUID


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> AuthenticatedUser:
    # In a real implementation, validate JWT, verify expiration, and extract user_id
    token = credentials.credentials
    if not token or token == "expired":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    # Stub user_id extraction
    return AuthenticatedUser(user_id=uuid4())


# Shared response models
class ErrorResponse(BaseModel):
    detail: str = Field(..., examples=["Unauthorized"])


class MessageResponse(BaseModel):
    message: str


# Auth models
class SignUpRequest(BaseModel):
    login: str
    password: str


class LoginRequest(BaseModel):
    login: str
    password: str


class LoginResponse(BaseModel):
    jwt_token: str


# Project and Document models
class DocumentShort(BaseModel):
    id: UUID
    name: str
    uploaded_at: datetime


class DocumentListItem(BaseModel):
    id: UUID
    name: str
    size: int
    uploaded_at: datetime


class DocumentUpdate(BaseModel):
    name: Optional[str] = None


class DocumentDetail(BaseModel):
    id: UUID
    name: str
    size: int
    updated_at: datetime


class ProjectWithDocuments(BaseModel):
    id: UUID
    name: str
    description: str
    owner_id: UUID
    created_at: datetime
    documents: List[DocumentShort]


class ProjectInfo(BaseModel):
    id: UUID
    name: str
    description: str
    owner_id: UUID
    created_at: datetime


class ProjectUpdateRequest(BaseModel):
    name: str
    description: str


class ProjectUpdatedResponse(BaseModel):
    id: UUID
    name: str
    description: str
    owner_id: UUID
    updated_at: datetime


# /auth
@auth.post(
    "/sign_up",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
    responses={
        201: {"description": "Created"},
        400: {
            "description": "Bad Request – Login already exists.",
            "model": ErrorResponse,
        },
    },
)
def sign_up(payload: SignUpRequest):
    # Stub: return 201 Created with no content as per contract
    return Response(status_code=status.HTTP_201_CREATED)


@auth.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    tags=["auth"],
    summary="Authenticate user and receive JWT token",
    responses={
        200: {"description": "OK", "model": LoginResponse},
        401: {"description": "Unauthorized – Invalid credentials.", "model": ErrorResponse},
    },
)
def login(payload: LoginRequest):
    # Stub: Always return a fake token
    return LoginResponse(jwt_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ...FAKE...")


# /projects
@projects.get(
    "/",
    response_model=List[ProjectWithDocuments],
    summary="Get all projects accessible for the authenticated user",
    responses={
        200: {"description": "OK"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
    },
)
def get_projects(user: AuthenticatedUser = Depends(get_current_user)):
    example_project_id = uuid4()
    example_owner_id = uuid4()
    example_doc_id = uuid4()
    now = datetime(2025, 8, 11, 10, 0, 0, tzinfo=timezone.utc)
    uploaded = datetime(2025, 8, 11, 12, 0, 0, tzinfo=timezone.utc)
    return [
        ProjectWithDocuments(
            id=example_project_id,
            name="Project Alpha",
            description="Project description",
            owner_id=example_owner_id,
            created_at=now,
            documents=[
                DocumentShort(
                    id=example_doc_id,
                    name="design.pdf",
                    uploaded_at=uploaded,
                )
            ],
        )
    ]


@projects.get(
    "/{project_id}/info",
    response_model=ProjectInfo,
    summary="Return project details if the user has access",
    responses={
        200: {"description": "OK"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden", "model": ErrorResponse},
        404: {"description": "Not Found", "model": ErrorResponse},
    },
)
def get_project_info(
    project_id: UUID = Path(..., description="Project ID"),
    user: AuthenticatedUser = Depends(get_current_user),
):
    return ProjectInfo(
        id=project_id,
        name="Project Alpha",
        description="Detailed description",
        owner_id=uuid4(),
        created_at=datetime(2025, 8, 11, 10, 0, 0, tzinfo=timezone.utc),
    )


@projects.put(
    "/{project_id}/info",
    response_model=ProjectUpdatedResponse,
    summary="Update project name and description (Owner or users with edit rights)",
    responses={
        200: {"description": "OK"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden", "model": ErrorResponse},
        404: {"description": "Not Found", "model": ErrorResponse},
    },
)
def update_project_info(
    project_id: UUID = Path(..., description="Project ID"),
    payload: ProjectUpdateRequest = Body(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    return ProjectUpdatedResponse(
        id=project_id,
        name=payload.name,
        description=payload.description,
        owner_id=uuid4(),
        updated_at=datetime(2025, 8, 11, 12, 10, 0, tzinfo=timezone.utc),
    )


@projects.delete(
    "/{project_id}",
    response_model=MessageResponse,
    summary="Delete project and all associated documents (Only project owner)",
    responses={
        200: {"description": "OK", "model": MessageResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden", "model": ErrorResponse},
        404: {"description": "Not Found", "model": ErrorResponse},
    },
)
def delete_project(
    project_id: UUID = Path(..., description="Project ID"),
    user: AuthenticatedUser = Depends(get_current_user),
):
    return MessageResponse(message="Project deleted successfully")


@projects.get(
    "/{project_id}/documents",
    response_model=List[DocumentListItem],
    tags=["documents"],
    summary="Get all documents belonging to a project",
    responses={
        200: {"description": "OK"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden", "model": ErrorResponse},
        404: {"description": "Not Found", "model": ErrorResponse},
    },
)
def list_project_documents(
    project_id: UUID = Path(..., description="Project ID"),
    user: AuthenticatedUser = Depends(get_current_user),
):
    return [
        DocumentListItem(
            id=uuid4(),
            name="design.pdf",
            size=24576,
            uploaded_at=datetime(2025, 8, 11, 12, 0, 0, tzinfo=timezone.utc),
        )
    ]


@projects.post(
    "/{project_id}/documents",
    response_model=List[DocumentListItem],
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
    summary="Upload one or multiple documents to a project",
    responses={
        201: {"description": "Created"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden", "model": ErrorResponse},
        404: {"description": "Not Found", "model": ErrorResponse},
        415: {"description": "Unsupported Media Type", "model": ErrorResponse},
    },
)
def upload_documents(
    project_id: UUID = Path(..., description="Project ID"),
    files: List[UploadFile] = File(..., description="files[]"),
    user: AuthenticatedUser = Depends(get_current_user),
):
    now = datetime(2025, 8, 11, 12, 0, 0, tzinfo=timezone.utc)
    return [
        DocumentListItem(
            id=uuid4(),
            name=f.filename,
            size=24576,
            uploaded_at=now,
        )
        for f in files
    ]


@projects.post(
    "/{project_id}/invite",
    response_model=MessageResponse,
    summary="Grant a user access to a project (Only project owner)",
    responses={
        200: {"description": "OK", "model": MessageResponse},
        400: {"description": "Bad Request – User already has access", "model": ErrorResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden – Not project owner", "model": ErrorResponse},
        404: {"description": "Not Found – Project or user not found", "model": ErrorResponse},
    },
)
def invite_user_to_project(
    project_id: UUID = Path(..., description="Project ID"),
    user_login: str = Query(..., alias="user", description="Login of the user to grant access to"),
    user: AuthenticatedUser = Depends(get_current_user),
):
    # Response shape per contract
    # We wrap it in MessageResponse for message, but also include detail in message text
    return MessageResponse(message=f"Access granted | project_id={project_id} | granted_to={user_login}")


# /document
@documents.get(
    "/{document_id}",
    summary="Download a document if the user has access to its project",
    responses={
        200: {
            "description": "OK - Binary file stream",
            "content": {
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"},
                    "examples": {"download": {"summary": "Binary stream", "value": ""}},
                }
            },
            "headers": {
                "Content-Disposition": {
                    "description": 'attachment; filename="design.pdf"',
                    "schema": {"type": "string"},
                },
                "Content-Type": {
                    "description": "application/pdf (depends on file type)",
                    "schema": {"type": "string"},
                },
            },
        },
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden", "model": ErrorResponse},
        404: {"description": "Not Found", "model": ErrorResponse},
    },
)
def download_document(
    document_id: UUID = Path(..., description="Document ID"),
    user: AuthenticatedUser = Depends(get_current_user),
):
    # Stub: return empty stream with headers to illustrate docs
    content = b""
    return StreamingResponse(
        iter([content]),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="design.pdf"'},
    )


@documents.put(
    "/{document_id}",
    response_model=DocumentDetail,
    summary="Update document content or metadata",
    responses={
        200: {"description": "OK"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden", "model": ErrorResponse},
        404: {"description": "Not Found", "model": ErrorResponse},
    },
)
def update_document(
    document_id: UUID = Path(..., description="Document ID"),
    # Either upload a new file (multipart/form-data) or send JSON to rename
    file: Optional[UploadFile] = File(
        default=None, description="New file content (multipart/form-data)"
    ),
    meta: Optional[DocumentUpdate] = Body(
        default=None, description="Metadata update (JSON)"
    ),
    user: AuthenticatedUser = Depends(get_current_user),
):
    updated_name = meta.name if meta and meta.name else (file.filename if file else "updated_design.pdf")
    updated_size = 30000
    return DocumentDetail(
        id=document_id,
        name=updated_name,
        size=updated_size,
        updated_at=datetime(2025, 8, 11, 12, 30, 0, tzinfo=timezone.utc),
    )


@documents.delete(
    "/{document_id}",
    response_model=MessageResponse,
    summary="Delete document from its project",
    responses={
        200: {"description": "OK", "model": MessageResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden", "model": ErrorResponse},
        404: {"description": "Not Found", "model": ErrorResponse},
    },
)
def delete_document(
    document_id: UUID = Path(..., description="Document ID"),
    user: AuthenticatedUser = Depends(get_current_user),
):
    return MessageResponse(message="Document deleted successfully")
