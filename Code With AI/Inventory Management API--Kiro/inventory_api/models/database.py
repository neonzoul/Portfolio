"""
SQLModel database entities for the inventory management system.

This module defines the database schema using SQLModel, which combines
SQLAlchemy's ORM capabilities with Pydantic's validation and serialization.
"""

from sqlmodel import SQLModel, Field, CheckConstraint
from pydantic import ConfigDict
from typing import Optional


class Product(SQLModel, table=True):
    """
    Database model for products. SQLModel combines SQLAlchemy's ORM 
    capabilities with Pydantic's validation and serialization.
    
    This represents the actual database table structure with constraints
    to ensure data integrity, particularly preventing negative quantities.
    """
    
    # Auto-incrementing primary key for database efficiency
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Business identifier that users interact with - unique and indexed
    sku: str = Field(
        unique=True, 
        index=True, 
        min_length=1, 
        max_length=50,
        description="Stock Keeping Unit - unique product identifier"
    )
    
    # Required product name with reasonable length constraints
    name: str = Field(
        min_length=1, 
        max_length=255,
        description="Human-readable product name"
    )
    
    # Optional description field
    description: Optional[str] = Field(
        default=None, 
        max_length=1000,
        description="Optional product description"
    )
    
    # Current stock quantity - must be non-negative
    quantity: int = Field(
        ge=0,
        description="Current stock quantity (must be >= 0)"
    )
    
    # Database constraint to prevent negative quantities - this is our safety net
    __table_args__ = (
        CheckConstraint('quantity >= 0', name='positive_quantity'),
    )
    
    model_config = ConfigDict(
        # Enable validation on assignment
        validate_assignment=True,
        # Use enum values instead of enum objects in JSON
        use_enum_values=True,
        # Generate schema with examples
        json_schema_extra={
            "example": {
                "sku": "TSHIRT-RED-L",
                "name": "Red T-Shirt (Large)",
                "description": "Comfortable cotton t-shirt in red, size large",
                "quantity": 25
            }
        }
    )