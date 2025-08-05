# 🧹 Clean Start Guide for RAG

This guide will help you run the RAG project with completely clean PostgreSQL and Qdrant databases.

## 🚀 Quick Start

```bash
# Navigate to your project directory
cd /path/to/your/project
```

### Option 2: Manual Clean Start

If you prefer to do it manually, follow these steps:

## 📋 Prerequisites

1. **Docker** must be running
2. **Python virtual environment** should be activated
3. **Project dependencies** should be installed

## 🔧 Step-by-Step Manual Process

### 1. Stop Existing Services

```bash
# Stop all running containers
docker stop $(docker ps -q) 2>/dev/null || true

# Remove containers
docker rm $(docker ps -aq) 2>/dev/null || true

# Remove volumes
docker volume rm $(docker volume ls -q) 2>/dev/null || true
```

### 2. Clear Qdrant Storage

```bash
# Remove Qdrant storage directory
rm -rf qdrant_storage/*
```

### 3. Start Fresh PostgreSQL

```bash
# Navigate to docker directory
cd docker

# Start PostgreSQL with pgvector
docker-compose up -d pgvector

# Wait for PostgreSQL to be ready
sleep 10

# Go back to project root
cd ..
```

### 4. Start Fresh Qdrant

```bash
# Start Qdrant server
docker run -d \
    --name qdrant \
    -p 6333:6333 \
    -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant

# Wait for Qdrant to be ready
sleep 5
```

### 5. Run Database Migrations

```bash
# Navigate to alembic directory
cd src/models/db_schemes/minirag

# Run migrations
alembic upgrade head

# Go back to project root
cd ../../../..
```

### 6. Set Up Environment

```bash
# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    cp env.example .env
    echo "✅ .env file created. Please update it with your API keys."
fi
```

### 7. Start the Application

```bash
# Navigate to src directory
cd src

# Activate virtual environment
source venv/bin/activate

# Start the application
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🌐 Service URLs

After running the clean start:

- **Application**: http://localhost:8000
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **PostgreSQL**: localhost:5470

## 🔍 Verification Steps

### 1. Check PostgreSQL Connection

```bash
# Test database connection
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5470,
        database='postgres',
        user='postgres',
        password='postgres'
    )
    print('✅ PostgreSQL connection successful')
    conn.close()
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
"
```

### 2. Check Qdrant Connection

```bash
# Test Qdrant connection
curl -s http://localhost:6333/collections | jq .
```

### 3. Check Application

```bash
# Test application health
curl -s http://localhost:8000/health | jq .
```

## 🚨 Troubleshooting

### Database Connection Issues

If you get database connection errors:

1. **Check if PostgreSQL is running**:
   ```bash
   docker ps | grep pgvector
   ```

2. **Check PostgreSQL logs**:
   ```bash
   docker logs pgvector
   ```

3. **Wait longer for startup**:
   ```bash
   sleep 20  # Wait 20 seconds instead of 10
   ```

### Qdrant Connection Issues

If you get Qdrant connection errors:

1. **Check if Qdrant is running**:
   ```bash
   docker ps | grep qdrant
   ```

2. **Check Qdrant logs**:
   ```bash
   docker logs qdrant
   ```

3. **Restart Qdrant**:
   ```bash
   docker restart qdrant
   ```

### Migration Issues

If migrations fail:

1. **Check database connection**:
   ```bash
   cd src/models/db_schemes/minirag
   python3 -c "import psycopg2; conn = psycopg2.connect(host='localhost', port=5470, database='postgres', user='postgres', password='postgres'); print('Connected'); conn.close()"
   ```

2. **Check migration status**:
   ```bash
   alembic current
   ```

3. **Reset migrations**:
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

## 🎯 What Gets Cleared

When you run the clean start:

- ✅ **PostgreSQL data**: All tables, users, and data
- ✅ **Qdrant collections**: All vector collections and embeddings
- ✅ **Application data**: All projects, files, and user data
- ✅ **Logs**: All application and database logs

## 🔄 Regular Restart

For regular restarts (without clearing data):

```bash
# Stop services
docker stop pgvector qdrant

# Start services
cd docker && docker-compose up -d pgvector && cd ..
docker start qdrant

# Start application
cd src && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📝 Notes

- The clean start will **completely erase all data**
- Make sure to backup any important data before running
- The process takes about 2-3 minutes to complete
- All services will be running on their default ports
- The application will be ready for fresh testing

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify Docker is running: `docker info`
3. Check service logs: `docker logs <service-name>`
4. Ensure ports 5470, 6333, and 8000 are available 