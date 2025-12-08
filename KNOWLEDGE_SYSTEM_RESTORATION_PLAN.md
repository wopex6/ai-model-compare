# 🔧 Knowledge System Restoration Plan

**Status:** DEFERRED - To be implemented in Phase 2 (Month 2)  
**Current State:** Disabled due to blocking I/O in async context  
**Priority:** Medium (after performance optimizations)

---

## **Problem Summary**

### **Root Cause**
- **File:** `ai_compare/knowledge_vector_store.py:34`
- **Issue:** ChromaDB's `PersistentClient()` uses synchronous SQLite backend
- **Impact:** Blocks async event loop on every search operation
- **Result:** 10-minute HARAKIRI timeout on PythonAnywhere

### **Blocking Code**
```python
# knowledge_vector_store.py (Line 34)
self.client = chromadb.PersistentClient(
    path=str(self.storage_path),
    settings=Settings(anonymized_telemetry=False, allow_reset=True)
)

# knowledge_system.py (Line 336)
def search_knowledge(self, ...):  # ← SYNCHRONOUS!
    return self.vector_store.search(...)  # ← Blocks async loop
```

### **Failed Attempts**
1. ❌ `asyncio.to_thread()` wrapper - Still hangs (SQLite not thread-safe)
2. ❌ Disabling model pre-initialization - Unrelated issue
3. ✅ Temporary disable - **WORKING SOLUTION**

---

## **Restoration Options**

### **Option A: Process Pool Wrapper** ⚠️
**NOT RECOMMENDED** - Fragile workaround

**Time:** 1 week  
**Complexity:** Low  
**Reliability:** ⚠️ Poor  
**Performance:** Slow (process overhead)

```python
from concurrent.futures import ProcessPoolExecutor
import asyncio

knowledge_executor = ProcessPoolExecutor(max_workers=2)

async def search_knowledge_async(character_id, query):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        knowledge_executor,
        knowledge_system.search_knowledge,
        character_id, query
    )
```

**Pros:**
- Minimal code changes
- Quick to implement

**Cons:**
- Still blocking in subprocess
- High process overhead (300-500ms per search)
- May still timeout on large queries
- Fragile - not production-ready

**Verdict:** ❌ Don't use - bandaid solution

---

### **Option B: Qdrant Migration** ✅
**RECOMMENDED** - Proper async solution

**Time:** 2-3 weeks  
**Complexity:** Medium  
**Reliability:** ✅ Excellent  
**Performance:** Fast (better than ChromaDB)

#### **Why Qdrant?**
- ✅ Fully async Python client (`AsyncQdrantClient`)
- ✅ Better performance than ChromaDB
- ✅ Production-proven (used by major companies)
- ✅ Free for self-hosted deployment
- ✅ Better filtering and metadata support
- ✅ Active development and good documentation
- ✅ Works perfectly with PythonAnywhere

#### **Implementation Plan**

**Week 1: Setup & Integration**
```python
# Install
pip install qdrant-client

# New async implementation
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import asyncio

class AsyncKnowledgeVectorStore:
    """Fully async vector store using Qdrant"""
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.client = None
    
    async def initialize(self):
        """Async initialization"""
        self.client = AsyncQdrantClient(path=self.storage_path)
    
    async def get_or_create_collection(self, character_id: str):
        """Create collection if not exists"""
        collection_name = f"knowledge_{character_id}"
        
        collections = await self.client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)
        
        if not exists:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=384,  # sentence-transformers/all-MiniLM-L6-v2
                    distance=Distance.COSINE
                )
            )
        
        return collection_name
    
    async def add_text_chunks(self,
                             character_id: str,
                             chunks: List[str],
                             source_id: str,
                             metadata: Dict):
        """Add chunks to vector store (async)"""
        collection = await self.get_or_create_collection(character_id)
        
        # Generate embeddings (use async embedding service)
        embeddings = await self._generate_embeddings(chunks)
        
        # Prepare points
        points = [
            PointStruct(
                id=f"{source_id}_{i}",
                vector=embedding,
                payload={
                    "text": chunk,
                    "source_id": source_id,
                    **metadata
                }
            )
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        
        # Upload (async)
        await self.client.upsert(
            collection_name=collection,
            points=points
        )
    
    async def search(self,
                    character_id: str,
                    query: str,
                    n_results: int = 5,
                    filter_author: Optional[str] = None):
        """Async semantic search"""
        collection = await self.get_or_create_collection(character_id)
        
        # Generate query embedding (async)
        query_embedding = await self._generate_embedding(query)
        
        # Build filter
        search_filter = None
        if filter_author:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="author",
                        match=MatchValue(value=filter_author)
                    )
                ]
            )
        
        # Search (async)
        results = await self.client.search(
            collection_name=collection,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=n_results
        )
        
        # Format results
        return [
            {
                "text": hit.payload["text"],
                "metadata": {
                    k: v for k, v in hit.payload.items() 
                    if k != "text"
                },
                "score": hit.score
            }
            for hit in results
        ]
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text (async)"""
        # Use sentence-transformers with async wrapper
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._embedding_model.encode,
            text
        )
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (async batch)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._embedding_model.encode,
            texts
        )
```

