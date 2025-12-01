# Google ADK: Assessment & Decision Document

**Date**: December 1, 2025  
**Prepared for**: Engineering Team  
**Decision Authority**: CTO  
**Status**: Decision Made - Phase 1 Implementation Only

---

## Executive Summary

You correctly identified that we don't have real Google ADK or Vertex AI integration yet. We have:
- ❌ No actual Google ADK components
- ❌ No Vertex AI API calls (using fallback logic)
- ⚠️  Misleading documentation claiming "MCP representation" via InMemorySessionService

**CTO Decision**: 
- ✅ Implement Vertex AI integration (HIGH VALUE - 2-3 hours)
- ⏸️  Skip MCP, A2A, long-running ops, advanced evaluation (NO VALUE - skip entirely)
- ❌ No checkbox compliance; only real business value

---

## The Problem You Identified

You asked: "Why is session_service.py a MCP representation?"

**Answer**: It's not. That was an error in our documentation.
- InMemorySessionService is just session management
- MCP is a protocol for tool discovery and execution
- These are different things
- Our current approach works fine without MCP

---

## What We Actually Need

### Google ADK Components Worth Using

#### 1. **Vertex AI Generative Models** ✅
**What**: Real Google Cloud Vertex AI SDK for LLM calls  
**Why**: 
- Better models available (Gemini 2.0 Flash)
- Unified interface (no manual retry logic)
- Built-in cost tracking
- Production-grade infrastructure

**Current state**: Using mock/fallback logic  
**What we need**: Real Vertex AI client  
**Effort**: 2-3 hours  
**Value**: HIGH  
**Decision**: IMPLEMENT IMMEDIATELY

#### 2. **MCP Protocol** ⏸️ (Optional)
**What**: Standardized tool discovery and execution  
**Why**: Useful if adding many tools  
**Current state**: Single tax API via requests.post()  
**What we need**: MCP server wrapping tools  
**Effort**: 3-4 hours  
**Value**: MEDIUM (only if planning 2+ new tools)  
**Decision**: DEFER - implement only if needed

---

### Google ADK Components We Don't Need

#### ❌ A2A Protocol (Agent-to-Agent)
- **Why skip**: We have one orchestrator, no cross-agent communication
- **Benefit**: None for our design
- **When to revisit**: If agents need to communicate with each other

#### ❌ Long-running Operations
- **Why skip**: Pipeline completes in 5-10 seconds
- **Benefit**: None (pause/resume not needed)
- **When to revisit**: If supporting 30+ minute jobs

#### ❌ ADK Agent Framework
- **Why skip**: Our sequential + parallel orchestration is clear and efficient
- **Benefit**: None (unnecessary abstraction layer)
- **When to revisit**: If agents need built-in state machines

#### ❌ Advanced Tracing
- **Why skip**: Audit ledger is superior to generic tracing
- **Benefit**: None (we have better alternative)
- **When to revisit**: Never (our approach is better)

#### ❌ Session Persistence
- **Why skip**: In-memory sessions sufficient for MVP
- **Benefit**: None for current scope
- **When to revisit**: If sessions need to survive service restarts

#### ❌ Agent Evaluation Framework
- **Why skip**: verify_numerics.py validates business logic perfectly
- **Benefit**: None (different purpose than generic evaluation)
- **When to revisit**: If evaluating model performance (not our goal)

---

## Implementation Plan

### Phase 1: Vertex AI Integration (DO THIS)
**Timeline**: 2-3 hours  
**Value**: HIGH  

**Files to create/modify**:
1. `core/vertex_ai_client.py` - NEW
   - Real Vertex AI SDK
   - Gemini 2.0 Flash support
   - Cost tracking
   - Async interface
   - Fallback to mock if no credentials

2. `agents/bundle_agent.py` - MODIFY
   - Change import: `from core.llm_client` → `from core.vertex_ai_client`
   - Make LLM call async
   - No business logic changes

3. `agents/pricing_agent.py` - MODIFY
   - Change import: `from core.llm_client` → `from core.vertex_ai_client`
   - Make LLM call async
   - No business logic changes

4. `requirements.txt` - ADD
   - `google-cloud-aiplatform>=1.35.0`
   - `vertexai>=0.30.0`

**Testing**:
- `bash run.sh` still works
- `python verify_numerics.py` still passes
- Agents get Vertex AI responses (not mock)

---

