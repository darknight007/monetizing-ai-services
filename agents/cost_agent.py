"""
Cost Agent
Calculates costs across multiple LLM models asynchronously.
"""
import asyncio
from typing import List, Dict, Any
from core.audit_ledger import append_entry


# Industry-standard pricing per 1K tokens (as of Dec 2025)
MODEL_PRICING = {
    "gpt-4o": 0.03,
    "gemini-pro": 0.025,
    "llama-2": 0.007,
    "claude-3": 0.015
}

# Workflow overhead cost (infrastructure, orchestration, etc.)
WORKFLOW_COST = 0.01


async def compute_cost_row(row: Dict[str, Any], model: str) -> Dict[str, Any]:
    """
    Calculate cost for a single row and model combination.
    
    Args:
        row: Usage data with tokens_in, tokens_out, workflows
        model: LLM model name
        
    Returns:
        Dict with cost breakdown
    """
    # Simulate async I/O (cost lookup, database query, etc.)
    await asyncio.sleep(0.05)
    
    # Token costs (convert to thousands)
    tokens_in_k = row["tokens_in"] / 1000.0
    tokens_out_k = row["tokens_out"] / 1000.0
    
    # Get model pricing (with fallback)
    model_price_per_1k = MODEL_PRICING.get(model, 0.01)
    
    # Calculate total cost
    token_cost = (tokens_in_k + tokens_out_k) * model_price_per_1k
    workflow_overhead = WORKFLOW_COST * row["workflows"]
    total_cost = token_cost + workflow_overhead
    
    return {
        "region": row["region"],
        "product": row["product"],
        "model": model,
        "workflows": row["workflows"],
        "token_cost": round(token_cost, 4),
        "workflow_overhead": round(workflow_overhead, 4),
        "cost": round(total_cost, 4)
    }


async def run_async(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Asynchronously compute costs for all row/model combinations.
    
    Args:
        rows: List of aggregated usage data
        
    Returns:
        List of cost projections
    """
    tasks = []
    models = list(MODEL_PRICING.keys())
    
    # Create tasks for all combinations
    for row in rows:
        for model in models:
            tasks.append(compute_cost_row(row, model))
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out any errors
    valid_results = [
        r for r in results 
        if not isinstance(r, Exception)
    ]
    
    # Log any errors
    errors = [r for r in results if isinstance(r, Exception)]
    if errors:
        print(f"WARNING: {len(errors)} cost calculations failed", flush=True)
    
    return valid_results


def run(rows: List[Dict[str, Any]], session_id: str = None) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for cost calculation.
    
    Args:
        rows: List of aggregated usage data
        session_id: Optional session ID for audit trail
        
    Returns:
        List of cost projections
        
    Raises:
        ValueError: If input data is invalid
    """
    try:
        if not rows:
            raise ValueError("No usage data provided to CostAgent")
        
        # Validate input data structure
        required_fields = ["region", "product", "workflows", "tokens_in", "tokens_out"]
        for i, row in enumerate(rows):
            missing = [f for f in required_fields if f not in row]
            if missing:
                raise ValueError(f"Row {i} missing required fields: {missing}")
        
        # Run async computation
        results = asyncio.run(run_async(rows))
        
        # Audit logging
        if session_id:
            # Calculate summary statistics
            total_cost = sum(r["cost"] for r in results)
            avg_cost = total_cost / len(results) if results else 0
            
            append_entry({
                "agent": "CostAgent",
                "session": session_id,
                "summary": results,
                "total_projections": len(results),
                "models_analyzed": list(MODEL_PRICING.keys()),
                "total_cost": round(total_cost, 2),
                "average_cost": round(avg_cost, 4)
            })
        
        return results
    
    except ValueError as e:
        if session_id:
            append_entry({
                "agent": "CostAgent",
                "session": session_id,
                "error": str(e),
                "error_type": "ValueError"
            })
        raise
    
    except Exception as e:
        if session_id:
            append_entry({
                "agent": "CostAgent",
                "session": session_id,
                "error": f"Unexpected error: {str(e)}",
                "error_type": type(e).__name__
            })
        raise


def get_model_pricing() -> Dict[str, float]:
    """
    Get current model pricing configuration.
    
    Returns:
        Dict of model names to prices per 1K tokens
    """
    return MODEL_PRICING.copy()
