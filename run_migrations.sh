#!/bin/bash

echo "🔄 Running Database Migrations..."
echo "================================"

# Navigate to the alembic directory
cd src/models/db_schemes/minirag

# Check if we're in the right directory
if [ ! -f "alembic.ini" ]; then
    echo "❌ Error: alembic.ini not found. Please run this script from the project root."
    exit 1
fi

# Activate virtual environment
if [ -f "../../../venv/bin/activate" ]; then
    source ../../../venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found at ../../../venv/bin/activate"
    echo "💡 Please ensure the virtual environment is set up correctly."
    exit 1
fi

# Check if alembic is available
if ! command -v alembic &> /dev/null; then
    echo "❌ Alembic not found. Please install it in your virtual environment:"
    echo "   pip install alembic"
    exit 1
fi

# Test database connection
echo "🔍 Testing database connection..."
if ! psql -h localhost -U postgres -d minirag -c "SELECT 1;" > /dev/null 2>&1; then
    echo "❌ Cannot connect to database. Please check:"
    echo "   - PostgreSQL is running"
    echo "   - Database 'minirag' exists"
    echo "   - User 'postgres' has correct password"
    exit 1
fi
echo "✅ Database connection successful"

# Run migrations
echo ""
echo "🚀 Applying migrations..."
if alembic upgrade head; then
    echo "✅ Migrations completed successfully!"
    
    # Show current status
    echo ""
    echo "📊 Current migration status:"
    alembic current
else
    echo "❌ Migration failed!"
    echo "💡 Check the error messages above and refer to MIGRATION_GUIDE.md for troubleshooting."
    exit 1
fi 