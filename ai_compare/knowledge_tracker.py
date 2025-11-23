"""
Knowledge Processing Tracker
Tracks what texts/sources have been discovered and processed
Prevents redundant work and maintains knowledge state
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict, field
from pathlib import Path


@dataclass
class ProcessedSource:
    """Record of a processed knowledge source"""
    source_id: str
    author: Optional[str]
    title: Optional[str]
    field: Optional[str]
    source_type: str
    processed_date: str
    chunk_count: int
    character_id: str
    url: Optional[str] = None
    status: str = "completed"  # completed, failed, partial
    error_message: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class DiscoveryRecord:
    """Record of a discovery attempt"""
    discovery_id: str
    character_id: str
    search_query: str
    discovered_date: str
    sources_found: int
    sources_processed: int
    discovery_method: str  # web_search, api, manual, etc.
    search_metadata: Dict = field(default_factory=dict)


class KnowledgeTracker:
    """
    Tracks all knowledge processing activities
    Ensures no redundant processing
    Maintains state across sessions
    """
    
    def __init__(self, storage_path: str = "knowledge_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Tracking files
        self.processed_file = self.storage_path / "processed_sources.json"
        self.discoveries_file = self.storage_path / "discoveries.json"
        self.index_file = self.storage_path / "source_index.json"
        
        # Load existing data
        self.processed_sources = self._load_processed_sources()
        self.discoveries = self._load_discoveries()
        self.source_index = self._load_source_index()
    
    def _load_processed_sources(self) -> Dict[str, ProcessedSource]:
        """Load processed sources from disk"""
        if not self.processed_file.exists():
            return {}
        
        try:
            with open(self.processed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    k: ProcessedSource(**v) 
                    for k, v in data.items()
                }
        except Exception as e:
            print(f"Error loading processed sources: {e}")
            return {}
    
    def _load_discoveries(self) -> List[DiscoveryRecord]:
        """Load discovery records from disk"""
        if not self.discoveries_file.exists():
            return []
        
        try:
            with open(self.discoveries_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [DiscoveryRecord(**record) for record in data]
        except Exception as e:
            print(f"Error loading discoveries: {e}")
            return []
    
    def _load_source_index(self) -> Dict[str, List[str]]:
        """
        Load source index
        Maps: character_id -> [source_ids]
        """
        if not self.index_file.exists():
            return {}
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading source index: {e}")
            return {}
    
    def _save_processed_sources(self):
        """Save processed sources to disk"""
        try:
            data = {
                k: asdict(v) 
                for k, v in self.processed_sources.items()
            }
            with open(self.processed_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving processed sources: {e}")
    
    def _save_discoveries(self):
        """Save discovery records to disk"""
        try:
            data = [asdict(record) for record in self.discoveries]
            with open(self.discoveries_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving discoveries: {e}")
    
    def _save_source_index(self):
        """Save source index to disk"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.source_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving source index: {e}")
    
    def is_source_processed(self, source_id: str, character_id: Optional[str] = None) -> bool:
        """
        Check if a source has already been processed
        Optionally filter by character
        """
        if source_id not in self.processed_sources:
            return False
        
        if character_id:
            return self.processed_sources[source_id].character_id == character_id
        
        return True
    
    def is_author_processed(self, author: str, character_id: str) -> bool:
        """Check if any works by this author have been processed for this character"""
        for source in self.processed_sources.values():
            if (source.author and source.author.lower() == author.lower() and 
                source.character_id == character_id):
                return True
        return False
    
    def get_processed_by_author(self, author: str, character_id: Optional[str] = None) -> List[ProcessedSource]:
        """Get all processed sources by an author"""
        results = []
        for source in self.processed_sources.values():
            if source.author and source.author.lower() == author.lower():
                if character_id is None or source.character_id == character_id:
                    results.append(source)
        return results
    
    def get_processed_by_field(self, field: str, character_id: Optional[str] = None) -> List[ProcessedSource]:
        """Get all processed sources in a field"""
        results = []
        for source in self.processed_sources.values():
            if source.field and field.lower() in source.field.lower():
                if character_id is None or source.character_id == character_id:
                    results.append(source)
        return results
    
    def get_character_sources(self, character_id: str) -> List[ProcessedSource]:
        """Get all sources processed for a character"""
        return [
            source for source in self.processed_sources.values()
            if source.character_id == character_id
        ]
    
    def get_unprocessed_authors(self, 
                                all_authors: List[str], 
                                character_id: str) -> List[str]:
        """Get list of authors that haven't been processed yet"""
        processed_authors = {
            source.author.lower() 
            for source in self.processed_sources.values()
            if source.author and source.character_id == character_id
        }
        
        return [
            author for author in all_authors
            if author.lower() not in processed_authors
        ]
    
    def mark_source_processed(self,
                             source_id: str,
                             character_id: str,
                             author: Optional[str] = None,
                             title: Optional[str] = None,
                             field: Optional[str] = None,
                             source_type: str = "text",
                             chunk_count: int = 0,
                             url: Optional[str] = None,
                             status: str = "completed",
                             error_message: Optional[str] = None,
                             metadata: Optional[Dict] = None):
        """Mark a source as processed"""
        
        processed = ProcessedSource(
            source_id=source_id,
            author=author,
            title=title,
            field=field,
            source_type=source_type,
            processed_date=datetime.now().isoformat(),
            chunk_count=chunk_count,
            character_id=character_id,
            url=url,
            status=status,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        self.processed_sources[source_id] = processed
        
        # Update index
        if character_id not in self.source_index:
            self.source_index[character_id] = []
        if source_id not in self.source_index[character_id]:
            self.source_index[character_id].append(source_id)
        
        # Save to disk
        self._save_processed_sources()
        self._save_source_index()
    
    def record_discovery(self,
                        character_id: str,
                        search_query: str,
                        sources_found: int,
                        sources_processed: int,
                        discovery_method: str,
                        search_metadata: Optional[Dict] = None) -> str:
        """Record a discovery attempt"""
        
        discovery_id = f"{character_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        record = DiscoveryRecord(
            discovery_id=discovery_id,
            character_id=character_id,
            search_query=search_query,
            discovered_date=datetime.now().isoformat(),
            sources_found=sources_found,
            sources_processed=sources_processed,
            discovery_method=discovery_method,
            search_metadata=search_metadata or {}
        )
        
        self.discoveries.append(record)
        self._save_discoveries()
        
        return discovery_id
    
    def get_recent_discoveries(self, character_id: Optional[str] = None, limit: int = 10) -> List[DiscoveryRecord]:
        """Get recent discovery records"""
        discoveries = self.discoveries
        
        if character_id:
            discoveries = [d for d in discoveries if d.character_id == character_id]
        
        # Sort by date, most recent first
        discoveries.sort(key=lambda x: x.discovered_date, reverse=True)
        
        return discoveries[:limit]
    
    def get_statistics(self, character_id: Optional[str] = None) -> Dict:
        """Get processing statistics"""
        sources = self.processed_sources.values()
        
        if character_id:
            sources = [s for s in sources if s.character_id == character_id]
        
        authors = set(s.author for s in sources if s.author)
        fields = set(s.field for s in sources if s.field)
        
        return {
            "total_sources": len(list(sources)),
            "total_authors": len(authors),
            "total_fields": len(fields),
            "total_chunks": sum(s.chunk_count for s in sources),
            "authors": sorted(list(authors)),
            "fields": sorted(list(fields)),
            "by_status": {
                status: len([s for s in sources if s.status == status])
                for status in ["completed", "failed", "partial"]
            }
        }
    
    def needs_discovery(self, 
                       character_id: str,
                       discovery_frequency: str = "weekly") -> bool:
        """
        Check if it's time for a new discovery run
        Based on last discovery date and frequency setting
        """
        recent = self.get_recent_discoveries(character_id, limit=1)
        
        if not recent:
            return True
        
        last_discovery = datetime.fromisoformat(recent[0].discovered_date)
        now = datetime.now()
        days_since = (now - last_discovery).days
        
        frequency_map = {
            "never": float('inf'),
            "daily": 1,
            "weekly": 7,
            "monthly": 30
        }
        
        threshold = frequency_map.get(discovery_frequency, 7)
        return days_since >= threshold
    
    def clear_character_data(self, character_id: str):
        """Clear all data for a character (useful for testing)"""
        # Remove from processed sources
        to_remove = [
            source_id for source_id, source in self.processed_sources.items()
            if source.character_id == character_id
        ]
        for source_id in to_remove:
            del self.processed_sources[source_id]
        
        # Remove from discoveries
        self.discoveries = [
            d for d in self.discoveries 
            if d.character_id != character_id
        ]
        
        # Remove from index
        if character_id in self.source_index:
            del self.source_index[character_id]
        
        # Save changes
        self._save_processed_sources()
        self._save_discoveries()
        self._save_source_index()
