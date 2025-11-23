"""
Dynamic Knowledge Discovery System
Automatically discovers new texts, books, articles by authors or in fields
Uses multiple sources: web search, APIs, digital libraries
"""
import asyncio
import hashlib
import re
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
import aiohttp
from bs4 import BeautifulSoup


@dataclass
class DiscoveredSource:
    """A discovered knowledge source"""
    source_id: str
    title: str
    author: Optional[str]
    field: Optional[str]
    url: Optional[str]
    source_type: str  # book, article, paper, video, website
    description: Optional[str] = None
    year: Optional[int] = None
    isbn: Optional[str] = None
    confidence_score: float = 0.0  # How confident we are this is relevant
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class KnowledgeDiscovery:
    """
    Discovers new knowledge sources dynamically
    Generic and extensible - works for any domain
    """
    
    def __init__(self):
        self.discovery_sources = {
            "gutenberg": ProjectGutenbergDiscovery(),
            "sacred_texts": SacredTextsDiscovery(),
            "web_search": WebSearchDiscovery(),
            "openlibrary": OpenLibraryDiscovery()
        }
    
    async def discover_by_author(self, 
                                 author: str,
                                 max_results: int = 10,
                                 source_types: Optional[List[str]] = None) -> List[DiscoveredSource]:
        """
        Discover works by a specific author
        Generic - works for any author
        """
        all_discoveries = []
        
        # Search across all discovery sources in parallel
        tasks = []
        for source_name, discovery_engine in self.discovery_sources.items():
            if discovery_engine.supports_author_search():
                tasks.append(
                    discovery_engine.search_by_author(author, max_results)
                )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        for result in results:
            if isinstance(result, Exception):
                print(f"Discovery error: {result}")
                continue
            if result:
                all_discoveries.extend(result)
        
        # Filter by source type if specified
        if source_types:
            all_discoveries = [
                d for d in all_discoveries 
                if d.source_type in source_types
            ]
        
        # Deduplicate and rank
        unique_discoveries = self._deduplicate_sources(all_discoveries)
        ranked_discoveries = self._rank_by_relevance(unique_discoveries, author=author)
        
        return ranked_discoveries[:max_results]
    
    async def discover_by_field(self,
                                field: str,
                                concepts: Optional[List[str]] = None,
                                max_results: int = 10) -> List[DiscoveredSource]:
        """
        Discover works in a specific field
        Generic - works for any field
        """
        all_discoveries = []
        
        # Search across all discovery sources
        tasks = []
        for source_name, discovery_engine in self.discovery_sources.items():
            if discovery_engine.supports_field_search():
                tasks.append(
                    discovery_engine.search_by_field(field, concepts, max_results)
                )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                print(f"Discovery error: {result}")
                continue
            if result:
                all_discoveries.extend(result)
        
        # Deduplicate and rank
        unique_discoveries = self._deduplicate_sources(all_discoveries)
        ranked_discoveries = self._rank_by_relevance(
            unique_discoveries, 
            field=field, 
            concepts=concepts
        )
        
        return ranked_discoveries[:max_results]
    
    async def discover_related_authors(self,
                                       primary_author: str,
                                       field: str,
                                       max_authors: int = 5) -> List[Tuple[str, float]]:
        """
        Discover authors related to a primary author
        Returns: List of (author_name, relevance_score)
        """
        related = []
        
        # Use web search to find related authors
        web_discovery = self.discovery_sources.get("web_search")
        if web_discovery:
            query = f"{primary_author} similar authors {field}"
            related = await web_discovery.find_related_authors(query, max_authors)
        
        return related
    
    def _deduplicate_sources(self, sources: List[DiscoveredSource]) -> List[DiscoveredSource]:
        """Remove duplicate sources based on title and author similarity"""
        seen_signatures = set()
        unique_sources = []
        
        for source in sources:
            # Create signature for deduplication
            signature = self._create_source_signature(source)
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_sources.append(source)
        
        return unique_sources
    
    def _create_source_signature(self, source: DiscoveredSource) -> str:
        """Create a unique signature for a source"""
        # Normalize title and author for comparison
        title = re.sub(r'[^\w\s]', '', source.title.lower())
        author = re.sub(r'[^\w\s]', '', source.author.lower()) if source.author else ""
        
        signature_string = f"{title}_{author}"
        return hashlib.md5(signature_string.encode()).hexdigest()
    
    def _rank_by_relevance(self,
                          sources: List[DiscoveredSource],
                          author: Optional[str] = None,
                          field: Optional[str] = None,
                          concepts: Optional[List[str]] = None) -> List[DiscoveredSource]:
        """
        Rank sources by relevance
        Generic scoring based on various factors
        """
        for source in sources:
            score = 0.0
            
            # Author match (exact)
            if author and source.author:
                if author.lower() in source.author.lower():
                    score += 10.0
            
            # Field match
            if field and source.field:
                if field.lower() in source.field.lower():
                    score += 5.0
            
            # Concept match in title or description
            if concepts:
                text = f"{source.title} {source.description or ''}".lower()
                matching_concepts = sum(1 for c in concepts if c.lower() in text)
                score += matching_concepts * 2.0
            
            # Prefer books over articles
            if source.source_type == "book":
                score += 3.0
            elif source.source_type == "article":
                score += 1.0
            
            # Prefer sources with URLs (downloadable/accessible)
            if source.url:
                score += 2.0
            
            # Recency bonus (if year available)
            if source.year:
                # No penalty for older philosophical texts
                if source.year > 2000:
                    score += 1.0
            
            source.confidence_score = score
        
        # Sort by score descending
        sources.sort(key=lambda x: x.confidence_score, reverse=True)
        return sources


