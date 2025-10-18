"""User profile management system for collecting and storing personal information."""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

class UserProfileManager:
    """Manages user profiles and personal information storage."""
    
    def __init__(self, storage_dir: str = "user_profiles"):
        # Use absolute path to prevent directory confusion
        if not os.path.isabs(storage_dir):
            project_root = Path(__file__).parent.parent
            self.storage_dir = project_root / storage_dir
        else:
            self.storage_dir = Path(storage_dir)
        
        self.storage_dir.mkdir(exist_ok=True)
        self.profile_cache = {}
        
        print(f"UserProfileManager: Storing profiles in {self.storage_dir.absolute()}")
    
    def create_user_profile(self, user_id: str = None) -> str:
        """Create a new user profile."""
        if not user_id:
            user_id = str(uuid.uuid4())
        
        profile_data = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "personal_info": {
                "name": "",
                "email": "",
                "age": None,
                "location": "",
                "occupation": "",
                "interests": [],
                "bio": ""
            },
            "preferences": {
                "communication_style": "friendly",
                "topics_of_interest": [],
                "language_preference": "en",
                "personality_type": "",
                "learning_style": "",
                "goals": []
            },
            "ai_interaction_history": {
                "total_conversations": 0,
                "favorite_topics": [],
                "preferred_models": [],
                "feedback_scores": []
            },
            "privacy_settings": {
                "data_sharing": False,
                "analytics": True,
                "personalization": True,
                "marketing": False
            },
            "metadata": {
                "profile_completion": 0,
                "last_login": None,
                "session_count": 0
            }
        }
        
        self._save_profile(profile_data)
        self.profile_cache[user_id] = profile_data
        return user_id
    
    def load_user_profile(self, user_id: str, force_reload: bool = False) -> Optional[Dict]:
        """Load a user profile."""
        if not user_id:
            return None
        
        # Check cache first (unless force_reload is True)
        if not force_reload and user_id in self.profile_cache:
            return self.profile_cache[user_id]
        
        profile_file = self.storage_dir / f"{user_id}.json"
        
        if profile_file.exists():
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                # Update cache
                self.profile_cache[user_id] = profile_data
                return profile_data
            except Exception as e:
                print(f"Error loading profile {user_id}: {e}")
        
        return None
    
    def update_personal_info(self, user_id: str, personal_info: Dict) -> bool:
        """Update personal information for a user."""
        profile = self.load_user_profile(user_id, force_reload=True)
        if not profile:
            return False
        
        # Update personal info fields
        for key, value in personal_info.items():
            if key in profile["personal_info"]:
                profile["personal_info"][key] = value
        
        profile["last_updated"] = datetime.now().isoformat()
        profile["metadata"]["profile_completion"] = self._calculate_completion(profile)
        
        self._save_profile(profile)
        self.profile_cache[user_id] = profile
        return True
    
    def update_preferences(self, user_id: str, preferences: Dict) -> bool:
        """Update user preferences."""
        profile = self.load_user_profile(user_id, force_reload=True)
        if not profile:
            return False
        
        # Update preference fields
        for key, value in preferences.items():
            if key in profile["preferences"]:
                profile["preferences"][key] = value
        
        profile["last_updated"] = datetime.now().isoformat()
        profile["metadata"]["profile_completion"] = self._calculate_completion(profile)
        
        self._save_profile(profile)
        self.profile_cache[user_id] = profile
        return True
    
    def update_privacy_settings(self, user_id: str, privacy_settings: Dict) -> bool:
        """Update privacy settings."""
        profile = self.load_user_profile(user_id, force_reload=True)
        if not profile:
            return False
        
        # Update privacy settings
        for key, value in privacy_settings.items():
            if key in profile["privacy_settings"]:
                profile["privacy_settings"][key] = value
        
        profile["last_updated"] = datetime.now().isoformat()
        
        self._save_profile(profile)
        self.profile_cache[user_id] = profile
        return True
    
    def record_interaction(self, user_id: str, interaction_data: Dict) -> bool:
        """Record AI interaction data."""
        profile = self.load_user_profile(user_id, force_reload=True)
        if not profile:
            return False
        
        # Update interaction history
        history = profile["ai_interaction_history"]
        history["total_conversations"] += 1
        
        if "topic" in interaction_data:
            if interaction_data["topic"] not in history["favorite_topics"]:
                history["favorite_topics"].append(interaction_data["topic"])
        
        if "model" in interaction_data:
            if interaction_data["model"] not in history["preferred_models"]:
                history["preferred_models"].append(interaction_data["model"])
        
        if "feedback_score" in interaction_data:
            history["feedback_scores"].append({
                "score": interaction_data["feedback_score"],
                "timestamp": datetime.now().isoformat()
            })
        
        profile["last_updated"] = datetime.now().isoformat()
        profile["metadata"]["last_login"] = datetime.now().isoformat()
        profile["metadata"]["session_count"] += 1
        
        self._save_profile(profile)
        self.profile_cache[user_id] = profile
        return True
    
    def get_user_summary(self, user_id: str) -> Optional[Dict]:
        """Get a summary of user information for AI context."""
        profile = self.load_user_profile(user_id)
        if not profile:
            return None
        
        return {
            "name": profile["personal_info"]["name"],
            "interests": profile["personal_info"]["interests"],
            "communication_style": profile["preferences"]["communication_style"],
            "topics_of_interest": profile["preferences"]["topics_of_interest"],
            "personality_type": profile["preferences"]["personality_type"],
            "goals": profile["preferences"]["goals"],
            "interaction_count": profile["ai_interaction_history"]["total_conversations"],
            "favorite_topics": profile["ai_interaction_history"]["favorite_topics"][:5]  # Top 5
        }
    
    def list_all_profiles(self) -> List[Dict]:
        """List all user profiles with basic info."""
        profiles = []
        
        for profile_file in self.storage_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                profile_info = {
                    "user_id": profile_data["user_id"],
                    "name": profile_data["personal_info"]["name"] or "Anonymous",
                    "created_at": profile_data["created_at"],
                    "last_updated": profile_data["last_updated"],
                    "completion": profile_data["metadata"]["profile_completion"],
                    "total_conversations": profile_data["ai_interaction_history"]["total_conversations"]
                }
                profiles.append(profile_info)
                
            except Exception as e:
                print(f"Error reading profile file {profile_file}: {e}")
        
        # Sort by last updated
        profiles.sort(key=lambda x: x["last_updated"], reverse=True)
        return profiles
    
    def delete_profile(self, user_id: str) -> bool:
        """Delete a user profile."""
        profile_file = self.storage_dir / f"{user_id}.json"
        
        try:
            if profile_file.exists():
                profile_file.unlink()
            
            if user_id in self.profile_cache:
                del self.profile_cache[user_id]
            
            return True
        except Exception as e:
            print(f"Error deleting profile {user_id}: {e}")
            return False
    
    def export_profile(self, user_id: str, format: str = "json") -> Optional[str]:
        """Export user profile data."""
        profile = self.load_user_profile(user_id)
        if not profile:
            return None
        
        if format == "json":
            return json.dumps(profile, indent=2, ensure_ascii=False)
        
        elif format == "txt":
            lines = [
                f"User Profile Export - {profile['created_at']}",
                f"User ID: {profile['user_id']}",
                "=" * 50,
                "",
                "Personal Information:",
                f"  Name: {profile['personal_info']['name']}",
                f"  Email: {profile['personal_info']['email']}",
                f"  Age: {profile['personal_info']['age']}",
                f"  Location: {profile['personal_info']['location']}",
                f"  Occupation: {profile['personal_info']['occupation']}",
                f"  Interests: {', '.join(profile['personal_info']['interests'])}",
                f"  Bio: {profile['personal_info']['bio']}",
                "",
                "Preferences:",
                f"  Communication Style: {profile['preferences']['communication_style']}",
                f"  Topics of Interest: {', '.join(profile['preferences']['topics_of_interest'])}",
                f"  Personality Type: {profile['preferences']['personality_type']}",
                f"  Goals: {', '.join(profile['preferences']['goals'])}",
                "",
                "AI Interaction History:",
                f"  Total Conversations: {profile['ai_interaction_history']['total_conversations']}",
                f"  Favorite Topics: {', '.join(profile['ai_interaction_history']['favorite_topics'])}",
                ""
            ]
            
            return "\n".join(lines)
        
        return None
    
    def _calculate_completion(self, profile: Dict) -> int:
        """Calculate profile completion percentage."""
        total_fields = 0
        completed_fields = 0
        
        # Personal info fields
        personal_info = profile["personal_info"]
        for key, value in personal_info.items():
            total_fields += 1
            if value and (isinstance(value, list) and len(value) > 0 or not isinstance(value, list)):
                completed_fields += 1
        
        # Preference fields
        preferences = profile["preferences"]
        for key, value in preferences.items():
            total_fields += 1
            if value and (isinstance(value, list) and len(value) > 0 or not isinstance(value, list)):
                completed_fields += 1
        
        return int((completed_fields / total_fields) * 100) if total_fields > 0 else 0
    
    def _save_profile(self, profile_data: Dict) -> None:
        """Save profile data to file."""
        profile_file = self.storage_dir / f"{profile_data['user_id']}.json"
        
        try:
            # Ensure directory exists
            self.storage_dir.mkdir(exist_ok=True)
            
            # Create backup of existing file
            if profile_file.exists():
                backup_file = profile_file.with_suffix('.json.bak')
                profile_file.rename(backup_file)
            
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            # Remove backup on successful save
            backup_file = profile_file.with_suffix('.json.bak')
            if backup_file.exists():
                backup_file.unlink()
                
        except Exception as e:
            print(f"Error saving profile {profile_data.get('user_id', 'unknown')}: {e}")
            # Restore backup if save failed
            backup_file = profile_file.with_suffix('.json.bak')
            if backup_file.exists():
                backup_file.rename(profile_file)
