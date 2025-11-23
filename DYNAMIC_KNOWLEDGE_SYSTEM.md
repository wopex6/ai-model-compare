# Dynamic Knowledge Expansion System

## 🎯 Overview

A **fully generic, self-expanding knowledge system** that automatically discovers, processes, and integrates knowledge from multiple sources for AI characters. 

### Key Features

✅ **No Hard-Coding** - Works with ANY author, field, or domain  
✅ **Auto-Discovery** - Finds new texts automatically  
✅ **Smart Tracking** - Never processes the same source twice  
✅ **Semantic Search** - Vector-based knowledge retrieval  
✅ **Easy Integration** - Works with existing and future characters  
✅ **Metadata-Driven** - Configure via profiles, not code changes  

## 🏗️ Architecture

### Components

1. **Knowledge Config** (`knowledge_config.py`)
   - Metadata-driven character profiles
   - No hard-coded authors/fields
   - Easy extensibility

2. **Knowledge Tracker** (`knowledge_tracker.py`)
   - Tracks processed sources
   - Prevents redundant work
   - Maintains processing history

3. **Knowledge Discovery** (`knowledge_discovery.py`)
   - Discovers new texts by author/field
   - Multiple sources: Project Gutenberg, Sacred Texts, Open Library, Web
   - Generic and extensible

4. **Vector Store** (`knowledge_vector_store.py`)
   - ChromaDB-based semantic search
   - Character-isolated collections
   - Efficient retrieval

5. **Knowledge System** (`knowledge_system.py`)
   - Main orchestrator
   - Integrates all components
   - Simple API

6. **Enhanced Chatbot** (`knowledge_enhanced_chatbot.py`)
   - Mixin for easy integration
   - Decorator for existing classes
   - Helper functions

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install chromadb aiohttp beautifulsoup4 lxml
```

### 2. Define a Character Profile

```python
from ai_compare.knowledge_config import CharacterKnowledgeProfile, KnowledgeDomain

# Option A: Full control
my_character = CharacterKnowledgeProfile(
    character_name="Buddha",
    primary_domains=[KnowledgeDomain.SPIRITUALITY, KnowledgeDomain.PHILOSOPHY],
    primary_authors=["Gautama Buddha", "Thich Nhat Hanh"],
    fields_of_study=["Buddhism", "Meditation", "Mindfulness"],
    core_concepts=["suffering", "enlightenment", "compassion", "mindfulness"],
    enable_auto_discovery=True
)

# Register it
from ai_compare.knowledge_config import register_character_profile
register_character_profile("buddhist_sage", my_character)
```

### 3. Add Knowledge to Existing Chatbot

#### Method A: Using Mixin

```python
from ai_compare.chatbot import AIChatbot
from ai_compare.knowledge_enhanced_chatbot import KnowledgeEnhancedMixin

class WisdomChatbot(KnowledgeEnhancedMixin, AIChatbot):
    def __init__(self):
        super().__init__("wisdom_sage", "casual_learner")
        self.setup_knowledge("wisdom_sage")  # That's it!
    
    async def chat(self, user_message: str, include_context: bool = True):
        # Automatically enhanced with knowledge
        return await self.chat_with_knowledge(user_message, include_context)
```

#### Method B: Using Decorator

```python
from ai_compare.knowledge_enhanced_chatbot import with_knowledge_enhancement

@with_knowledge_enhancement("stoic_philosopher")
class StoicChatbot(AIChatbot):
    def __init__(self):
        super().__init__("stoic_philosopher")
    # Knowledge automatically integrated!
```

#### Method C: Manual Integration

```python
from ai_compare.knowledge_system import search_character_knowledge

async def chat(self, user_message: str):
    # Get relevant knowledge
    knowledge = search_character_knowledge(
        character_id="wisdom_sage",
        query=user_message,
        n_results=3
    )
    
    # Add to prompt
    context = "\n\nRelevant wisdom:\n"
    for result in knowledge:
        context += f"\n{result['text']}\n"
    
    # Generate response with context
    enhanced_message = user_message + context
    response = await self.generate_response(enhanced_message)
    return response
