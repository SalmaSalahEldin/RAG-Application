#!/bin/bash
echo "🚀 Starting Qdrant Server..."
echo "📝 This will start Qdrant server on localhost:6333"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Qdrant container is already running
if docker ps | grep -q qdrant; then
    echo "✅ Qdrant server is already running"
    echo "🌐 Access Qdrant at: http://localhost:6333"
else
    echo "🔧 Starting Qdrant server..."
    docker run -d \
        --name qdrant \
        -p 6333:6333 \
        -p 6334:6334 \
        -v $(pwd)/qdrant_storage:/qdrant/storage \
        qdrant/qdrant
    
    echo "✅ Qdrant server started successfully!"
    echo "🌐 Access Qdrant at: http://localhost:6333"
    echo "📊 Dashboard at: http://localhost:6333/dashboard"
fi

echo ""
echo "💡 To stop Qdrant server: docker stop qdrant"
echo "💡 To remove Qdrant container: docker rm qdrant" 