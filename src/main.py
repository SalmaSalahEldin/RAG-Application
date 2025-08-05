from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routes import base_router, data_router, nlp_router
from routes.auth import auth_router
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

app = FastAPI()

async def startup_span():
    settings = get_settings()

    try:
        # Build connection string with optional password
        if settings.POSTGRES_PASSWORD:
            postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
        else:
            postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"

        app.db_engine = create_async_engine(postgres_conn)
        app.db_client = sessionmaker(
            app.db_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Set the database client for the database module
        import database
        database.db_client = app.db_client

        # Initialize LLM clients only if API keys are available
        print(f"🔧 Checking OpenAI API key: {settings.OPENAI_API_KEY[:20] if settings.OPENAI_API_KEY else 'NOT SET'}...")
        
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key-here":
            print("✅ OpenAI API key found - LLM features enabled")
            llm_provider_factory = LLMProviderFactory(settings)
            vectordb_provider_factory = VectorDBProviderFactory(config=settings, db_client=app.db_client)

            # generation client
            print(f"🔧 Creating generation client for provider: {settings.GENERATION_BACKEND}")
            app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
            if app.generation_client:
                app.generation_client.set_generation_model(model_id = settings.GENERATION_MODEL_ID)
                print("✅ Generation client initialized")
            else:
                print("❌ Failed to create generation client")

            # embedding client
            print(f"🔧 Creating embedding client for provider: {settings.EMBEDDING_BACKEND}")
            app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
            if app.embedding_client:
                app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                                     embedding_size=settings.EMBEDDING_MODEL_SIZE)
                print("✅ Embedding client initialized")
            else:
                print("❌ Failed to create embedding client")
            
            # vector db client
            print(f"🔧 Creating vector database client for provider: {settings.VECTOR_DB_BACKEND}")
            app.vectordb_client = vectordb_provider_factory.create(
                provider=settings.VECTOR_DB_BACKEND
            )
            if app.vectordb_client:
                print("✅ Vector database client created, attempting to connect...")
                try:
                    await app.vectordb_client.connect()
                    print("✅ Vector database client initialized")
                except Exception as e:
                    print(f"❌ Vector database connection failed: {e}")
                    app.vectordb_client = None
            else:
                print("❌ Failed to create vector database client")

            app.template_parser = TemplateParser(
                language=settings.PRIMARY_LANG,
                default_language=settings.DEFAULT_LANG,
            )
            print("✅ Template parser initialized")
        else:
            # Set mock clients for testing without API keys
            app.generation_client = None
            app.embedding_client = None
            app.vectordb_client = None
            app.template_parser = None
            print("⚠️  Warning: No OpenAI API key provided. LLM features will be disabled.")
            
    except Exception as e:
        print(f"⚠️  Warning: Database connection failed: {e}")
        print("📝 Using mock database for testing...")
        
        # Set mock clients
        app.generation_client = None
        app.embedding_client = None
        app.vectordb_client = None
        app.template_parser = None
        
        # Set mock database client
        import database
        database.db_client = None


async def shutdown_span():
    if hasattr(app, 'db_engine') and app.db_engine:
        app.db_engine.dispose()
    if hasattr(app, 'vectordb_client') and app.vectordb_client:
        await app.vectordb_client.disconnect()

app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)

app.include_router(base_router)
app.include_router(auth_router)
app.include_router(data_router)
app.include_router(nlp_router)

# Serve static files
assets_path = os.path.join(os.path.dirname(__file__), "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

@app.get("/")
async def root():
    """Serve the main application interface."""
    return FileResponse(os.path.join(assets_path, "index.html"))

# Import database module
from database import get_db
