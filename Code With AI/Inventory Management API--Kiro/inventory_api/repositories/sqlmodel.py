"""
SQLModel repository implementation with atomic transaction support.

This module provides the concrete implementation of the ProductRepositoryProtocol
using SQLModel/SQLAlchemy with proper async support and atomic operations.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel

from inventory_api.models.database import Product
from inventory_api.models.api import ProductCreate
from inventory_api.core.exceptions import DuplicateSKU


class SQLModelProductRepository:
    """
    SQLModel implementation of the ProductRepositoryProtocol.
    
    This class handles all database operations using SQLModel/SQLAlchemy
    with emphasis on atomic transactions for stock operations to prevent
    race conditions and maintain data integrity.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.
        
        Args:
            session: Async SQLAlchemy session for database operations
        """
        self.session = session
    
    async def create_product(self, product_data: ProductCreate) -> Product:
        """
        Create a new product in the database.
        
        Args:
            product_data: Validated product creation data
            
        Returns:
            Product: The created product with assigned database ID
            
        Raises:
            DuplicateSKU: If a product with the same SKU already exists
        """
        # Create Product instance from the validated input data
        product = Product(
            sku=product_data.sku,
            name=product_data.name,
            description=product_data.description,
            quantity=product_data.quantity
        )
        
        try:
            self.session.add(product)
            await self.session.commit()
            await self.session.refresh(product)  # Get the assigned ID
            return product
        except IntegrityError as e:
            await self.session.rollback()
            # Check if this is a duplicate SKU error
            if "UNIQUE constraint failed" in str(e) or "sku" in str(e).lower():
                raise DuplicateSKU(product_data.sku)
            raise  # Re-raise other integrity errors
    
    async def get_all_products(self) -> list[Product]:
        """
        Retrieve all products from the database.
        
        Returns:
            list[Product]: List of all products, ordered by SKU for consistency
        """
        stmt = select(Product).order_by(Product.sku)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """
        Retrieve a product by its SKU.
        
        Args:
            sku: The Stock Keeping Unit identifier
            
        Returns:
            Product | None: The product if found, None otherwise
        """
        stmt = select(Product).where(Product.sku == sku)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def add_stock_atomic(self, sku: str, amount: int) -> Optional[Product]:
        """
        Atomically add stock to a product with race condition prevention.
        
        Even though stock addition doesn't risk negative values, we still use
        atomic transactions to prevent lost updates and ensure data consistency.
        
        ATOMIC TRANSACTION PATTERN:
        1. Begin transaction (implicit with session)
        2. SELECT FOR UPDATE - locks the product row
        3. Verify product exists
        4. Update quantity (safe operation - only adding)
        5. COMMIT - releases lock and persists changes
        
        RACE CONDITION SCENARIO PREVENTED:
        - Request A: Add 10 items (reads quantity=50)
        - Request B: Add 5 items (reads quantity=50) 
        - Without locking: Both update based on 50, result could be 55 or 60
        - With locking: Serialized execution ensures result is always 65
        
        Args:
            sku: The Stock Keeping Unit identifier
            amount: Amount to add (must be positive)
            
        Returns:
            Product | None: Updated product if found, None if product doesn't exist
            
        Raises:
            ValueError: If amount is not positive
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # 🔒 CRITICAL: SELECT FOR UPDATE acquires an exclusive lock on the product row
        # This lock is held until the transaction completes (COMMIT or ROLLBACK)
        # Other transactions attempting to SELECT FOR UPDATE on the same row will wait
        stmt = select(Product).where(Product.sku == sku).with_for_update()
        result = await self.session.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            # Product doesn't exist - return None without modifying anything
            # Transaction will be rolled back automatically
            return None
        
        # ✅ SAFE UPDATE: We have exclusive access to this product row
        # No other transaction can read or modify this product until we commit
        product.quantity += amount
        
        # 💾 COMMIT: Persists changes and releases the lock
        # Other waiting transactions can now proceed
        await self.session.commit()
        return product
    
    async def remove_stock_atomic(self, sku: str, amount: int) -> Optional[Product]:
        """
        Atomically remove stock from a product with comprehensive safety checks.
        
        This method implements the critical READ-CHECK-UPDATE pattern within
        a database transaction to prevent race conditions and ensure stock never goes negative.
        This is the most important method for preventing overselling in e-commerce scenarios.
        
        ATOMIC TRANSACTION PATTERN (Read-Check-Update):
        1. Begin transaction (implicit with session)
        2. SELECT FOR UPDATE - locks the product row exclusively
        3. Verify product exists
        4. CHECK: Ensure sufficient stock is available
        5. UPDATE: Decrease quantity only if check passes
        6. COMMIT: Release lock and persist changes
        
        RACE CONDITION SCENARIO PREVENTED:
        Initial state: Product has quantity = 1
        - Customer A: Wants to buy 1 item
        - Customer B: Wants to buy 1 item (simultaneously)
        
        WITHOUT ATOMIC TRANSACTIONS:
        T1: A reads quantity=1 ✓ (sufficient)    T2: B reads quantity=1 ✓ (sufficient)
        T1: A updates quantity=0 ✓               T2: B updates quantity=0 ✓
        Result: Both customers get the item, but stock is oversold!
        
        WITH ATOMIC TRANSACTIONS:
        T1: A locks row, reads quantity=1 ✓      T2: B waits for lock...
        T1: A updates quantity=0 ✓, commits     T2: B gets lock, reads quantity=0 ❌
        T1: Lock released                        T2: B gets "insufficient stock" error
        Result: Only A gets the item, B gets proper error message
        
        Args:
            sku: The Stock Keeping Unit identifier
            amount: Amount to remove (must be positive)
            
        Returns:
            Product | None: Updated product if successful, None if product doesn't exist
                           or insufficient stock available
            
        Raises:
            ValueError: If amount is not positive
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # 🔒 CRITICAL SECTION START: Acquire exclusive lock on product row
        # SELECT FOR UPDATE prevents other transactions from reading or modifying
        # this specific product until our transaction completes
        # This is the foundation of our race condition prevention
        stmt = select(Product).where(Product.sku == sku).with_for_update()
        result = await self.session.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            # Product doesn't exist - return None without modifying anything
            # Transaction will be rolled back automatically
            return None
        
        # 🛡️ SAFETY CHECK: Verify sufficient stock while holding the lock
        # This is the critical check that prevents overselling
        # Because we hold the lock, no other transaction can modify the quantity
        # between this check and the update below
        if product.quantity < amount:
            # ❌ INSUFFICIENT STOCK: Don't modify anything
            # Return None to signal insufficient stock
            # The transaction will be rolled back automatically
            # The lock will be released, allowing other transactions to proceed
            return None
        
        # ✅ SAFE UPDATE: We have verified sufficient stock and hold the exclusive lock
        # No other transaction can interfere with this update
        product.quantity -= amount
        
        # 💾 COMMIT: Persist changes and release the lock
        # This makes the stock reduction visible to other transactions
        # Other waiting transactions can now proceed with the updated quantity
        await self.session.commit()
        
        # 🔒 CRITICAL SECTION END: Lock is released, other transactions can proceed
        return product