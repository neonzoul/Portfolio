"""
Service protocol interfaces for the inventory management system.

This module defines the contracts for business logic operations using typing.Protocol,
enabling dependency inversion and easy testing while maintaining type safety.
"""

from typing import Protocol
from inventory_api.models.api import ProductCreate, ProductResponse


class ProductServiceProtocol(Protocol):
    """
    Protocol defining the contract for product business operations.
    
    This protocol encapsulates all business logic for product management,
    including validation, error handling, and coordination of repository operations.
    The service layer sits between the API layer and repository layer.
    
    All methods are async to support non-blocking operations and return
    API response models rather than database entities.
    """
    
    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """
        Create a new product with business logic validation.
        
        This method handles:
        - Input validation beyond basic Pydantic validation
        - Duplicate SKU detection and error handling
        - Conversion between database entities and API response models
        
        Args:
            product_data: Validated product creation data
            
        Returns:
            ProductResponse: The created product data
            
        Raises:
            DuplicateSKU: If a product with the same SKU already exists
            ValidationError: If business rules are violated
            DatabaseError: If database operation fails
        """
        ...
    
    async def get_all_products(self) -> list[ProductResponse]:
        """
        Retrieve all products with business logic applied.
        
        Returns:
            list[ProductResponse]: List of all products as API response models
            
        Raises:
            DatabaseError: If database operation fails
        """
        ...
    
    async def get_product_by_sku(self, sku: str) -> ProductResponse:
        """
        Retrieve a product by SKU with error handling.
        
        Args:
            sku: The Stock Keeping Unit identifier
            
        Returns:
            ProductResponse: The product data
            
        Raises:
            ProductNotFound: If no product exists with the given SKU
            DatabaseError: If database operation fails
        """
        ...
    
    async def add_stock(self, sku: str, amount: int) -> ProductResponse:
        """
        Add stock to a product with business logic validation.
        
        This method handles:
        - Amount validation (must be positive)
        - Product existence validation
        - Atomic stock addition through repository
        - Error handling and conversion
        
        Args:
            sku: The Stock Keeping Unit identifier
            amount: Amount to add (must be positive)
            
        Returns:
            ProductResponse: Updated product data
            
        Raises:
            ProductNotFound: If no product exists with the given SKU
            ValueError: If amount is not positive
            DatabaseError: If database operation fails
        """
        ...
    
    async def remove_stock(self, sku: str, amount: int) -> ProductResponse:
        """
        Remove stock from a product with safety checks and business logic.
        
        This method handles:
        - Amount validation (must be positive)
        - Product existence validation
        - Insufficient stock detection and error handling
        - Atomic stock removal through repository
        - Error handling and conversion
        
        Args:
            sku: The Stock Keeping Unit identifier
            amount: Amount to remove (must be positive)
            
        Returns:
            ProductResponse: Updated product data
            
        Raises:
            ProductNotFound: If no product exists with the given SKU
            InsufficientStock: If not enough stock is available
            ValueError: If amount is not positive
            DatabaseError: If database operation fails
        """
        ...