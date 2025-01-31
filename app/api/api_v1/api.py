from fastapi import APIRouter, Depends, HTTPException, Security, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Any, Dict, List
from datetime import datetime

from app.core.config import Settings
from app.core.orchestrator import OrchestrationAgent
from app.utils.exceptions import OrchestrationError, SecurityError

settings = Settings()
api_router = APIRouter()
orchestrator = OrchestrationAgent()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

@api_router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    """Login endpoint to get access token"""
    try:
        # Initialize agents if not already initialized
        if not orchestrator.agents:
            await orchestrator.initialize_agents()
            
        auth_result = await orchestrator.agents["security"].process({
            "operation": "authenticate",
            "username": form_data.username,
            "password": form_data.password
        })
        return auth_result
    except SecurityError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Get current user from token"""
    try:
        # Initialize agents if not already initialized
        if not orchestrator.agents:
            await orchestrator.initialize_agents()
            
        auth_result = await orchestrator.agents["security"].process({
            "operation": "authorize",
            "token": token,
            "action": "read"  # Basic read permission check
        })
        return auth_result
    except SecurityError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/process")
async def process_request(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Process a request through the agent system"""
    try:
        result = await orchestrator.process_request(request)
        return result
    except OrchestrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/workflow/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get the status of a specific workflow"""
    try:
        return await orchestrator.get_workflow_status(workflow_id)
    except OrchestrationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/agent/{agent_name}")
async def get_agent_status(
    agent_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get the status of a specific agent"""
    try:
        return await orchestrator.get_agent_status(agent_name)
    except OrchestrationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/customer")
async def create_customer(
    customer_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new customer"""
    try:
        # Validate user has create permission
        await orchestrator.agents["security"].process({
            "operation": "authorize",
            "token": current_user.get("token"),
            "action": "create"
        })

        # Validate customer data
        validation_result = await orchestrator.agents["security"].process({
            "operation": "validate",
            "data": {
                "email": customer_data.get("email", ""),
                "phone": customer_data.get("phone", "")
            }
        })

        if not validation_result["valid"]:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid data format: {validation_result['validation_results']}"
            )

        # Process customer creation
        result = await orchestrator.process_request({
            "operation": "create",
            "entity": "customer",
            "data": customer_data
        })
        return result

    except SecurityError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except OrchestrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/customer/{customer_id}")
async def get_customer(
    customer_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get customer by ID"""
    try:
        # Validate user has read permission
        await orchestrator.agents["security"].process({
            "operation": "authorize",
            "token": current_user.get("token"),
            "action": "read"
        })

        result = await orchestrator.process_request({
            "operation": "read",
            "entity": "customer",
            "id": customer_id
        })
        return result

    except SecurityError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except OrchestrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/customer/{customer_id}")
async def update_customer(
    customer_id: str,
    customer_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update customer by ID"""
    try:
        # Validate user has update permission
        await orchestrator.agents["security"].process({
            "operation": "authorize",
            "token": current_user.get("token"),
            "action": "update"
        })

        # Validate customer data
        if "email" in customer_data or "phone" in customer_data:
            validation_result = await orchestrator.agents["security"].process({
                "operation": "validate",
                "data": {
                    "email": customer_data.get("email", ""),
                    "phone": customer_data.get("phone", "")
                }
            })

            if not validation_result["valid"]:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid data format: {validation_result['validation_results']}"
                )

        result = await orchestrator.process_request({
            "operation": "update",
            "entity": "customer",
            "id": customer_id,
            "data": customer_data
        })
        return result

    except SecurityError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except OrchestrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/customer/{customer_id}")
async def delete_customer(
    customer_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Delete customer by ID"""
    try:
        # Validate user has delete permission
        await orchestrator.agents["security"].process({
            "operation": "authorize",
            "token": current_user.get("token"),
            "action": "delete"
        })

        result = await orchestrator.process_request({
            "operation": "delete",
            "entity": "customer",
            "id": customer_id
        })
        return result

    except SecurityError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except OrchestrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/customers")
async def list_customers(
    skip: int = 0,
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List customers with pagination"""
    try:
        # Validate user has read permission
        await orchestrator.agents["security"].process({
            "operation": "authorize",
            "token": current_user.get("token"),
            "action": "read"
        })

        result = await orchestrator.process_request({
            "operation": "list",
            "entity": "customer",
            "skip": skip,
            "limit": limit
        })
        return result

    except SecurityError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except OrchestrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analytics/report")
async def generate_analytics_report(
    report_config: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate analytics report"""
    try:
        # Validate user has read permission
        await orchestrator.agents["security"].process({
            "operation": "authorize",
            "token": current_user.get("token"),
            "action": "read"
        })

        result = await orchestrator.process_request({
            "operation": "analytics",
            "config": report_config
        })
        return result

    except SecurityError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except OrchestrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
