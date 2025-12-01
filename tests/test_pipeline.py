"""
Comprehensive Test Suite for Ask-Scrooge
Tests core pipeline, agents, and integration points.
"""
import pytest
import json
import os
from pathlib import Path

# Core services
from core.session_service import InMemorySessionService
from core.memory_bank import MemoryBank
from core.audit_ledger import append_entry, read_ledger, query_ledger, get_stats
from core.llm_client import call_llm, validate_llm_config

# Agents
from agents.data_agent import run as data_run
from agents.cost_agent import run as cost_run, get_model_pricing
from agents.bundle_agent import run as bundle_run
from agents.pricing_agent import run as pricing_run, calculate_bill
from agents.compliance_agent import run as compliance_run, get_supported_regions


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def session_service():
    """Create fresh session service for each test."""
    return InMemorySessionService()


@pytest.fixture
def memory_bank():
    """Create fresh memory bank for each test."""
    return MemoryBank()


@pytest.fixture
def test_session(session_service):
    """Create test session."""
    return session_service.create_session()


@pytest.fixture
def sample_usage_data():
    """Sample usage data for testing."""
    return [
        {"customer_id": "test_001", "region": "US", "product": "CRM", 
         "workflows": 100, "avg_tokens_in": 2000, "avg_tokens_out": 400, "month": "2025-11"},
        {"customer_id": "test_002", "region": "EU", "product": "Analytics", 
         "workflows": 50, "avg_tokens_in": 3000, "avg_tokens_out": 600, "month": "2025-11"}
    ]


@pytest.fixture
def sample_usage_file(tmp_path, sample_usage_data):
    """Create temporary usage data file."""
    file_path = tmp_path / "test_usage.json"
    with open(file_path, 'w') as f:
        json.dump(sample_usage_data, f)
    return str(file_path)


# ============================================
# Core Services Tests
# ============================================

class TestSessionService:
    """Test session management."""
    
    def test_create_session(self, session_service):
        sid = session_service.create_session()
        assert sid is not None
        assert len(sid) == 36  # UUID4 length
    
    def test_append_to_session(self, session_service, test_session):
        session_service.append(test_session, {"test": "data"})
        session_data = session_service.get(test_session)
        assert len(session_data["history"]) == 1
    
    def test_get_nonexistent_session(self, session_service):
        result = session_service.get("nonexistent")
        assert result is None
    
    def test_cleanup_expired(self, session_service):
        sid = session_service.create_session()
        count = session_service.cleanup_expired(ttl_seconds=0)
        assert count >= 1


class TestMemoryBank:
    """Test memory storage."""
    
    def test_store_and_read(self, memory_bank, test_session):
        memory_bank.store(test_session, "key1", "value1")
        result = memory_bank.read(test_session, "key1")
        assert result == ["value1"]
    
    def test_read_latest(self, memory_bank, test_session):
        memory_bank.store(test_session, "key1", "value1")
        memory_bank.store(test_session, "key1", "value2")
        result = memory_bank.read_latest(test_session, "key1")
        assert result == "value2"
    
    def test_clear_session(self, memory_bank, test_session):
        memory_bank.store(test_session, "key1", "value1")
        assert memory_bank.clear_session(test_session)
        assert not memory_bank.session_exists(test_session)


class TestAuditLedger:
    """Test audit logging."""
    
    def test_append_entry(self, test_session):
        entry = append_entry({"agent": "TestAgent", "session": test_session, "test": True})
        assert "ts" in entry
        assert "iso_timestamp" in entry
    
    def test_read_ledger(self):
        entries = read_ledger()
        assert isinstance(entries, list)
    
    def test_query_ledger(self, test_session):
        append_entry({"agent": "TestAgent", "session": test_session})
        results = query_ledger(agent="TestAgent", session=test_session)
        assert len(results) >= 1
    
    def test_get_stats(self):
        stats = get_stats()
        assert "total_entries" in stats


class TestLLMClient:
    """Test LLM wrapper."""
    
    def test_call_llm_fallback(self):
        result = call_llm("test prompt", use_gemini=False)
        assert "text" in result
        assert "tokens" in result
        assert "model" in result
    
    def test_validate_config(self):
        config = validate_llm_config()
        assert "mode" in config
        assert "ready" in config


# ============================================
# Agent Tests
# ============================================

class TestDataAgent:
    """Test data aggregation agent."""
    
    def test_run_with_file(self, test_session, sample_usage_file):
        result = data_run(test_session, path=sample_usage_file)
        assert len(result) == 2
        assert all("region" in r for r in result)
        assert all("product" in r for r in result)
    
    def test_aggregation_logic(self, test_session, sample_usage_file):
        result = data_run(test_session, path=sample_usage_file)
        # Check that workflows are summed
        for row in result:
            assert row["workflows"] > 0
            assert row["tokens_in"] > 0
            assert row["tokens_out"] > 0
    
    def test_missing_file(self, test_session):
        with pytest.raises(FileNotFoundError):
            data_run(test_session, path="nonexistent.json")


