"""
Dynamic Knowledge Expansion System - Main Integration Layer
Orchestrates discovery, processing, tracking, and retrieval
Generic and character-agnostic - works for ANY AI character
"""
import asyncio
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import aiohttp
from bs4 import BeautifulSoup

from .knowledge_config import (
    CharacterKnowledgeProfile, 
    get_character_profile,
    register_character_profile
)
from .knowledge_tracker import KnowledgeTracker
from .knowledge_discovery import KnowledgeDiscovery, DiscoveredSource
from .knowledge_vector_store import KnowledgeVectorStore, SimpleTextChunker


class DynamicKnowledgeSystem:
    """
    Main orchestrator for dynamic knowledge expansion
    Fully generic - no hard-coded authors, fields, or concepts
    Auto-integrates with any character configuration
    """
    
    def __init__(self, storage_path: str = "knowledge_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Initialize subsystems
        self.tracker = KnowledgeTracker(storage_path)
        self.discovery = KnowledgeDiscovery()
        self.vector_store = KnowledgeVectorStore(str(self.storage_path / "vector_db"))
        self.chunker = SimpleTextChunker()
    
    async def expand_character_knowledge(self, 
                                        character_id: str,
                                        force_discovery: bool = False) -> Dict:
        """
        Main entry point: Expand knowledge for any character
        Fully automatic and generic
        
        Returns: Summary of what was discovered and processed
        """
        # Get character profile
        profile = get_character_profile(character_id)
        if not profile:
            return {
                "error": f"No knowledge profile found for {character_id}",
                "character_id": character_id
            }
        
        # Check if discovery is needed
        if not force_discovery and not profile.enable_auto_discovery:
            return {
                "message": "Auto-discovery disabled for this character",
                "character_id": character_id
            }
        
        if not force_discovery and not self.tracker.needs_discovery(
            character_id, 
            profile.discovery_frequency
        ):
            return {
                "message": "Discovery not needed yet",
                "character_id": character_id,
                "next_discovery": "Based on frequency settings"
            }
        
        # Perform discovery and processing
        summary = await self._discover_and_process(character_id, profile)
        
        return summary
    
    async def _discover_and_process(self,
                                    character_id: str,
                                    profile: CharacterKnowledgeProfile) -> Dict:
        """
        Discover new sources and process them
        Generic - works for any character profile
        """
        summary = {
            "character_id": character_id,
            "character_name": profile.character_name,
            "discovered": 0,
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "new_authors": [],
            "new_sources": [],
            "errors": []
        }
        
        # 1. Discover by primary authors
        all_discovered = []
        
        for author in profile.primary_authors:
            # Check if already processed
            if self.tracker.is_author_processed(author, character_id):
                summary["skipped"] += 1
                continue
            
            try:
                discovered = await self.discovery.discover_by_author(
                    author=author,
                    max_results=profile.max_sources_per_author
                )
                all_discovered.extend(discovered)
                
                if discovered:
                    summary["new_authors"].append(author)
            
            except Exception as e:
                summary["errors"].append(f"Discovery failed for {author}: {str(e)}")
        
        # 2. Discover by fields
        for field in profile.fields_of_study:
            try:
                discovered = await self.discovery.discover_by_field(
                    field=field,
                    concepts=profile.core_concepts,
                    max_results=5
                )
                all_discovered.extend(discovered)
            
            except Exception as e:
                summary["errors"].append(f"Discovery failed for {field}: {str(e)}")
        
        summary["discovered"] = len(all_discovered)
        
        # 3. Process discovered sources
        for source in all_discovered:
            # Check if already processed
            if self.tracker.is_source_processed(source.source_id, character_id):
                summary["skipped"] += 1
                continue
            
            try:
                success = await self._process_source(character_id, source)
                
                if success:
                    summary["processed"] += 1
                    summary["new_sources"].append({
                        "title": source.title,
                        "author": source.author,
                        "type": source.source_type
                    })
                else:
                    summary["failed"] += 1
            
            except Exception as e:
                summary["failed"] += 1
                summary["errors"].append(f"Processing failed for {source.title}: {str(e)}")
        
        # 4. Record discovery
        self.tracker.record_discovery(
            character_id=character_id,
            search_query=f"Authors: {', '.join(profile.primary_authors[:3])}...",
            sources_found=summary["discovered"],
            sources_processed=summary["processed"],
            discovery_method="automatic",
            search_metadata={
                "authors": profile.primary_authors,
                "fields": profile.fields_of_study
            }
        )
        
        return summary
    
    async def _process_source(self, 
                             character_id: str, 
                             source: DiscoveredSource) -> bool:
        """
        Download, chunk, and store a source
        Generic - works for any source type
        """
        try:
            # 1. Download content
            content = await self._download_source(source)
            
            if not content:
                self.tracker.mark_source_processed(
                    source_id=source.source_id,
                    character_id=character_id,
                    author=source.author,
                    title=source.title,
                    field=source.field,
                    source_type=source.source_type,
                    url=source.url,
                    status="failed",
                    error_message="Failed to download content"
                )
                return False
            
            # 2. Chunk content
            chunks = self.chunker.chunk_by_sentences(
                text=content,
                max_chunk_size=500,
                overlap=50
            )
            
            if not chunks:
                self.tracker.mark_source_processed(
                    source_id=source.source_id,
                    character_id=character_id,
                    author=source.author,
                    title=source.title,
                    field=source.field,
                    source_type=source.source_type,
                    url=source.url,
                    status="failed",
                    error_message="No chunks created"
                )
                return False
            
            # 3. Add to vector store
            chunk_count = self.vector_store.add_text_chunks(
                character_id=character_id,
                chunks=chunks,
                source_id=source.source_id,
                author=source.author,
                title=source.title,
                field=source.field,
                metadata=source.metadata
            )
            
            # 4. Mark as processed
            self.tracker.mark_source_processed(
                source_id=source.source_id,
                character_id=character_id,
                author=source.author,
                title=source.title,
                field=source.field,
                source_type=source.source_type,
                chunk_count=chunk_count,
                url=source.url,
                status="completed",
                metadata=source.metadata
            )
            
            return True
        
        except Exception as e:
            print(f"Error processing source {source.title}: {e}")
            
            self.tracker.mark_source_processed(
                source_id=source.source_id,
                character_id=character_id,
                author=source.author,
                title=source.title,
                field=source.field,
                source_type=source.source_type,
                url=source.url,
                status="failed",
                error_message=str(e)
            )
            
            return False
    
    async def _download_source(self, source: DiscoveredSource) -> Optional[str]:
        """
        Download source content
        Generic - handles different source types
        """
        if not source.url:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source.url, timeout=30) as response:
                    if response.status != 200:
                        return None
                    
                    content_type = response.headers.get('content-type', '').lower()
                    
                    # Handle HTML
                    if 'html' in content_type:
                        html = await response.text()
                        return self._extract_text_from_html(html)
                    
                    # Handle plain text
                    elif 'text' in content_type:
                        return await response.text()
                    
                    # Handle PDF (basic - would need PyPDF2)
                    elif 'pdf' in content_type:
                        # Placeholder - implement PDF parsing if needed
                        return None
                    
                    else:
                        return None
        
        except Exception as e:
            print(f"Download error for {source.url}: {e}")
            return None
    
    def _extract_text_from_html(self, html: str) -> str:
        """
        Extract clean text from HTML
        Generic text extraction
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n')
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        
        except Exception as e:
            print(f"HTML extraction error: {e}")
            return ""
    
    def search_knowledge(self,
                        character_id: str,
                        query: str,
                        n_results: int = 5,
                        filter_author: Optional[str] = None,
                        filter_field: Optional[str] = None) -> List[Dict]:
        """
        Search character's knowledge base
        Generic semantic search
        """
        return self.vector_store.search(
            character_id=character_id,
            query=query,
            n_results=n_results,
            filter_author=filter_author,
            filter_field=filter_field
        )
    
    def get_character_stats(self, character_id: str) -> Dict:
        """Get comprehensive statistics for a character"""
        tracker_stats = self.tracker.get_statistics(character_id)
        vector_stats = self.vector_store.get_statistics(character_id)
        recent_discoveries = self.tracker.get_recent_discoveries(character_id, limit=5)
        
        return {
            "character_id": character_id,
            "tracker": tracker_stats,
            "vector_store": vector_stats,
            "recent_discoveries": [
                {
                    "date": d.discovered_date,
                    "query": d.search_query,
                    "found": d.sources_found,
                    "processed": d.sources_processed
                }
                for d in recent_discoveries
            ]
        }
    
    def add_manual_source(self,
                         character_id: str,
                         text: str,
                         author: str,
                         title: str,
                         field: Optional[str] = None,
                         source_type: str = "manual") -> bool:
        """
        Manually add a text source
        Useful for adding custom content
        """
        try:
            import hashlib
            source_id = f"manual_{hashlib.md5(f'{author}_{title}'.encode()).hexdigest()[:12]}"
            
            # Check if already exists
            if self.tracker.is_source_processed(source_id, character_id):
                return False
            
            # Chunk the text
            chunks = self.chunker.chunk_by_sentences(text)
            
            # Add to vector store
            chunk_count = self.vector_store.add_text_chunks(
                character_id=character_id,
                chunks=chunks,
                source_id=source_id,
                author=author,
                title=title,
                field=field,
                metadata={"manual_upload": True}
            )
            
            # Mark as processed
            self.tracker.mark_source_processed(
                source_id=source_id,
                character_id=character_id,
                author=author,
                title=title,
                field=field,
                source_type=source_type,
                chunk_count=chunk_count,
                status="completed"
            )
            
            return True
        
        except Exception as e:
            print(f"Error adding manual source: {e}")
            return False


# ============================================================
# Convenience Functions for Easy Integration
# ============================================================

# Global instance (lazy initialization)
_knowledge_system = None


def get_knowledge_system() -> DynamicKnowledgeSystem:
    """Get or create global knowledge system instance"""
    global _knowledge_system
    if _knowledge_system is None:
        _knowledge_system = DynamicKnowledgeSystem()
    return _knowledge_system


async def expand_knowledge_for_character(character_id: str, force: bool = False) -> Dict:
    """Convenience function: Expand knowledge for a character"""
    system = get_knowledge_system()
    return await system.expand_character_knowledge(character_id, force)


def search_character_knowledge(character_id: str, query: str, n_results: int = 5) -> List[Dict]:
    """Convenience function: Search character knowledge"""
    system = get_knowledge_system()
    return system.search_knowledge(character_id, query, n_results)


def get_knowledge_stats(character_id: str) -> Dict:
    """Convenience function: Get character knowledge stats"""
    system = get_knowledge_system()
    return system.get_character_stats(character_id)


def register_new_character(character_id: str, profile: CharacterKnowledgeProfile):
    """Convenience function: Register a new character"""
    register_character_profile(character_id, profile)
