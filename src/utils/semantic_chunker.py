"""
Semantic Chunking Utility for RAG

This module provides semantic text chunking capabilities using LangChain's SemanticChunker.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from helpers.config import get_settings

logger = logging.getLogger(__name__)

@dataclass
class ChunkedDocument:
    """Represents a chunked document with content and metadata."""
    page_content: str
    metadata: Dict[str, Any]

class SemanticChunkerUtility:
    """
    Utility class for semantic chunking using LangChain's SemanticChunker.
    
    This class provides semantic chunking functionality while maintaining
    compatibility with the existing project structure.
    """
    
    def __init__(self, embeddings_model: Optional[str] = None):
        """
        Initialize the semantic chunker utility.
        
        Args:
            embeddings_model: The embeddings model to use for semantic chunking.
                            Defaults to OpenAI embeddings.
        """
        self.settings = get_settings()
        
        # Initialize embeddings
        if embeddings_model == "openai" or embeddings_model is None:
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=self.settings.OPENAI_API_KEY,
                model="text-embedding-3-large"
            )
        else:
            # Add support for other embedding models here
            raise ValueError(f"Unsupported embeddings model: {embeddings_model}")
        
        # Initialize semantic chunker
        self.semantic_chunker = SemanticChunker(
            embeddings=self.embeddings,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=95
        )
        
        logger.info("SemanticChunkerUtility initialized successfully")
    
    def chunk_text_semantically(self, 
                               texts: List[str], 
                               metadatas: List[Dict[str, Any]] = None,
                               chunk_size: int = 1000,
                               overlap_size: int = 200) -> List[ChunkedDocument]:
        """
        Chunk text semantically using LangChain's SemanticChunker.
        
        Args:
            texts: List of text strings to chunk
            metadatas: List of metadata dictionaries corresponding to texts
            chunk_size: Maximum size of each chunk (characters)
            overlap_size: Overlap size between chunks (characters)
            
        Returns:
            List of ChunkedDocument objects
        """
        try:
            # Combine all texts into a single text for semantic chunking
            combined_text = "\n\n".join(texts)
            
            # Create a single document for semantic chunking
            document = Document(
                page_content=combined_text,
                metadata=metadatas[0] if metadatas else {}
            )
            
            # Perform semantic chunking
            chunks = self.semantic_chunker.split_documents([document])
            
            # Convert to ChunkedDocument format
            chunked_documents = []
            for i, chunk in enumerate(chunks):
                # Preserve original metadata and add chunk-specific info
                chunk_metadata = chunk.metadata.copy() if chunk.metadata else {}
                chunk_metadata.update({
                    "chunk_index": i,
                    "chunk_size": len(chunk.page_content),
                    "chunking_method": "semantic"
                })
                
                chunked_documents.append(ChunkedDocument(
                    page_content=chunk.page_content,
                    metadata=chunk_metadata
                ))
            
            logger.info(f"Semantically chunked {len(texts)} texts into {len(chunked_documents)} chunks")
            return chunked_documents
            
        except Exception as e:
            logger.error(f"Error in semantic chunking: {e}")
            # Fallback to simple chunking if semantic chunking fails
            return self._fallback_chunking(texts, metadatas, chunk_size, overlap_size)
    
    def _fallback_chunking(self, 
                           texts: List[str], 
                           metadatas: List[Dict[str, Any]] = None,
                           chunk_size: int = 1000,
                           overlap_size: int = 200) -> List[ChunkedDocument]:
        """
        Fallback chunking method when semantic chunking fails.
        
        Args:
            texts: List of text strings to chunk
            metadatas: List of metadata dictionaries corresponding to texts
            chunk_size: Maximum size of each chunk (characters)
            overlap_size: Overlap size between chunks (characters)
            
        Returns:
            List of ChunkedDocument objects
        """
        logger.warning("Using fallback chunking method")
        
        combined_text = " ".join(texts)
        chunks = []
        
        # Simple character-based chunking with overlap
        start = 0
        while start < len(combined_text):
            end = start + chunk_size
            
            # Find a good break point (space or newline) near the end
            if end < len(combined_text):
                # Look for a space or newline within the last 100 characters
                for i in range(end, max(start, end - 100), -1):
                    if combined_text[i] in [' ', '\n']:
                        end = i
                        break
            
            chunk_text = combined_text[start:end].strip()
            
            if chunk_text:
                # Preserve original metadata
                chunk_metadata = metadatas[0].copy() if metadatas else {}
                chunk_metadata.update({
                    "chunk_index": len(chunks),
                    "chunk_size": len(chunk_text),
                    "chunking_method": "fallback"
                })
                
                chunks.append(ChunkedDocument(
                    page_content=chunk_text,
                    metadata=chunk_metadata
                ))
            
            # Move start position with overlap
            start = end - overlap_size
            if start >= len(combined_text):
                break
        
        logger.info(f"Fallback chunked {len(texts)} texts into {len(chunks)} chunks")
        return chunks
    
    def chunk_by_sentences(self, 
                          texts: List[str], 
                          metadatas: List[Dict[str, Any]] = None,
                          max_chunk_size: int = 1000) -> List[ChunkedDocument]:
        """
        Chunk text by sentences while respecting semantic boundaries.
        
        Args:
            texts: List of text strings to chunk
            metadatas: List of metadata dictionaries corresponding to texts
            max_chunk_size: Maximum size of each chunk (characters)
            
        Returns:
            List of ChunkedDocument objects
        """
        import re
        
        combined_text = " ".join(texts)
        sentences = re.split(r'[.!?]+', combined_text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If adding this sentence would exceed the limit, start a new chunk
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                # Save current chunk
                chunk_metadata = metadatas[0].copy() if metadatas else {}
                chunk_metadata.update({
                    "chunk_index": chunk_index,
                    "chunk_size": len(current_chunk),
                    "chunking_method": "sentence_based"
                })
                
                chunks.append(ChunkedDocument(
                    page_content=current_chunk.strip(),
                    metadata=chunk_metadata
                ))
                
                current_chunk = sentence
                chunk_index += 1
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk if it exists
        if current_chunk.strip():
            chunk_metadata = metadatas[0].copy() if metadatas else {}
            chunk_metadata.update({
                "chunk_index": chunk_index,
                "chunk_size": len(current_chunk),
                "chunking_method": "sentence_based"
            })
            
            chunks.append(ChunkedDocument(
                page_content=current_chunk.strip(),
                metadata=chunk_metadata
            ))
        
        logger.info(f"Sentence-based chunked {len(texts)} texts into {len(chunks)} chunks")
        return chunks
    
    def get_chunking_stats(self, chunks: List[ChunkedDocument]) -> Dict[str, Any]:
        """
        Get statistics about the chunking process.
        
        Args:
            chunks: List of chunked documents
            
        Returns:
            Dictionary containing chunking statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0,
                "chunking_method": "none"
            }
        
        chunk_sizes = [len(chunk.page_content) for chunk in chunks]
        chunking_method = chunks[0].metadata.get("chunking_method", "unknown")
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "chunking_method": chunking_method,
            "total_characters": sum(chunk_sizes)
        } 