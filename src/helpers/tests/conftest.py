"""
Pytest configuration and fixtures for RAG testing suite.

This module provides common fixtures and configuration for all tests in the RAG project.
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app
from database import get_db
from models.db_schemes.minirag.schemes import User, Project, Asset, DataChunk
from models.enums.AssetTypeEnum import AssetTypeEnum
from models.enums.ProcessingEnum import ProcessingEnum
from stores.llm.LLMEnums import LLMProviderEnums
from stores.vectordb.VectorDBEnums import VectorDBProviderEnums

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/minirag_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="session")
async def test_session_factory(test_engine):
    """Create test session factory."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    yield async_session

@pytest.fixture
async def test_session(test_session_factory):
    """Create test database session."""
    async with test_session_factory() as session:
        yield session

@pytest.fixture
def test_client():
    """Create test client for FastAPI app."""
    return TestClient(app)

@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    return User(
        user_id=1,
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True
    )

@pytest.fixture
def mock_project():
    """Create a mock project for testing."""
    return Project(
        project_id=1,
        project_code=1,
        user_id=1,
        project_uuid="test-uuid-123"
    )

@pytest.fixture
def mock_asset():
    """Create a mock asset for testing."""
    return Asset(
        asset_id=1,
        asset_project_id=1,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name="test_file.txt",
        asset_size=1024
    )

@pytest.fixture
def mock_chunk():
    """Create a mock data chunk for testing."""
    return DataChunk(
        chunk_id=1,
        chunk_project_id=1,
        chunk_asset_id=1,
        chunk_text="This is a test chunk content.",
        chunk_metadata={"source": "test_file.txt"},
        chunk_order=1
    )

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    mock_client = Mock()
    mock_client.generate_text = AsyncMock(return_value="Generated response")
    mock_client.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])
    return mock_client

@pytest.fixture
def mock_vector_db_client():
    """Create a mock vector database client for testing."""
    mock_client = Mock()
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    mock_client.create_collection = AsyncMock(return_value=True)
    mock_client.insert_many = AsyncMock(return_value=True)
    mock_client.search_by_vector = AsyncMock(return_value=[])
    mock_client.get_collection_info = Mock(return_value=Mock(vectors_count=10))
    return mock_client

@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock()
    settings.OPENAI_API_KEY = "test-api-key"
    settings.GENERATION_BACKEND = LLMProviderEnums.OPENAI.value
    settings.EMBEDDING_BACKEND = LLMProviderEnums.OPENAI.value
    settings.VECTOR_DB_BACKEND = VectorDBProviderEnums.QDRANT.value
    settings.POSTGRES_HOST = "localhost"
    settings.POSTGRES_PORT = 5432
    settings.POSTGRES_USERNAME = "postgres"
    settings.POSTGRES_PASSWORD = "postgres"
    settings.POSTGRES_MAIN_DATABASE = "minirag_test"
    return settings

@pytest.fixture
def sample_text_file():
    """Create sample text file content for testing."""
    return """
    This is a sample text file for testing purposes.
    
    It contains multiple paragraphs with various content.
    
    The purpose is to test text processing and chunking functionality.
    
    This file should be processed into chunks for vector storage.
    """

@pytest.fixture
def sample_pdf_content():
    """Create sample PDF content for testing."""
    return [
        Mock(page_content="Page 1 content", metadata={"page": 1}),
        Mock(page_content="Page 2 content", metadata={"page": 2}),
        Mock(page_content="Page 3 content", metadata={"page": 3})
    ]

@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    return {"Authorization": "Bearer test-token"}

@pytest.fixture
def test_file_upload():
    """Create test file upload data."""
    return {
        "file": ("test_file.txt", b"This is test file content", "text/plain")
    }

# Override database dependency for testing
async def override_get_db():
    """Override database dependency for testing."""
    async_session = sessionmaker(
        create_async_engine(TEST_DATABASE_URL), 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db 