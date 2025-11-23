# Dynamic Knowledge System - Architecture Diagram

## 🏗️ System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERACTS WITH AI                        │
│                   "What is wu wei in Taoism?"                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  KNOWLEDGE-ENHANCED CHATBOT                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  WisdomChatbot (KnowledgeEnhancedMixin + AIChatbot)      │  │
│  │  - Receives user message                                  │  │
│  │  - Searches knowledge base                                │  │
│  │  - Enhances AI prompt with discovered texts               │  │
│  │  - Returns response with citations                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DYNAMIC KNOWLEDGE SYSTEM                        │
│                   (Main Orchestrator)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • Expand Knowledge (discover + process)                  │  │
│  │  • Search Knowledge (semantic retrieval)                  │  │
│  │  • Get Statistics                                         │  │
│  │  • Add Manual Sources                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────┬───────────────┬─────────────────┬─────────────────────┘
          │               │                 │
          ▼               ▼                 ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────────┐
│  DISCOVERY  │  │   TRACKER   │  │  VECTOR STORE   │
│   ENGINE    │  │             │  │   (ChromaDB)    │
└─────────────┘  └─────────────┘  └─────────────────┘
```

## 📊 Component Architecture

### 1. Character Configuration Layer
```
┌──────────────────────────────────────────────────────┐
│         CHARACTER KNOWLEDGE PROFILES                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │ Sage Wei   │  │  Marcus    │  │    Max     │    │
│  │ (Taoist)   │  │  (Stoic)   │  │ (Motivator)│    │
│  │            │  │            │  │            │    │
│  │ Authors:   │  │ Authors:   │  │ Authors:   │    │
│  │ • Lao Tzu  │  │ • M.Aurel. │  │ • T.Robbins│    │
│  │ • Zhuangzi │  │ • Epictetus│  │ • B.Burchar│    │
│  │            │  │            │  │            │    │
│  │ Fields:    │  │ Fields:    │  │ Fields:    │    │
│  │ • Taoism   │  │ • Stoicism │  │ • Peak Perf│    │
│  │ • Eastern  │  │ • Ethics   │  │ • Goals    │    │
│  └────────────┘  └────────────┘  └────────────┘    │
│                                                       │
│  ✅ NO HARD-CODING - All metadata-driven            │
│  ✅ EXTENSIBLE - Add new characters easily          │
└──────────────────────────────────────────────────────┘
```

### 2. Knowledge Discovery Flow
```
┌──────────────────────────────────────────────────────────┐
│               KNOWLEDGE DISCOVERY ENGINE                  │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  1. CHARACTER PROFILE                                     │
│     ↓                                                     │
│  "Need texts by: Lao Tzu, Zhuangzi"                     │
│     ↓                                                     │
│  2. SEARCH MULTIPLE SOURCES                              │
│     ├─→ Project Gutenberg  → "Tao Te Ching (free)"     │
│     ├─→ Sacred Texts       → "Zhuangzi texts"          │
│     ├─→ Open Library       → "Commentaries"            │
│     └─→ [Your API]         → [Custom sources]          │
│     ↓                                                     │
│  3. DISCOVERED SOURCES                                    │
│     • Title: "Tao Te Ching"                              │
│     • Author: "Lao Tzu"                                  │
│     • URL: https://...                                   │
│     • Confidence: 0.95                                   │
│     ↓                                                     │
│  4. CHECK TRACKER                                         │
│     "Already processed?" → No → Continue                 │
│                          → Yes → Skip                    │
│     ↓                                                     │
│  5. DOWNLOAD & PROCESS                                    │
│     Download → Extract Text → Chunk → Vector Store       │
│     ↓                                                     │
│  6. MARK AS PROCESSED                                     │
│     Update tracker → Never process again                 │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 3. Knowledge Processing Pipeline
```
┌─────────────────────────────────────────────────────────────┐
│              PROCESSING PIPELINE                             │
└─────────────────────────────────────────────────────────────┘

  📥 RAW SOURCE                                               
  ┌──────────────────────────────────────┐
  │ "The Tao that can be told is not     │
  │  the eternal Tao. The name that can  │
  │  be named is not the eternal name... │
  │  [full text of Tao Te Ching]         │
  └──────────────────────────────────────┘
             ▼
  🔪 CHUNKING (SimpleTextChunker)
  ┌──────────────────────────────────────┐
  │ Chunk 1: "The Tao that can be told   │
  │           is not the eternal Tao..." │
  │                                       │
  │ Chunk 2: "The name that can be named │
  │           is not the eternal name..." │
  │                                       │
  │ Chunk 3: "The nameless is the origin │
  │           of heaven and earth..."     │
  │ [500 chars each, 50 char overlap]    │
  └──────────────────────────────────────┘
             ▼
  🔢 EMBEDDING (ChromaDB)
  ┌──────────────────────────────────────┐
  │ Vector 1: [0.234, 0.567, 0.891, ...] │
  │ Vector 2: [0.123, 0.456, 0.789, ...] │
  │ Vector 3: [0.345, 0.678, 0.012, ...] │
  │ [High-dimensional semantic vectors]   │
  └──────────────────────────────────────┘
             ▼
  💾 STORAGE (Vector Database)
  ┌──────────────────────────────────────┐
  │ Collection: knowledge_wisdom_sage     │
  │                                       │
  │ Chunk ID | Vector | Metadata         │
  │ ────────────────────────────────────│
  │ tao_ch1_0| [...]  | Lao Tzu, Ch.1   │
  │ tao_ch1_1| [...]  | Lao Tzu, Ch.1   │
  │ tao_ch2_0| [...]  | Lao Tzu, Ch.2   │
  │ [Searchable semantic database]        │
  └──────────────────────────────────────┘
             ▼
  ✅ TRACKED
  ┌──────────────────────────────────────┐
  │ processed_sources.json                │
  │ {                                     │
  │   "tao_te_ching": {                  │
  │     "author": "Lao Tzu",             │
  │     "status": "completed",           │
  │     "chunks": 81,                    │
  │     "date": "2025-11-21"             │
  │   }                                   │
  │ }                                     │
  └──────────────────────────────────────┘
```

