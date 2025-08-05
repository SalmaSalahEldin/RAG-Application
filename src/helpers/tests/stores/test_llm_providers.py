"""
Tests for LLM providers.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from stores.llm.providers.OpenAIProvider import OpenAIProvider
from stores.llm.providers.CoHereProvider import CoHereProvider
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.llm.LLMEnums import LLMProviderEnums

class TestOpenAIProvider:
    """Test cases for OpenAIProvider class."""

    def test_create_instance(self, mock_settings):
        """Test creating OpenAIProvider instance."""
        provider = OpenAIProvider(config=mock_settings)
        assert provider is not None
        assert hasattr(provider, 'config')

    def test_set_generation_model(self, mock_settings):
        """Test setting generation model."""
        provider = OpenAIProvider(config=mock_settings)
        provider.set_generation_model(model_id="gpt-3.5-turbo")
        assert provider.generation_model_id == "gpt-3.5-turbo"

    def test_set_embedding_model(self, mock_settings):
        """Test setting embedding model."""
        provider = OpenAIProvider(config=mock_settings)
        provider.set_embedding_model(model_id="text-embedding-ada-002", embedding_size=1536)
        assert provider.embedding_model_id == "text-embedding-ada-002"
        assert provider.embedding_model_size == 1536

    @pytest.mark.asyncio
    async def test_generate_text_success(self, mock_settings):
        """Test generating text successfully."""
        provider = OpenAIProvider(config=mock_settings)
        provider.set_generation_model(model_id="gpt-3.5-turbo")
        
        # Mock OpenAI client
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Generated response"))]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            result = await provider.generate_text(prompt="Test prompt")
            
            assert result == "Generated response"
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_text_no_model(self, mock_settings):
        """Test generating text without setting model."""
        provider = OpenAIProvider(config=mock_settings)
        
        with pytest.raises(ValueError, match="Generation model not set"):
            await provider.generate_text(prompt="Test prompt")

    @pytest.mark.asyncio
    async def test_embed_text_success(self, mock_settings):
        """Test embedding text successfully."""
        provider = OpenAIProvider(config=mock_settings)
        provider.set_embedding_model(model_id="text-embedding-ada-002", embedding_size=1536)
        
        # Mock OpenAI client
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            
            result = await provider.embed_text(texts=["test text"])
            
            assert result == [[0.1, 0.2, 0.3]]
            mock_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_text_no_model(self, mock_settings):
        """Test embedding text without setting model."""
        provider = OpenAIProvider(config=mock_settings)
        
        with pytest.raises(ValueError, match="Embedding model not set"):
            await provider.embed_text(texts=["test text"])

    @pytest.mark.asyncio
    async def test_generate_text_error(self, mock_settings):
        """Test generating text with error."""
        provider = OpenAIProvider(config=mock_settings)
        provider.set_generation_model(model_id="gpt-3.5-turbo")
        
        # Mock OpenAI client to raise exception
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
            
            result = await provider.generate_text(prompt="Test prompt")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_embed_text_error(self, mock_settings):
        """Test embedding text with error."""
        provider = OpenAIProvider(config=mock_settings)
        provider.set_embedding_model(model_id="text-embedding-ada-002", embedding_size=1536)
        
        # Mock OpenAI client to raise exception
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.embeddings.create = AsyncMock(side_effect=Exception("API Error"))
            
            result = await provider.embed_text(texts=["test text"])
            
            assert result is None

class TestCoHereProvider:
    """Test cases for CoHereProvider class."""

    def test_create_instance(self, mock_settings):
        """Test creating CoHereProvider instance."""
        provider = CoHereProvider(config=mock_settings)
        assert provider is not None
        assert hasattr(provider, 'config')

    def test_set_generation_model(self, mock_settings):
        """Test setting generation model."""
        provider = CoHereProvider(config=mock_settings)
        provider.set_generation_model(model_id="command")
        assert provider.generation_model_id == "command"

    def test_set_embedding_model(self, mock_settings):
        """Test setting embedding model."""
        provider = CoHereProvider(config=mock_settings)
        provider.set_embedding_model(model_id="embed-english-v3.0", embedding_size=1024)
        assert provider.embedding_model_id == "embed-english-v3.0"
        assert provider.embedding_model_size == 1024

    @pytest.mark.asyncio
    async def test_generate_text_success(self, mock_settings):
        """Test generating text successfully."""
        provider = CoHereProvider(config=mock_settings)
        provider.set_generation_model(model_id="command")
        
        # Mock Cohere client
        with patch('cohere.AsyncClient') as mock_cohere:
            mock_client = Mock()
            mock_cohere.return_value = mock_client
            
            mock_response = Mock()
            mock_response.generations = [Mock(text="Generated response")]
            mock_client.generate = AsyncMock(return_value=mock_response)
            
            result = await provider.generate_text(prompt="Test prompt")
            
            assert result == "Generated response"
            mock_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_text_success(self, mock_settings):
        """Test embedding text successfully."""
        provider = CoHereProvider(config=mock_settings)
        provider.set_embedding_model(model_id="embed-english-v3.0", embedding_size=1024)
        
        # Mock Cohere client
        with patch('cohere.AsyncClient') as mock_cohere:
            mock_client = Mock()
            mock_cohere.return_value = mock_client
            
            mock_response = Mock()
            mock_response.embeddings = [Mock(values=[0.1, 0.2, 0.3])]
            mock_client.embed = AsyncMock(return_value=mock_response)
            
            result = await provider.embed_text(texts=["test text"])
            
            assert result == [[0.1, 0.2, 0.3]]
            mock_client.embed.assert_called_once()

class TestLLMProviderFactory:
    """Test cases for LLMProviderFactory class."""

    def test_create_openai_provider(self, mock_settings):
        """Test creating OpenAI provider."""
        factory = LLMProviderFactory(config=mock_settings)
        provider = factory.create(provider=LLMProviderEnums.OPENAI.value)
        
        assert provider is not None
        assert isinstance(provider, OpenAIProvider)

    def test_create_cohere_provider(self, mock_settings):
        """Test creating Cohere provider."""
        factory = LLMProviderFactory(config=mock_settings)
        provider = factory.create(provider=LLMProviderEnums.COHERE.value)
        
        assert provider is not None
        assert isinstance(provider, CoHereProvider)

    def test_create_invalid_provider(self, mock_settings):
        """Test creating invalid provider."""
        factory = LLMProviderFactory(config=mock_settings)
        
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            factory.create(provider="invalid_provider")

    def test_create_provider_without_api_key(self, mock_settings):
        """Test creating provider without API key."""
        # Remove API key from settings
        mock_settings.OPENAI_API_KEY = None
        mock_settings.COHERE_API_KEY = None
        
        factory = LLMProviderFactory(config=mock_settings)
        
        # Should return None when no API key is available
        provider = factory.create(provider=LLMProviderEnums.OPENAI.value)
        assert provider is None 