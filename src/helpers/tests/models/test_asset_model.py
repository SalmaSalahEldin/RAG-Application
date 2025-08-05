"""
Tests for AssetModel class.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from models import AssetModel
from models.db_schemes.minirag.schemes import Asset
from models.enums.AssetTypeEnum import AssetTypeEnum

class TestAssetModel:
    """Test cases for AssetModel class."""

    @pytest.mark.asyncio
    async def test_create_instance(self, test_session):
        """Test creating AssetModel instance."""
        model = await AssetModel.create_instance(db_client=test_session)
        assert model is not None
        assert hasattr(model, 'db_client')

    @pytest.mark.asyncio
    async def test_create_asset_success(self, test_session, mock_asset):
        """Test creating a new asset."""
        model = await AssetModel.create_instance(db_client=test_session)
        
        # Mock session.begin for transaction
        test_session.begin = AsyncMock()
        test_session.begin.return_value.__aenter__ = AsyncMock()
        test_session.begin.return_value.__aexit__ = AsyncMock()
        
        # Mock session.add and session.refresh
        test_session.add = Mock()
        test_session.refresh = AsyncMock()
        
        result = await model.create_asset(asset=mock_asset)
        
        assert result is not None
        test_session.add.assert_called_once_with(mock_asset)

    @pytest.mark.asyncio
    async def test_get_all_project_assets(self, test_session, mock_asset):
        """Test getting all assets for a project."""
        model = await AssetModel.create_instance(db_client=test_session)
        
        # Mock the session to return a list of assets
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalars.return_value.all.return_value = [mock_asset]
        
        assets = await model.get_all_project_assets(
            asset_project_id=1, 
            asset_type=AssetTypeEnum.FILE.value
        )
        
        assert len(assets) == 1
        assert assets[0].asset_id == mock_asset.asset_id

    @pytest.mark.asyncio
    async def test_get_asset_record_success(self, test_session, mock_asset):
        """Test getting an asset record by project and name."""
        model = await AssetModel.create_instance(db_client=test_session)
        
        # Mock the session to return the asset
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar_one_or_none.return_value = mock_asset
        
        result = await model.get_asset_record(
            asset_project_id=1, 
            asset_name="test_file.txt"
        )
        
        assert result is not None
        assert result.asset_id == mock_asset.asset_id

    @pytest.mark.asyncio
    async def test_get_asset_record_not_found(self, test_session):
        """Test getting an asset record that doesn't exist."""
        model = await AssetModel.create_instance(db_client=test_session)
        
        # Mock the session to return None
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await model.get_asset_record(
            asset_project_id=1, 
            asset_name="nonexistent_file.txt"
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_asset_by_id_success(self, test_session, mock_asset):
        """Test getting an asset by ID."""
        model = await AssetModel.create_instance(db_client=test_session)
        
        # Mock the session to return the asset
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar_one_or_none.return_value = mock_asset
        
        result = await model.get_asset_by_id(asset_id=1, asset_project_id=1)
        
        assert result is not None
        assert result.asset_id == mock_asset.asset_id

    @pytest.mark.asyncio
    async def test_get_asset_by_id_not_found(self, test_session):
        """Test getting an asset by ID that doesn't exist."""
        model = await AssetModel.create_instance(db_client=test_session)
        
        # Mock the session to return None
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await model.get_asset_by_id(asset_id=999, asset_project_id=1)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_project_assets(self, test_session, mock_asset):
        """Test getting all assets for a project."""
        model = await AssetModel.create_instance(db_client=test_session)
        
        # Mock the session to return a list of assets
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalars.return_value.all.return_value = [mock_asset]
        
        assets = await model.get_project_assets(project_id=1)
        
        assert len(assets) == 1
        assert assets[0].asset_id == mock_asset.asset_id

    @pytest.mark.asyncio
    async def test_get_project_assets_empty(self, test_session):
        """Test getting assets for a project with no assets."""
        model = await AssetModel.create_instance(db_client=test_session)
        
        # Mock the session to return empty list
        test_session.execute = AsyncMock()
        test_session.execute.return_value.scalars.return_value.all.return_value = []
        
        assets = await model.get_project_assets(project_id=1)
        
        assert len(assets) == 0

    @pytest.mark.asyncio
    async def test_insert_many_assets(self, test_session):
        """Test inserting multiple assets."""
        model = await AssetModel.create_instance(db_client=test_session)
        
        # Create test assets
        assets = [
            Asset(asset_project_id=1, asset_type=AssetTypeEnum.FILE.value, asset_name="file1.txt", asset_size=1024),
            Asset(asset_project_id=1, asset_type=AssetTypeEnum.FILE.value, asset_name="file2.txt", asset_size=2048)
        ]
        
        # Mock session.begin for transaction
        test_session.begin = AsyncMock()
        test_session.begin.return_value.__aenter__ = AsyncMock()
        test_session.begin.return_value.__aexit__ = AsyncMock()
        
        # Mock session.add_all
        test_session.add_all = Mock()
        
        result = await model.insert_many_assets(assets=assets, batch_size=100)
        
        assert result == len(assets)
        test_session.add_all.assert_called_once_with(assets) 