class TestCostAgent:
    """Test cost calculation agent."""
    
    def test_run_basic(self, test_session):
        sample_rows = [
            {"region": "US", "product": "CRM", "workflows": 100, "tokens_in": 10000, "tokens_out": 2000}
        ]
        result = cost_run(sample_rows, session_id=test_session)
        assert len(result) > 0
        assert all("cost" in r for r in result)
    
    def test_multiple_models(self, test_session):
        sample_rows = [
            {"region": "US", "product": "CRM", "workflows": 100, "tokens_in": 10000, "tokens_out": 2000}
        ]
        result = cost_run(sample_rows, session_id=test_session)
        models = set(r["model"] for r in result)
        assert len(models) >= 3  # Multiple models calculated
    
    def test_empty_input(self, test_session):
        with pytest.raises(ValueError):
            cost_run([], session_id=test_session)
    
    def test_get_model_pricing(self):
        pricing = get_model_pricing()
        assert isinstance(pricing, dict)
        assert "gemini-pro" in pricing


class TestBundleAgent:
    """Test bundle recommendation agent."""
    
    def test_run_basic(self, test_session):
        sample_rows = [
            {"region": "US", "product": "CRM", "workflows": 100},
            {"region": "EU", "product": "Analytics", "workflows": 50}
        ]
        result = bundle_run(sample_rows, test_session)
        assert "bundle_name" in result
        assert "expected_uplift_pct" in result
    
    def test_single_product(self, test_session):
        sample_rows = [
            {"region": "US", "product": "CRM", "workflows": 100}
        ]
        result = bundle_run(sample_rows, test_session)
        assert "Premium" in result["bundle_name"]
    
    def test_empty_input(self, test_session):
        with pytest.raises(ValueError):
            bundle_run([], test_session)


class TestPricingAgent:
    """Test pricing recommendation agent."""
    
    def test_run_basic(self, test_session):
        sample_costs = [
            {"region": "US", "product": "CRM", "model": "gemini-pro", "cost": 10.5}
        ]
        sample_bundle = {"bundle_name": "CRM+Analytics", "expected_uplift_pct": 5}
        
        result = pricing_run(sample_costs, sample_bundle, test_session)
        assert "base_fee" in result
        assert "per_workflow" in result
        assert "per_1k_tokens" in result
        assert result["base_fee"] > 0
    
    def test_calculate_bill(self):
        recommendation = {
            "base_fee": 100.0,
            "per_workflow": 0.10,
            "per_1k_tokens": 0.005
        }
        bill = calculate_bill(recommendation, workflows=100, tokens_in=50000, tokens_out=10000)
        assert bill["base_fee"] == 100.0
        assert bill["subtotal"] > 100.0
    
    def test_empty_costs(self, test_session):
        sample_bundle = {"bundle_name": "Test", "expected_uplift_pct": 5}
        with pytest.raises(ValueError):
            pricing_run([], sample_bundle, test_session)


class TestComplianceAgent:
    """Test compliance validation agent."""
    
    def test_get_supported_regions(self):
        regions = get_supported_regions()
        assert isinstance(regions, list)
        assert "US" in regions
        assert "EU" in regions
    
    def test_run_requires_tax_api(self, test_session):
        # This test will fail if tax API not running - that's expected
        recommendation = {"base_fee": 100.0, "currency": "USD"}
        # We expect this to fail gracefully
        result = compliance_run(recommendation, "US", session_id=test_session)
        assert "compliance_status" in result


# ============================================
# Integration Tests
# ============================================

class TestPipelineIntegration:
    """Test full pipeline integration."""
    
    def test_full_pipeline(self, test_session, sample_usage_file):
        """Test complete pipeline flow."""
        # Step 1: Data Agent
        rows = data_run(test_session, path=sample_usage_file)
        assert len(rows) > 0
        
        # Step 2: Cost Agent
        costs = cost_run(rows, session_id=test_session)
        assert len(costs) > 0
        
        # Step 3: Bundle Agent
        bundle = bundle_run(rows, test_session)
        assert "bundle_name" in bundle
        
        # Step 4: Pricing Agent
        recommendation = pricing_run(costs, bundle, test_session)
        assert recommendation["base_fee"] > 0
        
        # Verify audit trail was created
        ledger_entries = query_ledger(session=test_session)
        agents = set(e.get("agent") for e in ledger_entries)
        assert "DataAgent" in agents
        assert "CostAgent" in agents
        assert "BundleAgent" in agents
        assert "PricingAgent" in agents


# ============================================
# Data Validation Tests
# ============================================

class TestDataValidation:
    """Test input data validation."""
    
    def test_usage_data_schema(self, sample_usage_data):
        """Validate usage data has required fields."""
        required_fields = ["customer_id", "region", "product", "workflows", 
                          "avg_tokens_in", "avg_tokens_out", "month"]
        for record in sample_usage_data:
            for field in required_fields:
                assert field in record
    
    def test_positive_values(self, sample_usage_data):
        """Validate numeric fields are positive."""
        for record in sample_usage_data:
            assert record["workflows"] >= 0
            assert record["avg_tokens_in"] >= 0
            assert record["avg_tokens_out"] >= 0


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
