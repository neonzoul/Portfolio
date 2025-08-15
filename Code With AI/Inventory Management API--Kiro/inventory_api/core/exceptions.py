"""
Custom exception classes and FastAPI exception handlers.

This module defines all custom exceptions used throughout the application
and provides FastAPI exception handlers that convert them to appropriate
HTTP responses with proper status codes.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
import logging


class InventoryException(Exception):
    """
    Base exception for all inventory-related operations.
    
    All custom exceptions in the application should inherit from this
    base class to enable consistent error handling.
    """
    
    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class ProductNotFound(InventoryException):
    """
    Raised when a requested product cannot be found.
    
    This exception maps to HTTP 404 Not Found responses.
    """
    
    def __init__(self, sku: str):
        super().__init__(
            message=f"Product with SKU '{sku}' not found",
            details=f"No product exists with the specified SKU: {sku}"
        )
        self.sku = sku


class InsufficientStock(InventoryException):
    """
    Raised when attempting to remove more stock than available.
    
    This exception maps to HTTP 400 Bad Request responses and prevents
    negative inventory levels.
    """
    
    def __init__(self, sku: str, requested_amount: int, available_amount: int):
        super().__init__(
            message=f"Insufficient stock for product '{sku}'",
            details=f"Requested: {requested_amount}, Available: {available_amount}"
        )
        self.sku = sku
        self.requested_amount = requested_amount
        self.available_amount = available_amount


class DuplicateSKU(InventoryException):
    """
    Raised when attempting to create a product with an existing SKU.
    
    This exception maps to HTTP 400 Bad Request responses and ensures
    SKU uniqueness constraints are enforced.
    """
    
    def __init__(self, sku: str):
        super().__init__(
            message=f"Product with SKU '{sku}' already exists",
            details=f"A product with SKU '{sku}' is already registered in the system"
        )
        self.sku = sku


class DatabaseError(InventoryException):
    """
    Raised when database operations fail.
    
    This exception wraps SQLAlchemy errors and maps to HTTP 500 Internal
    Server Error responses.
    """
    
    def __init__(self, operation: str, original_error: Exception):
        super().__init__(
            message=f"Database error during {operation}",
            details=str(original_error)
        )
        self.operation = operation
        self.original_error = original_error


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Configure FastAPI exception handlers for custom exceptions.
    
    This function registers exception handlers that convert custom exceptions
    into appropriate HTTP responses with proper status codes and error messages.
    
    Args:
        app: FastAPI application instance
    """
    
    # Set up logging for error tracking
    logger = logging.getLogger(__name__)
    
    @app.exception_handler(ProductNotFound)
    async def product_not_found_handler(request: Request, exc: ProductNotFound):
        """Handle ProductNotFound exceptions with 404 status."""
        logger.info(f"Product not found: {exc.sku}")
        return JSONResponse(
            status_code=404,
            content={
                "error": "Product Not Found",
                "message": exc.message,
                "details": exc.details,
                "sku": exc.sku,
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(InsufficientStock)
    async def insufficient_stock_handler(request: Request, exc: InsufficientStock):
        """Handle InsufficientStock exceptions with 400 status."""
        logger.warning(f"Insufficient stock for {exc.sku}: requested {exc.requested_amount}, available {exc.available_amount}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "Insufficient Stock",
                "message": exc.message,
                "details": exc.details,
                "sku": exc.sku,
                "requested": exc.requested_amount,
                "available": exc.available_amount,
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(DuplicateSKU)
    async def duplicate_sku_handler(request: Request, exc: DuplicateSKU):
        """Handle DuplicateSKU exceptions with 400 status."""
        logger.warning(f"Attempt to create duplicate SKU: {exc.sku}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "Duplicate SKU",
                "message": exc.message,
                "details": exc.details,
                "sku": exc.sku,
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        """Handle DatabaseError exceptions with 500 status."""
        logger.error(f"Database error during {exc.operation}: {exc.original_error}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Database Error",
                "message": exc.message,
                "details": "An internal database error occurred. Please try again later.",
                "operation": exc.operation,
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """Handle SQLAlchemy IntegrityError exceptions."""
        logger.error(f"Database integrity error: {exc.orig}")
        
        # Check if this is a duplicate SKU error
        if "UNIQUE constraint failed" in str(exc.orig) and "sku" in str(exc.orig):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Duplicate SKU",
                    "message": "A product with this SKU already exists",
                    "details": "SKU must be unique across all products",
                    "path": str(request.url.path)
                }
            )
        
        # Check for other constraint violations
        if "CHECK constraint failed" in str(exc.orig):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Data Constraint Violation",
                    "message": "The operation violates data constraints",
                    "details": "Please check that all values meet the required constraints (e.g., quantity >= 0)",
                    "path": str(request.url.path)
                }
            )
        
        # Generic integrity error
        return JSONResponse(
            status_code=400,
            content={
                "error": "Data Integrity Error",
                "message": "The operation violates data integrity constraints",
                "details": "Please check your input data and try again",
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Handle FastAPI request validation errors with detailed messages.
        
        This provides user-friendly error messages for validation failures,
        including field-specific details and suggestions for correction.
        """
        logger.warning(f"Request validation error: {exc.errors()}")
        
        # Format validation errors into user-friendly messages
        formatted_errors = []
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"][1:])  # Skip 'body' prefix
            error_type = error["type"]
            error_msg = error["msg"]
            
            # Create more user-friendly error messages
            if error_type == "value_error":
                if "SKU must contain only" in error_msg:
                    formatted_errors.append({
                        "field": field_path,
                        "message": "SKU format is invalid",
                        "details": "SKU must contain only uppercase letters, numbers, and hyphens (e.g., 'PROD-001')",
                        "provided_value": error.get("input")
                    })
                else:
                    formatted_errors.append({
                        "field": field_path,
                        "message": error_msg,
                        "details": "Please check the field value and format",
                        "provided_value": error.get("input")
                    })
            elif error_type == "greater_than":
                formatted_errors.append({
                    "field": field_path,
                    "message": f"{field_path} must be greater than {error['ctx']['gt']}",
                    "details": "Amount must be a positive number",
                    "provided_value": error.get("input")
                })
            elif error_type == "greater_than_equal":
                formatted_errors.append({
                    "field": field_path,
                    "message": f"{field_path} must be greater than or equal to {error['ctx']['ge']}",
                    "details": "Quantity cannot be negative",
                    "provided_value": error.get("input")
                })
            elif error_type == "missing":
                formatted_errors.append({
                    "field": field_path,
                    "message": f"{field_path} is required",
                    "details": "This field must be provided in the request",
                    "provided_value": None
                })
            elif error_type == "string_too_short":
                formatted_errors.append({
                    "field": field_path,
                    "message": f"{field_path} is too short",
                    "details": f"Minimum length is {error['ctx']['min_length']} characters",
                    "provided_value": error.get("input")
                })
            elif error_type == "string_too_long":
                formatted_errors.append({
                    "field": field_path,
                    "message": f"{field_path} is too long",
                    "details": f"Maximum length is {error['ctx']['max_length']} characters",
                    "provided_value": error.get("input")
                })
            else:
                formatted_errors.append({
                    "field": field_path,
                    "message": error_msg,
                    "details": "Please check the field value and format",
                    "provided_value": error.get("input")
                })
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Request validation failed",
                "details": f"Found {len(formatted_errors)} validation error(s)",
                "validation_errors": formatted_errors,
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        """Handle Pydantic validation errors."""
        logger.warning(f"Pydantic validation error: {exc.errors()}")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Data validation failed",
                "details": str(exc),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle ValueError exceptions from business logic."""
        logger.warning(f"Value error: {exc}")
        
        return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid Value",
                "message": str(exc),
                "details": "Please check your input values and try again",
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Handle any unhandled exceptions with a generic 500 response.
        
        This is a catch-all handler that ensures the API always returns
        a proper JSON response, even for unexpected errors.
        """
        logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "details": "Please try again later. If the problem persists, contact support.",
                "path": str(request.url.path)
            }
        )