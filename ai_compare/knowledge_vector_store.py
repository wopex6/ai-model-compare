"""
Vector Store for Knowledge Retrieval
Uses ChromaDB for semantic search across processed texts
Generic and character-agnostic
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import hashlib


try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("ChromaDB not installed. Install with: pip install chromadb")


class KnowledgeVectorStore:
    """
    Vector store for semantic knowledge retrieval
    Generic - works for any character/domain
    """
    
    def __init__(self, storage_path: str = "knowledge_data/vector_db"):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is required. Install with: pip install chromadb")
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.storage_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Cache for collections
        self._collections = {}
    
    def get_or_create_collection(self, 
                                 character_id: str,
                                 embedding_function: Optional[str] = None) -> any:
        """
        Get or create a collection for a character
        Each character has their own collection for knowledge isolation
        """
        collection_name = f"knowledge_{character_id}"
        
        if collection_name in self._collections:
            return self._collections[collection_name]
        
        # Create or get collection
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"character_id": character_id}
            )
            self._collections[collection_name] = collection
            return collection
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise
    
    def add_text_chunks(self,
                       character_id: str,
                       chunks: List[str],
                       source_id: str,
                       author: Optional[str] = None,
                       title: Optional[str] = None,
                       field: Optional[str] = None,
                       metadata: Optional[Dict] = None) -> int:
        """
        Add text chunks to vector store
        Generic - works for any content
        
        Returns: Number of chunks added
        """
        collection = self.get_or_create_collection(character_id)
        
        # Prepare data
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            
            # Create unique ID
            chunk_id = self._create_chunk_id(source_id, i)
            
            # Prepare metadata
            chunk_metadata = {
                "source_id": source_id,
                "chunk_index": i,
                "character_id": character_id
            }
            
            if author:
                chunk_metadata["author"] = author
            if title:
                chunk_metadata["title"] = title
            if field:
                chunk_metadata["field"] = field
            if metadata:
                chunk_metadata.update(metadata)
            
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append(chunk_metadata)
        
        # Add to collection in batches
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_docs = documents[i:i+batch_size]
            batch_metadata = metadatas[i:i+batch_size]
            
            try:
                collection.add(
                    ids=batch_ids,
                    documents=batch_docs,
                    metadatas=batch_metadata
                )
            except Exception as e:
                print(f"Error adding batch {i}: {e}")
        
        return len(ids)
    
    def search(self,
              character_id: str,
              query: str,
              n_results: int = 5,
              filter_author: Optional[str] = None,
              filter_field: Optional[str] = None,
              filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Semantic search across character's knowledge base
        Generic - works with any query
        
        Returns: List of relevant chunks with metadata
        """
        collection = self.get_or_create_collection(character_id)
        
        # Build filter criteria
        where_filter = {}
        if filter_author:
            where_filter["author"] = filter_author
        if filter_field:
            where_filter["field"] = filter_field
        if filter_metadata:
            where_filter.update(filter_metadata)
        
        # Perform search
        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter if where_filter else None
            )
            
            # Format results
            formatted_results = []
            
            if results and results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else []
                distances = results['distances'][0] if results['distances'] else []
                
                for i, doc in enumerate(documents):
                    result = {
                        "text": doc,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "distance": distances[i] if i < len(distances) else None,
                        "relevance_score": 1.0 - (distances[i] if i < len(distances) else 0.5)
                    }
                    formatted_results.append(result)
            
            return formatted_results
        
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_sources_for_character(self, character_id: str) -> List[str]:
        """Get all unique source IDs for a character"""
        collection = self.get_or_create_collection(character_id)
        
        try:
            # Get all documents
            results = collection.get()
            
            # Extract unique source IDs
            if results and results['metadatas']:
                source_ids = set(
                    meta.get('source_id') 
                    for meta in results['metadatas'] 
                    if meta.get('source_id')
                )
                return list(source_ids)
        except Exception as e:
            print(f"Error getting sources: {e}")
        
        return []
    
    def get_count(self, character_id: str) -> int:
        """Get total number of chunks for a character"""
        collection = self.get_or_create_collection(character_id)
        
        try:
            return collection.count()
        except Exception as e:
            print(f"Error getting count: {e}")
            return 0
    
    def delete_source(self, character_id: str, source_id: str) -> int:
        """Delete all chunks from a specific source"""
        collection = self.get_or_create_collection(character_id)
        
        try:
            # Get all IDs for this source
            results = collection.get(
                where={"source_id": source_id}
            )
            
            if results and results['ids']:
                collection.delete(ids=results['ids'])
                return len(results['ids'])
        except Exception as e:
            print(f"Error deleting source: {e}")
        
        return 0
    
    def clear_character_knowledge(self, character_id: str):
        """Clear all knowledge for a character"""
        collection_name = f"knowledge_{character_id}"
        
        try:
            self.client.delete_collection(name=collection_name)
            if collection_name in self._collections:
                del self._collections[collection_name]
        except Exception as e:
            print(f"Error clearing knowledge: {e}")
    
    def get_statistics(self, character_id: str) -> Dict:
        """Get statistics about character's knowledge base"""
        collection = self.get_or_create_collection(character_id)
        
        try:
            total_chunks = collection.count()
            
            # Get all metadata to calculate stats
            results = collection.get()
            
            authors = set()
            fields = set()
            sources = set()
            
            if results and results['metadatas']:
                for meta in results['metadatas']:
                    if meta.get('author'):
                        authors.add(meta['author'])
                    if meta.get('field'):
                        fields.add(meta['field'])
                    if meta.get('source_id'):
                        sources.add(meta['source_id'])
            
            return {
                "total_chunks": total_chunks,
                "unique_authors": len(authors),
                "unique_fields": len(fields),
                "unique_sources": len(sources),
                "authors": sorted(list(authors)),
                "fields": sorted(list(fields))
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {
                "total_chunks": 0,
                "unique_authors": 0,
                "unique_fields": 0,
                "unique_sources": 0,
                "authors": [],
                "fields": []
            }
    
    def _create_chunk_id(self, source_id: str, chunk_index: int) -> str:
        """Create unique chunk ID"""
        combined = f"{source_id}_{chunk_index}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def batch_search(self,
                    character_id: str,
                    queries: List[str],
                    n_results: int = 5) -> List[List[Dict]]:
        """
        Perform batch search for multiple queries
        More efficient than individual searches
        """
        collection = self.get_or_create_collection(character_id)
        
        try:
            results = collection.query(
                query_texts=queries,
                n_results=n_results
            )
            
            # Format results for each query
            formatted_batch = []
            
            if results and results['documents']:
                for query_idx in range(len(queries)):
                    query_results = []
                    
                    if query_idx < len(results['documents']):
                        documents = results['documents'][query_idx]
                        metadatas = results['metadatas'][query_idx] if results['metadatas'] else []
                        distances = results['distances'][query_idx] if results['distances'] else []
                        
                        for i, doc in enumerate(documents):
                            result = {
                                "text": doc,
                                "metadata": metadatas[i] if i < len(metadatas) else {},
                                "distance": distances[i] if i < len(distances) else None,
                                "relevance_score": 1.0 - (distances[i] if i < len(distances) else 0.5)
                            }
                            query_results.append(result)
                    
                    formatted_batch.append(query_results)
            
            return formatted_batch
        except Exception as e:
            print(f"Batch search error: {e}")
            return [[] for _ in queries]


class SimpleTextChunker:
    """
    Simple text chunking utility
    Splits text into manageable chunks for vector storage
    """
    
    @staticmethod
    def chunk_by_sentences(text: str, 
                          max_chunk_size: int = 500,
                          overlap: int = 50) -> List[str]:
        """
        Chunk text by sentences with overlap
        Generic - works for any text
        """
        import re
        
        # Split into sentences (simple approach)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > max_chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                if overlap > 0 and len(current_chunk) > 1:
                    # Keep last few sentences for overlap
                    overlap_text = ' '.join(current_chunk[-2:])
                    current_chunk = current_chunk[-2:] if len(overlap_text) < overlap else []
                    current_size = len(overlap_text)
                else:
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    @staticmethod
    def chunk_by_paragraphs(text: str, max_chunk_size: int = 1000) -> List[str]:
        """
        Chunk text by paragraphs
        Good for preserving context
        """
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            if current_size + para_size > max_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            current_chunk.append(para)
            current_size += para_size
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
