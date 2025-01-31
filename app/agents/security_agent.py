from typing import Any, Dict, Optional
import jwt
from datetime import datetime, timedelta
import re
from passlib.context import CryptContext
from app.agents.base_agent import BaseAgent
from app.utils.exceptions import SecurityError

class DataSecurityAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__("Data Security Agent", api_key)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # For demo purposes - in production, use a proper user database
        self.users = {
            "admin": {
                "username": "admin",
                "hashed_password": self.get_password_hash("admin"),
                "role": "admin"
            }
        }
        
        # Define role permissions
        self.role_permissions = {
            "admin": ["create", "read", "update", "delete"],
            "editor": ["create", "read", "update"],
            "viewer": ["read"]
        }
        
        # Define validation patterns
        self.validation_patterns = {
            "email": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
            "phone": r"^\+?1?\d{9,15}$",
            "password": r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$"  # At least 8 chars, 1 letter and 1 number
        }

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process security-related requests"""
        operation = request.get("operation")
        
        if operation == "authenticate":
            return await self._authenticate_user(request)
        elif operation == "authorize":
            return await self._authorize_request(request)
        elif operation == "validate":
            return await self._validate_data(request)
        else:
            raise SecurityError(f"Unknown security operation: {operation}")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.api_key, algorithm="HS256")

    async def _authenticate_user(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user and return token"""
        username = request.get("username")
        password = request.get("password")
        
        if not username or not password:
            raise SecurityError("Username and password are required")
        
        user = self.users.get(username)
        if not user:
            raise SecurityError("Invalid username or password")
        
        if not self.verify_password(password, user["hashed_password"]):
            raise SecurityError("Invalid username or password")
        
        access_token = self.create_access_token(
            data={"sub": username, "role": user["role"]},
            expires_delta=timedelta(minutes=30)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    async def _authorize_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Authorize a request based on token and permissions"""
        token = request.get("token")
        action = request.get("action")
        
        try:
            payload = jwt.decode(token, self.api_key, algorithms=["HS256"])
            username = payload.get("sub")
            role = payload.get("role")
            
            if not username or not role:
                raise SecurityError("Invalid token")
            
            if action not in self.role_permissions.get(role, []):
                raise SecurityError(f"User does not have permission to perform {action}")
            
            return {
                "authorized": True,
                "username": username,
                "role": role,
                "token": token
            }
            
        except jwt.ExpiredSignatureError:
            raise SecurityError("Token has expired")
        except jwt.JWTError:
            raise SecurityError("Invalid token")

    async def _validate_data(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against security rules"""
        data = request.get("data", {})
        validation_results = {}
        is_valid = True
        
        for field, value in data.items():
            if field in self.validation_patterns and value:
                pattern = self.validation_patterns[field]
                is_match = bool(re.match(pattern, value))
                validation_results[field] = is_match
                is_valid = is_valid and is_match
        
        return {
            "valid": is_valid,
            "validation_results": validation_results
        }
