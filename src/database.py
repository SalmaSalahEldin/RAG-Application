from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

# This will be set by the main app
db_client = None

async def get_db():
    """Database dependency."""
    if db_client is None:
        # For testing without database, yield a mock session
        class MockSession:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
            async def execute(self, *args, **kwargs):
                # Return a mock result object
                class MockResult:
                    def scalar_one_or_none(self):
                        return None
                return MockResult()
            async def commit(self):
                pass
            async def add(self, *args, **kwargs):
                pass
            async def refresh(self, *args, **kwargs):
                pass
        mock_session = MockSession()
        yield mock_session
    else:
        async with db_client() as session:
            yield session 