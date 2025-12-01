"""
Pricing Agent
Recommends pricing strategy based on cost analysis and Vertex AI insights.
Uses real Vertex AI (Gemini) for LLM-based justification.
"""
import asyncio
from typing import List, Dict, Any
from statistics import median, mean
from core.vertex_ai_client import call_llm
from core.audit_ledger import append_entry


# Pricing model types
PRICING_MODELS = ["FLAT", "USAGE", "HYBRID"]

# Default configuration
DEFAULT_MARGIN = 3.0  # 3x cost multiplier
DEFAULT_PI_INDEX = 0.85  # Pricing Index (normalized score, 1.0 = optimal)


def run(
    cost_rows: List[Dict[str, Any]],
    bundle: Dict[str, Any],
    session_id: str
) -> Dict[str, Any]:
    """
    Recommend pricing strategy based on cost projections.
    
    Args:
        cost_rows: Cost projections from CostAgent
        bundle: Bundle recommendation from BundleAgent
        session_id: Session identifier for audit trail
        
    Returns:
        Dict with pricing recommendation
        
    Strategy:
        1. Calculate cost statistics (median, mean, min, max)
        2. Apply margin to determine base pricing
        3. Derive per-unit pricing for usage-based components
        4. Get Vertex AI LLM justification
        5. Calculate Pricing Index (PI)
    """
    # Run async implementation in sync context
    return asyncio.run(_run_async(cost_rows, bundle, session_id))


async def _run_async(
    cost_rows: List[Dict[str, Any]],
    bundle: Dict[str, Any],
    session_id: str
) -> Dict[str, Any]:
    """
    Async implementation of pricing recommendation.
    
    Args:
        cost_rows: Cost projections from CostAgent
        bundle: Bundle recommendation from BundleAgent
        session_id: Session identifier for audit trail
        
    Returns:
        Dict with pricing recommendation
    """
    try:
        if not cost_rows:
            raise ValueError("No cost data provided to PricingAgent")
        
        # Extract costs from projections
        costs = [row["cost"] for row in cost_rows if "cost" in row]
        
        if not costs:
            raise ValueError("No valid cost data found")
        
        # Calculate cost statistics
        median_cost = median(costs)
        mean_cost = mean(costs)
        min_cost = min(costs)
        max_cost = max(costs)
        
        # Determine pricing model (default: HYBRID)
        pricing_model = "HYBRID"
        
        # Calculate HYBRID pricing components
        # Base fee: covers median monthly cost + margin
        base_fee = round(median_cost * DEFAULT_MARGIN * 10, 2)
        
        # Per-workflow charge: small percentage of base cost
        per_workflow = round(median_cost * 0.05, 3)
        
        # Per-1K-tokens charge: micro-pricing for token consumption
        per_1k_tokens = round(median_cost * 0.002, 4)
        
        # Calculate Pricing Index (PI)
        # Factors: margin efficiency, cost predictability, market positioning
        cost_variance = (max_cost - min_cost) / mean_cost if mean_cost > 0 else 0
        pi_index = round(DEFAULT_PI_INDEX * (1 - cost_variance * 0.1), 2)
        pi_index = max(0.5, min(1.0, pi_index))  # Clamp between 0.5 and 1.0
        
        # Build recommendation
        recommendation = {
            "model": pricing_model,
            "base_fee": base_fee,
            "per_workflow": per_workflow,
            "per_1k_tokens": per_1k_tokens,
            "pi_index": pi_index,
            "currency": "USD",
            "billing_period": "monthly",
            "cost_analysis": {
                "median_cost": round(median_cost, 4),
                "mean_cost": round(mean_cost, 4),
                "min_cost": round(min_cost, 4),
                "max_cost": round(max_cost, 4),
                "cost_variance": round(cost_variance, 2)
            },
            "margin_applied": DEFAULT_MARGIN,
            "bundle_name": bundle.get("bundle_name", "Unknown")
        }
        
        # Get LLM justification from Vertex AI
        prompt = f"Recommend pricing strategy given median monthly cost of ${median_cost:.2f}. " \
                 f"Bundle: {bundle.get('bundle_name')}. Cost range: ${min_cost:.2f}-${max_cost:.2f}"
        
        llm_response = await call_llm(
            prompt=prompt,
            model="gemini-2.0-flash",
            max_tokens=256,
            temperature=0.7
        )
        recommendation["justification"] = llm_response["text"]
        recommendation["llm_model"] = llm_response["model"]
        recommendation["llm_source"] = llm_response["source"]
        recommendation["llm_cost_usd"] = llm_response.get("cost_usd", 0.0)
        
        # Calculate example monthly bill
        example_usage = {
            "workflows": 100,
            "tokens_in": 200000,
            "tokens_out": 50000
        }
        
        total_tokens_k = (example_usage["tokens_in"] + example_usage["tokens_out"]) / 1000
        example_bill = (
            base_fee +
            (per_workflow * example_usage["workflows"]) +
            (per_1k_tokens * total_tokens_k)
        )
        
        recommendation["example_calculation"] = {
            "assumptions": example_usage,
            "base_fee": base_fee,
            "workflow_charge": round(per_workflow * example_usage["workflows"], 2),
            "token_charge": round(per_1k_tokens * total_tokens_k, 2),
            "total_monthly": round(example_bill, 2)
        }
        
        # Audit logging
        append_entry({
            "agent": "PricingAgent",
            "session": session_id,
            "recommendation": recommendation,
            "cost_projections_analyzed": len(cost_rows)
        })
        
        return recommendation
    
    except ValueError as e:
        append_entry({
            "agent": "PricingAgent",
            "session": session_id,
            "error": str(e),
            "error_type": "ValueError"
        })
        raise
    
    except Exception as e:
        append_entry({
            "agent": "PricingAgent",
            "session": session_id,
            "error": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__
        })
        raise


def calculate_bill(
    recommendation: Dict[str, Any],
    workflows: int,
    tokens_in: int,
    tokens_out: int
) -> Dict[str, Any]:
    """
    Calculate bill for given usage based on pricing recommendation.
    
    Args:
        recommendation: Pricing recommendation from run()
        workflows: Number of workflows executed
        tokens_in: Total input tokens
        tokens_out: Total output tokens
        
    Returns:
        Dict with bill breakdown
    """
    base = recommendation.get("base_fee", 0)
    per_wf = recommendation.get("per_workflow", 0)
    per_token = recommendation.get("per_1k_tokens", 0)
    
    total_tokens_k = (tokens_in + tokens_out) / 1000
    
    workflow_charge = per_wf * workflows
    token_charge = per_token * total_tokens_k
    total = base + workflow_charge + token_charge
    
    return {
        "base_fee": base,
        "workflow_charge": round(workflow_charge, 2),
        "token_charge": round(token_charge, 2),
        "subtotal": round(total, 2),
        "usage": {
            "workflows": workflows,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out
        }
    }
