from fastapi import APIRouter, status
from fastapi.responses import Response

projects=APIRouter(prefix="/projects", tags=["projects"])

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