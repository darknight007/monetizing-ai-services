"""
Memory Bank
Provides session-scoped key-value storage for agent communication.
"""
from typing import Dict, List, Any, Optional


class MemoryBank:
    """
    In-memory storage for session-specific data.
    
    Enables agents to share state within a session without
    polluting global scope or requiring external storage.
    
    PRODUCTION NOTE: Replace with Redis for distributed systems.
    """
    
    def __init__(self):
        # Structure: {session_id: {key: [values]}}
        self.memory: Dict[str, Dict[str, List[Any]]] = {}
    
    def store(self, session_id: str, key: str, value: Any) -> None:
        """
        Store a value in session memory.
        
        Args:
            session_id: Session identifier
            key: Storage key
            value: Value to store (appended to list)
            
        Note:
            Values are appended to a list, allowing multiple
            writes to the same key within a session.
        """
        if session_id not in self.memory:
            self.memory[session_id] = {}
        
        if key not in self.memory[session_id]:
            self.memory[session_id][key] = []
        
        self.memory[session_id][key].append(value)
    
    def read(self, session_id: str, key: str) -> List[Any]:
        """
        Read values from session memory.
        
        Args:
            session_id: Session identifier
            key: Storage key
            
        Returns:
            List of values (empty list if key not found)
        """
        return self.memory.get(session_id, {}).get(key, [])
    
    def read_latest(self, session_id: str, key: str) -> Optional[Any]:
        """
        Read most recent value for a key.
        
        Args:
            session_id: Session identifier
            key: Storage key
            
        Returns:
            Latest value or None if not found
        """
        values = self.read(session_id, key)
        return values[-1] if values else None
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear all data for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session existed, False otherwise
        """
        if session_id in self.memory:
            del self.memory[session_id]
            return True
        return False
    
    def clear_key(self, session_id: str, key: str) -> bool:
        """
        Clear specific key within a session.
        
        Args:
            session_id: Session identifier
            key: Storage key
            
        Returns:
            True if key existed, False otherwise
        """
        if session_id in self.memory and key in self.memory[session_id]:
            del self.memory[session_id][key]
            return True
        return False
    
    def get_session_keys(self, session_id: str) -> List[str]:
        """
        Get all keys for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of keys (empty if session not found)
        """
        return list(self.memory.get(session_id, {}).keys())
    
    def session_exists(self, session_id: str) -> bool:
        """
        Check if session has any data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session has data
        """
        return session_id in self.memory
