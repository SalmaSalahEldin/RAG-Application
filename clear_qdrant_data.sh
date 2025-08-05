#!/bin/bash

echo "🗑️  Clearing All Qdrant Data..."
echo "==============================="

# Function to check if Qdrant server is running
check_qdrant_server() {
    if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to delete all collections via API
delete_collections_via_api() {
    echo "🔍 Checking for existing collections..."
    
    # Get all collections
    collections=$(curl -s http://localhost:6333/collections | jq -r '.collections[].name' 2>/dev/null)
    
    if [ -n "$collections" ]; then
        echo "📋 Found collections:"
        echo "$collections" | while read -r collection; do
            if [ -n "$collection" ]; then
                echo "   - $collection"
                # Delete the collection
                response=$(curl -s -X DELETE "http://localhost:6333/collections/$collection")
                if echo "$response" | jq -e '.status.ok' > /dev/null 2>&1; then
                    echo "   ✅ Deleted collection: $collection"
                else
                    echo "   ❌ Failed to delete collection: $collection"
                fi
            fi
        done
    else
        echo "ℹ️  No collections found"
    fi
}

# Function to clear local storage
clear_local_storage() {
    echo ""
    echo "🗂️  Clearing local Qdrant storage..."
    
    if [ -d "qdrant_storage" ]; then
        echo "📁 Found qdrant_storage directory"
        
        # Check if there are any files
        if [ "$(ls -A qdrant_storage 2>/dev/null)" ]; then
            echo "📄 Found files in qdrant_storage:"
            ls -la qdrant_storage/
            
            # Remove all contents
            rm -rf qdrant_storage/*
            echo "✅ Cleared all files from qdrant_storage/"
        else
            echo "ℹ️  qdrant_storage directory is already empty"
        fi
    else
        echo "ℹ️  qdrant_storage directory not found"
    fi
}

# Function to clear Qdrant Docker container (if running)
clear_docker_qdrant() {
    echo ""
    echo "🐳 Checking for Qdrant Docker containers..."
    
    if docker ps | grep -q qdrant; then
        echo "📦 Found running Qdrant container"
        container_name=$(docker ps | grep qdrant | awk '{print $NF}')
        echo "   Container: $container_name"
        
        # Stop and remove the container
        echo "🛑 Stopping Qdrant container..."
        docker stop "$container_name"
        docker rm "$container_name"
        echo "✅ Removed Qdrant container"
    else
        echo "ℹ️  No running Qdrant containers found"
    fi
}

# Main execution
echo "🔍 Checking Qdrant status..."

if check_qdrant_server; then
    echo "✅ Qdrant server is running on localhost:6333"
    delete_collections_via_api
else
    echo "ℹ️  Qdrant server is not running or not accessible"
fi

clear_local_storage
clear_docker_qdrant

echo ""
echo "🧹 Additional cleanup..."

# Remove any Qdrant-related temporary files
if [ -d "/tmp/qdrant" ]; then
    echo "🗑️  Clearing Qdrant temporary files..."
    rm -rf /tmp/qdrant
fi

# Check for any Qdrant processes
qdrant_processes=$(pgrep -f qdrant 2>/dev/null || true)
if [ -n "$qdrant_processes" ]; then
    echo "🔄 Found Qdrant processes: $qdrant_processes"
    echo "💡 You may want to restart Qdrant after clearing data"
fi

echo ""
echo "✅ Qdrant data clearing completed!"
echo ""
echo "🎯 Summary of actions taken:"
echo "   - ✅ Cleared all collections (if server was running)"
echo "   - ✅ Cleared local storage files"
echo "   - ✅ Removed Docker containers (if any)"
echo "   - ✅ Cleared temporary files"
echo ""
echo "🚀 To restart Qdrant (if needed):"
echo "   - Local storage mode: No restart needed"
echo "   - Server mode: ./start_qdrant.sh"
echo "   - Docker mode: docker run -d --name qdrant -p 6333:6333 -v \$(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant" 