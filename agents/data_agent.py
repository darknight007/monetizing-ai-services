"""
Data Agent
Aggregates usage data by region and product for cost analysis.
"""
import json
from typing import List, Dict, Any
from pathlib import Path
from core.audit_ledger import append_entry


def run(session_id: str, path: str = "data/synthetic_usage.json") -> List[Dict[str, Any]]:
    """
    Aggregate usage data by region and product.
    
    Args:
        session_id: Session identifier for audit trail
        path: Path to usage data JSON file
        
    Returns:
        List of aggregated usage records
        
    Raises:
        FileNotFoundError: If data file not found
        json.JSONDecodeError: If data file is malformed
    """
    try:
        # Load and validate data file
        if not Path(path).exists():
            raise FileNotFoundError(f"Usage data file not found: {path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("Usage data must be a JSON array")
        
        # Aggregate by (region, product) key
        agg = {}
        for record in data:
            # Validate required fields
            required_fields = ["region", "product", "workflows", "avg_tokens_in", "avg_tokens_out"]
            missing = [f for f in required_fields if f not in record]
            if missing:
                print(f"WARNING: Skipping record missing fields: {missing}", flush=True)
                continue
            
            key = (record["region"], record["product"])
            
            if key not in agg:
                agg[key] = {
                    "workflows": 0,
                    "tokens_in": 0,
                    "tokens_out": 0
                }
            
            # Accumulate metrics
            agg[key]["workflows"] += record["workflows"]
            agg[key]["tokens_in"] += record["workflows"] * record["avg_tokens_in"]
            agg[key]["tokens_out"] += record["workflows"] * record["avg_tokens_out"]
        
        # Convert to output format
        output = [
            {
                "region": key[0],
                "product": key[1],
                **value
            }
            for key, value in agg.items()
        ]
        
        # Audit logging
        append_entry({
            "agent": "DataAgent",
            "session": session_id,
            "summary": output,
            "source_file": path,
            "records_processed": len(data),
            "aggregated_rows": len(output)
        })
        
        return output
    
    except FileNotFoundError as e:
        error_msg = str(e)
        append_entry({
            "agent": "DataAgent",
            "session": session_id,
            "error": error_msg,
            "error_type": "FileNotFoundError"
        })
        raise
    
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in {path}: {str(e)}"
        append_entry({
            "agent": "DataAgent",
            "session": session_id,
            "error": error_msg,
            "error_type": "JSONDecodeError"
        })
        raise ValueError(error_msg)
    
    except Exception as e:
        error_msg = f"Unexpected error in DataAgent: {str(e)}"
        append_entry({
            "agent": "DataAgent",
            "session": session_id,
            "error": error_msg,
            "error_type": type(e).__name__
        })
        raise
