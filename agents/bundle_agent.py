"""
Bundle Agent
Proposes optimal product bundles based on usage patterns and Vertex AI insights.
"""
import asyncio
from typing import List, Dict, Any
from core.vertex_ai_client import call_llm
from core.audit_ledger import append_entry


def run(rows: List[Dict[str, Any]], session_id: str) -> Dict[str, Any]:
    """
    Propose product bundle based on co-occurrence and usage patterns.
    
    Args:
        rows: Aggregated usage data by region/product
        session_id: Session identifier for audit trail
        
    Returns:
        Dict with bundle recommendation
        
    Strategy:
        1. Identify top 2 products by total workflow volume
        2. Calculate expected bundle uplift
        3. Get Vertex AI justification for recommendation
    """
    # Run async LLM call in sync context
    return asyncio.run(_run_async(rows, session_id))


async def _run_async(rows: List[Dict[str, Any]], session_id: str) -> Dict[str, Any]:
    """Async implementation of bundle agent."""
    try:
        if not rows:
            raise ValueError("No usage data provided to BundleAgent")
        
        # Aggregate workflow counts by product across all regions
        product_workflows = {}
        for row in rows:
            product = row.get("product")
            workflows = row.get("workflows", 0)
            
            if product:
                product_workflows[product] = product_workflows.get(product, 0) + workflows
        
        if not product_workflows:
            raise ValueError("No valid product data found")
        
        # Sort by workflow count and select top 2
        sorted_products = sorted(
            product_workflows.items(),
            key=lambda x: -x[1]
        )
        
        if len(sorted_products) < 2:
            # Single product case
            top_product = sorted_products[0][0]
            bundle = {
                "bundle_name": f"{top_product}-Premium",
                "products": [top_product],
                "expected_uplift_pct": 3,
                "confidence": "low",
                "reason": "Single product detected, limited bundling opportunity"
            }
        else:
            # Multi-product bundle
            product1, workflows1 = sorted_products[0]
            product2, workflows2 = sorted_products[1]
            
            # Calculate bundle metrics
            total_workflows = workflows1 + workflows2
            balance_ratio = min(workflows1, workflows2) / max(workflows1, workflows2)
            
            # Estimate uplift based on product balance
            # Better balance = higher cross-sell potential
            expected_uplift = 5 + int(balance_ratio * 10)
            
            bundle = {
                "bundle_name": f"{product1}+{product2}",
                "products": [product1, product2],
                "expected_uplift_pct": expected_uplift,
                "confidence": "medium" if balance_ratio > 0.5 else "low",
                "workflows_product1": workflows1,
                "workflows_product2": workflows2,
                "balance_ratio": round(balance_ratio, 2)
            }
        
        # Get Vertex AI justification
        prompt = f"Propose a compelling bundle for products {bundle['products']} based on usage patterns. " \
                 f"Top products have workflow volumes: {sorted_products[:2]}"
        
        llm_response = await call_llm(prompt, model="gemini-2.0-flash")
        bundle["llm_justification"] = llm_response
        
        # Audit logging
        append_entry({
            "agent": "BundleAgent",
            "session": session_id,
            "bundle": bundle,
            "analysis": {
                "total_products_analyzed": len(product_workflows),
                "top_products": sorted_products[:3]
            }
        })
        
        return bundle
    
    except ValueError as e:
        append_entry({
            "agent": "BundleAgent",
            "session": session_id,
            "error": str(e),
            "error_type": "ValueError"
        })
        raise
    
    except Exception as e:
        append_entry({
            "agent": "BundleAgent",
            "session": session_id,
            "error": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__
        })
        raise
