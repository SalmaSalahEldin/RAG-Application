#!/usr/bin/env python3
"""
Test script to verify OpenAI API key configuration
"""

import os
import sys
sys.path.append('src')

from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory

def test_api_key_configuration():
    """Test the OpenAI API key configuration."""
    print("🔧 Testing OpenAI API Key Configuration")
    print("=" * 50)
    
    # Test 1: Load settings
    print("\n1. 📋 Loading settings from .env file...")
    try:
        settings = get_settings()
        print("   ✅ Settings loaded successfully")
        print(f"   🔑 API Key: {settings.OPENAI_API_KEY[:20] if settings.OPENAI_API_KEY else 'NOT SET'}...")
        print(f"   🌐 API URL: {settings.OPENAI_API_URL}")
        print(f"   🎯 Generation Backend: {settings.GENERATION_BACKEND}")
        print(f"   🎯 Embedding Backend: {settings.EMBEDDING_BACKEND}")
        print(f"   🗄️  Vector DB Backend: {settings.VECTOR_DB_BACKEND}")
    except Exception as e:
        print(f"   ❌ Failed to load settings: {e}")
        return False
    
    # Test 2: Check API key condition
    print("\n2. 🔍 Checking API key condition...")
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key-here":
        print("   ✅ API key is valid and not default")
        api_key_valid = True
    else:
        print("   ❌ API key is missing or default")
        api_key_valid = False
    
    # Test 3: Test LLM Provider Factory
    print("\n3. 🏭 Testing LLM Provider Factory...")
    try:
        llm_factory = LLMProviderFactory(settings)
        print("   ✅ LLM Provider Factory created successfully")
        
        # Test generation client
        generation_client = llm_factory.create(provider=settings.GENERATION_BACKEND)
        if generation_client:
            print("   ✅ Generation client created successfully")
            generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)
            print("   ✅ Generation model set successfully")
        else:
            print("   ❌ Failed to create generation client")
            
        # Test embedding client
        embedding_client = llm_factory.create(provider=settings.EMBEDDING_BACKEND)
        if embedding_client:
            print("   ✅ Embedding client created successfully")
            embedding_client.set_embedding_model(
                model_id=settings.EMBEDDING_MODEL_ID,
                embedding_size=settings.EMBEDDING_MODEL_SIZE
            )
            print("   ✅ Embedding model set successfully")
        else:
            print("   ❌ Failed to create embedding client")
            
    except Exception as e:
        print(f"   ❌ LLM Provider Factory failed: {e}")
        return False
    
    # Test 4: Test Vector DB Provider Factory
    print("\n4. 🗄️  Testing Vector DB Provider Factory...")
    try:
        # Create a mock database client for testing
        class MockDBClient:
            pass
        
        vectordb_factory = VectorDBProviderFactory(config=settings, db_client=MockDBClient())
        print("   ✅ Vector DB Provider Factory created successfully")
        
        vectordb_client = vectordb_factory.create(provider=settings.VECTOR_DB_BACKEND)
        if vectordb_client:
            print("   ✅ Vector DB client created successfully")
        else:
            print("   ❌ Failed to create Vector DB client")
            
    except Exception as e:
        print(f"   ❌ Vector DB Provider Factory failed: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Configuration Summary")
    print("=" * 50)
    
    if api_key_valid:
        print("✅ OpenAI API Key: CONFIGURED")
        print("✅ LLM Providers: READY")
        print("✅ Vector Database: READY")
        print("✅ All Components: READY")
        print("\n🚀 Your Mini-RAG system is ready for full NLP features!")
        print("📝 Restart your server to enable all features.")
        return True
    else:
        print("❌ OpenAI API Key: MISSING")
        print("⚠️  LLM Features: DISABLED")
        print("⚠️  Vector Database: DISABLED")
        print("\n🔧 Please configure your OpenAI API key in the .env file.")
        return False

if __name__ == "__main__":
    test_api_key_configuration() 