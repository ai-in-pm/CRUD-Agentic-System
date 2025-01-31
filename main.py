import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from loguru import logger
import os

from app.core.config import Settings
from app.api.api_v1.api import api_router
from app.core.orchestrator import OrchestrationAgent

# Load environment variables
load_dotenv()

# Initialize Orchestration Agent
orchestrator = OrchestrationAgent()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI-Driven CRUD Management System")
    await orchestrator.initialize_agents()
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI-Driven CRUD Management System")
    await orchestrator.shutdown_agents()

# Initialize FastAPI app
app = FastAPI(
    title="AI-Driven CRUD Management System",
    description="A collaborative AI agent system for efficient database management",
    version="1.0.0",
    lifespan=lifespan
)

# Load settings
settings = Settings()

# Add API router
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
