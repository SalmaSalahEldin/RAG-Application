"""
Tests for ChunkModel class.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from models import ChunkModel
from models.db_schemes.minirag.schemes import DataChunk

class TestChunkModel:
    """Test cases for ChunkModel class."""

    @pytest.mark.asyncio
    async def test_create_instance(self, test_session):
        """Test creating ChunkModel instance."""
        model = await ChunkModel.create_instance(db_client=test_session)
        assert model is not None
        assert hasattr(model, 'db_client')

    @pytest.mark.asyncio
    async def test_create_chunk_success(self, test_session, mock_chunk):
        """Test creating a new chunk."""
        model = await ChunkModel.create_instance(db_client=test_session)
        
        # Mock session.begin for transaction
        test_session.begin = AsyncMock()
        test_session.begin.return_value.__aenter__ = AsyncMock()
        test_session.begin.return_value.__aexit__ = AsyncMock()
        
        # Mock session.add and session.refresh
        test_session.add = Mock()
        test_session.refresh = AsyncMock()
        
        result = await model.create_chunk(chunk=mock_chunk)
        
        assert result is not None
        test_session.add.assert_called_once_with(mock_chunk)

    @pytest.mark.asyncio
    async def test_get_chunk_success(self, test_session, mock_chunk):
        """Test getting a chunk by ID."""
        model = await ChunkModel.create_instance(db_client=test_session)
        
        # Mock the session to return the chunk
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar_one_or_none.return_value = mock_chunk
        
        result = await model.get_chunk(chunk_id=1)
        
        assert result is not None
        assert result.chunk_id == mock_chunk.chunk_id

    @pytest.mark.asyncio
    async def test_get_chunk_not_found(self, test_session):
        """Test getting a chunk that doesn't exist."""
        model = await ChunkModel.create_instance(db_client=test_session)
        
        # Mock the session to return None
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await model.get_chunk(chunk_id=999)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_insert_many_chunks(self, test_session):
        """Test inserting multiple chunks."""
        model = await ChunkModel.create_instance(db_client=test_session)
        
        # Create test chunks
        chunks = [
            DataChunk(chunk_project_id=1, chunk_asset_id=1, chunk_text="Chunk 1", chunk_metadata={}, chunk_order=1),
            DataChunk(chunk_project_id=1, chunk_asset_id=1, chunk_text="Chunk 2", chunk_metadata={}, chunk_order=2)
        ]
        
        # Mock session.begin for transaction
        test_session.begin = AsyncMock()
        test_session.begin.return_value.__aenter__ = AsyncMock()
        test_session.begin.return_value.__aexit__ = AsyncMock()
        
        # Mock session.add_all
        test_session.add_all = Mock()
        
        result = await model.insert_many_chunks(chunks=chunks, batch_size=100)
        
        assert result == len(chunks)
        test_session.add_all.assert_called_once_with(chunks)

    @pytest.mark.asyncio
    async def test_delete_chunks_by_project_id(self, test_session):
        """Test deleting chunks by project ID."""
        model = await ChunkModel.create_instance(db_client=test_session)
        
        # Mock session.begin for transaction
        test_session.begin = AsyncMock()
        test_session.begin.return_value.__aenter__ = AsyncMock()
        test_session.begin.return_value.__aexit__ = AsyncMock()
        
        # Mock session.execute to return a result with rowcount
        mock_result = Mock()
        mock_result.rowcount = 5
        test_session.execute = AsyncMock(return_value=mock_result)
        
        result = await model.delete_chunks_by_project_id(project_id=1)
        
        assert result == 5

    @pytest.mark.asyncio
    async def test_get_project_chunks(self, test_session, mock_chunk):
        """Test getting chunks for a project with pagination."""
        model = await ChunkModel.create_instance(db_client=test_session)
        
        # Mock the session to return a list of chunks
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalars.return_value.all.return_value = [mock_chunk]
        
        chunks = await model.get_project_chunks(project_id=1, page_no=1, page_size=10)
        
        assert len(chunks) == 1
        assert chunks[0].chunk_id == mock_chunk.chunk_id

    @pytest.mark.asyncio
    async def test_get_project_chunks_empty(self, test_session):
        """Test getting chunks for a project with no chunks."""
        model = await ChunkModel.create_instance(db_client=test_session)
        
        # Mock the session to return empty list
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalars.return_value.all.return_value = []
        
        chunks = await model.get_project_chunks(project_id=1, page_no=1, page_size=10)
        
        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_get_total_chunks_count(self, test_session):
        """Test getting total chunk count for a project."""
        model = await ChunkModel.create_instance(db_client=test_session)
        
        # Mock the session to return count
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar.return_value = 25
        
        count = await model.get_total_chunks_count(project_id=1)
        
        assert count == 25

    @pytest.mark.asyncio
    async def test_get_total_chunks_count_zero(self, test_session):
        """Test getting total chunk count for a project with no chunks."""
        model = await ChunkModel.create_instance(db_client=test_session)
        
        # Mock the session to return zero
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar.return_value = 0
        
        count = await model.get_total_chunks_count(project_id=1)
        
        assert count == 0

    @pytest.mark.asyncio
    async def test_insert_many_chunks_with_batching(self, test_session):
        """Test inserting chunks with batching."""
        model = await ChunkModel.create_instance(db_client=test_session)
        
        # Create test chunks
        chunks = [
            DataChunk(chunk_project_id=1, chunk_asset_id=1, chunk_text=f"Chunk {i}", chunk_metadata={}, chunk_order=i)
            for i in range(1, 6)  # 5 chunks
        ]
        
        # Mock session.begin for transaction
        test_session.begin = AsyncMock()
        test_session.begin.return_value.__aenter__ = AsyncMock()
        test_session.begin.return_value.__aexit__ = AsyncMock()
        
        # Mock session.add_all
        test_session.add_all = Mock()
        
        result = await model.insert_many_chunks(chunks=chunks, batch_size=2)
        
        assert result == len(chunks)
        # Should be called multiple times due to batching
        assert test_session.add_all.call_count > 0 