```

### 4. Expand Knowledge

```python
from ai_compare.knowledge_system import expand_knowledge_for_character

# Trigger discovery and processing
summary = await expand_knowledge_for_character("wisdom_sage", force=True)

print(f"Discovered: {summary['discovered']}")
print(f"Processed: {summary['processed']}")
print(f"New authors: {summary['new_authors']}")
```

## 📋 Complete Examples

### Example 1: Create New Character from Scratch

```python
from ai_compare.knowledge_config import create_custom_profile, register_character_profile
from ai_compare.knowledge_enhanced_chatbot import KnowledgeEnhancedMixin
from ai_compare.chatbot import AIChatbot

# 1. Create profile (super easy)
profile = create_custom_profile(
    character_name="Scientist",
    domains=["science"],
    authors=["Carl Sagan", "Richard Feynman"],
    concepts=["curiosity", "cosmos", "empiricism"],
    fields_of_study=["Physics", "Astronomy"]
)

# 2. Register
register_character_profile("scientist", profile)

# 3. Create chatbot
class ScientistChatbot(KnowledgeEnhancedMixin, AIChatbot):
    def __init__(self):
        super().__init__("scientist_personality", "casual_learner")
        self.setup_knowledge("scientist")

# 4. Use it
bot = ScientistChatbot()
await bot.expand_knowledge(force=True)  # Discover Sagan/Feynman works
response = await bot.chat("Tell me about the cosmos")  # Auto-enhanced!
```

### Example 2: Add to Existing Wisdom Sage

```python
# In wisdom_chatbot.py

from .knowledge_enhanced_chatbot import KnowledgeEnhancedMixin

class WisdomChatbot(KnowledgeEnhancedMixin, AIChatbot):
    """Enhanced with dynamic knowledge"""
    
    def __init__(self, personality_preset: str = "wisdom_sage", user_preset: str = "casual_learner"):
        super().__init__(personality_preset, user_preset)
        self.setup_knowledge("wisdom_sage")  # ONE LINE!
        
    async def chat(self, user_message: str, include_context: bool = True) -> Dict:
        """Auto-enhanced with discovered Taoist texts"""
        # Detect wisdom requests (your existing code)
        wisdom_response = await self._check_wisdom_request(user_message)
        if wisdom_response:
            return wisdom_response
        
        # Enhanced with knowledge system
        return await self.chat_with_knowledge(user_message, include_context)
```

### Example 3: Manual Control

```python
from ai_compare.knowledge_system import get_knowledge_system

system = get_knowledge_system()

# Add custom text manually
system.add_manual_source(
    character_id="wisdom_sage",
    text="The Tao that can be told is not the eternal Tao...",
    author="Lao Tzu",
    title="Tao Te Ching - Chapter 1",
    field="Taoism"
)

# Search specific author
results = system.search_knowledge(
    character_id="wisdom_sage",
    query="What is wu wei?",
    n_results=5,
    filter_author="Lao Tzu"
)

