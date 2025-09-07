from typing import List, Optional
from uuid import UUID

from app.domain.models import Project, ProjectMembership, ProjectRole
from app.domain.exceptions import (
    ProjectNotFoundError,
    UserNotFoundError,
    PermissionDeniedError,
    ProjectAlreadyExistsError,
    UserAlreadyMemberError,
    InsufficientPermissionsError,
)
from app.ports.repositories import (
    ProjectsRepository,
    UsersRepository,
    ProjectMembershipsRepository,
)


class ProjectsService:
    def __init__(
        self,
        projects_repo: ProjectsRepository,
        users_repo: UsersRepository,
        memberships_repo: ProjectMembershipsRepository,
    ):
        self.projects_repo = projects_repo
        self.users_repo = users_repo
        self.memberships_repo = memberships_repo

    def create_project(self, name: str, description: str, owner_id: UUID) -> Project:
        """Tworzy nowy projekt z użytkownikiem jako właścicielem."""
        owner = self.users_repo.get(owner_id)
        if not owner:
            raise UserNotFoundError(f"User with id {owner_id} not found")

        project = Project(name=name, description=description, owner_id=owner_id)
        created_project = self.projects_repo.add(project)

        membership = ProjectMembership(
            project_id=created_project.id,
            user_id=owner_id,
            role=ProjectRole.owner,  # Fixed enum value from OWNER to owner
        )
        self.memberships_repo.add(membership)

        return created_project

    def get_project(self, project_id: UUID, user_id: UUID) -> Project:
        """Pobiera projekt jeśli użytkownik ma do niego dostęp."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        membership = self.memberships_repo.get(project_id, user_id)
        if (
            not membership or membership.role == ProjectRole.viewer
        ):  # Fixed enum value from VIEWER to viewer
            raise PermissionDeniedError("You don't have access to this project")

        return project

    def get_user_projects(self, user_id: UUID) -> List[Project]:
        """Pobiera wszystkie projekty użytkownika."""
        user = self.users_repo.get(user_id)
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")

        memberships = self.memberships_repo.list_by_user(user_id)
        projects = []
        for membership in memberships:
            project = self.projects_repo.get(membership.project_id)
            if project:
                projects.append(project)
        return projects

    def update_project(
        self,
        project_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Project:
        """Aktualizuje projekt jeśli użytkownik ma uprawnienia."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        membership = self.memberships_repo.get(project_id, user_id)
        if (
            not membership or membership.role == ProjectRole.viewer
        ):  # Fixed enum value from VIEWER to viewer
            raise PermissionDeniedError(
                "You don't have permission to edit this project"
            )

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description

        return self.projects_repo.update(project)

    def delete_project(self, project_id: UUID, user_id: UUID) -> None:
        """Usuwa projekt jeśli użytkownik jest właścicielem."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        membership = self.memberships_repo.get(project_id, user_id)
        if (
            not membership or membership.role != ProjectRole.owner
        ):  # Fixed enum value from VIEWER to viewer
            raise PermissionDeniedError(
                "You don't have permission to delete this project"
            )

        self.projects_repo.delete(project_id)

    def invite_user_to_project(
        self,
        project_id: UUID,
        inviter_id: UUID,
        invited_user_id: UUID,
        role: ProjectRole,
    ) -> ProjectMembership:
        """Zaprasza użytkownika do projektu."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        inviter_membership = self.memberships_repo.get(project_id, inviter_id)
        if (
            not inviter_membership or inviter_membership.role == ProjectRole.viewer
        ):  # Fixed enum value from VIEWER to viewer
            raise PermissionDeniedError("You don't have permission to invite users")

        invited_user = self.users_repo.get(invited_user_id)
        if not invited_user:
            raise UserNotFoundError(f"User with id {invited_user_id} not found")

        existing_membership = self.memberships_repo.get(project_id, invited_user_id)
        if existing_membership:
            raise UserAlreadyMemberError("User is already a member of this project")

        membership = ProjectMembership(
            project_id=project_id, user_id=invited_user_id, role=role
        )
        return self.memberships_repo.add(membership)

    def update_user_role(
        self,
        project_id: UUID,
        updater_id: UUID,
        target_user_id: UUID,
        newrole: ProjectRole,
    ) -> ProjectMembership:
        """Aktualizuje rolę użytkownika w projekcie."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        updater_membership = self.memberships_repo.get(project_id, updater_id)
        if (
            not updater_membership or updater_membership.role != ProjectRole.owner
        ):  # Fixed enum value from OWNER to owner
            raise InsufficientPermissionsError(
                "Only project owner can update user roles"
            )

        target_membership = self.memberships_repo.get(project_id, target_user_id)
        if not target_membership:
            raise UserNotFoundError("User is not a member of this project")

        if (
            target_membership.role == ProjectRole.owner
        ):  # Fixed enum value from OWNER to owner
            raise PermissionDeniedError("Cannot change owner role")

        target_membership.role = newrole
        return self.memberships_repo.update(target_membership)

    def remove_user_from_project(
        self, project_id: UUID, remover_id: UUID, target_user_id: UUID
    ) -> bool:
        """Usuwa użytkownika z projektu."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        remover_membership = self.memberships_repo.get(project_id, remover_id)
        if (
            not remover_membership or remover_membership.role == ProjectRole.viewer
        ):  # Fixed enum value from VIEWER to viewer
            raise InsufficientPermissionsError(
                "You don't have permission to remove users"
            )

        target_membership = self.memberships_repo.get(project_id, target_user_id)
        if not target_membership:
            raise UserNotFoundError("User is not a member of this project")

        if (
            target_membership.role == ProjectRole.owner
        ):  # Fixed enum value from OWNER to owner
            raise PermissionDeniedError("Cannot remove project owner")

        return self.memberships_repo.delete(project_id, target_user_id)
