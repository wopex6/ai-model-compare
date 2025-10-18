"""Conversation persistence manager for saving and loading chat history."""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

class ConversationManager:
    """Manages conversation persistence and session handling."""
    
    def __init__(self, storage_dir: str = "conversations"):
        # Use absolute path to prevent directory confusion
        if not os.path.isabs(storage_dir):
            # Store conversations in the project directory
            project_root = Path(__file__).parent.parent
            self.storage_dir = project_root / storage_dir
        else:
            self.storage_dir = Path(storage_dir)
        
        self.storage_dir.mkdir(exist_ok=True)
        self.current_session_id = None
        self.conversation_cache = {}
        
        # Log storage location for debugging
        print(f"ConversationManager: Storing conversations in {self.storage_dir.absolute()}")
    
    def create_session(self, session_type: str = "chat") -> str:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        
        session_data = {
            "session_id": session_id,
            "session_type": session_type,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "messages": [],
            "metadata": {
                "personality": None,
                "context_enabled": True,
                "message_count": 0
            }
        }
        
        self._save_session(session_data)
        self.conversation_cache[session_id] = session_data
        return session_id
    
    def load_session(self, session_id: str, force_reload: bool = False) -> Optional[Dict]:
        """Load an existing conversation session."""
        if not session_id:
            return None
            
        # Check cache first (unless force_reload is True)
        if not force_reload and session_id in self.conversation_cache:
            cached_data = self.conversation_cache[session_id]
            print(f"Returning cached session {session_id} with {len(cached_data.get('messages', []))} messages")
            return cached_data
        
        session_file = self.storage_dir / f"{session_id}.json"
        print(f"Loading session from disk: {session_file.absolute()}")
        
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    
                # Validate session data structure
                if not isinstance(session_data, dict) or 'session_id' not in session_data:
                    print(f"Invalid session data structure in {session_id}")
                    return None
                    
                # Update cache with fresh data
                self.conversation_cache[session_id] = session_data
                self.current_session_id = session_id
                print(f"Successfully loaded session {session_id} from disk with {len(session_data.get('messages', []))} messages")
                return session_data
            except Exception as e:
                print(f"Error loading session {session_id}: {e}")
        else:
            print(f"Session file does not exist: {session_file}")
        
        return None
    
    def save_message(self, session_id: str, role: str, content: str, metadata: Dict = None) -> bool:
        """Save a message to the conversation history."""
        # Force reload from disk to get latest data
        session_data = self.load_session(session_id, force_reload=True)
        if not session_data:
            return False
        
        message = {
            "role": role,  # "user", "assistant", "system"
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        session_data["messages"].append(message)
        session_data["last_updated"] = datetime.now().isoformat()
        session_data["metadata"]["message_count"] = len(session_data["messages"])
        
        self._save_session(session_data)
        # Update cache with the new data
        self.conversation_cache[session_id] = session_data
        print(f"Saved message to session {session_id}, now has {len(session_data['messages'])} messages")
        return True
    
    def get_conversation_history(self, session_id: str, limit: int = None, force_reload: bool = False) -> List[Dict]:
        """Get conversation history for a session."""
        session_data = self.load_session(session_id, force_reload=force_reload)
        if not session_data:
            return []
        
        messages = session_data["messages"]
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_context_messages(self, session_id: str, max_tokens: int = 4000) -> List[Dict]:
        """Get recent messages that fit within token limit for context."""
        messages = self.get_conversation_history(session_id)
        
        # Approximate token counting (rough estimate)
        context_messages = []
        total_tokens = 0
        
        # Start from most recent and work backwards
        for message in reversed(messages):
            # Rough token estimate: 1 token ≈ 0.75 words
            message_tokens = len(message["content"].split()) / 0.75
            
            if total_tokens + message_tokens > max_tokens:
                break
            
            context_messages.insert(0, message)
            total_tokens += message_tokens
        
        return context_messages
    
    def update_session_metadata(self, session_id: str, metadata: Dict) -> bool:
        """Update session metadata (personality, settings, etc.)."""
        session_data = self.load_session(session_id)
        if not session_data:
            return False
        
        session_data["metadata"].update(metadata)
        session_data["last_updated"] = datetime.now().isoformat()
        
        self._save_session(session_data)
        self.conversation_cache[session_id] = session_data
        return True
    
    def list_sessions(self, session_type: str = None) -> List[Dict]:
        """List all available conversation sessions."""
        sessions = []
        
        for session_file in self.storage_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                if session_type and session_data.get("session_type") != session_type:
                    continue
                
                session_info = {
                    "session_id": session_data["session_id"],
                    "session_type": session_data.get("session_type", "chat"),
                    "created_at": session_data["created_at"],
                    "last_updated": session_data["last_updated"],
                    "message_count": session_data["metadata"]["message_count"],
                    "preview": self._get_session_preview(session_data)
                }
                sessions.append(session_info)
                
            except Exception as e:
                print(f"Error reading session file {session_file}: {e}")
        
        # Sort by last updated (most recent first)
        sessions.sort(key=lambda x: x["last_updated"], reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session."""
        session_file = self.storage_dir / f"{session_id}.json"
        
        try:
            if session_file.exists():
                session_file.unlink()
            
            if session_id in self.conversation_cache:
                del self.conversation_cache[session_id]
            
            if self.current_session_id == session_id:
                self.current_session_id = None
            
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    def export_session(self, session_id: str, format: str = "json") -> Optional[str]:
        """Export session data in various formats."""
        session_data = self.load_session(session_id)
        if not session_data:
            return None
        
        if format == "json":
            return json.dumps(session_data, indent=2, ensure_ascii=False)
        
        elif format == "txt":
            lines = [
                f"Conversation Export - {session_data['created_at']}",
                f"Session Type: {session_data.get('session_type', 'chat')}",
                f"Messages: {len(session_data['messages'])}",
                "=" * 50,
                ""
            ]
            
            for msg in session_data["messages"]:
                timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"[{timestamp}] {msg['role'].upper()}: {msg['content']}")
                lines.append("")
            
            return "\n".join(lines)
        
        return None
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Clean up sessions older than specified days."""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        for session_file in self.storage_dir.glob("*.json"):
            try:
                if session_file.stat().st_mtime < cutoff_date:
                    session_file.unlink()
                    deleted_count += 1
            except Exception as e:
                print(f"Error cleaning up {session_file}: {e}")
        
        return deleted_count
    
    def _save_session(self, session_data: Dict) -> None:
        """Save session data to file."""
        session_file = self.storage_dir / f"{session_data['session_id']}.json"
        
        try:
            # Ensure directory exists
            self.storage_dir.mkdir(exist_ok=True)
            
            # Create backup of existing file
            if session_file.exists():
                backup_file = session_file.with_suffix('.json.bak')
                session_file.rename(backup_file)
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            print(f"Session {session_data['session_id']} saved to {session_file.absolute()}")
            
            # Remove backup on successful save
            backup_file = session_file.with_suffix('.json.bak')
            if backup_file.exists():
                backup_file.unlink()
                
        except Exception as e:
            print(f"Error saving session {session_data.get('session_id', 'unknown')}: {e}")
            # Restore backup if save failed
            backup_file = session_file.with_suffix('.json.bak')
            if backup_file.exists():
                backup_file.rename(session_file)
                print(f"Restored backup for session {session_data.get('session_id', 'unknown')}")
    
    def _get_session_preview(self, session_data: Dict) -> str:
        """Get a preview of the session for display."""
        messages = session_data.get("messages", [])
        
        if not messages:
            return "No messages"
        
        # Get first user message or first message
        for msg in messages:
            if msg["role"] == "user":
                preview = msg["content"][:100]
                return preview + "..." if len(msg["content"]) > 100 else preview
        
        # Fallback to first message
        first_msg = messages[0]["content"][:100]
        return first_msg + "..." if len(messages[0]["content"]) > 100 else first_msg
