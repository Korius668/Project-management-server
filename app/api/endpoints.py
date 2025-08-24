from fastapi import (
    FastAPI,
    APIRouter,
    status
)
from fastapi.responses import Response


auth=APIRouter(prefix="/auth", tags=["auth"])
projects=APIRouter(prefix="/projects", tags=["projects"])
documents=APIRouter(prefix="/documents", tags=["documents"])


# /auth
@auth.post("/sign_up")
def sign_up():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@auth.post("/login")
def login():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)

# /projects
@projects.get("/")
def get_projects():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@projects.get("/{project_id}/info")
def get_project_info():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@projects.put("/{project_id}/info")
def update_project_info():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@projects.delete("/{project_id}")
def delete_project():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@projects.get("/{project_id}/documents")
def list_project_documents():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@projects.post("/{project_id}/documents")
def upload_documents():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@projects.post("/{project_id}/invite")
def invite_user_to_project():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)

#   /documents
@documents.get("/{document_id}")
def download_document():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@documents.put("/{document_id}")
def update_document():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@documents.delete("/{document_id}")
def delete_document():
    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)


def get_application() -> FastAPI:
    """Application factory."""

    app = FastAPI(title="API Contract")

    # Routes
    app.include_router(auth)
    app.include_router(projects)
    app.include_router(documents)

    return app

app = get_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("app.api.endpoints:app", host="0.0.0.0", port=8000, reload=True) 