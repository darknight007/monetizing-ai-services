"""
Session Management Service
Handles session lifecycle and state persistence for the monetization pipeline.
"""
import uuid
import time
from typing import Dict, List, Optional, Any


class InMemorySessionService:
    """
    In-memory session storage for demo/MVP.
    
    PRODUCTION NOTE: Replace with Redis/Memcached for distributed systems.
    """
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self) -> str:
        """
        Create a new session with unique ID.
        
        Returns:
            str: Session ID (UUID4)
        """
        sid = str(uuid.uuid4())
        self.sessions[sid] = {
            "created_at": time.time(),
            "history": [],
            "metadata": {}
        }
        return sid
    
    def append(self, sid: str, record: Dict[str, Any]) -> None:
        """
        Append a record to session history.
        
        Args:
            sid: Session ID
            record: Data to append
            
        Raises:
            KeyError: If session not found
        """
        if sid not in self.sessions:
            raise KeyError(f"Session {sid} not found")
        
        record["timestamp"] = time.time()
        self.sessions[sid]["history"].append(record)
    
    def get(self, sid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data.
        
        Args:
            sid: Session ID
            
        Returns:
            Session data dict or None if not found
        """
        return self.sessions.get(sid)
    
    def delete(self, sid: str) -> bool:
        """
        Delete a session.
        
        Args:
            sid: Session ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if sid in self.sessions:
            del self.sessions[sid]
            return True
        return False
    
    def list_sessions(self) -> List[str]:
        """
        Get all active session IDs.
        
        Returns:
            List of session IDs
        """
        return list(self.sessions.keys())
    
    def cleanup_expired(self, ttl_seconds: int = 3600) -> int:
        """
        Remove sessions older than TTL.
        
        Args:
            ttl_seconds: Time-to-live in seconds (default: 1 hour)
            
        Returns:
            Number of sessions cleaned up
        """
        now = time.time()
        expired = [
            sid for sid, data in self.sessions.items()
            if now - data["created_at"] > ttl_seconds
        ]
        
        for sid in expired:
            del self.sessions[sid]
        
        return len(expired)
