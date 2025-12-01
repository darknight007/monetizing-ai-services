"""
Compliance Agent
Validates tax and regulatory compliance via external API.

Version 2 enhancements:
- Multi-jurisdiction compliance checks
- Real-time regulatory updates
- Automated compliance report generation
"""
import requests
import os
from typing import Dict, Any
from core.audit_ledger import append_entry


# Configuration
DEFAULT_TAX_API_URL = "http://localhost:9000"
DEFAULT_TIMEOUT = 5  # seconds
DEFAULT_API_KEY = "demo-key-12345"  # Override with env var TAX_API_KEY


def run(
    recommendation: Dict[str, Any],
    region: str,
    session_id: str = None
) -> Dict[str, Any]:
    """
    Validate pricing recommendation against tax/regulatory requirements.
    
    Args:
        recommendation: Pricing recommendation from PricingAgent
        region: Geographic region for compliance check (US, EU, APAC, etc.)
        session_id: Optional session ID for audit trail
        
    Returns:
        Dict with compliance validation result
        
    Raises:
        ValueError: If required data is missing
    """
    try:
        # Validate inputs
        if not recommendation:
            raise ValueError("No pricing recommendation provided")
        
        if not region:
            raise ValueError("Region must be specified for compliance check")
        
        base_fee = recommendation.get("base_fee")
        if base_fee is None:
            raise ValueError("Pricing recommendation missing base_fee")
        
        # Call tax validation API
        result = _call_tax_api(region, base_fee)
        
        # Enhance result with compliance metadata
        result["region"] = region
        result["validated_amount"] = base_fee
        result["currency"] = recommendation.get("currency", "USD")
        result["compliance_status"] = "PASSED" if result.get("ok") else "FAILED"
        
        # Audit logging
        if session_id:
            append_entry({
                "agent": "ComplianceAgent",
                "session": session_id,
                "region": region,
                "api_response": result,
                "status": result["compliance_status"]
            })
        
        return result
    
    except ValueError as e:
        if session_id:
            append_entry({
                "agent": "ComplianceAgent",
                "session": session_id,
                "error": str(e),
                "error_type": "ValueError",
                "region": region
            })
        raise
    
    except Exception as e:
        error_msg = f"Compliance check failed: {str(e)}"
        result = {
            "ok": False,
            "error": error_msg,
            "region": region,
            "compliance_status": "ERROR"
        }
        
        if session_id:
            append_entry({
                "agent": "ComplianceAgent",
                "session": session_id,
                "error": error_msg,
                "error_type": type(e).__name__,
                "region": region
            })
        
        return result


def _call_tax_api(region: str, amount: float) -> Dict[str, Any]:
    """
    Call external tax validation API.
    
    Args:
        region: Geographic region
        amount: Amount to validate
        
    Returns:
        API response dict
        
    Raises:
        requests.RequestException: If API call fails
    """
    url = f"{DEFAULT_TAX_API_URL}/validate_tax"
    
    payload = {
        "region": region,
        "amount": amount
    }
    
    # Get API key from environment or use default
    api_key = os.getenv("TAX_API_KEY", DEFAULT_API_KEY)
    
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=DEFAULT_TIMEOUT,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": api_key
            }
        )
        
        response.raise_for_status()
        return response.json()
    
    except requests.Timeout:
        raise Exception(f"Tax API timeout after {DEFAULT_TIMEOUT}s")
    
    except requests.ConnectionError:
        raise Exception(f"Cannot connect to tax API at {url}")
    
    except requests.HTTPError as e:
        raise Exception(f"Tax API HTTP error: {e.response.status_code}")
    
    except Exception as e:
        raise Exception(f"Tax API call failed: {str(e)}")


def validate_multiple_regions(
    recommendation: Dict[str, Any],
    regions: list,
    session_id: str = None
) -> Dict[str, Dict[str, Any]]:
    """
    Validate pricing across multiple regions.
    
    Args:
        recommendation: Pricing recommendation
        regions: List of region codes
        session_id: Optional session ID for audit trail
        
    Returns:
        Dict mapping region to validation result
    """
    results = {}
    
    for region in regions:
        try:
            result = run(recommendation, region, session_id)
            results[region] = result
        except Exception as e:
            results[region] = {
                "ok": False,
                "error": str(e),
                "region": region,
                "compliance_status": "ERROR"
            }
    
    # Aggregate audit entry
    if session_id:
        all_passed = all(r.get("compliance_status") == "PASSED" for r in results.values())
        append_entry({
            "agent": "ComplianceAgent",
            "session": session_id,
            "operation": "multi_region_validation",
            "regions": regions,
            "all_passed": all_passed,
            "results_summary": {
                region: r.get("compliance_status")
                for region, r in results.items()
            }
        })
    
    return results


def get_supported_regions() -> list:
    """
    Get list of supported regions.
    
    Returns:
        List of region codes
    """
    return ["US", "EU", "APAC", "LATAM", "MEA"]
