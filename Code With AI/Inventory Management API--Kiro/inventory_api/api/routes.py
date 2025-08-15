"""
FastAPI route definitions for the inventory management API.

This module defines all API endpoints with proper HTTP semantics,
request/response models, and error handling.
"""

from fastapi import APIRouter, Depends, status

from inventory_api.models.api import (
    ProductCreate,
    ProductResponse,
    ProductListResponse,
    StockOperation,
    ErrorResponse,
    ValidationErrorResponse,
    InsufficientStockErrorResponse,
    DuplicateSKUErrorResponse
)
from inventory_api.services.protocols import ProductServiceProtocol
from inventory_api.api.dependencies import get_product_service
# Exceptions are now handled by global exception handlers in main.py


# Create router instance
router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ProductResponse,
    responses={
        201: {"description": "Product created successfully"},
        400: {
            "description": "Bad Request - Invalid data or duplicate SKU",
            "model": DuplicateSKUErrorResponse
        },
        422: {
            "description": "Validation Error - Invalid request format",
            "model": ValidationErrorResponse
        },
        500: {
            "description": "Internal Server Error",
            "model": ErrorResponse
        }
    }
)
async def create_product(
    product_data: ProductCreate,
    service: ProductServiceProtocol = Depends(get_product_service)
) -> ProductResponse:
    """
    Create a new product.
    
    Creates a new product with the provided SKU, name, description, and initial quantity.
    The SKU must be unique across all products.
    
    - **sku**: Unique Stock Keeping Unit identifier (alphanumeric and hyphens only)
    - **name**: Human-readable product name
    - **description**: Optional product description
    - **quantity**: Initial stock quantity (must be >= 0)
    
    Returns the created product with all its details.
    
    **Error Scenarios:**
    - 400: Duplicate SKU or invalid business logic
    - 422: Request validation errors (invalid format, missing fields, etc.)
    - 500: Internal server or database errors
    """
    # Let exceptions bubble up to be handled by the global exception handlers
    return await service.create_product(product_data)


@router.get(
    "",
    response_model=ProductListResponse,
    responses={
        200: {"description": "List of all products retrieved successfully"},
        500: {
            "description": "Internal Server Error",
            "model": ErrorResponse
        }
    }
)
async def get_all_products(
    service: ProductServiceProtocol = Depends(get_product_service)
) -> ProductListResponse:
    """
    Retrieve all products.
    
    Returns a list of all products in the inventory with their current stock levels.
    The list may be empty if no products have been created yet.
    
    Returns a ProductListResponse containing the list of products.
    
    **Error Scenarios:**
    - 500: Internal server or database errors
    """
    products = await service.get_all_products()
    return ProductListResponse(products=products)


@router.get(
    "/{sku}",
    response_model=ProductResponse,
    responses={
        200: {"description": "Product retrieved successfully"},
        404: {
            "description": "Product not found",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal Server Error",
            "model": ErrorResponse
        }
    }
)
async def get_product_by_sku(
    sku: str,
    service: ProductServiceProtocol = Depends(get_product_service)
) -> ProductResponse:
    """
    Retrieve a product by SKU.
    
    Returns the product details for the specified Stock Keeping Unit (SKU).
    
    - **sku**: The Stock Keeping Unit identifier
    
    Returns the product with all its details including current stock quantity.
    
    **Error Scenarios:**
    - 404: Product with the specified SKU does not exist
    - 500: Internal server or database errors
    """
    return await service.get_product_by_sku(sku)


@router.patch(
    "/{sku}/add",
    response_model=ProductResponse,
    responses={
        200: {"description": "Stock added successfully"},
        400: {
            "description": "Bad Request - Invalid amount",
            "model": ErrorResponse
        },
        404: {
            "description": "Product not found",
            "model": ErrorResponse
        },
        422: {
            "description": "Validation Error - Invalid request format",
            "model": ValidationErrorResponse
        },
        500: {
            "description": "Internal Server Error",
            "model": ErrorResponse
        }
    }
)
async def add_stock(
    sku: str,
    operation: StockOperation,
    service: ProductServiceProtocol = Depends(get_product_service)
) -> ProductResponse:
    """
    Add stock to a product.
    
    Increases the stock quantity of the specified product by the given amount.
    This operation is atomic and safe for concurrent access.
    
    - **sku**: The Stock Keeping Unit identifier
    - **amount**: Amount to add (must be positive)
    
    Returns the updated product with the new stock quantity.
    
    **Error Scenarios:**
    - 400: Invalid business logic (e.g., invalid amount)
    - 404: Product with the specified SKU does not exist
    - 422: Request validation errors (e.g., amount <= 0)
    - 500: Internal server or database errors
    """
    return await service.add_stock(sku, operation.amount)


@router.patch(
    "/{sku}/remove",
    response_model=ProductResponse,
    responses={
        200: {"description": "Stock removed successfully"},
        400: {
            "description": "Bad Request - Invalid amount or insufficient stock",
            "model": InsufficientStockErrorResponse
        },
        404: {
            "description": "Product not found",
            "model": ErrorResponse
        },
        422: {
            "description": "Validation Error - Invalid request format",
            "model": ValidationErrorResponse
        },
        500: {
            "description": "Internal Server Error",
            "model": ErrorResponse
        }
    }
)
async def remove_stock(
    sku: str,
    operation: StockOperation,
    service: ProductServiceProtocol = Depends(get_product_service)
) -> ProductResponse:
    """
    Remove stock from a product.
    
    Decreases the stock quantity of the specified product by the given amount.
    This operation includes safety checks to prevent negative stock levels
    and is atomic to handle concurrent access safely.
    
    - **sku**: The Stock Keeping Unit identifier
    - **amount**: Amount to remove (must be positive and <= current stock)
    
    Returns the updated product with the new stock quantity.
    
    **Important**: This operation will fail if there is insufficient stock,
    ensuring that stock levels never go negative.
    
    **Error Scenarios:**
    - 400: Insufficient stock or invalid business logic
    - 404: Product with the specified SKU does not exist
    - 422: Request validation errors (e.g., amount <= 0)
    - 500: Internal server or database errors
    """
    return await service.remove_stock(sku, operation.amount)