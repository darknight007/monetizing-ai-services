# Google ADK Migration Strategy for Ask-Scrooge
**Status**: Comprehensive Plan for Google ADK Integration  
**Date**: December 1, 2025  
**Scope**: Full migration while preserving existing functionality  
**Objective**: Replace all misrepresentations with authentic Google ADK components

---

## Executive Summary

**Current State**: Custom agent framework claiming MCP/ADK but using only in-memory implementations  
**Target State**: Full Google ADK stack with Vertex AI, real MCP, Agent-to-Agent protocol  
**Timeline**: 6-8 hours for complete integration  
**Risk**: Low (backward-compatible wrappers preserve existing API)

---

## What's Actually Implemented vs. What's Needed

### Truth Table: Current vs. Required

| Component | Current | Google ADK | Status |
|-----------|---------|-----------|--------|
| **Agent Framework** | Custom orchestration | `google.ai.agent` (ADK) | ❌ Missing |
| **LLM Integration** | Direct API calls + retry logic | `Vertex AI SDK` | ❌ Fake |
| **Multi-agent** | Sequential execution | ADK parallel/sequential/loop agents | ⚠️ Partial |
| **Sessions** | In-memory dict | ADK SessionService | ❌ Misrepresented |
| **Memory** | MemoryBank KV store | ADK Memory Bank + context compaction | ⚠️ Partial |
| **Tools** | Custom OpenAPI mock | Real MCP + built-in tools | ❌ Fake MCP claim |
| **Tool Protocol** | FastAPI endpoints | Model Context Protocol (MCP) server | ❌ Not MCP |
| **Observability** | GCP logging + JSONL | Vertex AI tracing + ADK metrics | ⚠️ Partial |
| **Agent-to-Agent** | None | A2A Protocol | ❌ Missing |
| **Agent Evaluation** | Manual testing | ADK Agent Evaluation Framework | ❌ Missing |
| **Long-Running** | No pause/resume | ADK LongRunningOperations | ❌ Missing |
| **Vertex AI** | None | Full Vertex AI integration | ❌ Missing |

---

## Google ADK: The 5+ Key Concepts You Need

### 1. Multi-Agent System ✅ Partially (will enhance)
**What You Have**: Sequential agent pipeline  
**What You Need**: ADK agent framework with parallel/sequential/loop execution

**Current**: `ui/app.py` manually orchestrates agents  
**Target**: Use `google.ai.agent.Agent` class with ADK orchestration

### 2. Tools Integration ❌ Misrepresented (will fix)
**What You Have Claimed**: "MCP custom tools"  
**What You Actually Have**: Custom FastAPI endpoints  
**What You Need**: Real MCP (Model Context Protocol) server

**Current**: `tools/openapi_tax_mock.py` (FastAPI, not MCP)  
**Target**: Real MCP server implementing protocol

### 3. Sessions & Memory ⚠️ Partially misrepresented (will fix)
**What You Have Claimed**: "MCP-style custom tool"  
**What You Actually Have**: Plain Python dict  
**What You Need**: ADK SessionService + proper Memory Bank

**Current**: `core/session_service.py` (in-memory dict)  
**Target**: Proper ADK SessionService with state persistence

### 4. Observability: Logging, Tracing, Metrics ⚠️ Partial (will enhance)
**What You Have**: Custom GCP logging + audit ledger  
**What You Need**: Vertex AI Cloud Trace + ADK instrumentation

**Current**: `core/gcp_logging.py` (custom implementation)  
**Target**: Vertex AI built-in tracing integration

### 5. Agent Evaluation ❌ Missing (will add)
**What You Have**: Manual pytest tests  
**What You Need**: ADK Agent Evaluation Framework

**Current**: `tests/test_pipeline.py` (standard unit tests)  
**Target**: ADK agent evaluation with metrics

### BONUS: A2A Protocol ❌ Missing (will add)
**What You Have**: None  
**What You Need**: Agent-to-Agent communication protocol

---

## Implementation Plan

### Phase 1: Replace LLM Client with Vertex AI (2 hours)

**Current File**: `core/llm_client.py`

**Changes**:
```python
# FROM:
from anthropic import Anthropic
import openai

# TO:
from vertexai.generative_models import GenerativeModel
from vertexai import init
```

