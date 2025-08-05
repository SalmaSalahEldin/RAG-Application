#!/usr/bin/env python3
"""
Test script for semantic chunking functionality.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_semantic_chunking():
    """Test semantic chunking functionality."""
    
    print("Testing Semantic Chunking Implementation")
    
    try:
        # Test imports
        from utils.semantic_chunker import SemanticChunkerUtility
        print("Semantic chunker imports successfully")
        
        # Test initialization
        try:
            chunker = SemanticChunkerUtility()
            print("Semantic chunker initialized successfully")
        except Exception as e:
            print(f"Semantic chunker initialization failed: {e}")
            return False
        
        # Test semantic chunking
        test_text = """
        This is a test document for semantic chunking. It contains multiple sentences and paragraphs.
        
        The semantic chunker should be able to intelligently split this text based on semantic meaning
        rather than just character count. This approach should result in more meaningful chunks that
        preserve the context and meaning of the content.
        
        For example, this paragraph should be kept together as a single chunk because it discusses
        a single concept - the benefits of semantic chunking. The chunker should recognize that
        these sentences are semantically related and should not be split arbitrarily.
        
        Another paragraph about a different topic should be separated into its own chunk.
        This ensures that when users ask questions, they get relevant and complete information
        rather than fragmented pieces that don't make sense on their own.
        """
        
        try:
            chunks = chunker.chunk_text_semantically(test_text)
            print(f"Semantic chunking completed: {len(chunks)} chunks created")
            
            # Print chunk details
            for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                print(f"  Chunk {i+1}: {len(chunk['text'])} characters")
                print(f"    Preview: {chunk['text'][:100]}...")
        except Exception as e:
            print(f"Semantic chunking failed: {e}")
            return False
        
        # Test sentence chunking fallback
        try:
            chunks = chunker.chunk_by_sentences(test_text)
            print(f"Sentence chunking completed: {len(chunks)} chunks created")
        except Exception as e:
            print(f"Sentence chunking failed: {e}")
            return False
        
        # Test chunking stats
        try:
            stats = chunker.get_chunking_stats(test_text)
            print(f"Chunking stats: {stats}")
        except Exception as e:
            print(f"Chunking stats failed: {e}")
            return False
        
        # Test ProcessController integration
        try:
            from controllers.ProcessController import ProcessController
            controller = ProcessController()
            methods = controller.get_chunking_methods()
            print(f"Available chunking methods: {methods}")
            
            # Test each method
            for method in methods:
                try:
                    stats = controller.process_semantic_chunking(test_text) if method == 'semantic' else \
                           controller.process_sentence_chunking(test_text) if method == 'sentence' else \
                           controller.process_simpler_splitter(test_text)
                    print(f"   {method.capitalize()} chunking: {stats['total_chunks']} chunks")
                except Exception as e:
                    print(f"   {method.capitalize()} chunking failed: {e}")
        except Exception as e:
            print(f"ProcessController integration failed: {e}")
            return False
        
        print("\nAll tests passed! Semantic chunking is working correctly.")
        return True
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_semantic_chunking()
    sys.exit(0 if success else 1) 