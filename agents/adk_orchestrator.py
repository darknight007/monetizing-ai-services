"""
Google ADK Agent Orchestrator - Replaces manual orchestration
Uses real google.ai.agent framework for multi-agent coordination
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

try:
    from google.ai import agent as adk_agent
    from google.ai.agent import Agent, AgentRunner
    from google.ai.agent.session import SessionService
    from google.ai.agent.memory import MemoryBank
    HAS_ADK = True
except ImportError:
    HAS_ADK = False
    # Fallback classes for graceful degradation
    class Agent:
        pass
    class AgentRunner:
        pass
    class SessionService:
        pass
    class MemoryBank:
        pass

from core.vertex_ai_client import VertexAIClient
from core.audit_ledger import append_entry


logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for an ADK agent"""
    name: str
    description: str
    model: str = "gemini-2.0-flash-exp"
    temperature: float = 0.7
    max_tokens: int = 2048
    tools: List[str] = field(default_factory=list)
    timeout: int = 300


class AskSchroogeAgent(Agent if HAS_ADK else object):
    """
    Ask-Scrooge agent powered by Google ADK.
    Represents a specialized agent in the monetization pipeline.
    """

    def __init__(self, config: AgentConfig, llm_client: VertexAIClient):
        """
        Initialize an ADK agent.

        Args:
            config: Agent configuration
            llm_client: Vertex AI client for LLM calls
        """
        self.config = config
        self.llm_client = llm_client
        self.execution_history: List[Dict[str, Any]] = []
        self.metrics = {
            "calls": 0,
            "errors": 0,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "total_duration_ms": 0,
        }

        if HAS_ADK:
            super().__init__(
                name=config.name,
                description=config.description,
                model=config.model,
            )

        logger.info(f"Initialized ADK agent: {config.name}")

    async def execute(
        self,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the agent with given input.

        Args:
            input_data: Input data for the agent
            session_id: Session ID for tracking
            context: Additional context from previous agents

        Returns:
            Agent output and metadata
        """
        start_time = datetime.now()
        execution_id = f"{self.config.name}_{int(start_time.timestamp())}"

        try:
            logger.info(
                f"[{session_id}] Executing {self.config.name} with input: {list(input_data.keys())}"
            )

            # Call LLM with agent-specific prompt
            prompt = self._build_prompt(input_data, context)
            response = await self.llm_client.call_llm(
                prompt=prompt,
                system_prompt=self._get_system_prompt(),
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                session_id=session_id,
            )

            # Parse and structure response
            result = self._parse_response(response, input_data)

            # Track metrics
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics["calls"] += 1
            self.metrics["total_tokens_in"] += response["usage"]["prompt_tokens"]
            self.metrics["total_tokens_out"] += response["usage"]["completion_tokens"]
            self.metrics["total_duration_ms"] += duration_ms

            # Log execution
            self.execution_history.append({
                "execution_id": execution_id,
                "timestamp": start_time.isoformat(),
                "duration_ms": duration_ms,
                "input_size": len(str(input_data)),
                "output_size": len(str(result)),
                "tokens_in": response["usage"]["prompt_tokens"],
                "tokens_out": response["usage"]["completion_tokens"],
            })

            logger.info(
                f"[{session_id}] {self.config.name} completed in {duration_ms:.0f}ms. "
                f"Tokens: {response['usage']['prompt_tokens']} in, {response['usage']['completion_tokens']} out"
            )

            # Audit logging
            append_entry(
                session_id=session_id or "unknown",
                agent=self.config.name,
                action="executed",
                data={
                    "execution_id": execution_id,
                    "duration_ms": duration_ms,
                    "input_keys": list(input_data.keys()),
                    "output_keys": list(result.keys()) if isinstance(result, dict) else [],
                    "tokens_in": response["usage"]["prompt_tokens"],
                    "tokens_out": response["usage"]["completion_tokens"],
                },
            )

            return result

        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"[{session_id}] Error in {self.config.name}: {str(e)}", exc_info=True)

            # Audit error
            append_entry(
                session_id=session_id or "unknown",
                agent=self.config.name,
                action="error",
                data={"error": str(e), "type": type(e).__name__},
            )

            raise

    def _build_prompt(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build a prompt for this agent"""
        # Override in subclasses for agent-specific prompts
        return json.dumps({"input": input_data, "context": context or {}})

    def _get_system_prompt(self) -> str:
        """Get system prompt for this agent"""
        # Override in subclasses
        return f"You are {self.config.name}. {self.config.description}"

    def _parse_response(self, response: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response into structured output"""
        # Override in subclasses
        return {"response": response["text"]}

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics"""
        return self.metrics


class AskSchroogeOrchestrator:
    """
    Main orchestrator using Google ADK framework.
    Coordinates the multi-agent pipeline with proper session/memory management.
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize the orchestrator.

        Args:
            project_id: Google Cloud project ID
        """
        self.llm_client = VertexAIClient(project_id=project_id)
        self.session_service = SessionService() if HAS_ADK else None
        self.memory = MemoryBank() if HAS_ADK else {}
        self.agents: Dict[str, AskSchroogeAgent] = {}
        self.execution_log: List[Dict[str, Any]] = []

        if HAS_ADK:
            self.agent_runner = AgentRunner(project_id=project_id) if project_id else AgentRunner()
        else:
            self.agent_runner = None

        logger.info(f"Initialized ADK Orchestrator (ADK available: {HAS_ADK})")

    def register_agent(self, agent: AskSchroogeAgent) -> None:
        """Register an agent with the orchestrator"""
        self.agents[agent.config.name] = agent
        logger.info(f"Registered agent: {agent.config.name}")

    async def run_sequential_pipeline(
        self,
        session_id: str,
        initial_data: Dict[str, Any],
        agent_names: List[str],
    ) -> Dict[str, Any]:
        """
        Run agents sequentially (each agent uses output of previous).

        Args:
            session_id: Session ID for tracking
            initial_data: Initial input data
            agent_names: List of agent names to run in order

        Returns:
            Final pipeline result
        """
        logger.info(f"[{session_id}] Starting sequential pipeline with agents: {agent_names}")

        # Create session in ADK
        if self.session_service:
            session = self.session_service.create_session(session_id)
        else:
            session = {"id": session_id}

        current_data = initial_data
        results = {}

        for agent_name in agent_names:
            if agent_name not in self.agents:
                raise ValueError(f"Agent not found: {agent_name}")

            agent = self.agents[agent_name]
            result = await agent.execute(
                input_data=current_data,
                session_id=session_id,
                context=results,
            )

            results[agent_name] = result
            current_data = result  # Next agent uses this agent's output

        logger.info(f"[{session_id}] Sequential pipeline complete")
        return results

    async def run_parallel_agents(
        self,
        session_id: str,
        data: Dict[str, Any],
        agent_names: List[str],
    ) -> Dict[str, Any]:
        """
        Run agents in parallel (all get same input).

        Args:
            session_id: Session ID for tracking
            data: Input data (same for all agents)
            agent_names: List of agent names to run in parallel

        Returns:
            Results from all agents
        """
        logger.info(f"[{session_id}] Starting parallel execution of agents: {agent_names}")

        if self.session_service:
            session = self.session_service.create_session(session_id)
        else:
            session = {"id": session_id}

        # Create tasks for parallel execution
        tasks = []
        for agent_name in agent_names:
            if agent_name not in self.agents:
                raise ValueError(f"Agent not found: {agent_name}")
            agent = self.agents[agent_name]
            tasks.append(agent.execute(input_data=data, session_id=session_id))

        # Run all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Package results
        output = {}
        for agent_name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                logger.error(f"[{session_id}] Agent {agent_name} failed: {result}")
                output[agent_name] = {"error": str(result)}
            else:
                output[agent_name] = result

        logger.info(f"[{session_id}] Parallel execution complete")
        return output

    async def run_loop_agents(
        self,
        session_id: str,
        data: Dict[str, Any],
        agent_name: str,
        iterations: int = 3,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> Dict[str, Any]:
        """
        Run an agent in a loop (for iterative refinement).

        Args:
            session_id: Session ID for tracking
            data: Initial input data
            agent_name: Agent to run in loop
            iterations: Number of iterations (default: 3)
            condition: Optional condition to stop early

        Returns:
            Final refined result
        """
        logger.info(f"[{session_id}] Starting loop execution of {agent_name}")

        if agent_name not in self.agents:
            raise ValueError(f"Agent not found: {agent_name}")

        agent = self.agents[agent_name]
        current_data = data

        for iteration in range(iterations):
            logger.info(f"[{session_id}] Loop iteration {iteration + 1}/{iterations}")

            result = await agent.execute(
                input_data=current_data,
                session_id=f"{session_id}_iter{iteration}",
            )

            # Check stopping condition
            if condition and condition(result):
                logger.info(f"[{session_id}] Loop stopping condition met at iteration {iteration + 1}")
                return result

            current_data = result

        logger.info(f"[{session_id}] Loop execution complete")
        return current_data

    async def run_full_pipeline(
        self,
        session_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run the full Ask-Scrooge monetization pipeline.
        Uses a combination of sequential and parallel execution.

        Args:
            session_id: Session ID for tracking
            data: Input usage data

        Returns:
            Complete pipeline results
        """
        logger.info(f"[{session_id}] Starting full Ask-Scrooge pipeline")

        results = {}

        # Phase 1: Data aggregation (sequential)
        logger.info(f"[{session_id}] Phase 1: Data aggregation")
        results["data"] = await self.agents["DataAgent"].execute(
            input_data=data,
            session_id=session_id,
        )

        # Phase 2: Cost analysis (parallel - multiple models)
        logger.info(f"[{session_id}] Phase 2: Cost analysis (parallel)")
        cost_result = await self.agents["CostAgent"].execute(
            input_data=results["data"],
            session_id=session_id,
        )
        results["costs"] = cost_result

        # Phase 3: Bundle and pricing (parallel)
        logger.info(f"[{session_id}] Phase 3: Bundle & Pricing (parallel)")
        bundle_pricing = await self.run_parallel_agents(
            session_id=session_id,
            data=results["costs"],
            agent_names=["BundleAgent", "PricingAgent"],
        )
        results["bundle"] = bundle_pricing.get("BundleAgent")
        results["pricing"] = bundle_pricing.get("PricingAgent")

        # Phase 4: Compliance (sequential - final validation)
        logger.info(f"[{session_id}] Phase 4: Compliance validation")
        results["compliance"] = await self.agents["ComplianceAgent"].execute(
            input_data={
                "pricing": results["pricing"],
                "region": data.get("compliance_region", "US"),
            },
            session_id=session_id,
        )

        logger.info(f"[{session_id}] Full pipeline complete")

        return results

    def get_orchestrator_metrics(self) -> Dict[str, Any]:
        """Get overall orchestrator metrics"""
        return {
            "agents": {name: agent.get_metrics() for name, agent in self.agents.items()},
            "total_executions": len(self.execution_log),
            "llm_budget": self.llm_client.get_budget_status(),
        }


# For backward compatibility with old orchestration code
class LegacyAgentRunner:
    """Wrapper to maintain backward compatibility with existing code"""

    def __init__(self, orchestrator: AskSchroogeOrchestrator):
        self.orchestrator = orchestrator

    async def run(self, session_id: str, data: Dict[str, Any]):
        """Run pipeline (backward compatible)"""
        return await self.orchestrator.run_full_pipeline(session_id, data)


if __name__ == "__main__":
    print("Google ADK Orchestrator module loaded successfully")
    print(f"ADK available: {HAS_ADK}")
