from typing import List, Optional
from uuid import UUID

from app.domain.models import Project, ProjectMembership, ProjectRole, Document
from fastapi import UploadFile 
from app.ports.head_repository import Repository


class ProjectsService:
    def __init__(self, repository: Repository):
        self.repository = repository

    def create_project(
        self, name: str, description: str, owner_id: UUID
    ) -> Project:
        """Create new project with user as owner."""
        return self.repository.create_project(name, description, owner_id)

    def get_project(self, project_id: UUID, user_id: UUID) -> Project:
        """Get project if user has access."""
        return self.repository.get_project(project_id, user_id)
    
    def get_project_info(self, project_id: UUID, user_id: UUID)-> dict:
        """Pobiera pełne informacje o projekcie z członkami i dokumentami."""
        return self.repository.get_project_info(project_id, user_id)

    def get_user_projects(self, user_id: UUID) -> List[Project]:
        """Get all user projects."""
        return self.repository.get_user_projects(user_id)

    def update_project( self, project_id: UUID, user_id: UUID, 
            name: Optional[str] = None, description: Optional[str] = None,
                    ) -> Project:
        """Aktualizuje projekt jeśli użytkownik ma uprawnienia.""" 
        return self.repository.update_project(project_id, user_id, name, description)

    def delete_project(self, project_id: UUID, user_id: UUID) -> None:
        """Usuwa projekt jeśli użytkownik jest właścicielem."""
        return self.repository.delete_project(project_id, user_id)

    def invite_user_to_project(self,    project_id: UUID,   inviter_id: UUID,   
            invited_user_id: UUID,  role: ProjectRole,
                                ) -> ProjectMembership:
        """Zaprasza użytkownika do projektu."""
        return self.repository.invite_user_to_project(project_id, inviter_id, invited_user_id, role)

    def update_user_role(self,  project_id: UUID,   updater_id: UUID,   target_user_id: UUID,
            new_role: ProjectRole
                        ) -> ProjectMembership:
        """Aktualizuje rolę użytkownika w projekcie."""
        return self.repository.update_user_role(project_id, updater_id, target_user_id, new_role)

    def remove_user_from_project(self, project_id: UUID, remover_id: UUID, target_user_id: UUID) -> bool:
        """Usuwa użytkownika z projektu."""
        return self.repository.remove_user_from_project(project_id, remover_id, target_user_id)
    
 
    async def upload_project_documents(self, project_id: UUID,  
            user_id: UUID,  files: List[UploadFile]
                                       ) -> List[Document]:
        """Upload multiple documents to a project using file storage port."""
        return await self.repository.upload_project_documents(project_id, user_id, files)

    def get_project_documents(self, project_id: UUID, user_id: UUID):
        """Pobiera dokumenty projektu."""
        return self.repository.get_project_documents(project_id, user_id)
