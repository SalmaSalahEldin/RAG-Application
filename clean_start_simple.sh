#!/bin/bash

echo "Simple Clean Start for RAG..."
echo "====================================="

echo "🗑️  Clearing Qdrant storage..."
rm -rf qdrant_storage/* 2>/dev/null || true

echo ""
echo "🎯 Setting up environment..."
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp env.example .env
    echo "✅ .env file created. Please update it with your API keys."
fi

echo ""
echo "🔧 Running database migrations..."
cd src/models/db_schemes/minirag

# Activate virtual environment and check database connection
echo "Testing database connection..."
source ../../../venv/bin/activate
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
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('💡 Make sure PostgreSQL is running and accessible')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "Running Alembic migrations..."
    alembic upgrade head
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Cannot run migrations - database not accessible"
    echo "💡 Please ensure PostgreSQL is running and accessible"
    echo "💡 Default connection: localhost:5432, database: minirag, user: postgres, password: postgres"
fi

cd ../../../..

echo ""
echo "✅ Clean setup completed!"
echo ""
echo "🌐 Expected services:"
echo "   - PostgreSQL: localhost:5432 (database: minirag)"
echo "   - Qdrant: localhost:6333 (if using Qdrant server)"
echo ""
echo "🚀 To start the application:"
echo "   cd src && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
echo "💡 To check if services are running:"
echo "   - PostgreSQL: sudo systemctl status postgresql"
echo "   - Qdrant: curl http://localhost:6333/collections" 