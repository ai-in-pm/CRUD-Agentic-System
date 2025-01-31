from typing import Any, Dict, Optional
from loguru import logger

class BaseAgent:
    def __init__(self, name: str, api_key: Optional[str] = None):
        """Initialize base agent with name and API key"""
        self.name = name
        self.api_key = api_key
        self.is_initialized = False
        logger.info(f"Initializing {name}")

    async def initialize(self) -> Dict[str, Any]:
        """Initialize agent resources"""
        self.is_initialized = True
        return self.log_operation("initialize", {"status": "success"})

    async def cleanup(self) -> Dict[str, Any]:
        """Cleanup resources used by the agent"""
        self.is_initialized = False
        return self.log_operation("cleanup", {"status": "success"})

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request - to be implemented by child classes"""
        raise NotImplementedError("Process method must be implemented by child classes")

    def log_operation(self, operation: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Log an operation and its result"""
        logger.info(f"{self.name} - {operation}: {result}")
        return result

    def check_initialized(self) -> None:
        """Check if agent is initialized"""
        if not self.is_initialized:
            raise RuntimeError(f"{self.name} is not initialized")
