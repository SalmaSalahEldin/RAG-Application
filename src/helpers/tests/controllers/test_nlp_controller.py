"""
Tests for NLPController class.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from controllers import NLPController
from models.db_schemes.minirag.schemes import Project, DataChunk
from stores.llm.LLMEnums import DocumentTypeEnum

class TestNLPController:
    """Test cases for NLPController class."""

    def test_create_instance(self, mock_llm_client, mock_vector_db_client, mock_settings):
        """Test creating NLPController instance."""
        controller = NLPController(
            vectordb_client=mock_vector_db_client,
            generation_client=mock_llm_client,
            embedding_client=mock_llm_client,
            template_parser=Mock()
        )
        assert controller is not None
        assert hasattr(controller, 'vectordb_client')
        assert hasattr(controller, 'generation_client')
        assert hasattr(controller, 'embedding_client')

    def test_create_collection_name(self, mock_vector_db_client, mock_llm_client):
        """Test creating collection name."""
        controller = NLPController(
            vectordb_client=mock_vector_db_client,
            generation_client=mock_llm_client,
            embedding_client=mock_llm_client,
            template_parser=Mock()
        )
        
        # Mock the default_vector_size
        controller.vectordb_client.default_vector_size = 786
        
        collection_name = controller.create_collection_name(project_id="123")
        
        assert collection_name == "collection_786_123"

    def test_create_collection_name_no_vectordb_client(self):
        """Test creating collection name when vectordb_client is None."""
        controller = NLPController(
            vectordb_client=None,
            generation_client=Mock(),
            embedding_client=Mock(),
            template_parser=Mock()
        )
        
        with pytest.raises(ValueError, match="Vector database client is not initialized"):
            controller.create_collection_name(project_id="123")

    @pytest.mark.asyncio
    async def test_reset_vector_db_collection(self, mock_vector_db_client, mock_llm_client, mock_project):
        """Test resetting vector database collection."""
        controller = NLPController(
            vectordb_client=mock_vector_db_client,
            generation_client=mock_llm_client,
            embedding_client=mock_llm_client,
            template_parser=Mock()
        )
        
        # Mock the collection name creation
        controller.create_collection_name = Mock(return_value="test_collection")
        
        result = await controller.reset_vector_db_collection(project=mock_project)
        
        assert result is True
        mock_vector_db_client.delete_collection.assert_called_once_with(collection_name="test_collection")

    @pytest.mark.asyncio
    async def test_get_vector_db_collection_info(self, mock_vector_db_client, mock_llm_client, mock_project):
        """Test getting vector database collection info."""
        controller = NLPController(
            vectordb_client=mock_vector_db_client,
            generation_client=mock_llm_client,
            embedding_client=mock_llm_client,
            template_parser=Mock()
        )
        
        # Mock the collection name creation
        controller.create_collection_name = Mock(return_value="test_collection")
        
        # Mock collection info
        mock_collection_info = Mock()
        mock_collection_info.vectors_count = 10
        mock_collection_info.points_count = 5
        mock_vector_db_client.get_collection_info.return_value = mock_collection_info
        
        result = await controller.get_vector_db_collection_info(project=mock_project)
        
        assert result is not None
        mock_vector_db_client.get_collection_info.assert_called_once_with(collection_name="test_collection")

    @pytest.mark.asyncio
    async def test_index_into_vector_db_success(self, mock_vector_db_client, mock_llm_client, mock_project):
        """Test indexing into vector database successfully."""
        controller = NLPController(
            vectordb_client=mock_vector_db_client,
            generation_client=mock_llm_client,
            embedding_client=mock_llm_client,
            template_parser=Mock()
        )
        
        # Create test chunks
        chunks = [
            DataChunk(chunk_id=1, chunk_text="Test chunk 1", chunk_metadata={}, chunk_order=1),
            DataChunk(chunk_id=2, chunk_text="Test chunk 2", chunk_metadata={}, chunk_order=2)
        ]
        chunks_ids = [1, 2]
        
        # Mock the collection name creation
        controller.create_collection_name = Mock(return_value="test_collection")
        
        # Mock embedding
        mock_llm_client.embed_text.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        
        # Mock vector database operations
        mock_vector_db_client.insert_many.return_value = True
        
        result = await controller.index_into_vector_db(
            project=mock_project,
            chunks=chunks,
            chunks_ids=chunks_ids
        )
        
        assert result is True
        mock_vector_db_client.insert_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_into_vector_db_no_chunks(self, mock_vector_db_client, mock_llm_client, mock_project):
        """Test indexing with no chunks."""
        controller = NLPController(
            vectordb_client=mock_vector_db_client,
            generation_client=mock_llm_client,
            embedding_client=mock_llm_client,
            template_parser=Mock()
        )
        
        result = await controller.index_into_vector_db(
            project=mock_project,
            chunks=[],
            chunks_ids=[]
        )
        
        assert result is True

    @pytest.mark.asyncio
    async def test_search_vector_db_collection_success(self, mock_vector_db_client, mock_llm_client, mock_project):
        """Test searching vector database successfully."""
        controller = NLPController(
            vectordb_client=mock_vector_db_client,
            generation_client=mock_llm_client,
            embedding_client=mock_llm_client,
            template_parser=Mock()
        )
        
        # Mock the collection name creation
        controller.create_collection_name = Mock(return_value="test_collection")
        
        # Mock embedding
        mock_llm_client.embed_text.return_value = [[0.1, 0.2, 0.3]]
        
        # Mock search results
        mock_results = [Mock(text="Result 1", score=0.9), Mock(text="Result 2", score=0.8)]
        mock_vector_db_client.search_by_vector.return_value = mock_results
        
        result = await controller.search_vector_db_collection(
            project=mock_project,
            text="test query",
            limit=5
        )
        
        assert result == mock_results
        mock_vector_db_client.search_by_vector.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_vector_db_collection_no_embedding(self, mock_vector_db_client, mock_llm_client, mock_project):
        """Test searching when embedding fails."""
        controller = NLPController(
            vectordb_client=mock_vector_db_client,
            generation_client=mock_llm_client,
            embedding_client=mock_llm_client,
            template_parser=Mock()
        )
        
        # Mock the collection name creation
        controller.create_collection_name = Mock(return_value="test_collection")
        
        # Mock embedding to return None
        mock_llm_client.embed_text.return_value = None
        
        result = await controller.search_vector_db_collection(
            project=mock_project,
            text="test query",
            limit=5
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_answer_rag_question_success(self, mock_vector_db_client, mock_llm_client, mock_project):
        """Test answering RAG question successfully."""
        controller = NLPController(
            vectordb_client=mock_vector_db_client,
            generation_client=mock_llm_client,
            embedding_client=mock_llm_client,
            template_parser=Mock()
        )
        
        # Mock search results
        mock_search_results = [Mock(text="Context 1", score=0.9), Mock(text="Context 2", score=0.8)]
        
        # Mock the search method
        controller.search_vector_db_collection = AsyncMock(return_value=mock_search_results)
        
        # Mock generation
        mock_llm_client.generate_text.return_value = "Generated answer"
        
        result = await controller.answer_rag_question(
            project=mock_project,
            query="test question",
            limit=5
        )
        
        assert result is not None
        mock_llm_client.generate_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_answer_rag_question_no_search_results(self, mock_vector_db_client, mock_llm_client, mock_project):
        """Test answering RAG question when no search results."""
        controller = NLPController(
            vectordb_client=mock_vector_db_client,
            generation_client=mock_llm_client,
            embedding_client=mock_llm_client,
            template_parser=Mock()
        )
        
        # Mock the search method to return None
        controller.search_vector_db_collection = AsyncMock(return_value=None)
        
        result = await controller.answer_rag_question(
            project=mock_project,
            query="test question",
            limit=5
        )
        
        assert result is None 