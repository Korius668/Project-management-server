from fastapi import APIRouter, status, Depends, UploadFile, File, Response
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from fastapi.security import HTTPAuthorizationCredentials

from app.usecases.projects import ProjectsService
from app.infrastructure.db.db import get_session
from app.usecases.security import token_to_user
from app.domain.models import User, ProjectRole
from app.api.schemas.responses import (
    ProjectResponse,
    MembershipResponse,
    UploadDocumentsResponse,
    DocumentResponse,    
)
from app.adapters.repositories.sqlalchemy.head_repository import SqlAlchemyRepository


from pydantic import BaseModel

class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    model_config = {
        "arbitrary_types_allowed": True
    }
    
class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model_config = {
        "arbitrary_types_allowed": True
    }

projects = APIRouter(prefix="/projects", tags=["projects"])

def get_projects_service(session: Session = Depends(get_session)) -> ProjectsService:
    return ProjectsService(SqlAlchemyRepository(session))


@projects.post("/", status_code=status.HTTP_201_CREATED, response_model=ProjectResponse)
def create_project(
    data: ProjectCreateRequest,
    user_id: UUID = Depends(token_to_user),
    service: ProjectsService = Depends(get_projects_service),
) -> ProjectResponse:
    return ProjectResponse.from_domain(service.create_project(data.name, data.description, user_id))


@projects.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    user_id: UUID = Depends(token_to_user),
    service: ProjectsService = Depends(get_projects_service),
) -> ProjectResponse:
    return ProjectResponse.from_domain(service.get_project(project_id, user_id))


@projects.get("/{project_id}/info")
def get_project_info(
    project_id: UUID,
    user_id: UUID = Depends(token_to_user),
    service: ProjectsService = Depends(get_projects_service),
    
):
    return service.get_project_info(project_id, user_id)


@projects.put("/{project_id}/info", response_model=ProjectResponse)
def update_project_info(
    project_id: UUID,
    data: ProjectUpdateRequest,
    user_id: UUID = Depends(token_to_user),
    service: ProjectsService = Depends(get_projects_service),
) ->  ProjectResponse:
    return ProjectResponse.from_domain(service.update_project(project_id, user_id, data.name, data.description))


@projects.delete("/{project_id}")
def delete_project(
    project_id: UUID,
    user_id: UUID = Depends(token_to_user),
    service: ProjectsService = Depends(get_projects_service),
):
    service.delete_project(project_id, user_id)
    return {"message": f"Project {project_id} has been successfully deleted"}


@projects.get("/{project_id}/documents")
def list_project_documents(
    project_id: UUID,
    service: ProjectsService = Depends(get_projects_service),
    user_id: UUID = Depends(token_to_user),
):
    docs = service.get_project_documents(project_id, user_id)
    return UploadDocumentsResponse(uploaded_documents= [DocumentResponse.from_domain(doc) for doc in docs], message = f"Documents of project {project_id}")


@projects.post("/{project_id}/documents", response_model=UploadDocumentsResponse)
async def upload_documents(
    project_id: UUID,
    files: List[UploadFile] = File(...),
    user_id: UUID = Depends(token_to_user),
    service: ProjectsService = Depends(get_projects_service),
) -> UploadDocumentsResponse:
    # Parse metadata if provided
    docs = await service.upload_project_documents(
            project_id=project_id,
            user_id=user_id,
            files=files
        )
    return UploadDocumentsResponse(uploaded_documents= [DocumentResponse.from_domain(doc) for doc in docs],  message = f"Documents of project {project_id}")


@projects.post("/{project_id}/invite", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED,)
def invite_user_to_project(
    project_id: UUID,
    target_id: UUID,
    role: str,
    user_id: UUID = Depends(token_to_user),
    service: ProjectsService = Depends(get_projects_service),
) -> MembershipResponse:
    
    return MembershipResponse.from_membership( 
        service.invite_user_to_project(project_id, user_id, target_id, role)
    )


@projects.put("/{project_id}/members/{target_id}/role", response_model=MembershipResponse)
def update_user_role(
    project_id: UUID,
    target_id: UUID,
    role: str,
    user_id: UUID = Depends(token_to_user),
    service: ProjectsService = Depends(get_projects_service),
    
) -> MembershipResponse:
   
    return MembershipResponse.from_membership( 
        service.update_user_role(project_id, user_id, target_id,ProjectRole(role))
    )

@projects.delete("/{project_id}/members/{target_id}")
def remove_user_from_project(
    project_id: UUID,
    target_id: UUID,
    user_id: UUID = Depends(token_to_user),
    service: ProjectsService = Depends(get_projects_service),
    
):
    service.remove_user_from_project(project_id, user_id, target_id)
    return {"message": f"User {target_id} has been successfully deleted from project {project_id}"}
