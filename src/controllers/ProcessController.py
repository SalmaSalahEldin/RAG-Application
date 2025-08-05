from .BaseController import BaseController
from .ProjectController import ProjectController
import os
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from models import ProcessingEnum
from typing import List, Optional
from dataclasses import dataclass
from utils.semantic_chunker import SemanticChunkerUtility, ChunkedDocument

@dataclass
class Document:
    page_content: str
    metadata: dict

class ProcessController(BaseController):

    def __init__(self, project_id: str):
        super().__init__()

        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)
        
        # Initialize semantic chunker utility
        try:
            self.semantic_chunker = SemanticChunkerUtility()
            self.use_semantic_chunking = True
        except Exception as e:
            print(f"Warning: Could not initialize semantic chunker: {e}")
            self.semantic_chunker = None
            self.use_semantic_chunking = False

    def get_file_extension(self, file_id: str):
        return os.path.splitext(file_id)[-1]

    def get_file_loader(self, file_id: str):

        file_ext = self.get_file_extension(file_id=file_id)
        file_path = os.path.join(
            self.project_path,
            file_id
        )

        if not os.path.exists(file_path):
            return None

        if file_ext == ProcessingEnum.TXT.value:
            return TextLoader(file_path, encoding="utf-8")

        if file_ext == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path)
        
        return None

    def get_file_content(self, file_id: str):

        loader = self.get_file_loader(file_id=file_id)
        if loader:
            return loader.load()

        return None

    def process_file_content(self, file_content: list, file_id: str,
                            chunk_size: int=1000, overlap_size: int=200,
                            chunking_method: str="semantic") -> List[Document]:
        """
        Process file content using the specified chunking method.
        
        Args:
            file_content: List of document objects
            file_id: ID of the file being processed
            chunk_size: Maximum size of each chunk (characters)
            overlap_size: Overlap size between chunks (characters)
            chunking_method: Chunking method to use ("semantic", "sentence", "simple")
            
        Returns:
            List of Document objects
        """
        file_content_texts = [
            rec.page_content
            for rec in file_content
        ]

        file_content_metadata = [
            rec.metadata
            for rec in file_content
        ]

        if chunking_method == "semantic" and self.use_semantic_chunking:
            return self.process_semantic_chunking(
                texts=file_content_texts,
                metadatas=file_content_metadata,
                chunk_size=chunk_size,
                overlap_size=overlap_size
            )
        elif chunking_method == "sentence":
            return self.process_sentence_chunking(
                texts=file_content_texts,
                metadatas=file_content_metadata,
                max_chunk_size=chunk_size
            )
        else:
            # Fallback to simple chunking
            return self.process_simpler_splitter(
                texts=file_content_texts,
                metadatas=file_content_metadata,
                chunk_size=chunk_size,
            )

    def process_semantic_chunking(self, texts: List[str], metadatas: List[dict], 
                                 chunk_size: int, overlap_size: int) -> List[Document]:
        """
        Process text using semantic chunking.
        
        Args:
            texts: List of text strings to chunk
            metadatas: List of metadata dictionaries
            chunk_size: Maximum chunk size
            overlap_size: Overlap size between chunks
            
        Returns:
            List of Document objects
        """
        if not self.semantic_chunker:
            print("Warning: Semantic chunker not available, falling back to simple chunking")
            return self.process_simpler_splitter(texts, metadatas, chunk_size)
        
        try:
            # Use semantic chunking
            chunked_docs = self.semantic_chunker.chunk_text_semantically(
                texts=texts,
                metadatas=metadatas,
                chunk_size=chunk_size,
                overlap_size=overlap_size
            )
            
            # Convert to Document format for compatibility
            documents = []
            for chunked_doc in chunked_docs:
                documents.append(Document(
                    page_content=chunked_doc.page_content,
                    metadata=chunked_doc.metadata
                ))
            
            # Log chunking statistics
            stats = self.semantic_chunker.get_chunking_stats(chunked_docs)
            print(f"Semantic chunking completed: {stats}")
            
            return documents
            
        except Exception as e:
            print(f"Error in semantic chunking: {e}, falling back to simple chunking")
            return self.process_simpler_splitter(texts, metadatas, chunk_size)

    def process_sentence_chunking(self, texts: List[str], metadatas: List[dict], 
                                 max_chunk_size: int) -> List[Document]:
        """
        Process text using sentence-based chunking.
        
        Args:
            texts: List of text strings to chunk
            metadatas: List of metadata dictionaries
            max_chunk_size: Maximum chunk size
            
        Returns:
            List of Document objects
        """
        if not self.semantic_chunker:
            print("Warning: Semantic chunker not available, falling back to simple chunking")
            return self.process_simpler_splitter(texts, metadatas, max_chunk_size)
        
        try:
            # Use sentence-based chunking
            chunked_docs = self.semantic_chunker.chunk_by_sentences(
                texts=texts,
                metadatas=metadatas,
                max_chunk_size=max_chunk_size
            )
            
            # Convert to Document format for compatibility
            documents = []
            for chunked_doc in chunked_docs:
                documents.append(Document(
                    page_content=chunked_doc.page_content,
                    metadata=chunked_doc.metadata
                ))
            
            # Log chunking statistics
            stats = self.semantic_chunker.get_chunking_stats(chunked_docs)
            print(f"Sentence chunking completed: {stats}")
            
            return documents
            
        except Exception as e:
            print(f"Error in sentence chunking: {e}, falling back to simple chunking")
            return self.process_simpler_splitter(texts, metadatas, max_chunk_size)

    def process_simpler_splitter(self, texts: List[str], metadatas: List[dict], 
                                chunk_size: int, splitter_tag: str="\n") -> List[Document]:
        """
        Process text using simple character-based chunking (fallback method).
        
        Args:
            texts: List of text strings to chunk
            metadatas: List of metadata dictionaries
            chunk_size: Maximum chunk size
            splitter_tag: Tag to split text on
            
        Returns:
            List of Document objects
        """
        full_text = " ".join(texts)

        # split by splitter_tag
        lines = [ doc.strip() for doc in full_text.split(splitter_tag) if len(doc.strip()) > 1 ]

        chunks = []
        current_chunk = ""

        for line in lines:
            current_chunk += line + splitter_tag
            if len(current_chunk) >= chunk_size:
                # Preserve original metadata and add chunking info
                chunk_metadata = metadatas[0].copy() if metadatas else {}
                chunk_metadata.update({
                    "chunk_index": len(chunks),
                    "chunk_size": len(current_chunk.strip()),
                    "chunking_method": "simple"
                })
                
                chunks.append(Document(
                    page_content=current_chunk.strip(),
                    metadata=chunk_metadata
                ))

                current_chunk = ""

        if len(current_chunk) >= 0:
            # Preserve original metadata and add chunking info
            chunk_metadata = metadatas[0].copy() if metadatas else {}
            chunk_metadata.update({
                "chunk_index": len(chunks),
                "chunk_size": len(current_chunk.strip()),
                "chunking_method": "simple"
            })
            
            chunks.append(Document(
                page_content=current_chunk.strip(),
                metadata=chunk_metadata
            ))

        return chunks

    def get_chunking_methods(self) -> List[str]:
        """
        Get available chunking methods.
        
        Returns:
            List of available chunking methods (semantic is preferred/default)
        """
        methods = []
        
        if self.use_semantic_chunking:
            methods.extend(["semantic", "sentence"])
        
        # Always include simple as fallback
        methods.append("simple")
        
        return methods

    def get_chunking_stats(self, chunks: List[Document]) -> dict:
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


    

