"""
Product service implementation with business logic and error handling.

This module implements the ProductServiceProtocol, providing business logic
for product management operations including validation, error handling,
and coordination between the API and repository layers.
"""

from typing import Optional
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from inventory_api.models.api import ProductCreate, ProductResponse
from inventory_api.models.database import Product
from inventory_api.repositories.protocols import ProductRepositoryProtocol
from inventory_api.core.exceptions import (
    ProductNotFound,
    InsufficientStock,
    DuplicateSKU,
    DatabaseError
)


class ProductService:
    """
    Concrete implementation of product business logic.
    
    This service handles all business operations for products, including:
    - Input validation beyond basic Pydantic validation
    - Error handling and exception translation
    - Coordination between API models and repository operations
    - Business rule enforcement
    
    The service depends on a repository implementation through dependency injection,
    following the Dependency Inversion Principle.
    """
    
    def __init__(self, repository: ProductRepositoryProtocol):
        """
        Initialize the service with a repository dependency.
        
        Args:
            repository: Repository implementation for data access
        """
        self.repository = repository
    
    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """
        Create a new product with comprehensive error handling.
        
        This method implements business logic for product creation:
        1. Validates input data (already done by Pydantic)
        2. Attempts to create the product through repository
        3. Handles duplicate SKU errors
        4. Converts database entity to API response model
        
        Args:
            product_data: Validated product creation data
            
        Returns:
            ProductResponse: The created product data
            
        Raises:
            DuplicateSKU: If a product with the same SKU already exists
            DatabaseError: If database operation fails
        """
        try:
            # Attempt to create the product through repository
            product = await self.repository.create_product(product_data)
            
            # Convert database entity to API response model
            return ProductResponse(
                sku=product.sku,
                name=product.name,
                description=product.description,
                quantity=product.quantity
            )
            
        except IntegrityError as e:
            # Handle duplicate SKU constraint violation
            if "UNIQUE constraint failed" in str(e.orig) and "sku" in str(e.orig):
                raise DuplicateSKU(product_data.sku)
            # Re-raise as database error for other integrity issues
            raise DatabaseError("product creation", e)
            
        except SQLAlchemyError as e:
            # Handle other database errors
            raise DatabaseError("product creation", e)
    
    async def get_all_products(self) -> list[ProductResponse]:
        """
        Retrieve all products with error handling.
        
        Returns:
            list[ProductResponse]: List of all products as API response models
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            products = await self.repository.get_all_products()
            
            # Convert database entities to API response models
            return [
                ProductResponse(
                    sku=product.sku,
                    name=product.name,
                    description=product.description,
                    quantity=product.quantity
                )
                for product in products
            ]
            
        except SQLAlchemyError as e:
            raise DatabaseError("product retrieval", e)
    
    async def get_product_by_sku(self, sku: str) -> ProductResponse:
        """
        Retrieve a product by SKU with comprehensive error handling.
        
        Args:
            sku: The Stock Keeping Unit identifier
            
        Returns:
            ProductResponse: The product data
            
        Raises:
            ProductNotFound: If no product exists with the given SKU
            DatabaseError: If database operation fails
        """
        try:
            product = await self.repository.get_product_by_sku(sku)
            
            if product is None:
                raise ProductNotFound(sku)
            
            # Convert database entity to API response model
            return ProductResponse(
                sku=product.sku,
                name=product.name,
                description=product.description,
                quantity=product.quantity
            )
            
        except ProductNotFound:
            # Re-raise ProductNotFound as-is
            raise
            
        except SQLAlchemyError as e:
            raise DatabaseError("product retrieval", e)
    
    async def add_stock(self, sku: str, amount: int) -> ProductResponse:
        """
        Add stock to a product with comprehensive validation and error handling.
        
        This method implements business logic for stock addition:
        1. Validates amount is positive
        2. Attempts atomic stock addition through repository
        3. Handles product not found errors
        4. Converts result to API response model
        
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
        # Business rule validation
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        try:
            # Attempt atomic stock addition
            product = await self.repository.add_stock_atomic(sku, amount)
            
            if product is None:
                raise ProductNotFound(sku)
            
            # Convert database entity to API response model
            return ProductResponse(
                sku=product.sku,
                name=product.name,
                description=product.description,
                quantity=product.quantity
            )
            
        except ProductNotFound:
            # Re-raise ProductNotFound as-is
            raise
            
        except ValueError:
            # Re-raise ValueError as-is (from amount validation)
            raise
            
        except SQLAlchemyError as e:
            raise DatabaseError("stock addition", e)
    
    async def remove_stock(self, sku: str, amount: int) -> ProductResponse:
        """
        Remove stock from a product with comprehensive validation and error handling.
        
        This method implements critical business logic for stock removal:
        1. Validates amount is positive
        2. Attempts atomic stock removal through repository
        3. Handles product not found errors
        4. Handles insufficient stock errors
        5. Converts result to API response model
        
        The repository handles the atomic read-check-update pattern to prevent
        race conditions and ensure stock never goes negative.
        
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
        # Business rule validation
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        try:
            # First, get the current product to check stock levels for error reporting
            current_product = await self.repository.get_product_by_sku(sku)
            
            if current_product is None:
                raise ProductNotFound(sku)
            
            # Attempt atomic stock removal
            updated_product = await self.repository.remove_stock_atomic(sku, amount)
            
            if updated_product is None:
                # Repository returned None, meaning insufficient stock
                # We already know the product exists, so this must be insufficient stock
                raise InsufficientStock(sku, amount, current_product.quantity)
            
            # Convert database entity to API response model
            return ProductResponse(
                sku=updated_product.sku,
                name=updated_product.name,
                description=updated_product.description,
                quantity=updated_product.quantity
            )
            
        except (ProductNotFound, InsufficientStock, ValueError):
            # Re-raise these exceptions as-is
            raise
            
        except SQLAlchemyError as e:
            raise DatabaseError("stock removal", e)
    
    def _convert_to_response(self, product: Product) -> ProductResponse:
        """
        Helper method to convert database entity to API response model.
        
        This method centralizes the conversion logic and ensures consistency
        across all service methods.
        
        Args:
            product: Database product entity
            
        Returns:
            ProductResponse: API response model
        """
        return ProductResponse(
            sku=product.sku,
            name=product.name,
            description=product.description,
            quantity=product.quantity
        )