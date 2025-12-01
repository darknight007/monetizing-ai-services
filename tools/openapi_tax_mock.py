"""
OpenAPI Tax Validation Mock Service
Provides tax calculation and compliance validation for demo purposes.

Version 2 enhancements:
- OAuth2/JWT for production authentication
- Rate limiting per API key
- Webhook notifications for compliance changes
"""
from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator
from typing import Optional
import time
import logging
import os


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Key authentication (simple implementation)
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
VALID_API_KEYS = set(os.getenv("TAX_API_KEYS", "demo-key-12345,test-key-67890").split(","))


# FastAPI app
app = FastAPI(
    title="Tax Validation Service",
    description="Mock tax validation API for Ask-Scrooge monetization engine",
    version="1.0.0"
)


# Regional tax rates (simplified for demo)
TAX_RATES = {
    "US": 0.0,      # No federal sales tax (simplified)
    "EU": 0.20,     # Average VAT
    "APAC": 0.10,   # Average GST
    "LATAM": 0.15,  # Average VAT
    "MEA": 0.05     # Average VAT
}


class TaxCheckRequest(BaseModel):
    """Request model for tax validation."""
    region: str = Field(..., description="Geographic region code (US, EU, APAC, etc.)")
    amount: float = Field(..., gt=0, description="Amount to validate (must be positive)")
    currency: Optional[str] = Field("USD", description="Currency code")
    
    @validator('region')
    def validate_region(cls, v):
        """Validate region is supported."""
        if v.upper() not in TAX_RATES:
            raise ValueError(f"Unsupported region: {v}. Supported: {list(TAX_RATES.keys())}")
        return v.upper()
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount is reasonable."""
        if v > 1_000_000:
            raise ValueError("Amount exceeds maximum allowed value")
        return round(v, 2)


class TaxCheckResponse(BaseModel):
    """Response model for tax validation."""
    ok: bool
    region: str
    amount: float
    vat: float
    total_with_tax: float
    currency: str
    tax_rate_pct: float
    timestamp: float


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: float
    version: str


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """
    Verify API key for authentication.
    
    NOTE: Production should use OAuth2/JWT with proper key management.
    SOC2 Compliance: API keys should be rotated regularly and stored securely.
    """
    # Allow access without API key for health check and docs
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header."
        )
    
    if api_key not in VALID_API_KEYS:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return api_key


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(f"Response: {response.status_code} (took {duration:.3f}s)")
    
    return response


@app.get("/", tags=["info"])
async def root():
    """API root endpoint."""
    return {
        "service": "Tax Validation API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["monitoring"])
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        Health status and metadata
    """
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version="1.0.0"
    )


@app.get("/supported-regions", tags=["info"])
async def get_supported_regions():
    """
    Get list of supported regions and their tax rates.
    
    Returns:
        Dict of regions to tax rates
    """
    return {
        "regions": {
            region: {
                "tax_rate": rate,
                "tax_rate_pct": rate * 100
            }
            for region, rate in TAX_RATES.items()
        }
    }


@app.post("/validate_tax", response_model=TaxCheckResponse, tags=["validation"])
async def validate_tax(
    request: TaxCheckRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Validate tax calculation for a region and amount.
    
    **Authentication**: Requires X-API-Key header
    
    Args:
        request: Tax validation request
        api_key: Validated API key (injected by dependency)
        
    Returns:
        Tax calculation result with validation status
        
    Raises:
        HTTPException: If validation fails or authentication error
        
    SOC2 Note: All requests are logged with timestamps for audit trail
    """
    try:
        # Get tax rate for region
        vat_rate = TAX_RATES.get(request.region, 0.0)
        
        # Calculate tax and total
        vat_amount = request.amount * vat_rate
        total_with_tax = request.amount + vat_amount
        
        logger.info(
            f"Tax calculation: region={request.region}, "
            f"amount={request.amount}, vat={vat_amount:.2f}, "
            f"total={total_with_tax:.2f}"
        )
        
        return TaxCheckResponse(
            ok=True,
            region=request.region,
            amount=request.amount,
            vat=round(vat_amount, 2),
            total_with_tax=round(total_with_tax, 2),
            currency=request.currency,
            tax_rate_pct=vat_rate * 100,
            timestamp=time.time()
        )
    
    except Exception as e:
        logger.error(f"Tax validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bulk-validate", tags=["validation"])
async def bulk_validate_tax(
    requests: list[TaxCheckRequest],
    api_key: str = Depends(verify_api_key)
):
    """
    Validate tax for multiple regions/amounts in batch.
    
    **Authentication**: Requires X-API-Key header
    
    Args:
        requests: List of tax validation requests
        api_key: Validated API key (injected by dependency)
        
    Returns:
        List of validation results
    """
    results = []
    
    for req in requests:
        try:
            result = await validate_tax(req)
            results.append(result.dict())
        except Exception as e:
            results.append({
                "ok": False,
                "region": req.region,
                "error": str(e)
            })
    
    return {
        "total_requests": len(requests),
        "successful": sum(1 for r in results if r.get("ok")),
        "failed": sum(1 for r in results if not r.get("ok")),
        "results": results
    }


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {str(exc)}")
    return HTTPException(status_code=400, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="info")