**Week 2: Data Migration**
```python
# Migration script
async def migrate_chromadb_to_qdrant():
    """Migrate existing knowledge from ChromaDB to Qdrant"""
    
    # Read from old ChromaDB
    old_store = KnowledgeVectorStore("knowledge_data/vector_db")
    new_store = AsyncKnowledgeVectorStore("knowledge_data/qdrant_db")
    await new_store.initialize()
    
    # Get all characters
    characters = ["scientist", "psychologist", "zen_master", ...]
    
    for character_id in characters:
        print(f"Migrating {character_id}...")
        
        # Get all data from ChromaDB collection
        collection = old_store.get_or_create_collection(character_id)
        data = collection.get(include=["documents", "metadatas", "embeddings"])
        
        # Batch upload to Qdrant
        if data["ids"]:
            points = [
                PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={
                        "text": document,
                        **metadata
                    }
                )
                for doc_id, document, metadata, embedding in zip(
                    data["ids"],
                    data["documents"],
                    data["metadatas"],
                    data["embeddings"]
                )
            ]
            
            await new_store.client.upsert(
                collection_name=f"knowledge_{character_id}",
                points=points
            )
        
        print(f"✅ Migrated {len(data['ids'])} items for {character_id}")

# Run migration
asyncio.run(migrate_chromadb_to_qdrant())
```

**Week 3: Integration & Testing**
```python
# Update knowledge_system.py
class DynamicKnowledgeSystem:
    def __init__(self, storage_path: str = "knowledge_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Initialize subsystems
        self.tracker = KnowledgeTracker(storage_path)
        self.discovery = KnowledgeDiscovery()
        # NEW: Async vector store
        self.vector_store = AsyncKnowledgeVectorStore(
            str(self.storage_path / "qdrant_db")
        )
        self.chunker = SimpleTextChunker()
    
    async def initialize(self):
        """Must be called after instantiation"""
        await self.vector_store.initialize()
    
    async def search_knowledge(self,
                              character_id: str,
                              query: str,
                              n_results: int = 5) -> List[Dict]:
        """Now fully async!"""
        return await self.vector_store.search(
            character_id=character_id,
            query=query,
            n_results=n_results
        )
```

**Week 4: Deployment & Optimization**
- Deploy to PythonAnywhere
- Monitor performance
- Optimize query times
- Add caching if needed

**Installation on PythonAnywhere:**
```bash
# In PythonAnywhere Bash console
cd ~/ai-model-compare
source venv/bin/activate
pip install qdrant-client
pip install sentence-transformers  # For embeddings

# Run migration
python migrate_knowledge.py

# Test
python -c "import asyncio; from ai_compare.knowledge_system import DynamicKnowledgeSystem; asyncio.run(test())"
```

**Pros:**
- ✅ Fully async - no blocking anywhere
- ✅ Better performance (2-5x faster than ChromaDB)
- ✅ Production-ready and battle-tested
- ✅ Better scalability
- ✅ Excellent documentation
- ✅ Active community support

**Cons:**
- ⏱️ Takes 2-3 weeks to implement properly
- 📚 Learning curve (new API)
- 🔄 Data migration required
- 💾 Slightly larger disk footprint

**Cost:** FREE (self-hosted, same as ChromaDB)

**Verdict:** ✅ **RECOMMENDED - Best long-term solution**

---

### **Option C: Simple Keyword Search** 🚀
**QUICK ALTERNATIVE** - Good enough for most cases

**Time:** 3 days  
**Complexity:** Low  
**Reliability:** ✅ Good  
**Performance:** Medium (fast queries, less intelligent)

