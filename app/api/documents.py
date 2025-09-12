from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from fastapi.responses import Response, StreamingResponse
from uuid import UUID
from typing import Optional, Dict, Any
from pydantic import BaseModel


from app.usecases.documents import DocumentsService
from app.infrastructure.db.db import get_session
from app.adapters.repositories.sqlalchemy.head_repository import SqlAlchemyRepository
from app.api.schemas.responses import DocumentResponse
from app.usecases.security import token_to_user


class DocumentUpdateRequest(BaseModel):
    filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    model_config = {"arbitrary_types_allowed": True}


documents = APIRouter(prefix="/documents", tags=["documents"])


def get_documents_service(session=Depends(get_session)) -> DocumentsService:
    """Dependency injection for DocumentsService."""
    return DocumentsService(SqlAlchemyRepository(session))


@documents.get("/{document_id}", response_model=None)
async def download_document(  # Implemented download endpoint
    document_id: UUID,
    user_id: UUID = Depends(token_to_user),
    service: DocumentsService = Depends(get_documents_service),
) -> StreamingResponse:
    """Download/get document details."""

    file, document = await service.download_document(document_id, user_id)

    async def generate_chunks():
        file.seek(0)
        while True:
            chunk = file.read(8192)  # Read 8KB chunks
            if not chunk:
                break
            yield chunk
        file.close()

    headers = {"Content-Disposition": f'attachment; filename="{document.filename}"'}
    return StreamingResponse(
        generate_chunks(), media_type="application/octet-stream", headers=headers
    )


@documents.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=DocumentResponse
)
async def upload_document(
    project_id: UUID = Form(...),
    user_id: UUID = Depends(token_to_user),
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    service: DocumentsService = Depends(get_documents_service),
) -> DocumentResponse:
    """Upload a new document file to a project."""
    document = await service.upload_document(
        project_id=project_id,
        user_id=user_id,
        file=file,
        name=name,
        description=description,
    )

    return DocumentResponse.from_domain(document)


@documents.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    update_data: DocumentUpdateRequest,
    document_id: UUID,
    user_id: UUID = Depends(token_to_user),
    service: DocumentsService = Depends(get_documents_service),
) -> DocumentResponse:
    """Update document metadata."""
    document = service.update_document(
        document_id=document_id,
        user_id=user_id,
        filename=update_data.filename,
        metadata=update_data.metadata,
    )
    return DocumentResponse.from_domain(document)


@documents.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(  # Implemented delete endpoint
    document_id: UUID,
    user_id: UUID = Depends(token_to_user),
    service: DocumentsService = Depends(get_documents_service),
):
    """Delete a document."""
    await service.delete_document(document_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
