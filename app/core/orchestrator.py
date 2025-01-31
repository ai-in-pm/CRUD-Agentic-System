from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
from loguru import logger
import os

from app.agents.ingestion_agent import DataIngestionAgent
from app.agents.query_agent import DataQueryAgent
from app.agents.update_agent import DataUpdateAgent
from app.agents.security_agent import DataSecurityAgent
from app.agents.analytics_agent import DataAnalyticsAgent
from app.utils.exceptions import OrchestrationError

class OrchestrationAgent:
    def __init__(self):
        self.agents = {}
        self.workflow_history = []
        self.active_workflows = {}

    async def initialize_agents(self) -> None:
        """Initialize all agents"""
        try:
            # Initialize agents with their respective API keys
            self.agents = {
                "ingestion": DataIngestionAgent(os.getenv("OPENAI_API_KEY")),
                "query": DataQueryAgent(os.getenv("OPENAI_API_KEY")),
                "update": DataUpdateAgent(os.getenv("GROQ_API_KEY")),
                "security": DataSecurityAgent(os.getenv("JWT_SECRET_KEY")),
                "analytics": DataAnalyticsAgent(os.getenv("COHERE_API_KEY"))
            }

            # Initialize each agent
            init_tasks = []
            for name, agent in self.agents.items():
                logger.info(f"Initializing {name} agent...")
                init_tasks.append(agent.initialize())
            
            await asyncio.gather(*init_tasks)
            logger.info("All agents initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing agents: {str(e)}")
            raise OrchestrationError(f"Failed to initialize agents: {str(e)}")

    async def shutdown_agents(self) -> None:
        """Shutdown all agents"""
        try:
            # Cleanup tasks for each agent
            cleanup_tasks = []
            for name, agent in self.agents.items():
                logger.info(f"Shutting down {name} agent...")
                cleanup_tasks.append(agent.cleanup())
            
            await asyncio.gather(*cleanup_tasks)
            logger.info("All agents shut down successfully")
        
        except Exception as e:
            logger.error(f"Error shutting down agents: {str(e)}")
            raise OrchestrationError(f"Failed to shut down agents: {str(e)}")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request using the appropriate agents"""
        try:
            workflow_id = f"wf_{len(self.workflow_history) + 1}"
            workflow = {
                "workflow_id": workflow_id,
                "start_time": datetime.utcnow().isoformat(),
                "request": request,
                "status": "in_progress"
            }

            self.active_workflows[workflow_id] = workflow
            self.workflow_history.append(workflow)

            operation = request.get("operation")
            if operation == "create":
                result = await self._handle_create(request)
            elif operation == "read":
                result = await self._handle_read(request)
            elif operation == "update":
                result = await self._handle_update(request)
            elif operation == "delete":
                result = await self._handle_delete(request)
            elif operation == "list":
                result = await self._handle_list(request)
            else:
                raise OrchestrationError(f"Unknown operation: {operation}")

            workflow["status"] = "completed"
            workflow["end_time"] = datetime.utcnow().isoformat()
            workflow["result"] = result

            return result

        except Exception as e:
            if workflow_id in self.active_workflows:
                workflow = self.active_workflows[workflow_id]
                workflow["status"] = "failed"
                workflow["error"] = str(e)
                workflow["end_time"] = datetime.utcnow().isoformat()

            logger.error(f"Error processing request: {str(e)}")
            raise OrchestrationError(f"Failed to process request: {str(e)}")

    async def _handle_create(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create operation"""
        result = await self.agents["ingestion"].process(request)
        await self.agents["analytics"].process({"operation": "log_creation", "data": result})
        return result

    async def _handle_read(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle read operation"""
        return await self.agents["query"].process(request)

    async def _handle_update(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle update operation"""
        result = await self.agents["update"].process(request)
        await self.agents["analytics"].process({"operation": "log_update", "data": result})
        return result

    async def _handle_delete(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delete operation"""
        result = await self.agents["update"].process({"operation": "delete", **request})
        await self.agents["analytics"].process({"operation": "log_deletion", "data": result})
        return result

    async def _handle_list(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle list operation"""
        return await self.agents["query"].process({"operation": "list", **request})

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a specific workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            raise OrchestrationError(f"Workflow not found: {workflow_id}")
        return workflow

    async def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get the status of a specific agent"""
        agent = self.agents.get(agent_name)
        if not agent:
            raise OrchestrationError(f"Agent not found: {agent_name}")
        return {"name": agent.name, "initialized": agent.is_initialized}
