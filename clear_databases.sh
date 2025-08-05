#!/bin/bash

echo "Clearing databases for RAG..."
echo "===================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "🛑 Stopping existing containers..."
docker stop pgvector qdrant 2>/dev/null || true
docker rm pgvector qdrant 2>/dev/null || true

echo "🗑️  Removing PostgreSQL volume..."
docker volume rm mini-rag_pgvector_data 2>/dev/null || true

echo "🗑️  Clearing Qdrant storage..."
rm -rf qdrant_storage/* 2>/dev/null || true

echo ""
echo "🚀 Starting fresh PostgreSQL with pgvector..."

# Create .env file for docker-compose if it doesn't exist
if [ ! -f docker/.env ]; then
    echo "📝 Creating docker/.env file..."
    cat > docker/.env << EOF
POSTGRES_PASSWORD=postgres
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=password
EOF
fi

cd docker
docker compose up -d pgvector
cd ..

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 15

echo "🚀 Starting Qdrant server..."
docker run -d \
    --name qdrant \
    -p 6333:6333 \
    -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant

echo "⏳ Waiting for Qdrant to be ready..."
sleep 5

echo ""
echo "🔧 Running database migrations..."
cd src/models/db_schemes/minirag

# Check if we can connect to the database
echo "Testing database connection..."
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
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "Running Alembic migrations..."
    alembic upgrade head
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Cannot run migrations - database not accessible"
    echo "Please check if PostgreSQL is running on port 5470"
    echo "You may need to wait longer for PostgreSQL to start up"
fi

cd ../../../..

echo ""
echo "✅ Database clearing completed!"
echo ""
echo "🌐 Services running:"
echo "   - PostgreSQL (pgvector): localhost:5470"
echo "   - Qdrant: localhost:6333"
echo ""
echo "🚀 To start the application:"
echo "   cd src && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000" 