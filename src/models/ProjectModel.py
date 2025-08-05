from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum
from sqlalchemy.future import select
from sqlalchemy import func

class ProjectModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance

    async def create_project(self, project: Project):
        async with self.db_client() as session:
            async with session.begin():
                session.add(project)
            await session.commit()
            await session.refresh(project)
        
        return project

    async def get_project_or_create_one(self, project_code: int, user_id: int = None):
        """
        Get or create a project using project_code (user-facing ID).
        If user_id is provided, ensures user ownership and project_code uniqueness per user.
        """
        async with self.db_client() as session:
            async with session.begin():
                if user_id:
                    # User-specific project query using project_code
                    query = select(Project).where(
                        Project.project_code == project_code,
                        Project.user_id == user_id
                    )
                else:
                    # Legacy query without user filtering (for backward compatibility)
                    query = select(Project).where(Project.project_code == project_code)
                
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                
                if project is None:
                    if user_id:
                        # Create project with user association and project_code
                        project_rec = Project(
                            project_code=project_code,
                            user_id=user_id
                        )
                    else:
                        # Legacy creation without user_id (for backward compatibility)
                        project_rec = Project(
                            project_code=project_code
                        )

                    project = await self.create_project(project=project_rec)
                    return project
                else:
                    return project

    async def get_user_project(self, project_code: int, user_id: int):
        """
        Get a project only if it belongs to the specified user using project_code.
        Returns None if project doesn't exist or doesn't belong to user.
        """
        async with self.db_client() as session:
            async with session.begin():
                # First try to find by project_code
                query = select(Project).where(
                    Project.project_code == project_code,
                    Project.user_id == user_id
                )
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                
                # If not found by project_code, try by project_id (for backward compatibility)
                if project is None:
                    try:
                        project_id = int(project_code)
                        query = select(Project).where(
                            Project.project_id == project_id,
                            Project.user_id == user_id
                        )
                        result = await session.execute(query)
                        project = result.scalar_one_or_none()
                    except (ValueError, TypeError):
                        pass
                
                return project

    async def get_user_project_by_id(self, project_id: int, user_id: int):
        """
        Get a project by internal project_id only if it belongs to the specified user.
        Returns None if project doesn't exist or doesn't belong to user.
        """
        async with self.db_client() as session:
            async with session.begin():
                query = select(Project).where(
                    Project.project_id == project_id,
                    Project.user_id == user_id
                )
                result = await session.execute(query)
                return result.scalar_one_or_none()

    async def get_user_projects(self, user_id: int, page: int = 1, page_size: int = 10):
        """
        Get all projects belonging to a specific user with pagination.
        """
        async with self.db_client() as session:
            async with session.begin():
                # Count total projects for this user
                total_documents_result = await session.execute(select(
                    func.count(Project.project_id)
                ).where(Project.user_id == user_id))
                total_documents = total_documents_result.scalar_one()

                # Calculate total pages
                total_pages = total_documents // page_size
                if total_documents % page_size > 0:
                    total_pages += 1

                # Get user's projects with pagination
                query = select(Project).where(
                    Project.user_id == user_id
                ).offset((page - 1) * page_size).limit(page_size)
                result = await session.execute(query)
                projects = result.scalars().all()

                return projects, total_pages

    async def get_all_projects(self, page: int=1, page_size: int=10):
        """
        Get all projects (admin function - no user filtering).
        """
        async with self.db_client() as session:
            async with session.begin():
                total_documents_result = await session.execute(select(
                    func.count( Project.project_id )
                ))
                total_documents = total_documents_result.scalar_one()

                total_pages = total_documents // page_size
                if total_documents % page_size > 0:
                    total_pages += 1

                query = select(Project).offset((page - 1) * page_size ).limit(page_size)
                result = await session.execute(query)
                projects = result.scalars().all()

                return projects, total_pages

    async def delete_project(self, project_id: int):
        """
        Delete a project and all its associated data.
        """
        async with self.db_client() as session:
            async with session.begin():
                query = select(Project).where(Project.project_id == project_id)
                project = (await session.execute(query)).scalar_one_or_none()
                
                if project:
                    await session.delete(project)
                    await session.commit()
                    return True
                else:
                    return False