**New Implementation**:
```python
# core/vertex_ai_client.py (replaces llm_client.py)
import vertexai
from vertexai.generative_models import GenerativeModel, Tool
from google.cloud import aiplatform

class VertexAIClient:
    def __init__(self, project_id: str, location: str = "us-central1"):
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-2.0-flash-exp")
        self.client = aiplatform.gapic.TrainingServiceClient()
    
    async def call_llm(self, prompt: str, tools: List[Tool] = None) -> str:
        """Call Vertex AI Gemini with proper tool binding"""
        response = await self.model.generate_content_async(
            prompt,
            tools=tools if tools else [],
            safety_settings=self.safety_settings
        )
        return response.text
```

**What This Fixes**:
- ✅ Real Vertex AI integration (not mock)
- ✅ Proper tool binding for MCP tools
- ✅ Vertex AI tracing support
- ✅ Gemini 2.0 latest model

---

### Phase 2: Implement Real MCP Server (2 hours)

**Current File**: `tools/openapi_tax_mock.py` (NOT actually MCP)

**New Files**:
```
tools/
├── mcp_server.py          # Real MCP server
├── mcp_tools.py           # MCP tool definitions
└── openapi_tax_mock.py    # Keep as backup/reference
```

**New MCP Implementation**:
```python
# tools/mcp_server.py
from mcp.server import Server
from mcp.types import Tool, ToolResult
import asyncio
import json

class AskScroougeMCPServer(Server):
    def __init__(self):
        super().__init__("ask-scrooge-mcp")
        self.register_tool(self.tax_calculator_tool)
        self.register_tool(self.cost_analyzer_tool)
        self.register_tool(self.bundle_recommender_tool)
    
    async def tax_calculator_tool(self, amount: float, region: str) -> ToolResult:
        """MCP tool: Calculate regional tax"""
        tax_rates = {
            "US": 0.08,
            "EU": 0.21,
            "APAC": 0.10
        }
        tax_rate = tax_rates.get(region, 0.10)
        tax = amount * tax_rate
        return ToolResult(
            content=json.dumps({
                "amount": amount,
                "region": region,
                "tax_rate": tax_rate,
                "tax": tax,
                "total": amount + tax
            })
        )
    
    async def cost_analyzer_tool(self, tokens: int, model: str) -> ToolResult:
        """MCP tool: Analyze costs across models"""
        costs = {
            "gemini-2.0-flash": 0.025,
            "gpt-4o": 0.03,
            "claude-3-opus": 0.015
        }
        rate = costs.get(model, 0.025)
        token_cost = (tokens / 1000) * rate
        return ToolResult(
            content=json.dumps({
                "tokens": tokens,
                "model": model,
                "rate_per_1k": rate,
                "total_cost": token_cost
            })
        )
    
    async def bundle_recommender_tool(self, products: List[str]) -> ToolResult:
        """MCP tool: Recommend product bundles"""
        # Bundle logic here
        return ToolResult(content=json.dumps({...}))
```

**What This Fixes**:
- ✅ Real MCP server (not fake)
- ✅ Proper tool protocol
- ✅ Tool calling from Vertex AI
- ✅ Standard MCP compatibility

---

### Phase 3: Integrate Google ADK for Agent Orchestration (2 hours)

**New File**: `agents/adk_orchestrator.py`

**Implementation**:
```python
# agents/adk_orchestrator.py
from google.ai.agent import Agent, AgentRunner
from google.ai.agent.session import SessionService
from google.ai.agent.memory import MemoryBank
from typing import List, Dict, Any

class AskSchroogeADKAgent(Agent):
    """ADK-based agent for Ask-Scrooge pipeline"""
    
    def __init__(self, name: str, description: str, tools: List[str]):
        super().__init__(name=name, description=description)
        self.tools = tools
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent with ADK framework"""
        # ADK handles retry, rate limiting, tracing
        result = await self.execute(input_data)
        return result

class ADKPipeline:
    """ADK orchestrator for multi-agent pipeline"""
    
    def __init__(self, project_id: str):
        self.runner = AgentRunner(project_id=project_id)
        self.session_service = SessionService()
        self.memory = MemoryBank()
        
        # Create agents
        self.data_agent = AskSchroogeADKAgent(
            name="DataAgent",
            description="Aggregates usage data",
            tools=[]
        )
        self.cost_agent = AskSchroogeADKAgent(
            name="CostAgent",
            description="Computes costs",
            tools=["cost_analyzer"]
        )
        # ... more agents
    
    async def run_pipeline(self, session_id: str, data: Dict) -> Dict:
        """Run full pipeline with ADK orchestration"""
        session = self.session_service.create_session(session_id)
        
        # ADK handles parallel execution automatically
        results = await self.runner.run_agents_parallel(
            agents=[self.data_agent, self.cost_agent],
            input=data,
            session=session
        )
        
        return results
```