# ============================================================
# Discovery Engine Implementations
# ============================================================

class DiscoveryEngine:
    """Base class for discovery engines"""
    
    def supports_author_search(self) -> bool:
        return False
    
    def supports_field_search(self) -> bool:
        return False
    
    async def search_by_author(self, author: str, max_results: int) -> List[DiscoveredSource]:
        return []
    
    async def search_by_field(self, field: str, concepts: Optional[List[str]], max_results: int) -> List[DiscoveredSource]:
        return []


class ProjectGutenbergDiscovery(DiscoveryEngine):
    """
    Discover free books from Project Gutenberg
    Great for classical texts, philosophy, literature
    """
    
    BASE_URL = "https://www.gutenberg.org"
    
    def supports_author_search(self) -> bool:
        return True
    
    async def search_by_author(self, author: str, max_results: int = 10) -> List[DiscoveredSource]:
        """Search Project Gutenberg for books by author"""
        discovered = []
        
        try:
            # Project Gutenberg search URL
            search_url = f"{self.BASE_URL}/ebooks/search/?query={author.replace(' ', '+')}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        discovered = self._parse_gutenberg_results(html, author, max_results)
        except Exception as e:
            print(f"Project Gutenberg search error: {e}")
        
        return discovered
    
    def _parse_gutenberg_results(self, html: str, author: str, max_results: int) -> List[DiscoveredSource]:
        """Parse Gutenberg search results"""
        discovered = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find book listings (simplified - adjust based on actual HTML structure)
            books = soup.find_all('li', class_='booklink', limit=max_results)
            
            for book in books:
                try:
                    title_elem = book.find('span', class_='title')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    # Get book ID from href
                    link = book.find('a', class_='link')
                    book_url = None
                    if link and link.get('href'):
                        book_url = self.BASE_URL + link['href']
                    
                    source_id = f"gutenberg_{hashlib.md5(title.encode()).hexdigest()[:12]}"
                    
                    discovered.append(DiscoveredSource(
                        source_id=source_id,
                        title=title,
                        author=author,
                        field="Literature/Philosophy",
                        url=book_url,
                        source_type="book",
                        description=f"Free book from Project Gutenberg",
                        metadata={"source": "Project Gutenberg"}
                    ))
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error parsing Gutenberg results: {e}")
        
        return discovered


