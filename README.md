# 🤖 RAG: AI-Powered Question Answering System

A complete, production-ready AI-powered question-answering API service built with FastAPI, featuring **multi-user support with isolated document spaces**, modern web interface, semantic chunking, and comprehensive testing suite.

### Core Requirements
- ✅ **Authentication**: JWT-based user authentication with email & password
- ✅ **Protected Endpoints**: All API endpoints require authentication with user isolation
- ✅ **Upload Endpoint**: File upload with PDF/TXT support, semantic chunking, and vector storage
- ✅ **Ask Endpoint**: Question answering with similarity search and LLM integration
- ✅ **Logging**: Automatic query logging with timestamps, user tracking, and response times

### Bonus Features
- ✅ **Multi-user Support**: **FULLY IMPLEMENTED** - Complete isolated document spaces per user
- ✅ **Modern Web Interface**: Beautiful HTML/JS frontend with project management and file operations
- ✅ **Comprehensive Testing**: Full test suite with unit, integration, and system tests
- ✅ **Semantic Chunking**: Advanced text chunking using LangChain's semantic chunker
- ✅ **Delete Operations**: Complete file and project deletion with data cleanup
- ✅ **Vector Database**: Qdrant integration with 3072-dimensional embeddings

## 🏗️ Architecture Overview

### **System Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   FastAPI App   │    │  PostgreSQL DB  │
│   (HTML/JS)     │◄──►│   (Python)      │◄──►│   (with pgvector)│
│   + User Auth   │    │   + User Isol.  │    │   + User Data   │
│   + File Mgmt   │    │   + Semantic    │    │   + Projects    │
│   + Chat UI     │    │   + Chunking    │    │   + Assets      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Vector Store  │
                       │   (Qdrant)      │
                       │   + User Coll.  │
                       │   + 3072 dim    │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   LLM Provider  │
                       │   (OpenAI)      │
                       │   + GPT Models  │
                       └─────────────────┘
```

### **Component Architecture**

#### **1. Frontend Layer**
- **Technology**: HTML5, CSS3, JavaScript (Vanilla)
- **Features**:
  - User authentication (login/register)
  - Project management interface
  - File upload with drag-and-drop
  - Real-time chat interface
  - File content viewer
  - Responsive design

#### **2. API Layer (FastAPI)**
- **Framework**: FastAPI with async/await
- **Authentication**: JWT-based with user isolation
- **Endpoints**: RESTful API with comprehensive CRUD operations
- **Validation**: Pydantic models for request/response validation
- **Documentation**: Auto-generated OpenAPI/Swagger docs

#### **3. Business Logic Layer**
- **Controllers**: ProcessController, NLPController, DataController
- **Models**: SQLAlchemy ORM with async support
- **Services**: VectorDB, LLM providers, semantic chunking
- **Utilities**: Error handling, logging, configuration

#### **4. Data Layer**
- **Primary Database**: PostgreSQL with pgvector extension
- **Vector Database**: Qdrant for similarity search
- **File Storage**: Local file system with metadata tracking
- **Caching**: In-memory caching for frequently accessed data

#### **5. External Services**
- **LLM Provider**: OpenAI GPT models (GPT-3.5, GPT-4)
- **Embeddings**: OpenAI text-embedding-3-large (3072 dimensions)
- **Vector Search**: Qdrant with cosine similarity

## 🚀 Setup Instructions

### **Prerequisites**
- Python 3.8+
- PostgreSQL 12+
- Docker (optional, for Qdrant)
- OpenAI API key

### **1. Clone the Repository**
```bash
git clone https://github.com/SalmaSalahEldin/RAG-Application.git
cd RAG-Application
```

### **2. Environment Configuration**
```bash
# Copy environment template
cp env.example .env

# Edit .env with your configuration
nano .env
```

**Required Environment Variables:**
```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/minirag
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=minirag

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL_ID=text-embedding-3-large
EMBEDDING_MODEL_SIZE=3072

# Application Configuration
APP_NAME=RAG
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Vector Database Configuration
VECTOR_DB_BACKEND=qdrant
VECTOR_DB_URL=http://localhost:6333
```

### **3. Database Setup**
```bash
# Start PostgreSQL (if using Docker)
docker run -d \
  --name postgres-rag \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=minirag \
  -p 5432:5432 \
  postgres:15

# Or use local PostgreSQL
sudo -u postgres createdb minirag
```

### **4. Install Dependencies**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r src/requirements.txt
```

### **5. Run Database Migrations**
```bash
# Run migrations
./run_migrations.sh
```

### **6. Start Qdrant (Vector Database)**
```bash
# Using Docker
docker run -d \
  --name qdrant-rag \
  -p 6333:6333 \
  -p 6334:6334 \
  qdrant/qdrant

# Or use local Qdrant
./start_qdrant.sh
```

