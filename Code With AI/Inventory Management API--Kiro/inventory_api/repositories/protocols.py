"""
Repository protocol interfaces for the inventory management system.

This module defines the contracts for data access operations using typing.Protocol,
which allows for easy testing and implementation swapping while maintaining type safety.
"""

from typing import Protocol, Optional
from inventory_api.models.database import Product
from inventory_api.models.api import ProductCreate


class ProductRepositoryProtocol(Protocol):
    """
    Protocol defining the contract for product data access operations.
    
    This protocol follows the Repository pattern, abstracting data access
    operations and enabling dependency inversion. Implementations can use
    different storage backends while maintaining the same interface.
    
    All methods are async to support non-blocking database operations.
    """
    
    async def create_product(self, product_data: ProductCreate) -> Product:
        """
        Create a new product in the repository.
        
        Args:
            product_data: Product creation data with validation
            
        Returns:
            Product: The created product with assigned ID
            
        Raises:
            DuplicateSKU: If a product with the same SKU already exists
            ValidationError: If the product data is invalid
        """
        ...
    
    async def get_all_products(self) -> list[Product]:
        """
        Retrieve all products from the repository.
        
        Returns:
            list[Product]: List of all products, empty list if none exist
        """
        ...
    
    async def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """
        Retrieve a product by its SKU.
        
        Args:
            sku: The Stock Keeping Unit identifier
            
        Returns:
            Product | None: The product if found, None otherwise
        """
        ...
    
    async def add_stock_atomic(self, sku: str, amount: int) -> Optional[Product]:
        """
        Atomically add stock to a product.
        
        This operation must be atomic to prevent race conditions when
        multiple requests attempt to modify the same product simultaneously.
        
        Args:
            sku: The Stock Keeping Unit identifier
            amount: Amount to add (must be positive)
            
        Returns:
            Product | None: Updated product if found, None if product doesn't exist
            
        Raises:
            ValueError: If amount is not positive
        """
        ...
    
    async def remove_stock_atomic(self, sku: str, amount: int) -> Optional[Product]:
        """
        Atomically remove stock from a product with safety checks.
        
        This operation implements the critical read-check-update pattern within
        a transaction to prevent race conditions and ensure stock never goes negative.
        
        The implementation must:
        1. Lock the product row (SELECT FOR UPDATE)
        2. Check if sufficient stock is available
        3. Update the quantity if check passes
        4. Return None if insufficient stock (without modifying the product)
        
        Args:
            sku: The Stock Keeping Unit identifier
            amount: Amount to remove (must be positive)
            
        Returns:
            Product | None: Updated product if successful, None if product doesn't exist
                           or insufficient stock available
            
        Raises:
            ValueError: If amount is not positive
        """
        ...