class SacredTextsDiscovery(DiscoveryEngine):
    """
    Discover texts from sacred-texts.com
    Great for religious, spiritual, philosophical texts
    """
    
    BASE_URL = "https://www.sacred-texts.com"
    
    def supports_field_search(self) -> bool:
        return True
    
    async def search_by_field(self, field: str, concepts: Optional[List[str]], max_results: int) -> List[DiscoveredSource]:
        """Search sacred-texts.com by field"""
        discovered = []
        
        # Map fields to sacred-texts categories
        field_map = {
            "taoism": "/tao/",
            "daoism": "/tao/",
            "buddhism": "/bud/",
            "stoicism": "/cla/",
            "philosophy": "/phi/",
            "confucianism": "/cfu/",
            "hinduism": "/hin/"
        }
        
        category = field_map.get(field.lower())
        if not category:
            return discovered
        
        try:
            url = self.BASE_URL + category
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        discovered = self._parse_sacred_texts_catalog(html, field, category, max_results)
        except Exception as e:
            print(f"Sacred Texts search error: {e}")
        
        return discovered
    
    def _parse_sacred_texts_catalog(self, html: str, field: str, category: str, max_results: int) -> List[DiscoveredSource]:
        """Parse sacred-texts catalog page"""
        discovered = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find text links (simplified)
            links = soup.find_all('a', href=True, limit=max_results * 2)
            
            count = 0
            for link in links:
                if count >= max_results:
                    break
                
                href = link['href']
                # Filter for actual text files
                if href.endswith(('.htm', '.html', '.txt')) and category in href:
                    title = link.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    full_url = self.BASE_URL + href if not href.startswith('http') else href
                    source_id = f"sacred_{hashlib.md5(full_url.encode()).hexdigest()[:12]}"
                    
                    discovered.append(DiscoveredSource(
                        source_id=source_id,
                        title=title,
                        author=None,
                        field=field,
                        url=full_url,
                        source_type="text",
                        description=f"Text from sacred-texts.com",
                        metadata={"source": "Sacred Texts", "category": category}
                    ))
                    count += 1
        except Exception as e:
            print(f"Error parsing sacred texts: {e}")
        
        return discovered


class OpenLibraryDiscovery(DiscoveryEngine):
    """
    Discover books from Open Library API
    Comprehensive book database
    """
    
    BASE_URL = "https://openlibrary.org"
    
    def supports_author_search(self) -> bool:
        return True
    
    def supports_field_search(self) -> bool:
        return True
    
    async def search_by_author(self, author: str, max_results: int = 10) -> List[DiscoveredSource]:
        """Search Open Library by author"""
        discovered = []
        
        try:
            search_url = f"{self.BASE_URL}/search.json?author={author.replace(' ', '+')}&limit={max_results}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        discovered = self._parse_openlibrary_results(data, author)
        except Exception as e:
            print(f"Open Library search error: {e}")
        
        return discovered
    
    def _parse_openlibrary_results(self, data: Dict, author: str) -> List[DiscoveredSource]:
        """Parse Open Library API results"""
        discovered = []
        
        try:
            docs = data.get('docs', [])
            
            for doc in docs:
                title = doc.get('title', '')
                if not title:
                    continue
                
                # Get first ISBN if available
                isbn = None
                if doc.get('isbn'):
                    isbn = doc['isbn'][0]
                
                # Get publication year
                year = doc.get('first_publish_year')
                
                # Get Open Library key
                key = doc.get('key', '')
                book_url = f"{self.BASE_URL}{key}" if key else None
                
                source_id = f"openlibrary_{isbn or hashlib.md5(title.encode()).hexdigest()[:12]}"
                
                discovered.append(DiscoveredSource(
                    source_id=source_id,
                    title=title,
                    author=author,
                    field=None,
                    url=book_url,
                    source_type="book",
                    description=doc.get('subtitle', ''),
                    year=year,
                    isbn=isbn,
                    metadata={"source": "Open Library", "publisher": doc.get('publisher', [None])[0] if doc.get('publisher') else None}
                ))
        except Exception as e:
            print(f"Error parsing Open Library results: {e}")
        
        return discovered


class WebSearchDiscovery(DiscoveryEngine):
    """
    Web search for discovering new sources
    Fallback when other sources don't have content
    """
    
    def supports_author_search(self) -> bool:
        return True
    
    def supports_field_search(self) -> bool:
        return True
    
    async def search_by_author(self, author: str, max_results: int = 10) -> List[DiscoveredSource]:
        """
        Web search for author's works
        Note: This is a placeholder - implement with actual search API
        (e.g., Brave Search, Serper, or custom scraping)
        """
        # Placeholder - integrate with actual web search API
        return []
    
    async def search_by_field(self, field: str, concepts: Optional[List[str]], max_results: int) -> List[DiscoveredSource]:
        """
        Web search for field-related content
        Placeholder for actual implementation
        """
        return []
    
    async def find_related_authors(self, query: str, max_authors: int = 5) -> List[Tuple[str, float]]:
        """
        Find related authors via web search
        Placeholder for actual implementation
        """
        # This would use a search API to find related authors
        # Returns: [(author_name, relevance_score), ...]
        return []