**What This Fixes**:
- ✅ Real ADK agent framework
- ✅ ADK SessionService (not fake)
- ✅ ADK MemoryBank (not fake)
- ✅ Built-in parallel/sequential execution
- ✅ Built-in tracing and metrics

---

### Phase 4: Implement Agent Evaluation Framework (1 hour)

**New File**: `evaluation/agent_evaluator.py`

```python
# evaluation/agent_evaluator.py
from google.ai.agent.evaluation import AgentEvaluator, Metric
from typing import Dict, Any, List

class AskSchroogeEvaluator(AgentEvaluator):
    """ADK agent evaluation framework"""
    
    def __init__(self):
        super().__init__()
        self.register_metric("cost_accuracy", self.cost_accuracy_metric)
        self.register_metric("pricing_deviation", self.pricing_deviation_metric)
        self.register_metric("response_time", self.response_time_metric)
    
    async def cost_accuracy_metric(self, result: Dict, expected: Dict) -> float:
        """Evaluate cost calculation accuracy"""
        actual_cost = result.get("cost", 0)
        expected_cost = expected.get("cost", 0)
        deviation = abs(actual_cost - expected_cost) / expected_cost
        return 1.0 - min(deviation, 1.0)
    
    async def pricing_deviation_metric(self, result: Dict, expected: Dict) -> float:
        """Evaluate pricing accuracy"""
        actual_price = result.get("pricing", {}).get("total", 0)
        expected_price = expected.get("pricing", {}).get("total", 0)
        if expected_price == 0:
            return 1.0
        deviation = abs(actual_price - expected_price) / expected_price
        return 1.0 - min(deviation, 1.0)
    
    async def response_time_metric(self, result: Dict, expected: Dict) -> float:
        """Evaluate response time"""
        actual_time = result.get("duration_ms", 0)
        expected_time = expected.get("duration_ms", 5000)
        if actual_time <= expected_time:
            return 1.0
        return max(0, 1.0 - (actual_time - expected_time) / expected_time)
```

**What This Fixes**:
- ✅ Real agent evaluation framework
- ✅ Quantitative metrics
- ✅ Traceability and comparison

---

### Phase 5: Implement Agent-to-Agent (A2A) Protocol (1 hour)

**New File**: `agents/a2a_protocol.py`

```python
# agents/a2a_protocol.py
from google.ai.agent.a2a import A2AProtocol, AgentMessage
from typing import Dict, Any

class AskSchroogeA2AProtocol(A2AProtocol):
    """Agent-to-Agent communication protocol"""
    
    async def send_message(
        self, 
        from_agent: str, 
        to_agent: str, 
        message_type: str, 
        data: Dict[str, Any]
    ) -> AgentMessage:
        """Send message between agents"""
        
        # Example: DataAgent sends aggregated data to CostAgent
        if from_agent == "DataAgent" and to_agent == "CostAgent":
            return AgentMessage(
                sender="DataAgent",
                recipient="CostAgent",
                message_type="data_ready",
                payload=data,
                priority="high"
            )
        
        # Example: CostAgent sends costs to PricingAgent
        if from_agent == "CostAgent" and to_agent == "PricingAgent":
            return AgentMessage(
                sender="CostAgent",
                recipient="PricingAgent",
                message_type="costs_computed",
                payload=data,
                priority="high"
            )

# Usage in agents:
# In CostAgent:
a2a = AskSchroogeA2AProtocol()
await a2a.send_message("CostAgent", "PricingAgent", "costs_computed", costs)
```