### 4. Semantic Search & Retrieval
```
┌─────────────────────────────────────────────────────────────┐
│                  SEMANTIC SEARCH FLOW                        │
└─────────────────────────────────────────────────────────────┘

  👤 USER QUERY
  "What is wu wei in Taoism?"
             ▼
  🔢 QUERY EMBEDDING
  [0.456, 0.789, 0.012, ...]
             ▼
  🔍 VECTOR SEARCH (ChromaDB)
  ┌──────────────────────────────────────┐
  │ Search: knowledge_wisdom_sage         │
  │ Query Vector: [0.456, 0.789, ...]    │
  │ Top 5 Similar Chunks                  │
  └──────────────────────────────────────┘
             ▼
  📊 RANKED RESULTS
  ┌──────────────────────────────────────┐
  │ 1. Relevance: 0.92                    │
  │    "Wu wei is action without forcing, │
  │     allowing things to unfold..."     │
  │    Source: Tao Te Ching, Ch. 37      │
  │                                       │
  │ 2. Relevance: 0.88                    │
  │    "The sage acts without action,     │
  │     teaches without words..."         │
  │    Source: Tao Te Ching, Ch. 2       │
  │                                       │
  │ 3. Relevance: 0.85                    │
  │    "Do nothing and nothing is left    │
  │     undone..."                        │
  │    Source: Tao Te Ching, Ch. 48      │
  └──────────────────────────────────────┘
             ▼
  📝 ENHANCED AI PROMPT
  ┌──────────────────────────────────────┐
  │ Original: "What is wu wei?"           │
  │                                       │
  │ + Context from Tao Te Ching:         │
  │   [3 most relevant passages]          │
  │                                       │
  │ + Instruction: "Use this wisdom       │
  │   naturally, cite sources"            │
  └──────────────────────────────────────┘
             ▼
  🤖 AI RESPONSE
  "Wu wei, as taught in the Tao Te Ching,
   is the principle of effortless action..."
   
   [Cites: Tao Te Ching, Chapters 2, 37, 48]
```

### 5. Data Flow Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                    COMPLETE DATA FLOW                        │
└─────────────────────────────────────────────────────────────┘

CHARACTER       DISCOVERY       PROCESSING      STORAGE
PROFILE         ENGINE          PIPELINE        LAYER
   │               │                │              │
   ├─ Authors ────→ Search ───────→ Download ────→│
   │               │                │              │
   ├─ Fields ─────→ Find ─────────→ Extract ─────→│
   │               │                │              │
   ├─ Concepts ───→ Rank ─────────→ Chunk ───────→│
   │               │                │              │
   └─ Settings ───→ Filter ────────→ Embed ───────→ Vector DB
                   │                │              │
                   │                └─────────────→ Tracker
                   │
                   └─ Check Tracker (avoid duplicates)


RETRIEVAL       ENHANCEMENT     AI GENERATION
LAYER           LAYER           LAYER
   │               │                │
   │               │                │
   ←─ Query ──────← User Message ──│
   │               │                │
   ├─ Search ─────→ Add Context ───→ Generate
   │               │                │
   ├─ Rank ───────→ Format ────────→ Response
   │               │                │
   └─ Return ─────→ Cite Sources ──→ User
