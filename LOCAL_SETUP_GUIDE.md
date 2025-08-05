# 🏠 Local Setup Guide for Mini-RAG

This guide will help you set up PostgreSQL and Qdrant locally without Docker for the Mini-RAG project.

## 📋 Prerequisites

1. **PostgreSQL** installed and running locally
2. **Python** with virtual environment
3. **Qdrant** (optional - can use local storage)

## 🔧 PostgreSQL Setup

### Option 1: Install PostgreSQL Locally

#### Ubuntu/Debian:
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Switch to postgres user and create database
sudo -u postgres psql
```

#### macOS:
```bash
# Install with Homebrew
brew install postgresql

# Start PostgreSQL service
brew services start postgresql
```

#### Windows:
Download and install from: https://www.postgresql.org/download/windows/

### Option 2: Use Docker for PostgreSQL Only

If you prefer to use Docker just for PostgreSQL:

```bash
# Create a simple PostgreSQL container
docker run -d \
    --name postgres-minirag \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=minirag \
    -p 5432:5432 \
    postgres:15

# Wait for it to start
sleep 10
```

## 🗄️ Database Setup

### 1. Create Database and User

```bash
# Connect to PostgreSQL as postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE minirag;
CREATE USER minirag_user WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE minirag TO minirag_user;
\q
```

### 2. Install pgvector Extension

```bash
# Install pgvector extension
sudo apt install postgresql-15-pgvector  # Adjust version as needed

# Or if using Docker:
docker exec -it postgres-minirag psql -U postgres -d minirag -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## 🔍 Qdrant Setup

### Option 1: Local Storage (Recommended)

The project is configured to use Qdrant in local storage mode by default. No additional setup needed.

### Option 2: Qdrant Server

If you want to use Qdrant server:

```bash
# Install Qdrant
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz | tar xz

# Start Qdrant server
./qdrant
```

## ⚙️ Environment Configuration

### 1. Create Environment File

```bash
# Copy example environment file
cp env.example .env
```

### 2. Update Environment Variables

Edit `.env` file with your configuration:

```env
# Database Configuration
POSTGRES_USERNAME=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_MAIN_DATABASE=minirag

# Vector Database Configuration
VECTOR_DB_BACKEND=qdrant
VECTOR_DB_PATH=./qdrant_storage
VECTOR_DB_DISTANCE_METHOD=cosine

# OpenAI Configuration (Required for LLM features)
OPENAI_API_KEY=your-openai-api-key-here

# Other settings...
```

## 🚀 Quick Start

### 1. Run Clean Start Script

```bash
# Make sure you're in the project root
cd /path/to/your/project

# Run the simple clean start
./clean_start_simple.sh
```

### 2. Start the Application

```bash
# Navigate to src directory
cd src

# Activate virtual environment
source venv/bin/activate

# Start the application
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🔍 Verification

### 1. Check PostgreSQL Connection

```bash
# Test database connection
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='minirag',
        user='postgres',
        password='postgres'
    )
    print('✅ PostgreSQL connection successful')
    conn.close()
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
"
```

### 2. Check Application

```bash
# Test application health
curl -s http://localhost:8000/health
```

## 🛠️ Troubleshooting

### PostgreSQL Issues

1. **Service not running**:
   ```bash
   sudo systemctl status postgresql
   sudo systemctl start postgresql
   ```

2. **Connection refused**:
   ```bash
   # Check if PostgreSQL is listening
   sudo netstat -tlnp | grep 5432
   
   # Check PostgreSQL logs
   sudo tail -f /var/log/postgresql/postgresql-*.log
   ```

3. **Authentication failed**:
   ```bash
   # Edit PostgreSQL configuration
   sudo nano /etc/postgresql/*/main/pg_hba.conf
   
   # Add this line for local connections:
   local   all             all                                     trust
   
   # Restart PostgreSQL
   sudo systemctl restart postgresql
   ```

### Qdrant Issues

1. **Local storage not working**:
   ```bash
   # Check if qdrant_storage directory exists
   ls -la qdrant_storage/
   
   # Create if missing
   mkdir -p qdrant_storage/
   ```

2. **Qdrant server issues**:
   ```bash
   # Check if Qdrant is running
   curl http://localhost:6333/collections
   
   # Start Qdrant server if needed
   ./qdrant
   ```

### Migration Issues

1. **Database not accessible**:
   ```bash
   # Check database connection
   psql -h localhost -U postgres -d minirag
   ```

2. **Migration fails**:
   ```bash
   # Check migration status
   cd src/models/db_schemes/minirag
   alembic current
   
   # Reset migrations
   alembic downgrade base
   alembic upgrade head
   ```

## 📝 Notes

- **PostgreSQL**: Runs on port 5432 by default
- **Qdrant**: Uses local storage by default (no server needed)
- **Application**: Runs on port 8000
- **Database**: Uses `minirag` database with `postgres` user
- **Vector storage**: Stored in `./qdrant_storage/` directory

## 🔄 Regular Restart

For regular restarts (without clearing data):

```bash
# Start PostgreSQL (if using system service)
sudo systemctl start postgresql

# Start application
cd src && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify PostgreSQL is running: `sudo systemctl status postgresql`
3. Check application logs for specific errors
4. Ensure ports 5432 and 8000 are available
5. Verify your `.env` file has correct database settings 