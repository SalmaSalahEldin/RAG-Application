#!/bin/bash

# Run database migrations for Mini-RAG
echo "Running database migrations..."

# Navigate to the alembic directory
cd src/models/db_schemes/minirag

# Run migrations
alembic upgrade head

echo "Migrations completed!" 