# Get stats
stats = system.get_character_stats("wisdom_sage")
print(f"Total sources: {stats['tracker']['total_sources']}")
print(f"Authors: {stats['tracker']['authors']}")
```

## 🔧 Configuration

### Character Profile Options

```python
CharacterKnowledgeProfile(
    character_name="Name",
    
    # What to search for
    primary_domains=[KnowledgeDomain.PHILOSOPHY],
    primary_authors=["Author 1", "Author 2"],
    related_authors=["Related 1"],  # Optional
    fields_of_study=["Field 1", "Field 2"],
    core_concepts=["concept1", "concept2"],
    related_concepts=["related1"],  # Optional
    
    # Discovery settings
    enable_auto_discovery=True,
    max_sources_per_author=10,
    max_new_authors=5,
    discovery_frequency="weekly",  # never, daily, weekly, monthly
    
    # Search keywords for discovery
    discovery_keywords=["keyword1", "keyword2"],
    
    # Custom metadata
    custom_metadata={"key": "value"}
)
```

### Discovery Sources

Current implementations:
- ✅ **Project Gutenberg** - Free classical texts
- ✅ **Sacred Texts** - Spiritual/philosophical texts
- ✅ **Open Library** - Comprehensive book database
- 🔄 **Web Search** - Placeholder (add your API)

Easy to add more:
```python
class MyCustomDiscovery(DiscoveryEngine):
    def supports_author_search(self) -> bool:
        return True
    
    async def search_by_author(self, author: str, max_results: int):
        # Your implementation
        return discovered_sources
```

## 📊 Tracking & Statistics

### Check What's Been Processed

```python
tracker = system.tracker

# Check if author processed
if tracker.is_author_processed("Marcus Aurelius", "stoic_philosopher"):
    print("Already have Marcus Aurelius texts")

# Get processed sources by author
sources = tracker.get_processed_by_author("Lao Tzu", "wisdom_sage")
for source in sources:
    print(f"{source.title} - {source.chunk_count} chunks")

# Get unprocessed authors
profile = get_character_profile("wisdom_sage")
unprocessed = tracker.get_unprocessed_authors(
    profile.primary_authors,
    "wisdom_sage"
)
print(f"Still need to process: {unprocessed}")
```

### View Statistics

```python
stats = system.get_character_stats("wisdom_sage")

print(f"Total sources: {stats['tracker']['total_sources']}")
print(f"Total chunks: {stats['vector_store']['total_chunks']}")
print(f"Authors: {stats['tracker']['authors']}")
print(f"Fields: {stats['tracker']['fields']}")

# Recent discoveries
for discovery in stats['recent_discoveries']:
    print(f"{discovery['date']}: Found {discovery['found']}, Processed {discovery['processed']}")
```

## 🔄 Automatic Expansion

### Background Task

```python
# In your Flask app or background worker

async def periodic_knowledge_expansion():
    """Run periodically to expand knowledge"""
    characters = ["wisdom_sage", "stoic_philosopher", "super_motivational_coach"]
    
    for char_id in characters:
        try:
            summary = await expand_knowledge_for_character(char_id)
            if summary.get('processed', 0) > 0:
                print(f"Expanded {char_id}: {summary['processed']} new sources")
        except Exception as e:
            print(f"Error expanding {char_id}: {e}")

# Schedule this to run daily/weekly
```

### On-Demand Expansion

```python
# Flask route
@app.route('/api/admin/expand-knowledge/<character_id>', methods=['POST'])
@require_auth
async def expand_character_knowledge(character_id):
    """Admin endpoint to trigger knowledge expansion"""
    summary = await expand_knowledge_for_character(character_id, force=True)
    return jsonify(summary)
```

## 🎨 Future Character Integration

### The Magic: No Code Changes Needed!

To add a NEW character with knowledge:

1. **Create profile** (5 lines of code)
2. **Register it** (1 line)
3. **Add mixin** (1 line in class definition)
4. **Done!** ✅

```python
# Create
profile = create_custom_profile(
    character_name="Socrates",
    domains=["philosophy"],
    authors=["Plato", "Xenophon"],
    concepts=["dialectic", "virtue", "knowledge"]
)

# Register
register_character_profile("socratic_sage", profile)

# Use
@with_knowledge_enhancement("socratic_sage")
class SocraticChatbot(AIChatbot):
    pass

