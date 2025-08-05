from .providers import QdrantDBProvider, PGVectorProvider
from .VectorDBEnums import VectorDBEnums
from controllers.BaseController import BaseController
from sqlalchemy.orm import sessionmaker

class VectorDBProviderFactory:
    def __init__(self, config, db_client: sessionmaker=None):
        self.config = config
        self.base_controller = BaseController()
        self.db_client = db_client

    def create(self, provider: str):
        print(f"Creating vector database provider: {provider}")
        print(f"Available providers: {VectorDBEnums.QDRANT.value}, {VectorDBEnums.PGVECTOR.value}")
        
        if provider == VectorDBEnums.QDRANT.value:
            print("Creating Qdrant provider...")
            # Use the configured path
            qdrant_db_client = self.base_controller.get_database_path(db_name=self.config.VECTOR_DB_PATH)
            print(f"Qdrant path: {qdrant_db_client}")

            try:
                client = QdrantDBProvider(
                    db_client=qdrant_db_client,
                    distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                    default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                    index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
                )
                print("Qdrant provider created successfully")
                return client
            except Exception as e:
                print(f"Failed to create Qdrant provider: {e}")
                return None
        
        if provider == VectorDBEnums.PGVECTOR.value:
            return PGVectorProvider(
                db_client=self.db_client,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
            )
        
        return None
