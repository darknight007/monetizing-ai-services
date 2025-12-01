"""
Immutable Audit Ledger
Provides append-only logging for compliance and observability.
"""
import json
import time
import os
from typing import Dict, List, Any
from pathlib import Path


LEDGER_FILE = "output/audit_ledger.jsonl"


def _ensure_output_dir() -> None:
    """Create output directory if it doesn't exist."""
    Path(LEDGER_FILE).parent.mkdir(parents=True, exist_ok=True)


def append_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append entry to immutable audit ledger.
    
    Args:
        entry: Dictionary containing audit data
        
    Returns:
        The entry with timestamp added
        
    Note:
        - Automatically adds timestamp
        - Creates output directory if needed
        - Atomic write operation
    """
    _ensure_output_dir()
    
    # Create immutable copy with timestamp
    audit_entry = dict(entry)
    audit_entry["ts"] = time.time()
    audit_entry["iso_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    # Append to JSONL file (atomic operation)
    try:
        with open(LEDGER_FILE, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")
    except Exception as e:
        # Log to stderr but don't fail the operation
        print(f"WARNING: Failed to write audit entry: {e}", flush=True)
    
    return audit_entry


def read_ledger() -> List[Dict[str, Any]]:
    """
    Read all entries from audit ledger.
    
    Returns:
        List of audit entries (chronological order)
        
    Note:
        Returns empty list if ledger doesn't exist yet.
    """
    if not os.path.exists(LEDGER_FILE):
        return []
    
    entries = []
    try:
        with open(LEDGER_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except json.JSONDecodeError as e:
        print(f"WARNING: Corrupted audit ledger entry: {e}", flush=True)
    except Exception as e:
        print(f"ERROR: Failed to read audit ledger: {e}", flush=True)
    
    return entries


def query_ledger(
    agent: str = None,
    session: str = None,
    start_time: float = None,
    end_time: float = None
) -> List[Dict[str, Any]]:
    """
    Query audit ledger with filters.
    
    Args:
        agent: Filter by agent name
        session: Filter by session ID
        start_time: Filter by timestamp >= start_time
        end_time: Filter by timestamp <= end_time
        
    Returns:
        Filtered list of audit entries
    """
    entries = read_ledger()
    
    if agent:
        entries = [e for e in entries if e.get("agent") == agent]
    
    if session:
        entries = [e for e in entries if e.get("session") == session]
    
    if start_time:
        entries = [e for e in entries if e.get("ts", 0) >= start_time]
    
    if end_time:
        entries = [e for e in entries if e.get("ts", float('inf')) <= end_time]
    
    return entries


def get_stats() -> Dict[str, Any]:
    """
    Get statistics about the audit ledger.
    
    Returns:
        Dict with ledger statistics
    """
    if not os.path.exists(LEDGER_FILE):
        return {
            "exists": False,
            "total_entries": 0,
            "file_size_bytes": 0
        }
    
    entries = read_ledger()
    
    return {
        "exists": True,
        "total_entries": len(entries),
        "file_size_bytes": os.path.getsize(LEDGER_FILE),
        "first_entry": entries[0].get("ts") if entries else None,
        "last_entry": entries[-1].get("ts") if entries else None,
        "agents": list(set(e.get("agent") for e in entries if e.get("agent"))),
        "sessions": list(set(e.get("session") for e in entries if e.get("session")))
    }