```python
# Use aiosqlite for fully async SQLite
import aiosqlite
from typing import List, Dict, Optional

class SimpleAsyncKnowledgeStore:
    """Lightweight async knowledge store using SQLite FTS5"""
    
    def __init__(self, db_path: str = "knowledge_data/knowledge.db"):
        self.db_path = db_path
    
    async def initialize(self):
        """Create FTS5 table"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge 
                USING fts5(
                    character_id,
                    text,
                    author,
                    title,
                    field,
                    source_id,
                    tokenize='porter unicode61'
                )
            """)
            await db.commit()
    
    async def add_text_chunks(self,
                             character_id: str,
                             chunks: List[str],
                             source_id: str,
                             metadata: Dict):
        """Add chunks to database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executemany(
                """
                INSERT INTO knowledge 
                (character_id, text, author, title, field, source_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        character_id,
                        chunk,
                        metadata.get("author"),
                        metadata.get("title"),
                        metadata.get("field"),
                        source_id
                    )
                    for chunk in chunks
                ]
            )
            await db.commit()
    
    async def search(self,
                    character_id: str,
                    query: str,
                    n_results: int = 5,
                    filter_author: Optional[str] = None) -> List[Dict]:
        """Fast keyword-based search"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Build query
            sql = """
                SELECT 
                    text,
                    author,
                    title,
                    field,
                    rank
                FROM knowledge
                WHERE character_id = ?
                AND knowledge MATCH ?
            """
            params = [character_id, query]
            
            if filter_author:
                sql += " AND author = ?"
                params.append(filter_author)
            
            sql += " ORDER BY rank LIMIT ?"
            params.append(n_results)
            
            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()
            
            return [
                {
                    "text": row["text"],
                    "metadata": {
                        "author": row["author"],
                        "title": row["title"],
                        "field": row["field"]
                    }
                }
                for row in rows
            ]
    
    async def get_statistics(self, character_id: str) -> Dict:
        """Get knowledge stats"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) as total FROM knowledge WHERE character_id = ?",
                (character_id,)
            )
            result = await cursor.fetchone()
            return {"total_chunks": result[0]}
```

**Installation:**
```bash
pip install aiosqlite
```

**Integration:**
```python
# knowledge_system.py
async def search_knowledge(self,
                          character_id: str,
                          query: str,
                          n_results: int = 5) -> List[Dict]:
    """Now fully async with keyword search"""
    return await self.simple_store.search(
        character_id=character_id,
        query=query,
        n_results=n_results
    )
```

**Pros:**
- ✅ Very fast to implement (3 days)
- ✅ Fully async (aiosqlite)
- ✅ No external dependencies (just SQLite)
- ✅ Very fast queries (< 10ms)
- ✅ Works great for exact matches
- ✅ Zero migration (build from scratch)

**Cons:**
- ⚠️ Keyword-based only (not semantic/concept search)
- ⚠️ Might miss relevant content with different wording
- ⚠️ No similarity scoring (just match/no-match)
- ⚠️ Less "intelligent" than vector search

**Use Cases:**
- ✅ Looking for specific terms, names, quotes
- ✅ Title/author searches
- ✅ "Good enough" for 80% of queries
- ⚠️ Weaker for concept-based queries

**Verdict:** ✅ **Great fallback or interim solution**

---

## **Recommended Implementation Timeline**

### **Phase 2 - Month 2 (After Phase 1 Optimization)**

**Week 1: Prototype**
- Install Qdrant locally
- Create async wrapper classes
- Basic functionality tests
- Verify no blocking issues

**Week 2: Migration**
- Write migration script
- Test data integrity
- Backup existing ChromaDB data
- Run full migration locally

**Week 3: Integration**
- Update knowledge_system.py
- Update all call sites to async
- Integration tests
- Performance benchmarks

**Week 4: Deployment**
- Deploy to PythonAnywhere
- Smoke tests in production
- Monitor for issues
- Performance tuning

**Fallback Plan:**
If Qdrant has issues, switch to Option C (keyword search) in 3 days.

---

## **Technical Requirements**

### **For Qdrant (Option B)**
```bash
# Python packages
pip install qdrant-client>=1.7.0
pip install sentence-transformers>=2.2.0

# Disk space
~500MB for embeddings model
~50MB per 10,000 knowledge chunks
```

### **For Keyword Search (Option C)**
```bash
# Python packages
pip install aiosqlite>=0.19.0

# Disk space
~10MB per 10,000 knowledge chunks
```

