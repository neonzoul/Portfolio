"""
Pydantic models for API request/response handling.

These models define the contract between the API and clients, providing
validation, serialization, and documentation for all API operations.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
import re


class ProductCreate(BaseModel):
    """
    Input model for creating products. 
    
    Separating this from the database model allows us to control 
    exactly what fields the API accepts and apply specific validation rules.
    """
    
    sku: str = Field(
        min_length=1,
        max_length=50,
        description="Stock Keeping Unit - unique product identifier (alphanumeric, hyphens allowed)"
    )
    
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Human-readable product name"
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional product description"
    )
    
    quantity: int = Field(
        ge=0,
        description="Initial stock quantity (must be >= 0)"
    )
    
    @field_validator('sku')
    @classmethod
    def validate_sku_format(cls, v):
        """
        Validate SKU format - should contain only alphanumeric characters and hyphens.
        This ensures SKUs are URL-safe and follow common conventions.
        """
        if not re.match(r'^[A-Z0-9\-]+$', v):
            raise ValueError('SKU must contain only uppercase letters, numbers, and hyphens')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name_not_empty(cls, v):
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError('Product name cannot be empty or just whitespace')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Clean up description if provided."""
        if v is not None:
            v = v.strip()
            if not v:  # If description is empty after stripping, set to None
                return None
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sku": "TSHIRT-RED-L",
                "name": "Red T-Shirt (Large)",
                "description": "Comfortable cotton t-shirt in red, size large",
                "quantity": 25
            }
        }
    )


class StockOperation(BaseModel):
    """
    Model for stock add/remove operations. 
    
    Using a dedicated model makes the API contract clear and enables validation.
    The amount must be positive - the operation type (add/remove) is determined by the endpoint.
    """
    
    amount: int = Field(
        gt=0,
        description="Amount to add or remove (must be positive)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 5
            }
        }
    )


class ProductResponse(BaseModel):
    """
    Response model for product data.
    
    This matches our database entity but can be customized for API responses
    without affecting the database schema. It provides a stable API contract.
    """
    
    sku: str = Field(description="Stock Keeping Unit - unique product identifier")
    name: str = Field(description="Human-readable product name")
    description: Optional[str] = Field(description="Product description")
    quantity: int = Field(description="Current stock quantity")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "sku": "TSHIRT-RED-L",
                "name": "Red T-Shirt (Large)",
                "description": "Comfortable cotton t-shirt in red, size large",
                "quantity": 20
            }
        }
    )


class ProductListResponse(BaseModel):
    """
    Response model for listing multiple products.
    
    Wrapping the list in a model allows for future extensibility
    (e.g., adding pagination metadata) without breaking the API contract.
    """
    
    products: list[ProductResponse] = Field(description="List of products")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "products": [
                    {
                        "sku": "TSHIRT-RED-L",
                        "name": "Red T-Shirt (Large)",
                        "description": "Comfortable cotton t-shirt in red, size large",
                        "quantity": 20
                    },
                    {
                        "sku": "JEANS-BLUE-32",
                        "name": "Blue Jeans (32 waist)",
                        "description": "Classic blue denim jeans",
                        "quantity": 15
                    }
                ]
            }
        }
    )


class ValidationErrorDetail(BaseModel):
    """
    Detailed validation error information for a specific field.
    """
    
    field: str = Field(description="Field name that failed validation")
    message: str = Field(description="User-friendly error message")
    details: str = Field(description="Additional details about the error")
    provided_value: Optional[str] = Field(description="The value that was provided")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field": "sku",
                "message": "SKU format is invalid",
                "details": "SKU must contain only uppercase letters, numbers, and hyphens (e.g., 'PROD-001')",
                "provided_value": "invalid-sku"
            }
        }
    )


class ErrorResponse(BaseModel):
    """
    Standard error response model for consistent error handling across the API.
    """
    
    error: str = Field(description="Error type or category")
    message: str = Field(description="Main error message")
    details: str = Field(description="Additional error details")
    path: str = Field(description="API path where the error occurred")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Product Not Found",
                "message": "Product with SKU 'INVALID-001' not found",
                "details": "No product exists with the specified SKU: INVALID-001",
                "path": "/products/INVALID-001"
            }
        }
    )


class ValidationErrorResponse(BaseModel):
    """
    Detailed validation error response with field-specific information.
    """
    
    error: str = Field(description="Error type", default="Validation Error")
    message: str = Field(description="Main error message")
    details: str = Field(description="Summary of validation errors")
    validation_errors: list[ValidationErrorDetail] = Field(description="Detailed validation errors")
    path: str = Field(description="API path where the error occurred")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Validation Error",
                "message": "Request validation failed",
                "details": "Found 2 validation error(s)",
                "validation_errors": [
                    {
                        "field": "sku",
                        "message": "SKU format is invalid",
                        "details": "SKU must contain only uppercase letters, numbers, and hyphens (e.g., 'PROD-001')",
                        "provided_value": "invalid-sku"
                    },
                    {
                        "field": "quantity",
                        "message": "quantity must be greater than or equal to 0",
                        "details": "Quantity cannot be negative",
                        "provided_value": "-5"
                    }
                ],
                "path": "/products"
            }
        }
    )


class InsufficientStockErrorResponse(BaseModel):
    """
    Specific error response for insufficient stock scenarios.
    """
    
    error: str = Field(description="Error type", default="Insufficient Stock")
    message: str = Field(description="Main error message")
    details: str = Field(description="Additional error details")
    sku: str = Field(description="Product SKU that has insufficient stock")
    requested: int = Field(description="Amount requested to remove")
    available: int = Field(description="Amount currently available")
    path: str = Field(description="API path where the error occurred")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Insufficient Stock",
                "message": "Insufficient stock for product 'PROD-001'",
                "details": "Requested: 10, Available: 5",
                "sku": "PROD-001",
                "requested": 10,
                "available": 5,
                "path": "/products/PROD-001/remove"
            }
        }
    )


class DuplicateSKUErrorResponse(BaseModel):
    """
    Specific error response for duplicate SKU scenarios.
    """
    
    error: str = Field(description="Error type", default="Duplicate SKU")
    message: str = Field(description="Main error message")
    details: str = Field(description="Additional error details")
    sku: str = Field(description="SKU that already exists")
    path: str = Field(description="API path where the error occurred")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Duplicate SKU",
                "message": "Product with SKU 'PROD-001' already exists",
                "details": "A product with SKU 'PROD-001' is already registered in the system",
                "sku": "PROD-001",
                "path": "/products"
            }
        }
    )