### **7. Start the Application**
```bash
# Start the server
./start_server.sh

# Or manually
cd src
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **8. Access the Application**
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 🛠️ Tech Stack

### **Backend**
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with pgvector extension
- **ORM**: SQLAlchemy (async)
- **Authentication**: JWT (PyJWT)
- **Migrations**: Alembic
- **Testing**: pytest, pytest-asyncio, pytest-cov

### **AI/ML**
- **LLM Provider**: OpenAI GPT-3.5/4
- **Embeddings**: OpenAI text-embedding-3-large (3072d)
- **Vector Database**: Qdrant
- **Text Processing**: LangChain (semantic chunking)
- **Document Processing**: PyPDF2, python-multipart

### **Frontend**
- **Technology**: Vanilla JavaScript, HTML5, CSS3
- **Features**: Responsive design, real-time updates
- **UI Components**: Custom components with modern styling

### **Development & Testing**
- **Testing Framework**: pytest
- **Code Coverage**: pytest-cov
- **Linting**: flake8 (configurable)
- **Documentation**: Auto-generated OpenAPI/Swagger

### **Deployment**
- **Containerization**: Docker & Docker Compose
- **Process Management**: uvicorn
- **Environment Management**: python-dotenv

## 📚 API Usage & Swagger

### **Interactive Documentation**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### **Key Endpoints**

#### **Authentication**
```bash
# Register user
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "securepassword"
}

# Login
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### **Project Management**
```bash
# Create project
POST /api/v1/data/projects/create/{project_code}

# List user projects
GET /api/v1/data/projects

# Get project details
GET /api/v1/data/projects/{project_code}

# Delete project (and all files)
DELETE /api/v1/data/projects/{project_code}
```

#### **File Operations**
```bash
# Upload file
POST /api/v1/data/upload/{project_code}
Content-Type: multipart/form-data

# Process file (chunking & embedding)
POST /api/v1/data/process/{project_code}
{
  "asset_id": 123,
  "chunking_method": "semantic"
}

# Get file content
GET /api/v1/data/file/content/{project_code}/{asset_id}

# Delete single file
DELETE /api/v1/data/file/{project_code}/{asset_id}
```

#### **Question Answering**
```bash
# Ask question
POST /api/v1/nlp/ask/{project_code}
{
  "question": "What is the main topic of the document?",
  "limit": 10
}

# Get project index info
GET /api/v1/nlp/index/info/{project_code}
```

### **Response Format**
```json
{
  "signal": "SUCCESS",
  "data": {
    "answer": "The main topic is...",
    "sources": ["chunk1", "chunk2"],
    "metadata": {
      "processing_time": 1.23,
      "chunks_retrieved": 5
    }
  }
}
```

### **Error Handling**
```json
{
  "error": {
    "code": "FILE_NOT_FOUND",
    "title": "File Not Found",
    "message": "File with ID 123 not found",
    "suggestion": "Check if the file exists",
    "category": "file"
  }
}
```

## 🎯 Known Limitations

### **Current Limitations**
1. **File Size**: Maximum file size is 10MB (configurable)
2. **File Types**: Only PDF and TXT files are supported
3. **Vector Dimensions**: Fixed at 3072 dimensions (OpenAI text-embedding-3-large)
4. **Language Support**: Currently optimized for English text
5. **Concurrent Users**: No built-in rate limiting (can be added)
6. **File Storage**: Local file system only (no cloud storage)

### **Performance Considerations**
1. **Large Documents**: Very large documents may take time to process
2. **Memory Usage**: Vector operations can be memory-intensive
3. **API Rate Limits**: OpenAI API has rate limits
4. **Database Connections**: Connection pooling is recommended for production

### **Security Considerations**
1. **API Keys**: Store OpenAI API keys securely
2. **Database**: Use strong passwords for PostgreSQL
3. **HTTPS**: Enable HTTPS in production
4. **CORS**: Configure CORS for production deployment

### **Scalability Notes**
1. **Horizontal Scaling**: Application can be scaled horizontally
2. **Database**: Consider read replicas for high traffic
3. **Vector Database**: Qdrant supports clustering
4. **Caching**: Implement Redis for session management

## 🧪 Testing

### **Run All Tests**
```bash
# From project root
./run_tests.sh
```

### **Run Specific Test Categories**
```bash
# Unit tests
pytest src/helpers/tests/ -v

# Integration tests
pytest src/helpers/tests/integration/ -v

# With coverage
pytest src/helpers/tests/ --cov=src --cov-report=html
```

### **Test Coverage**
The project includes comprehensive tests:
- ✅ Unit tests for all components
- ✅ Integration tests for workflows
- ✅ System tests for end-to-end scenarios
- ✅ Authentication and authorization tests
- ✅ Multi-user isolation tests

## 📖 Additional Documentation

- [Local Setup Guide](LOCAL_SETUP_GUIDE.md) - Detailed local setup instructions
- [Migration Guide](MIGRATION_GUIDE.md) - Database migration procedures
- [Testing Guide](TESTING_GUIDE.md) - Comprehensive testing information
- [Semantic Chunking Guide](SEMANTIC_CHUNKING_GUIDE.md) - AI text processing details
- [Delete Endpoints Guide](DELETE_ENDPOINTS_GUIDE.md) - File and project deletion

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**🎉 RAG: A complete, AI-powered question-answering system with full multi-user support and modern architecture!**
