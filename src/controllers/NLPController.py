from .BaseController import BaseController
from models.db_schemes import Project, DataChunk
from stores.llm.LLMEnums import DocumentTypeEnum
from typing import List
import json

class NLPController(BaseController):

    def __init__(self, vectordb_client, generation_client, 
                 embedding_client, template_parser):
        super().__init__()

        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    def create_collection_name(self, project_id: str):
        if self.vectordb_client is None:
            raise ValueError("Vector database client is not initialized. Please check your configuration.")
        return f"collection_{self.vectordb_client.default_vector_size}_{project_id}".strip()
    
    async def reset_vector_db_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return await self.vectordb_client.delete_collection(collection_name=collection_name)
    
    async def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        collection_info = self.vectordb_client.get_collection_info(collection_name=collection_name)

        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
        )
    
    async def index_into_vector_db(self, project: Project, chunks: List[DataChunk],
                                   chunks_ids: List[int], 
                                   do_reset: bool = False):
        
        # step1: get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step2: filter out chunks with empty text content
        valid_chunks = []
        valid_chunk_ids = []
        for i, chunk in enumerate(chunks):
            if chunk.chunk_text and str(chunk.chunk_text).strip():
                valid_chunks.append(chunk)
                valid_chunk_ids.append(chunks_ids[i])
        
        if not valid_chunks:
            print(f"No valid chunks with text content found for project {project.project_id}")
            return True  # Return success but skip indexing
        
        # step3: manage items from valid chunks only
        texts = [c.chunk_text for c in valid_chunks]
        metadata = [c.chunk_metadata for c in valid_chunks]
        vectors = self.embedding_client.embed_text(text=texts, 
                                                  document_type=DocumentTypeEnum.DOCUMENT.value)

        # step3: create collection if not exists
        _ = await self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset,
        )

        # step5: insert into vector db
        _ = await self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            metadata=metadata,
            vectors=vectors,
            record_ids=valid_chunk_ids,
        )

        return True

    async def search_vector_db_collection(self, project: Project, text: str, limit: int = 10):

        # step1: get collection name
        query_vector = None
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step2: get text embedding vector
        vectors = self.embedding_client.embed_text(text=text, 
                                                 document_type=DocumentTypeEnum.QUERY.value)

        if not vectors or len(vectors) == 0:
            return False
        
        if isinstance(vectors, list) and len(vectors) > 0:
            query_vector = vectors[0]

        if not query_vector:
            return False    

        # step3: do semantic search
        results = await self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            vector=query_vector,
            limit=limit
        )

        if not results:
            return False

        return results
    
    async def answer_rag_question(self, project: Project, query: str, limit: int = 10):
        
        answer, full_prompt, chat_history = None, None, None

        # step1: retrieve related documents
        retrieved_documents = await self.search_vector_db_collection(
            project=project,
            text=query,
            limit=limit,
        )

        if not retrieved_documents or len(retrieved_documents) == 0:
            return answer, full_prompt, chat_history
        
        # step2: Construct LLM prompt
        system_prompt = self.template_parser.get("rag", "system_prompt")

        documents_prompts = "\n".join([
            self.template_parser.get("rag", "document_prompt", {
                    "doc_num": idx + 1,
                    "chunk_text": self.generation_client.process_text(doc.text),
            })
            for idx, doc in enumerate(retrieved_documents)
        ])

        footer_prompt = self.template_parser.get("rag", "footer_prompt", {
            "query": query
        })

        # step3: Construct Generation Client Prompts
        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value,
            )
        ]

        full_prompt = "\n\n".join([ documents_prompts,  footer_prompt])

        # step4: Retrieve the Answer
        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history
        )

        return answer, full_prompt, chat_history

    async def delete_vectors_by_asset_id(self, project: Project, asset_id: int) -> bool:
        """
        Delete all vectors associated with a specific asset.
        
        Args:
            project: Project object
            asset_id: Asset ID to delete vectors for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection_name = self.create_collection_name(project_id=project.project_id)
            print(f"Attempting to delete vectors for asset {asset_id} from collection {collection_name}")
            
            # Delete vectors by filter (asset_id)
            filter_condition = {"asset_id": asset_id}
            print(f"Using filter condition: {filter_condition}")
            
            success = await self.vectordb_client.delete_vectors_by_filter(
                collection_name=collection_name,
                filter_condition=filter_condition
            )
            
            if success:
                print(f"Successfully deleted vectors for asset {asset_id} from collection {collection_name}")
            else:
                print(f"Failed to delete vectors for asset {asset_id} from collection {collection_name}")
            
            return success
            
        except Exception as e:
            print(f"Error deleting vectors for asset {asset_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def delete_vectors_by_chunk_ids(self, project: Project, chunk_ids: List[int]) -> bool:
        """
        Delete specific vectors by chunk IDs.
        
        Args:
            project: Project object
            chunk_ids: List of chunk IDs to delete vectors for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection_name = self.create_collection_name(project_id=project.project_id)
            
            # Convert chunk IDs to strings for vector deletion
            vector_ids = [str(chunk_id) for chunk_id in chunk_ids]
            
            # Delete vectors by IDs
            success = await self.vectordb_client.delete_vectors_by_ids(
                collection_name=collection_name,
                vector_ids=vector_ids
            )
            
            if success:
                print(f"Successfully deleted {len(chunk_ids)} vectors from collection {collection_name}")
            else:
                print(f"Failed to delete vectors from collection {collection_name}")
            
            return success
            
        except Exception as e:
            print(f"Error deleting vectors for chunk IDs {chunk_ids}: {e}")
            return False

