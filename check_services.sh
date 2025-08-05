#!/bin/bash

echo "🔍 Checking Mini-RAG Services..."
echo "================================"

echo ""
echo "📊 PostgreSQL Status:"
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL client installed"
    
    # Check if PostgreSQL service is running
    if sudo systemctl is-active --quiet postgresql; then
        echo "✅ PostgreSQL service is running"
        
        # Test connection
        if psql -h localhost -U postgres -d postgres -c "SELECT 1;" &> /dev/null; then
            echo "✅ PostgreSQL connection successful"
        else
            echo "❌ PostgreSQL connection failed"
            echo "💡 Try: sudo -u postgres psql"
        fi
    else
        echo "❌ PostgreSQL service is not running"
        echo "💡 Start with: sudo systemctl start postgresql"
    fi
else
    echo "❌ PostgreSQL client not installed"
    echo "💡 Install with: sudo apt install postgresql-client"
fi

echo ""
echo "🗄️  Database Setup:"
# Check if minirag database exists
if psql -h localhost -U postgres -lqt | cut -d \| -f 1 | grep -qw minirag; then
    echo "✅ minirag database exists"
else
    echo "❌ minirag database not found"
    echo "💡 Create with: sudo -u postgres createdb minirag"
fi

echo ""
echo "🔍 Qdrant Status:"
if [ -d "qdrant_storage" ]; then
    echo "✅ Qdrant storage directory exists"
    echo "📁 Storage location: $(pwd)/qdrant_storage/"
else
    echo "❌ Qdrant storage directory not found"
    echo "💡 Creating qdrant_storage directory..."
    mkdir -p qdrant_storage
fi

echo ""
echo "🐍 Python Environment:"
if [ -d "src/venv" ]; then
    echo "✅ Virtual environment exists"
    
    # Check if psycopg2 is installed
    source src/venv/bin/activate
    if python -c "import psycopg2" &> /dev/null; then
        echo "✅ psycopg2 installed"
    else
        echo "❌ psycopg2 not installed"
        echo "💡 Install with: pip install psycopg2-binary"
    fi
else
    echo "❌ Virtual environment not found"
    echo "💡 Create with: python -m venv src/venv"
fi

echo ""
echo "📝 Environment File:"
if [ -f ".env" ]; then
    echo "✅ .env file exists"
else
    echo "❌ .env file not found"
    echo "💡 Create with: cp env.example .env"
fi

echo ""
echo "🎯 Summary:"
echo "To run the project with clean databases:"
echo "1. Ensure PostgreSQL is running: sudo systemctl start postgresql"
echo "2. Create database: sudo -u postgres createdb minirag"
echo "3. Run clean start: ./clean_start_simple.sh"
echo "4. Start application: cd src && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000" 