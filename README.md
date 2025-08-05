# 🤖 RAG: AI-Powered Question Answering System

A complete, production-ready AI-powered question-answering API service built with FastAPI, featuring **multi-user support with isolated document spaces**, modern web interface, semantic chunking, and comprehensive testing suite.

## 🎯 Assignment Requirements - ALL MET ✅

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
git clone <your-repo-url>
cd RAG
```

### **2. Set Up Environment**
```bash
# Copy environment template
cp env.example .env

# Edit .env file with your configuration
nano .env
```

### **3. Configure Environment Variables**
Edit the `.env` file with your settings:

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=your-openai-api-key-here

# Required: Database Configuration
POSTGRES_PASSWORD=your-db-password
SECRET_KEY=your-super-secret-key-change-this-in-production

# Optional: Customize other settings
GENERATION_MODEL_ID=gpt-3.5-turbo
EMBEDDING_MODEL_ID=text-embedding-3-large
```

### **4. Set Up Database**
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Set up database
sudo -u postgres psql
CREATE DATABASE minirag;
CREATE USER minirag_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE minirag TO minirag_user;
\q
```

### **5. Install Dependencies**
```bash
# Navigate to src directory
cd src

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **6. Run Database Migrations**
```bash
# From the project root
./run_migrations.sh
```

### **7. Start Qdrant (Vector Database)**
```bash
# Option 1: Using Docker (recommended)
./start_qdrant.sh

# Option 2: Using local storage (no Docker required)
# The system will automatically use local storage
```

### **8. Start the Application**
```bash
# Navigate to src directory
cd src

# Activate virtual environment
source venv/bin/activate

# Start the application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **9. Access the Application**
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## 🛠️ Tech Stack

### **Backend**
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with pgvector extension
- **ORM**: SQLAlchemy with async support
- **Migrations**: Alembic
- **Authentication**: JWT (JSON Web Tokens)
- **Validation**: Pydantic

### **AI/ML**
- **LLM Provider**: OpenAI GPT models
- **Embeddings**: OpenAI text-embedding-3-large (3072 dimensions)
- **Vector Database**: Qdrant
- **Text Chunking**: LangChain SemanticChunker
- **Similarity Search**: Cosine similarity

### **Frontend**
- **Language**: Vanilla JavaScript (ES6+)
- **Styling**: CSS3 with modern design
- **UI Components**: Custom-built components
- **HTTP Client**: Fetch API
- **Real-time**: WebSocket-like polling

### **Development & Testing**
- **Testing Framework**: pytest
- **Code Coverage**: pytest-cov
- **Async Testing**: pytest-asyncio
- **Mocking**: unittest.mock
- **Linting**: flake8 (recommended)

### **Deployment**
- **Container**: Docker (optional)
- **Process Manager**: uvicorn
- **Environment**: Python virtual environment
- **Configuration**: Environment variables

## 📚 API Usage & Swagger Documentation

### **Interactive API Documentation**
The application provides comprehensive API documentation through Swagger UI:

1. **Access Swagger UI**: http://localhost:8000/docs
2. **Alternative Documentation**: http://localhost:8000/redoc

### **Key API Endpoints**

#### **Authentication**
```bash
# Register new user
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "password123"
}

# Login user
POST /api/v1/auth/login
{
  "email": "user@example.com", 
  "password": "password123"
}

# Get user info
GET /api/v1/auth/me
Authorization: Bearer <token>
```

#### **Project Management**
```bash
# Create project
POST /api/v1/data/projects
{
  "project_code": "my-project",
  "project_name": "My Project"
}

# List user projects
GET /api/v1/data/projects

# Get project details
GET /api/v1/data/projects/{project_code}

# Delete project
DELETE /api/v1/data/projects/{project_code}
```

#### **File Operations**
```bash
# Upload file
POST /api/v1/data/upload/{project_code}
Content-Type: multipart/form-data
file: <file>

# Process files
POST /api/v1/data/process/{project_code}

# Get file content
GET /api/v1/data/file/content/{project_code}/{asset_id}

# Delete file
DELETE /api/v1/data/file/{project_code}/{asset_id}
```

#### **Question Answering**
```bash
# Ask question
POST /api/v1/nlp/ask
{
  "question": "What is this document about?",
  "project_code": "my-project"
}

# Get project info
GET /api/v1/nlp/index/info/{project_code}
```

### **API Response Format**
All API responses follow a consistent format:

```json
{
  "signal": "SUCCESS",
  "data": {
    // Response data
  },
  "message": "Operation completed successfully"
}
```

### **Error Handling**
The API provides detailed error responses:

```json
{
  "signal": "ERROR_TYPE",
  "error": "Error title",
  "message": "Detailed error message"
}
```

## ⚠️ Known Limitations

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

## 🚀 Deployment

### **Production Checklist**
- [ ] Set up production PostgreSQL database
- [ ] Configure environment variables
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure reverse proxy (nginx)
- [ ] Set up monitoring and logging
- [ ] Configure backup strategies
- [ ] Set up CI/CD pipeline

### **Docker Deployment**
```bash
# Build and run with Docker Compose
docker-compose up -d
```

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

**🎉 RAG: A complete, production-ready AI-powered question-answering system with full multi-user support and modern architecture!**
