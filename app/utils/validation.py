from typing import Any, Dict, Optional
from pydantic import BaseModel, ValidationError
from datetime import datetime

class BaseSchema(BaseModel):
    """Base schema for all data models"""
    created_at: datetime
    updated_at: Optional[datetime]
    version: int

class CustomerSchema(BaseSchema):
    """Schema for customer data"""
    customer_id: str
    name: str
    email: str
    phone: Optional[str]
    address: Optional[str]

class ProductSchema(BaseSchema):
    """Schema for product data"""
    product_id: str
    name: str
    description: str
    price: float
    stock: int

class OrderSchema(BaseSchema):
    """Schema for order data"""
    order_id: str
    customer_id: str
    products: Dict[str, int]  # product_id: quantity
    total_amount: float
    status: str

# Schema registry
SCHEMAS = {
    "default": BaseSchema,
    "customer": CustomerSchema,
    "product": ProductSchema,
    "order": OrderSchema
}

def validate_data_schema(data: Dict[str, Any], schema_name: str = "default") -> bool:
    """Validate data against a schema"""
    try:
        schema = SCHEMAS.get(schema_name, BaseSchema)
        schema(**data)
        return True
    except ValidationError:
        return False