# Done! System automatically:
# - Discovers Plato's works
# - Downloads and chunks them
# - Adds to vector DB
# - Enhances chat responses
# - Never repeats work
```

## 🔍 How It Works

### Discovery → Processing → Retrieval

```
1. DISCOVERY
   ├─ Check if discovery needed (based on frequency)
   ├─ Check processed sources (avoid duplicates)
   ├─ Search Project Gutenberg for "Marcus Aurelius"
   ├─ Search Sacred Texts for "Stoicism"
   └─ Return DiscoveredSource objects

2. PROCESSING
   ├─ Download source content
   ├─ Extract clean text
   ├─ Chunk into 500-char segments with overlap
   ├─ Add to ChromaDB vector store
   └─ Mark as processed in tracker

3. RETRIEVAL
   ├─ User asks question
   ├─ Semantic search in vector DB
   ├─ Return top N relevant chunks
   └─ Add to AI prompt as context
```

### Deduplication

- **Source signature** based on title + author hash
- **Chunk IDs** based on source + index
- **Tracker** prevents reprocessing
- **Smart ranking** by relevance score

## 📁 Data Storage

```
knowledge_data/
├── processed_sources.json      # What's been processed
├── discoveries.json             # Discovery history
├── source_index.json            # Character → Sources mapping
└── vector_db/                   # ChromaDB storage
    ├── knowledge_stoic_philosopher/
    ├── knowledge_wisdom_sage/
    └── knowledge_super_motivational_coach/
```

## 🛠️ API Reference

### Main Functions

```python
# System operations
system = get_knowledge_system()
await system.expand_character_knowledge(character_id, force=False)
system.search_knowledge(character_id, query, n_results=5)
system.get_character_stats(character_id)
system.add_manual_source(character_id, text, author, title)

# Convenience functions
await expand_knowledge_for_character(character_id, force=False)
search_character_knowledge(character_id, query, n_results=5)
get_knowledge_stats(character_id)

# Character registration
register_character_profile(character_id, profile)
get_character_profile(character_id)

# Chatbot integration
class MyBot(KnowledgeEnhancedMixin, AIChatbot):
    def __init__(self):
        self.setup_knowledge(character_id)
    
    await bot.chat_with_knowledge(message)
    await bot.expand_knowledge(force=False)
    bot.search_my_knowledge(query, n_results=5)
    bot.add_custom_knowledge(text, author, title)
```

## 🎯 Benefits

### For Developers

- ✅ **No hard-coding** - All configuration via metadata
- ✅ **Future-proof** - New characters = 5 lines of code
- ✅ **Maintainable** - Clear separation of concerns
- ✅ **Testable** - Each component isolated

### For AI Characters

- ✅ **Authentic** - Cites actual sources
- ✅ **Deep knowledge** - Access to full texts
- ✅ **Contextual** - Semantic search finds relevant passages
- ✅ **Growing** - Knowledge expands automatically

### For Users

- ✅ **Accurate** - Responses grounded in sources
- ✅ **Cited** - Can verify information
- ✅ **Rich** - More depth than hard-coded quotes
- ✅ **Fresh** - New discoveries added over time

## 🚨 Important Notes

1. **ChromaDB Required**: `pip install chromadb`
2. **Async Required**: Use `await` for expansion/discovery
3. **Storage**: Vector DB can get large (plan accordingly)
4. **Rate Limits**: External APIs may have limits
5. **Copyright**: Respect source licenses

## 🔮 Future Enhancements

- [ ] PDF parsing (add PyPDF2)
- [ ] Web search API integration (Brave, Serper)
- [ ] Multi-language support
- [ ] Knowledge graph visualization
- [ ] Cross-character knowledge sharing
- [ ] Citation formatting options
- [ ] Embeddings model selection
- [ ] Incremental updates
- [ ] Knowledge verification/quality scoring

## 📝 License & Attribution

Ensure compliance with source licenses (Project Gutenberg, Sacred Texts, etc.)

---

**Result**: A completely generic, self-expanding knowledge system that works with ANY character, never hard-codes authors/fields, automatically discovers new texts, and seamlessly integrates into existing and future chatbots! 🎉
