from qdrant_client import models, QdrantClient
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
import logging
from typing import List
from models.db_schemes import RetrievedDocument

class QdrantDBProvider(VectorDBInterface):

    def __init__(self, db_client: str, default_vector_size: int = 3072,
                                     distance_method: str = None, index_threshold: int=100):

        self.client = None
        self.db_client = db_client
        self.distance_method = None
        self.default_vector_size = default_vector_size

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT

        self.logger = logging.getLogger('uvicorn')

    async def connect(self):
        try:
            # Check if we have a path (local storage) or should try server
            if self.db_client and not self.db_client.startswith("http"):
                # Use local storage directly
                self.logger.info("Using Qdrant local storage...")
                self.client = QdrantClient(path=self.db_client)
                # Test the connection by listing collections
                self.client.get_collections()
                self.logger.info(f"Successfully connected to Qdrant local storage at: {self.db_client}")
            else:
                # Try to connect to Qdrant server first
                self.client = QdrantClient(host="localhost", port=6333)
                # Test the connection by listing collections
                self.client.get_collections()
                self.logger.info("Successfully connected to Qdrant server on localhost:6333")
        except Exception as e:
            self.logger.warning(f"Could not connect to Qdrant server: {e}")
            self.logger.info("Falling back to local storage...")
            
            try:
                self.client = QdrantClient(path=self.db_client)
                # Test the connection by listing collections
                self.client.get_collections()
                self.logger.info(f"Successfully connected to Qdrant local storage at: {self.db_client}")
            except Exception as local_e:
                if "already accessed by another instance" in str(local_e):
                    self.logger.warning(f"Qdrant local instance already running at: {self.db_client}")
                    self.logger.info("Attempting to use existing local instance...")
                    # Try one more time - sometimes it works despite the warning
                    self.client = QdrantClient(path=self.db_client)
                else:
                    self.logger.error(f"Failed to connect to Qdrant: {local_e}")
                    self.logger.error("To use Qdrant server, run: docker run -p 6333:6333 qdrant/qdrant")
                    raise local_e

    async def disconnect(self):
        self.client = None

    async def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)
    
    async def list_all_collections(self) -> List:
        return self.client.get_collections()
    
    def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name)
    
    async def delete_collection(self, collection_name: str):
        if self.is_collection_existed(collection_name):
            self.logger.info(f"Deleting collection: {collection_name}")
            return self.client.delete_collection(collection_name=collection_name)
        
    async def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
        if do_reset:
            _ = self.delete_collection(collection_name=collection_name)
        
        if not await self.is_collection_existed(collection_name):
            self.logger.info(f"Creating new Qdrant collection: {collection_name}")
            
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=self.distance_method
                )
            )

            return True
        
        return False
    
    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, 
                         record_id: str = None):
        
        if not self.is_collection_existed(collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False
        
        try:
            _ = self.client.upload_records(
                collection_name=collection_name,
                records=[
                    models.Record(
                        id=[record_id],
                        vector=vector,
                        payload={
                            "text": text, "metadata": metadata
                        }
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"Error while inserting batch: {e}")
            return False

        return True
    
    async def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):
        
        if metadata is None:
            metadata = [None] * len(texts)

        if record_ids is None:
            record_ids = list(range(0, len(texts)))

        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size

            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]

            batch_records = [
                models.Record(
                    id=batch_record_ids[x],
                    vector=batch_vectors[x],
                    payload={
                        "text": batch_texts[x], "metadata": batch_metadata[x]
                    }
                )

                for x in range(len(batch_texts))
            ]

            try:
                _ = self.client.upload_records(
                    collection_name=collection_name,
                    records=batch_records,
                )
            except Exception as e:
                self.logger.error(f"Error while inserting batch: {e}")
                return False

        return True
        
    async def search_by_vector(self, collection_name: str, vector: list, limit: int = 5):

        results = self.client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit
        )

        if not results or len(results) == 0:
            return None
        
        return [
            RetrievedDocument(**{
                "score": result.score,
                "text": result.payload["text"],
            })
            for result in results
        ]

    async def delete_vectors_by_ids(self, collection_name: str, vector_ids: List[str]) -> bool:
        """
        Delete specific vectors by their IDs.
        
        Args:
            collection_name: Name of the collection
            vector_ids: List of vector IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not await self.is_collection_existed(collection_name):
                self.logger.warning(f"Collection {collection_name} does not exist")
                return False
            
            # Convert string IDs to integers if needed
            ids_to_delete = []
            for vid in vector_ids:
                try:
                    if isinstance(vid, str):
                        ids_to_delete.append(int(vid))
                    else:
                        ids_to_delete.append(vid)
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid vector ID format: {vid}")
                    continue
            
            if not ids_to_delete:
                self.logger.warning("No valid vector IDs provided for deletion")
                return False
            
            # Delete vectors by IDs
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=ids_to_delete
                )
            )
            
            self.logger.info(f"Successfully deleted {len(ids_to_delete)} vectors from collection {collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting vectors by IDs from collection {collection_name}: {e}")
            return False

    async def delete_vectors_by_filter(self, collection_name: str, filter_condition: dict) -> bool:
        """
        Delete vectors that match a filter condition.
        
        Args:
            collection_name: Name of the collection
            filter_condition: Filter condition to match vectors for deletion
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not await self.is_collection_existed(collection_name):
                self.logger.warning(f"Collection {collection_name} does not exist")
                return False
            
            self.logger.info(f"Attempting to delete vectors with filter: {filter_condition}")
            
            # First, let's check what's actually in the collection
            try:
                # Get a sample of points to understand the structure
                sample_points = self.client.scroll(
                    collection_name=collection_name,
                    limit=5,
                    with_payload=True
                )
                self.logger.info(f"Sample points in collection {collection_name}: {sample_points}")
            except Exception as e:
                self.logger.warning(f"Could not get sample points: {e}")
            
            # Convert filter condition to Qdrant filter format
            qdrant_filter = self._convert_filter_to_qdrant(filter_condition)
            
            if not qdrant_filter:
                self.logger.warning("Invalid filter condition provided")
                return False
            
            self.logger.info(f"Converted filter to Qdrant format: {qdrant_filter}")
            
            # Delete vectors by filter
            result = self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=qdrant_filter
                )
            )
            
            self.logger.info(f"Successfully deleted vectors matching filter from collection {collection_name}. Result: {result}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting vectors by filter from collection {collection_name}: {e}")
            return False

    def _convert_filter_to_qdrant(self, filter_condition: dict):
        """
        Convert a filter condition to Qdrant filter format.
        
        Args:
            filter_condition: Dictionary containing filter conditions
            
        Returns:
            Qdrant filter object or None if invalid
        """
        try:
            conditions = []
            
            for key, value in filter_condition.items():
                if key == "asset_id":
                    # The metadata is stored as a nested structure in the payload
                    # Try the correct path: metadata.asset_id
                    conditions.append(
                        models.FieldCondition(
                            key="metadata.asset_id",
                            match=models.MatchValue(value=value)
                        )
                    )
                elif key == "project_id":
                    conditions.append(
                        models.FieldCondition(
                            key="metadata.project_id",
                            match=models.MatchValue(value=value)
                        )
                    )
                elif key == "chunk_id":
                    conditions.append(
                        models.FieldCondition(
                            key="metadata.chunk_id",
                            match=models.MatchValue(value=value)
                        )
                    )
                # Add more filter conditions as needed
            
            if conditions:
                # Use 'must' since we want to match all conditions
                return models.Filter(
                    must=conditions
                )
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error converting filter to Qdrant format: {e}")
            return None