**What This Fixes**:
- ✅ Real A2A protocol
- ✅ Inter-agent communication
- ✅ Message routing and priority

---

### Phase 6: Update requirements.txt (30 min)

**Current**:
```
fastapi>=0.103.0
gradio
requests==2.31.0
python-dotenv==1.0.0
pytest==7.4.0
google-cloud-logging==3.5.0
```

**New**:
```
# Google ADK
google-ai-agent>=0.1.0
vertexai>=0.1.0
google-cloud-aiplatform>=1.35.0

# MCP Protocol
mcp-sdk>=0.1.0

# Existing (kept for compatibility)
fastapi>=0.103.0
gradio
requests==2.31.0
python-dotenv==1.0.0
pytest==7.4.0
google-cloud-logging==3.5.0
```

---

### Phase 7: Update Configuration (30 min)

**New File**: `.env.example`

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_CLOUD_REGION=us-central1

# Vertex AI
VERTEX_AI_MODEL=gemini-2.0-flash-exp
VERTEX_AI_LOCATION=us-central1

# ADK
ADK_AGENT_TIMEOUT=300
ADK_PARALLELISM=4

# MCP Server
MCP_SERVER_PORT=8000
MCP_SERVER_HOST=localhost

# Existing
TAX_API_KEY=your-api-key
TAX_API_URL=http://localhost:9000
```

---

## File Mapping: Before → After

| Before (Fake) | After (Real Google ADK) | Status |
|---------------|------------------------|--------|
| `core/llm_client.py` | `core/vertex_ai_client.py` | Replace |
| `core/session_service.py` | ADK SessionService (wrapped) | Enhance |
| `core/memory_bank.py` | ADK MemoryBank (wrapped) | Enhance |
| `tools/openapi_tax_mock.py` | `tools/mcp_server.py` | Replace |
| Manual orchestration | `agents/adk_orchestrator.py` | New |
| N/A | `evaluation/agent_evaluator.py` | New |
| N/A | `agents/a2a_protocol.py` | New |
| `agents/*.py` | Updated to use ADK agents | Modify |

---

## Backward Compatibility Strategy

### Keep Existing API
All existing code (UI, tests) will continue working through wrapper classes:

```python
# core/compatibility.py
class SessionServiceAdapter:
    """Adapter to keep existing API working with ADK"""
    
    def __init__(self, adk_service):
        self._adk_service = adk_service
    
    def create_session(self) -> str:
        """Existing API - delegates to ADK"""
        return self._adk_service.create_session().id
    
    def get_session(self, session_id: str):
        """Existing API - delegates to ADK"""
        return self._adk_service.get_session(session_id)
```

### Update UI Gradually
No immediate UI changes needed - agents still return same JSON structure.

### Tests Pass as-is
Existing tests continue to work with ADK implementation.

---

## Implementation Checklist

### Step 1: Vertex AI Client (2 hours)
- [ ] Create `core/vertex_ai_client.py`
- [ ] Replace all imports of `core.llm_client`
- [ ] Update agents to use new client
- [ ] Test with Vertex AI credentials
- [ ] Verify Gemini 2.0 calls work
- [ ] Update `.env.example`

### Step 2: MCP Server (2 hours)
- [ ] Create `tools/mcp_server.py`
- [ ] Implement 3+ MCP tools
- [ ] Create `tools/mcp_tools.py`
- [ ] Update compliance agent to use MCP client
- [ ] Test tool calling from Vertex AI
- [ ] Document MCP server API

### Step 3: ADK Integration (2 hours)
- [ ] Create `agents/adk_orchestrator.py`
- [ ] Create `agents/adk_*.py` for each agent
- [ ] Update `ui/app.py` to use ADK orchestrator
- [ ] Test pipeline with ADK
- [ ] Verify parallel execution works
- [ ] Update README for ADK

### Step 4: Agent Evaluation (1 hour)
- [ ] Create `evaluation/agent_evaluator.py`
- [ ] Add 3+ evaluation metrics
- [ ] Create evaluation tests
- [ ] Document evaluation framework
- [ ] Add evaluation to CI/CD

### Step 5: A2A Protocol (1 hour)
- [ ] Create `agents/a2a_protocol.py`
- [ ] Implement inter-agent messaging
- [ ] Update agent communication
- [ ] Test message routing
- [ ] Document A2A usage

### Step 6: Configuration & Dependencies (1 hour)
- [ ] Update `requirements.txt`
- [ ] Update `.env.example`
- [ ] Update `Dockerfile`
- [ ] Update deployment guides
- [ ] Test Docker build

### Step 7: Documentation (1 hour)
- [ ] Replace misrepresentations in all docs
- [ ] Add Google ADK section to README
- [ ] Document MCP protocol
- [ ] Document agent evaluation
- [ ] Add architecture diagram with ADK

### Step 8: Testing (1 hour)
- [ ] Run all existing tests
- [ ] Add ADK-specific tests
- [ ] Test end-to-end pipeline
- [ ] Performance testing
- [ ] Stress testing with parallel agents

---

## Total Effort Summary

| Phase | Component | Hours | Status |
|-------|-----------|-------|--------|
| 1 | Vertex AI Client | 2 | Planned |
| 2 | MCP Server | 2 | Planned |
| 3 | ADK Orchestration | 2 | Planned |
| 4 | Agent Evaluation | 1 | Planned |
| 5 | A2A Protocol | 1 | Planned |
| 6 | Config & Dependencies | 1 | Planned |
| 7 | Documentation | 1 | Planned |
| 8 | Testing & Validation | 1 | Planned |
| | **TOTAL** | **11 hours** | |

**Buffer**: 2 hours (troubleshooting, integration issues)  
**Total with buffer**: ~12-13 hours  
**Realistic**: 8-10 hours (most items in parallel)

---

## Risk Mitigation

### Potential Issues

1. **Google ADK availability** (Low risk)
   - Mitigation: Use latest version, fallback to SDK docs

2. **Vertex AI credentials** (Medium risk)
   - Mitigation: Test with service account early
   - Fallback: Keep mock implementations available

3. **MCP protocol complexity** (Low risk)
   - Mitigation: Use Python SDK, plenty of examples
   - Fallback: OpenAPI wrapper if needed

4. **Breaking existing code** (Low risk - planned)
   - Mitigation: Adapter pattern for backward compat
   - Tests verify existing API still works

---

## Success Criteria

After migration, you will have:

✅ **Real Google ADK**: Not claims, actual `google.ai.agent` usage  
✅ **Real Vertex AI**: Gemini 2.0 with proper integration  
✅ **Real MCP**: Model Context Protocol server, not fake  
✅ **Real SessionService**: ADK SessionService, not in-memory dict  
✅ **Real MemoryBank**: ADK MemoryBank with context compaction  
✅ **Real Tool Protocol**: MCP tools properly bound  
✅ **Real Agent Evaluation**: ADK evaluation framework with metrics  
✅ **Real A2A Protocol**: Agent-to-Agent communication  
✅ **Real Observability**: Vertex AI tracing + ADK metrics  
✅ **All 5+ Key Concepts Covered**: Per Google ADK requirements

---

## Commands to Execute (After Migration)

```bash
# 1. Update dependencies
pip install -r requirements.txt

# 2. Set Google Cloud credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
export GOOGLE_CLOUD_PROJECT_ID=your-project-id

# 3. Run with ADK
python ui/app.py  # Now uses ADK orchestrator

# 4. Test evaluation framework
python -m pytest evaluation/test_evaluator.py -v

# 5. Deploy to Vertex AI
gcloud ai agent deploy ask-scrooge --region=us-central1
```

---

## Next Actions

1. **Get credentials**: Ensure you have Google Cloud service account with:
   - Vertex AI API enabled
   - Cloud Trace enabled
   - Cloud Logging enabled
   - AIplatform permissions

2. **Install ADK**: `pip install google-ai-agent vertexai`

3. **Start Phase 1**: Migrate LLM client to Vertex AI

4. **Test incrementally**: Each phase tested before moving to next

---

**This plan transforms Ask-Scrooge from a functional but misrepresented system into a genuine Google ADK showcase.**

Ready to begin Phase 1?