```

### 6. Component Interactions
```
┌───────────────────────────────────────────────────────────────┐
│                   COMPONENT INTERACTIONS                       │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  KnowledgeEnhancedMixin                                       │
│  ├─→ calls → KnowledgeSystem.search_knowledge()              │
│  ├─→ calls → KnowledgeSystem.expand_character_knowledge()    │
│  └─→ enhances → AIChatbot.chat()                             │
│                                                                │
│  KnowledgeSystem (orchestrator)                               │
│  ├─→ uses → KnowledgeConfig (profiles)                       │
│  ├─→ uses → KnowledgeTracker (state)                         │
│  ├─→ uses → KnowledgeDiscovery (sources)                     │
│  ├─→ uses → KnowledgeVectorStore (search)                    │
│  └─→ coordinates all components                               │
│                                                                │
│  KnowledgeTracker                                              │
│  ├─→ tracks → Processed Sources                               │
│  ├─→ tracks → Discovery History                               │
│  ├─→ prevents → Duplicate Processing                          │
│  └─→ persists to → JSON files                                 │
│                                                                │
│  KnowledgeDiscovery                                            │
│  ├─→ searches → Project Gutenberg                             │
│  ├─→ searches → Sacred Texts                                  │
│  ├─→ searches → Open Library                                  │
│  ├─→ deduplicates → DiscoveredSources                        │
│  └─→ ranks by → Relevance                                     │
│                                                                │
│  KnowledgeVectorStore                                          │
│  ├─→ uses → ChromaDB                                          │
│  ├─→ creates → Per-Character Collections                      │
│  ├─→ performs → Semantic Search                               │
│  └─→ returns → Ranked Results                                 │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

## 🎯 Key Design Principles

### 1. **Separation of Concerns**
```
Configuration → Discovery → Processing → Storage → Retrieval
     ↓              ↓           ↓           ↓         ↓
  Metadata      Find Text   Clean/Chunk  Vector DB  Search
```

### 2. **Dependency Injection**
```
Character Profile (metadata)
        ↓
Dynamic System Creation (no hard-coding)
        ↓
Runtime Configuration (extensible)
```

### 3. **Isolation**
```
Character A Knowledge ─┐
                       ├─→ Separate Vector Collections
Character B Knowledge ─┘    (No cross-contamination)
```

### 4. **Idempotency**
```
Process Source A ─→ Tracked
      ↓
Try Again ─→ Check Tracker ─→ Skip (already done)
```

### 5. **Extensibility**
```
New Discovery Source?
  ↓
Implement DiscoveryEngine interface
  ↓
Add to KnowledgeDiscovery.discovery_sources
  ↓
Works automatically!
```

## 📦 File Organization
```
ai_compare/
├── knowledge_config.py          ← Character profiles
│   ├── CharacterKnowledgeProfile
│   ├── KNOWLEDGE_PROFILES (pre-configured)
│   └── Helper functions
│
├── knowledge_tracker.py         ← State tracking
│   ├── ProcessedSource (what's done)
│   ├── DiscoveryRecord (history)
│   └── KnowledgeTracker (main class)
│
├── knowledge_discovery.py       ← Source discovery
│   ├── DiscoveredSource
│   ├── KnowledgeDiscovery
│   ├── ProjectGutenbergDiscovery
│   ├── SacredTextsDiscovery
│   ├── OpenLibraryDiscovery
│   └── WebSearchDiscovery (placeholder)
│
├── knowledge_vector_store.py    ← Semantic search
│   ├── KnowledgeVectorStore
│   └── SimpleTextChunker
│
├── knowledge_system.py          ← Main orchestrator
│   ├── DynamicKnowledgeSystem
│   └── Convenience functions
│
└── knowledge_enhanced_chatbot.py ← Integration
    ├── KnowledgeEnhancedMixin
    ├── with_knowledge_enhancement (decorator)
    └── Helper functions
```

## 🔄 Lifecycle

### Initial Setup
```
1. Define Character Profile (metadata)
2. Register Profile
3. Add Mixin to Chatbot
```

### First Expansion
```
1. Check Profile
2. Discover Sources (Gutenberg, Sacred Texts, etc.)
3. Download & Process
4. Store in Vector DB
5. Track as Processed
```

### Subsequent Expansions
```
1. Check Discovery Frequency
2. Check Tracker (skip processed)
3. Discover NEW sources only
4. Process & Store
5. Update Tracker
```

### Every Chat
```
1. User asks question
2. Search Vector DB (semantic)
3. Get relevant chunks
4. Enhance AI prompt
5. Generate response
6. Cite sources
```

---

**Result**: A fully generic, self-maintaining knowledge system that scales to unlimited characters and domains! 🎉
