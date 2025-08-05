"""
Tests for ProjectModel class.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from models import ProjectModel
from models.db_schemes.minirag.schemes import Project
from sqlalchemy import select

class TestProjectModel:
    """Test cases for ProjectModel class."""

    @pytest.mark.asyncio
    async def test_create_instance(self, test_session):
        """Test creating ProjectModel instance."""
        model = await ProjectModel.create_instance(db_client=test_session)
        assert model is not None
        assert hasattr(model, 'db_client')

    @pytest.mark.asyncio
    async def test_get_project_or_create_one_new_project(self, test_session, mock_user):
        """Test creating a new project."""
        model = await ProjectModel.create_instance(db_client=test_session)
        
        # Mock the session to return no existing project
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar_one_or_none.return_value = None
        
        # Mock session.begin for transaction
        test_session.begin = AsyncMock()
        test_session.begin.return_value.__aenter__ = AsyncMock()
        test_session.begin.return_value.__aexit__ = AsyncMock()
        
        result = await model.get_project_or_create_one(
            project_code=1, 
            user_id=mock_user.user_id
        )
        
        assert result is not None
        assert result.project_code == 1
        assert result.user_id == mock_user.user_id

    @pytest.mark.asyncio
    async def test_get_project_or_create_one_existing_project(self, test_session, mock_project):
        """Test getting an existing project."""
        model = await ProjectModel.create_instance(db_client=test_session)
        
        # Mock the session to return existing project
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar_one_or_none.return_value = mock_project
        
        result = await model.get_project_or_create_one(
            project_code=1, 
            user_id=1
        )
        
        assert result is not None
        assert result.project_id == mock_project.project_id

    @pytest.mark.asyncio
    async def test_get_user_project_success(self, test_session, mock_project):
        """Test getting a project that belongs to the user."""
        model = await ProjectModel.create_instance(db_client=test_session)
        
        # Mock the session to return the project
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar_one_or_none.return_value = mock_project
        
        result = await model.get_user_project(project_code=1, user_id=1)
        
        assert result is not None
        assert result.project_id == mock_project.project_id

    @pytest.mark.asyncio
    async def test_get_user_project_not_found(self, test_session):
        """Test getting a project that doesn't exist."""
        model = await ProjectModel.create_instance(db_client=test_session)
        
        # Mock the session to return None
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await model.get_user_project(project_code=999, user_id=1)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_project_by_id_success(self, test_session, mock_project):
        """Test getting a project by internal ID."""
        model = await ProjectModel.create_instance(db_client=test_session)
        
        # Mock the session to return the project
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar_one_or_none.return_value = mock_project
        
        result = await model.get_user_project_by_id(project_id=1, user_id=1)
        
        assert result is not None
        assert result.project_id == mock_project.project_id

    @pytest.mark.asyncio
    async def test_get_user_projects(self, test_session, mock_project):
        """Test getting all projects for a user."""
        model = await ProjectModel.create_instance(db_client=test_session)
        
        # Mock the session to return a list of projects
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalars.return_value.all.return_value = [mock_project]
        
        projects, total_pages = await model.get_user_projects(user_id=1, page=1, page_size=10)
        
        assert len(projects) == 1
        assert total_pages == 1
        assert projects[0].project_id == mock_project.project_id

    @pytest.mark.asyncio
    async def test_get_all_projects(self, test_session, mock_project):
        """Test getting all projects."""
        model = await ProjectModel.create_instance(db_client=test_session)
        
        # Mock the session to return a list of projects
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalars.return_value.all.return_value = [mock_project]
        
        projects = await model.get_all_projects()
        
        assert len(projects) == 1
        assert projects[0].project_id == mock_project.project_id

    @pytest.mark.asyncio
    async def test_delete_project_success(self, test_session, mock_project):
        """Test deleting a project."""
        model = await ProjectModel.create_instance(db_client=test_session)
        
        # Mock the session to return the project
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar_one_or_none.return_value = mock_project
        
        # Mock session.begin for transaction
        test_session.begin = AsyncMock()
        test_session.begin.return_value.__aenter__ = AsyncMock()
        test_session.begin.return_value.__aexit__ = AsyncMock()
        
        result = await model.delete_project(project_code=1, user_id=1)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, test_session):
        """Test deleting a project that doesn't exist."""
        model = await ProjectModel.create_instance(db_client=test_session)
        
        # Mock the session to return None
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await model.delete_project(project_code=999, user_id=1)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_create_project_success(self, test_session, mock_project):
        """Test creating a new project."""
        model = await ProjectModel.create_instance(db_client=test_session)
        
        # Mock session.begin for transaction
        test_session.begin = AsyncMock()
        test_session.begin.return_value.__aenter__ = AsyncMock()
        test_session.begin.return_value.__aexit__ = AsyncMock()
        
        # Mock session.add and session.refresh
        test_session.add = Mock()
        test_session.refresh = AsyncMock()
        
        result = await model.create_project(project=mock_project)
        
        assert result is not None
        test_session.add.assert_called_once_with(mock_project) 