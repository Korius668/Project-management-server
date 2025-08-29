from fastapi import APIRouter, status
from fastapi.responses import Response

documents = APIRouter(prefix="/documents", tags=["documents"])


@documents.get("/{document_id}")
def download_document():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@documents.put("/{document_id}")
def update_document():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@documents.delete("/{document_id}")
def delete_document():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)