### **PythonAnywhere Compatibility**
Both options work on PythonAnywhere:
- ✅ Qdrant: Self-hosted, no network restrictions
- ✅ aiosqlite: Built into Python standard library

---

## **Performance Expectations**

| Metric | ChromaDB (Blocking) | Qdrant (Async) | Keyword Search |
|--------|---------------------|----------------|----------------|
| **Query Time** | 100-200ms* | 50-100ms | 10-30ms |
| **Blocks Async?** | ❌ YES (FATAL) | ✅ No | ✅ No |
| **Semantic Search?** | ✅ Yes | ✅ Yes | ❌ No |
| **Reliability** | ⚠️ Hangs | ✅ Solid | ✅ Solid |
| **Scalability** | Limited | Excellent | Good |

*ChromaDB query time before hang - irrelevant since it blocks

### **Expected Response Times (with Qdrant)**
- Without knowledge: ~53 seconds (current)
- With knowledge: ~55 seconds (+2 seconds for search)
- **No timeouts, no blocking, fully async**

---

## **Testing Checklist**

### **Before Deployment**
- [ ] Local tests pass (all search types)
- [ ] Async behavior verified (no blocking)
- [ ] Data migration successful
- [ ] Performance benchmarks meet targets
- [ ] Error handling tested
- [ ] Memory usage acceptable

### **After Deployment**
- [ ] PythonAnywhere smoke tests
- [ ] Production search queries work
- [ ] No HARAKIRI timeouts
- [ ] Response times < 60 seconds
- [ ] Logs show no blocking
- [ ] User-facing features work

---

## **Risk Mitigation**

### **Risks**
1. **Qdrant doesn't work on PythonAnywhere**
   - Mitigation: Test locally first, have Option C ready
   
2. **Migration loses data**
   - Mitigation: Backup ChromaDB, verify before deletion
   
3. **Performance regression**
   - Mitigation: Benchmark before/after, tune as needed
   
4. **New blocking issues**
   - Mitigation: Extensive async testing, monitoring

### **Rollback Plan**
If anything fails:
1. Revert to knowledge_enabled = False
2. App continues working without knowledge
3. Investigate and fix issues
4. Retry deployment when ready

**Critical:** Never deploy breaking changes without rollback plan!

---

## **Success Criteria**

Knowledge system restoration is successful when:
- ✅ No blocking or hangs
- ✅ Response times < 60 seconds (including knowledge)
- ✅ No HARAKIRI timeouts
- ✅ Search results are relevant
- ✅ No production errors
- ✅ Users can enable/use knowledge features

---

## **Resources**

### **Documentation**
- [Qdrant Python Client](https://qdrant.tech/documentation/frameworks/python/)
- [Qdrant Async Operations](https://python-client.qdrant.tech/async/)
- [aiosqlite Documentation](https://aiosqlite.omnilib.dev/)
- [SQLite FTS5](https://www.sqlite.org/fts5.html)

### **Code Examples**
- [Qdrant Async Examples](https://github.com/qdrant/qdrant-client/tree/master/examples)
- [sentence-transformers](https://www.sbert.net/)

---

## **Decision Log**

| Date | Decision | Reason |
|------|----------|--------|
| 2025-12-07 | Disable knowledge system | ChromaDB blocking async loop |
| 2025-12-07 | Try asyncio.to_thread() | Attempted non-blocking wrapper |
| 2025-12-07 | Revert to disabled | to_thread() still hangs |
| 2025-12-08 | Defer to Phase 2 | Focus on performance first |
| 2025-12-08 | **Recommend Qdrant** | **Best async solution** |

---

## **Current Status**

**Knowledge System:** DISABLED  
**Blocking Issue:** ChromaDB synchronous SQLite backend  
**Workaround:** Force `_knowledge_enabled = False`  
**Next Steps:** Implement Phase 1 optimizations, then return to knowledge system in Phase 2

**App Status:** ✅ Stable and working without knowledge features

---

## **When to Start Phase 2**

**Prerequisites:**
1. ✅ Phase 1 complete (performance optimizations)
2. ✅ App is stable and users are happy
3. ✅ No urgent bugs or issues
4. ✅ Have 3-4 weeks of dedicated time
5. ✅ Can test thoroughly before deploying

**Earliest Start:** After Phase 1 completion (~4 weeks from now)

---

**Last Updated:** 2025-12-08  
**Next Review:** After Phase 1 completion  
**Owner:** Development Team  
**Priority:** Medium (deferred)
