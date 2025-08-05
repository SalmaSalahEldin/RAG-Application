from .BaseDataModel import BaseDataModel
from .db_schemes import Asset
from .enums.DataBaseEnum import DataBaseEnum
from sqlalchemy.future import select
from sqlalchemy import delete

class AssetModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance

    async def create_asset(self, asset: Asset):

        async with self.db_client() as session:
            async with session.begin():
                session.add(asset)
            await session.commit()
            await session.refresh(asset)
        return asset

    async def get_all_project_assets(self, asset_project_id: int, asset_type: str):
        """
        Get all assets of a specific type for a project.
        
        Args:
            asset_project_id: The project ID
            asset_type: The type of assets to retrieve
            
        Returns:
            List of Asset objects
        """
        async with self.db_client() as session:
            stmt = select(Asset).where(
                Asset.asset_project_id == asset_project_id,
                Asset.asset_type == asset_type
            )
            result = await session.execute(stmt)
            records = result.scalars().all()
        return records

    async def get_asset_record(self, asset_project_id: int, asset_name: str):
        """
        Get an asset by project ID and asset name.
        
        Args:
            asset_project_id: The project ID
            asset_name: The name of the asset
            
        Returns:
            Asset object or None if not found
        """
        async with self.db_client() as session:
            stmt = select(Asset).where(
                Asset.asset_project_id == asset_project_id,
                Asset.asset_name == asset_name
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
        return record

    async def get_asset_by_id(self, asset_id: int, asset_project_id: int):
        """
        Get an asset by ID and project ID.
        
        Args:
            asset_id: The ID of the asset
            asset_project_id: The project ID for validation
            
        Returns:
            Asset object or None if not found
        """
        import logging
        logger = logging.getLogger(__name__)
        
        async with self.db_client() as session:
            stmt = select(Asset).where(
                Asset.asset_id == asset_id,
                Asset.asset_project_id == asset_project_id
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            
            if record is None:
                logger.warning(f"Asset not found in database: asset_id={asset_id}, asset_project_id={asset_project_id}")
                # Let's also check if the asset exists at all (regardless of project)
                stmt_all = select(Asset).where(Asset.asset_id == asset_id)
                result_all = await session.execute(stmt_all)
                record_all = result_all.scalar_one_or_none()
                if record_all:
                    logger.warning(f"Asset {asset_id} exists but belongs to project {record_all.asset_project_id}, not {asset_project_id}")
                else:
                    logger.warning(f"Asset {asset_id} does not exist in the database at all")
            else:
                logger.info(f"Found asset: asset_id={record.asset_id}, asset_name={record.asset_name}, project_id={record.asset_project_id}")
            
        return record

    async def get_project_assets(self, project_id: int):
        """
        Get all assets for a specific project.
        """
        async with self.db_client() as session:
            stmt = select(Asset).where(Asset.asset_project_id == project_id)
            result = await session.execute(stmt)
            records = result.scalars().all()
        return records

    async def delete_asset(self, asset_id: int, asset_project_id: int):
        """
        Delete a single asset by ID.
        
        Args:
            asset_id: The ID of the asset to delete
            asset_project_id: The project ID for validation
            
        Returns:
            Number of deleted assets (should be 1 if successful, 0 if not found)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        async with self.db_client() as session:
            async with session.begin():
                stmt = delete(Asset).where(
                    Asset.asset_id == asset_id,
                    Asset.asset_project_id == asset_project_id
                )
                result = await session.execute(stmt)
                # The session.begin() context manager will handle the commit
                logger.info(f"Delete query executed: asset_id={asset_id}, project_id={asset_project_id}, rows_affected={result.rowcount}")
        
        return result.rowcount

    async def delete_all_project_assets(self, project_id: int):
        """
        Delete all assets for a specific project.
        
        Args:
            project_id: The project ID
            
        Returns:
            Number of deleted assets
        """
        async with self.db_client() as session:
            async with session.begin():
                stmt = delete(Asset).where(Asset.asset_project_id == project_id)
                result = await session.execute(stmt)
                await session.commit()
        return result.rowcount


    
