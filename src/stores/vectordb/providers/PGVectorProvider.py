from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import (DistanceMethodEnums, PgVectorTableSchemeEnums, 
                             PgVectorDistanceMethodEnums, PgVectorIndexTypeEnums)
import logging
from typing import List
from models.db_schemes import RetrievedDocument
from sqlalchemy.sql import text as sql_text
import json

class PGVectorProvider(VectorDBInterface):

    def __init__(self, db_client, default_vector_size: int = 3072,
                       distance_method: str = None, index_threshold: int=100):
        
        self.db_client = db_client
        self.default_vector_size = default_vector_size
        
        self.index_threshold = index_threshold

        if distance_method == DistanceMethodEnums.COSINE.value:
            distance_method = PgVectorDistanceMethodEnums.COSINE.value
        elif distance_method == DistanceMethodEnums.DOT.value:
            distance_method = PgVectorDistanceMethodEnums.DOT.value

        self.pgvector_table_prefix = PgVectorTableSchemeEnums._PREFIX.value
        self.distance_method = distance_method

        self.logger = logging.getLogger("uvicorn")
        self.default_index_name = lambda collection_name: f"{collection_name}_vector_idx"


    async def connect(self):
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(sql_text(
                    "CREATE EXTENSION IF NOT EXISTS vector"
                ))
                await session.commit()

    async def disconnect(self):
        pass

    async def is_collection_existed(self, collection_name: str) -> bool:

        record = None
        async with self.db_client() as session:
            async with session.begin():
                list_tbl = sql_text(f'SELECT * FROM pg_tables WHERE tablename = :collection_name')
                results = await session.execute(list_tbl, {"collection_name": collection_name})
                record = results.scalar_one_or_none()

        return record
    
    async def list_all_collections(self) -> List:
        records = []
        async with self.db_client() as session:
            async with session.begin():
                list_tbl = sql_text('SELECT tablename FROM pg_tables WHERE tablename LIKE :prefix')
                results = await session.execute(list_tbl, {"prefix": self.pgvector_table_prefix})
                records = results.scalars().all()
        
        return records
    
    async def get_collection_info(self, collection_name: str) -> dict:
        async with self.db_client() as session:
            async with session.begin():
                
                table_info_sql = sql_text(f'''
                    SELECT schemaname, tablename, tableowner, tablespace, hasindexes 
                    FROM pg_tables 
                    WHERE tablename = :collection_name
                ''')

                count_sql = sql_text(f'SELECT COUNT(*) FROM {collection_name}')

                table_info = await session.execute(table_info_sql, {"collection_name": collection_name})
                record_count = await session.execute(count_sql)

                table_data = table_info.fetchone()
                if not table_data:
                    return None
                
                return {
                    "table_info": {
                        "schemaname": table_data[0],
                        "tablename": table_data[1],
                        "tableowner": table_data[2],
                        "tablespace": table_data[3],
                        "hasindexes": table_data[4],
                    },
                    "record_count": record_count.scalar_one(),
                }
            
    async def delete_collection(self, collection_name: str):
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f"Deleting collection: {collection_name}")

                delete_sql = sql_text(f'DROP TABLE IF EXISTS {collection_name}')
                await session.execute(delete_sql)
                await session.commit()
        
        return True

    async def create_collection(self, collection_name: str,
                                      embedding_size: int,
                                      do_reset: bool = False):
        
        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)

        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.info(f"Creating collection: {collection_name}")
            async with self.db_client() as session:
                async with session.begin():
                    create_sql = sql_text(
                        f'CREATE TABLE {collection_name} ('
                            f'{PgVectorTableSchemeEnums.ID.value} bigserial PRIMARY KEY,'
                            f'{PgVectorTableSchemeEnums.TEXT.value} text, '
                            f'{PgVectorTableSchemeEnums.VECTOR.value} vector({embedding_size}), '
                            f'{PgVectorTableSchemeEnums.METADATA.value} jsonb DEFAULT \'{{}}\', '
                            f'{PgVectorTableSchemeEnums.CHUNK_ID.value} integer, '
                            f'FOREIGN KEY ({PgVectorTableSchemeEnums.CHUNK_ID.value}) REFERENCES chunks(chunk_id)'
                        ')'
                    )
                    await session.execute(create_sql)
                    await session.commit()
            
            return True

        return False
    
    async def is_index_existed(self, collection_name: str) -> bool:
        index_name = self.default_index_name(collection_name)
        async with self.db_client() as session:
            async with session.begin():
                check_sql = sql_text(f""" 
                                    SELECT 1 
                                    FROM pg_indexes 
                                    WHERE tablename = :collection_name
                                    AND indexname = :index_name
                                    """)
                results = await session.execute(check_sql, {"index_name": index_name, "collection_name": collection_name})
                
                return bool(results.scalar_one_or_none())
            
    async def create_vector_index(self, collection_name: str,
                                        index_type: str = PgVectorIndexTypeEnums.HNSW.value):
        is_index_existed = await self.is_index_existed(collection_name=collection_name)
        if is_index_existed:
            return False
        
        async with self.db_client() as session:
            async with session.begin():
                count_sql = sql_text(f'SELECT COUNT(*) FROM {collection_name}')
                result = await session.execute(count_sql)
                records_count = result.scalar_one()

                if records_count < self.index_threshold:
                    return False
                
                self.logger.info(f"START: Creating vector index for collection: {collection_name}")
                
                index_name = self.default_index_name(collection_name)
                create_idx_sql = sql_text(
                                            f'CREATE INDEX {index_name} ON {collection_name} '
                                            f'USING {index_type} ({PgVectorTableSchemeEnums.VECTOR.value} {self.distance_method})'
                                          )

                await session.execute(create_idx_sql)

                self.logger.info(f"END: Created vector index for collection: {collection_name}")

    async def reset_vector_index(self, collection_name: str, 
                                       index_type: str = PgVectorIndexTypeEnums.HNSW.value) -> bool:
        
        index_name = self.default_index_name(collection_name)
        async with self.db_client() as session:
            async with session.begin():
                drop_sql = sql_text(f'DROP INDEX IF EXISTS {index_name}')
                await session.execute(drop_sql)
        
        return await self.create_vector_index(collection_name=collection_name, index_type=index_type)

    
    async def insert_one(self, collection_name: str, text: str, vector: list,
                            metadata: dict = None,
                            record_id: str = None):
        
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False
        
        if not record_id:
            self.logger.error(f"Can not insert new record without chunk_id: {collection_name}")
            return False
        
        async with self.db_client() as session:
            async with session.begin():
                insert_sql = sql_text(f'INSERT INTO {collection_name} '
                                      f'({PgVectorTableSchemeEnums.TEXT.value}, {PgVectorTableSchemeEnums.VECTOR.value}, {PgVectorTableSchemeEnums.METADATA.value}, {PgVectorTableSchemeEnums.CHUNK_ID.value}) '
                                      'VALUES (:text, :vector, :metadata, :chunk_id)'
                                      )
                
                metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata is not None else "{}"
                await session.execute(insert_sql, {
                    'text': text,
                    'vector': "[" + ",".join([ str(v) for v in vector ]) + "]",
                    'metadata': metadata_json,
                    'chunk_id': record_id
                })
                await session.commit()

                await self.create_vector_index(collection_name=collection_name)
        
        return True
    

    async def insert_many(self, collection_name: str, texts: list,
                         vectors: list, metadata: list = None,
                         record_ids: list = None, batch_size: int = 50):
        
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Can not insert new records to non-existed collection: {collection_name}")
            return False
        
        if len(vectors) != len(record_ids):
            self.logger.error(f"Invalid data items for collection: {collection_name}")
            return False
        
        if not metadata or len(metadata) == 0:
            metadata = [None] * len(texts)
        
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i:i+batch_size]
                    batch_vectors = vectors[i:i + batch_size]
                    batch_metadata = metadata[i:i + batch_size]
                    batch_record_ids = record_ids[i:i + batch_size]

                    values = []

                    for _text, _vector, _metadata, _record_id in zip(batch_texts, batch_vectors, batch_metadata, batch_record_ids):
                        
                        metadata_json = json.dumps(_metadata, ensure_ascii=False) if _metadata is not None else "{}"
                        values.append({
                            'text': _text,
                            'vector': "[" + ",".join([ str(v) for v in _vector ]) + "]",
                            'metadata': metadata_json,
                            'chunk_id': _record_id
                        })
                    
                    batch_insert_sql = sql_text(f'INSERT INTO {collection_name} '
                                    f'({PgVectorTableSchemeEnums.TEXT.value}, '
                                    f'{PgVectorTableSchemeEnums.VECTOR.value}, '
                                    f'{PgVectorTableSchemeEnums.METADATA.value}, '
                                    f'{PgVectorTableSchemeEnums.CHUNK_ID.value}) '
                                    f'VALUES (:text, :vector, :metadata, :chunk_id)')
                    
                    await session.execute(batch_insert_sql, values)

        await self.create_vector_index(collection_name=collection_name)

        return True
    
    async def search_by_vector(self, collection_name: str, vector: list, limit: int):
        async with self.db_client() as session:
            async with session.begin():
                
                # Convert vector to PostgreSQL array format
                vector_str = "[" + ",".join(map(str, vector)) + "]"
                
                # Build the distance function based on the distance method
                if self.distance_method == PgVectorDistanceMethodEnums.COSINE.value:
                    distance_func = "1 - (embedding <=> :vector)"
                elif self.distance_method == PgVectorDistanceMethodEnums.DOT.value:
                    distance_func = "embedding <#> :vector"
                else:
                    distance_func = "1 - (embedding <=> :vector)"  # Default to cosine
                
                search_sql = sql_text(f'''
                    SELECT id, text, metadata, {distance_func} as distance
                    FROM {collection_name}
                    ORDER BY embedding <=> :vector
                    LIMIT :limit
                ''')
                
                results = await session.execute(search_sql, {
                    "vector": vector_str,
                    "limit": limit
                })
                
                records = results.fetchall()
                
                if not records:
                    return None
                
                return [
                    RetrievedDocument(
                        text=record[1],
                        score=float(record[3])
                    )
                    for record in records
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
            async with self.db_client() as session:
                async with session.begin():
                    # Convert IDs list to PostgreSQL array format
                    ids_str = "[" + ",".join(map(str, ids_to_delete)) + "]"
                    
                    delete_sql = sql_text(f'''
                        DELETE FROM {collection_name}
                        WHERE id = ANY(:ids)
                    ''')
                    
                    result = await session.execute(delete_sql, {"ids": ids_str})
                    await session.commit()
                    
                    deleted_count = result.rowcount
                    self.logger.info(f"Successfully deleted {deleted_count} vectors from collection {collection_name}")
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
            
            # Build WHERE clause based on filter conditions
            where_conditions = []
            params = {}
            
            for key, value in filter_condition.items():
                if key == "asset_id":
                    where_conditions.append("metadata->>'asset_id' = :asset_id")
                    params["asset_id"] = str(value)
                elif key == "project_id":
                    where_conditions.append("metadata->>'project_id' = :project_id")
                    params["project_id"] = str(value)
                elif key == "chunk_id":
                    where_conditions.append("metadata->>'chunk_id' = :chunk_id")
                    params["chunk_id"] = str(value)
                # Add more filter conditions as needed
            
            if not where_conditions:
                self.logger.warning("No valid filter conditions provided")
                return False
            
            # Build the DELETE query
            where_clause = " AND ".join(where_conditions)
            delete_sql = sql_text(f'''
                DELETE FROM {collection_name}
                WHERE {where_clause}
            ''')
            
            # Execute deletion
            async with self.db_client() as session:
                async with session.begin():
                    result = await session.execute(delete_sql, params)
                    await session.commit()
                    
                    deleted_count = result.rowcount
                    self.logger.info(f"Successfully deleted {deleted_count} vectors matching filter from collection {collection_name}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Error deleting vectors by filter from collection {collection_name}: {e}")
            return False
