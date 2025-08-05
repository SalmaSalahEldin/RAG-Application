#!/bin/bash

echo "🔍 Checking Migration Status..."
echo "==============================="

# Navigate to alembic directory
cd src/models/db_schemes/minirag

# Activate virtual environment
if [ -f "../../../venv/bin/activate" ]; then
    source ../../../venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found at ../../../venv/bin/activate"
    exit 1
fi

# Check if alembic is available
if ! command -v alembic &> /dev/null; then
    echo "❌ Alembic not found. Please install it in your virtual environment."
    exit 1
fi

echo ""
echo "📊 Current Migration Status:"
echo "----------------------------"
alembic current

echo ""
echo "📜 Migration History:"
echo "-------------------"
alembic history

echo ""
echo "🗄️  Database Tables:"
echo "------------------"
if command -v psql &> /dev/null; then
    psql -h localhost -U postgres -d minirag -c "\dt" 2>/dev/null || echo "❌ Cannot connect to database. Check PostgreSQL connection."
else
    echo "❌ psql not found. Please install PostgreSQL client."
fi

echo ""
echo "✅ Migration check completed!" 