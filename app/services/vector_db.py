from pinecone import Pinecone
from typing import List, Dict, Any, Optional
import numpy as np
from app.config import settings

class VectorDBService:
    def upsert_research(self, session_id: str, embedding: list, metadata: dict):
        if not self.initialized:
            return False
        self.index.upsert([(session_id, embedding, metadata)])
        return True

    def query_research(self, embedding: list, top_k: int = 5):
        if not self.initialized:
            return []
        return self.index.query(embedding, top_k=top_k, include_metadata=True)
    def __init__(self):
        self.index = None
        self.initialized = False
        self.init_pinecone()
    
    def init_pinecone(self):
        """Initialize Pinecone connection"""
        try:
            # Create Pinecone instance
            pc = Pinecone(
                api_key=settings.pinecone_api_key
            )
            
            # Check if index exists, create if not
            if settings.pinecone_index_name not in pc.list_indexes().names():
                pc.create_index(
                    name=settings.pinecone_index_name,
                    dimension=768,  # Standard embedding dimension
                    metric="cosine"
                )
            
            self.index = pc.Index(settings.pinecone_index_name)
            self.initialized = True
            print("Pinecone initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize Pinecone: {str(e)}")
            self.initialized = False
    
    async def store_chat_embeddings(self, session_id: str, messages: List[Dict], embeddings: List[List[float]]):
        """Store chat messages with their embeddings"""
        if not self.initialized:
            return False
        
        try:
            vectors = []
            for i, (message, embedding) in enumerate(zip(messages, embeddings)):
                vector_id = f"{session_id}_{i}"
                metadata = {
                    "session_id": session_id,
                    "message_type": message.get("message_type"),
                    "content": message.get("content"),
                    "timestamp": message.get("timestamp").isoformat() if message.get("timestamp") else None,
                    "user_id": message.get("user_id")
                }
                
                vectors.append((vector_id, embedding, metadata))
            
            # Upsert vectors in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            return True
            
        except Exception as e:
            print(f"Failed to store embeddings: {str(e)}")
            return False
    
    async def search_similar_messages(self, query_embedding: List[float], user_id: str, limit: int = 5) -> List[Dict]:
        """Search for similar messages in vector database"""
        if not self.initialized:
            return []
        
        try:
            results = self.index.query(
                vector=query_embedding,
                filter={"user_id": user_id},
                top_k=limit,
                include_metadata=True
            )
            
            similar_messages = []
            for match in results.matches:
                if match.metadata:
                    similar_messages.append({
                        "content": match.metadata.get("content", ""),
                        "message_type": match.metadata.get("message_type", ""),
                        "timestamp": match.metadata.get("timestamp", ""),
                        "score": match.score
                    })
            
            return similar_messages
            
        except Exception as e:
            print(f"Failed to search embeddings: {str(e)}")
            return []
    
    async def get_chat_history_embeddings(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Retrieve chat history with embeddings for a session"""
        if not self.initialized:
            return []
        
        try:
            # This is a simplified implementation
            # In production, you might want to use a different approach
            results = self.index.query(
                vector=[0] * 768,  # Dummy vector
                filter={"session_id": session_id},
                top_k=limit,
                include_metadata=True
            )
            
            messages = []
            for match in results.matches:
                if match.metadata:
                    messages.append({
                        "content": match.metadata.get("content", ""),
                        "message_type": match.metadata.get("message_type", ""),
                        "timestamp": match.metadata.get("timestamp", ""),
                        "score": match.score
                    })
            
            # Sort by timestamp
            messages.sort(key=lambda x: x.get("timestamp", ""))
            return messages
            
        except Exception as e:
            print(f"Failed to retrieve chat history: {str(e)}")
            return []
    
    async def delete_session_embeddings(self, session_id: str) -> bool:
        """Delete all embeddings for a session"""
        if not self.initialized:
            return False
        
        try:
            # Get all vectors for the session
            results = self.index.query(
                vector=[0] * 768,  # Dummy vector
                filter={"session_id": session_id},
                top_k=1000,
                include_metadata=True
            )
            
            # Delete all vectors
            vector_ids = [match.id for match in results.matches]
            if vector_ids:
                self.index.delete(ids=vector_ids)
            
            return True
            
        except Exception as e:
            print(f"Failed to delete session embeddings: {str(e)}")
            return False
    
    async def store_research_embeddings(self, symbol: str, research_data: Dict, embedding: List[float]):
        """Store research data with embeddings for future reference"""
        if not self.initialized:
            return False
        
        try:
            vector_id = f"research_{symbol}_{research_data.get('timestamp', '')}"
            metadata = {
                "type": "research",
                "symbol": symbol,
                "query": research_data.get("query", ""),
                "summary": research_data.get("summary", ""),
                "timestamp": research_data.get("timestamp", ""),
                "user_id": research_data.get("user_id", "")
            }
            
            self.index.upsert(vectors=[(vector_id, embedding, metadata)])
            return True
            
        except Exception as e:
            print(f"Failed to store research embeddings: {str(e)}")
            return False
    
    async def search_similar_research(self, query_embedding: List[float], symbol: str = None, limit: int = 3) -> List[Dict]:
        """Search for similar research reports"""
        if not self.initialized:
            return []
        
        try:
            filter_dict = {"type": "research"}
            if symbol:
                filter_dict["symbol"] = symbol
            
            results = self.index.query(
                vector=query_embedding,
                filter=filter_dict,
                top_k=limit,
                include_metadata=True
            )
            
            similar_research = []
            for match in results.matches:
                if match.metadata:
                    similar_research.append({
                        "symbol": match.metadata.get("symbol", ""),
                        "query": match.metadata.get("query", ""),
                        "summary": match.metadata.get("summary", ""),
                        "timestamp": match.metadata.get("timestamp", ""),
                        "score": match.score
                    })
            
            return similar_research
            
        except Exception as e:
            print(f"Failed to search research embeddings: {str(e)}")
            return []

# Global instance
vector_db = VectorDBService()