### Phase 2: MCP Server (OPTIONAL - DO ONLY IF NEEDED)
**Timeline**: 3-4 hours  
**Value**: MEDIUM  
**When**: Only if adding 2+ more tools

**Implementation**:
- Create `tools/mcp_server.py`
- Wrap tax validation API as MCP tool
- Agents call tools through MCP discovery

**Decision**: DEFER indefinitely until we need it

---

### Phase 3+: Everything Else (SKIP)
**Value**: ZERO  
**Effort**: 20+ hours of wasted engineering time  

Don't implement:
- A2A Protocol
- Long-running operations
- ADK Agent Framework
- Complex evaluation framework
- Session persistence
- Advanced tracing

---

## Why This Approach

**Principle**: "Google ADK should solve real problems in our project."

### Real Problem 1: Limited LLM Access
- **Current**: Fallback logic, hardcoded models
- **Solution**: Vertex AI provides unified interface
- **Benefit**: Better models, simpler code
- **Decision**: Implement

### Real Problem 2: Tool Scalability (Future)
- **Current**: Single tax API hardcoded
- **Solution**: MCP protocol for discovery
- **Benefit**: Scale to multiple tools
- **Decision**: Defer until needed

### Fake Problem 1: Agent Communication
- **Current**: Not needed (single orchestrator)
- **Proposal**: Add A2A Protocol
- **Benefit**: None (we don't have this use case)
- **Decision**: Skip

### Fake Problem 2: Execution Tracing
- **Current**: Audit ledger is perfect
- **Proposal**: Add Vertex AI tracing
- **Benefit**: None (our approach is better)
- **Decision**: Skip

### Fake Problem 3: Long-running Jobs
- **Current**: 5-10 second pipeline
- **Proposal**: Add pause/resume capability
- **Benefit**: None (not needed)
- **Decision**: Skip

---

## Success Criteria

### Phase 1 Success
✅ Real Vertex AI models used (not mocks)  
✅ Gemini 2.0 Flash available  
✅ Cost agent gets real pricing from Vertex AI  
✅ Retry logic handled by SDK  
✅ Business output unchanged  
✅ All tests pass  
✅ `bash run.sh` works  
✅ `docker-compose up` works  

### Not Measured
❌ Checkbox compliance with "Google ADK requirements"  
❌ Number of ADK components used  
❌ Matching external standards  

---

## Timeline

| Phase | Component | Timeline | Value | Status |
|-------|-----------|----------|-------|--------|
| 1 | Vertex AI | 2-3 hrs | HIGH | → DO IMMEDIATELY |
| 2 | MCP Server | 3-4 hrs | MEDIUM | ⏸️  DEFER |
| 3+ | A2A, etc | 20+ hrs | ZERO | ❌ SKIP |

---

## What We Keep (Unchanged)

✅ Multi-agent pipeline (works great)  
✅ Asyncio parallelization (efficient)  
✅ Audit ledger (superior to tracing)  
✅ GCP Cloud Logging (production-grade)  
✅ In-memory sessions (sufficient)  
✅ Current orchestration (clear and testable)  

---

## What We Add

✅ Vertex AI client (real LLM access)  
✅ Gemini 2.0 Flash support (better model)  
✅ Cost tracking via Vertex AI (built-in)  

---

## What We Skip

❌ A2A Protocol  
❌ Long-running operations  
❌ ADK agent framework  
❌ Advanced tracing  
❌ Complex evaluation  
❌ Session persistence  
❌ MCP (defer for now)  

---

## Engineering Decision

**CTO says**: Implement what solves real problems. Skip what doesn't.

This project doesn't need:
- Agent-to-agent communication → Skip A2A
- Long-running job support → Skip pause/resume
- Execution tracing framework → Audit ledger is better
- Complex session management → In-memory is fine
- Agent evaluation metrics → We evaluate pricing math, not agent performance

This project does need:
- Better LLM models → Implement Vertex AI
- Unified LLM interface → Vertex AI provides it
- Built-in cost tracking → Vertex AI includes it

**Recommendation**: Spend 2-3 hours on Phase 1 (Vertex AI).  
Skip 20+ hours of checkbox compliance.

---

## Conclusion

**Current state**: System works well with custom implementations.  
**What we're adding**: Real Vertex AI integration (where it matters).  
**What we're skipping**: Everything else (where it doesn't matter).  

This is the pragmatic approach: improve what needs improving, skip what doesn't.

---

**Status**: Ready to implement Phase 1  
**Next action**: Create Vertex AI client and update agents  
**Expected completion**: 2-3 hours
