# Atomic Transactions and Race Condition Prevention

This document provides an in-depth explanation of how the Inventory Management API prevents race conditions and maintains data integrity through atomic database transactions.

## 🎯 The Problem: Race Conditions in Inventory Management

### What is a Race Condition?

A race condition occurs when multiple processes or threads access shared data concurrently, and the final result depends on the timing of their execution. In inventory management, this can lead to:

- **Overselling:** Selling more items than available in stock
- **Negative Stock:** Stock levels going below zero
- **Lost Updates:** One transaction overwriting another's changes
- **Data Inconsistency:** Database state not reflecting actual business state

### Real-World Scenario

Consider this scenario with a product that has only 1 item in stock:

```
Initial State: Product "LAPTOP-001" has quantity = 1

Timeline:
T1: Customer A requests to buy 1 laptop
T2: Customer B requests to buy 1 laptop (almost simultaneously)

Without Proper Locking:
T1: Read quantity = 1 ✓ (sufficient stock)
T2: Read quantity = 1 ✓ (sufficient stock) 
T1: Update quantity = 0 ✓ (customer A gets the laptop)
T2: Update quantity = 0 ✓ (customer B also gets the laptop!)

Result: 2 laptops sold, but only 1 was in stock!
```

## 🔒 The Solution: Atomic Transactions with Row Locking

### Database-Level Locking

Our solution uses **SELECT FOR UPDATE** to implement row-level locking:

```python
async def remove_stock_atomic(self, sku: str, amount: int) -> Optional[Product]:
    """
    Atomically remove stock from a product with race condition prevention.
    
    This method implements the critical read-check-update pattern within
    a transaction to prevent race conditions and ensure stock never goes negative.
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    # 🔒 CRITICAL: SELECT FOR UPDATE locks the row until transaction completes
    # This prevents other transactions from reading or modifying the same product
    stmt = select(Product).where(Product.sku == sku).with_for_update()
    result = await self.session.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        return None  # Product doesn't exist
    
    # ✅ SAFETY CHECK: Verify sufficient stock while holding the lock
    # This check happens within the transaction, so no other process
    # can modify the quantity between the check and the update
    if product.quantity < amount:
        # Don't modify anything - insufficient stock
        # Transaction will be rolled back automatically
        return None
    
    # 🎯 SAFE UPDATE: We have the lock and sufficient stock
    product.quantity -= amount
    await self.session.commit()  # Releases the lock
    return product
```

### How SELECT FOR UPDATE Works

1. **Acquire Lock:** `SELECT ... FOR UPDATE` places an exclusive lock on the selected row(s)
2. **Block Concurrent Access:** Other transactions attempting to read the same row with `FOR UPDATE` will wait
3. **Perform Operations:** Read, validate, and update within the same transaction
4. **Release Lock:** `COMMIT` or `ROLLBACK` releases the lock

### The Corrected Scenario

With proper locking, the same scenario plays out differently:

```
Initial State: Product "LAPTOP-001" has quantity = 1

Timeline with Atomic Transactions:
T1: Customer A requests to buy 1 laptop
T2: Customer B requests to buy 1 laptop

T1: SELECT ... FOR UPDATE (acquires lock on LAPTOP-001)
T2: SELECT ... FOR UPDATE (waits for T1 to complete)
T1: Read quantity = 1 ✓ (sufficient stock)
T1: Update quantity = 0 ✓ 
T1: COMMIT (releases lock, customer A gets the laptop)
T2: Now proceeds with the lock
T2: Read quantity = 0 ❌ (insufficient stock)
T2: Return error without modifying data
T2: ROLLBACK (customer B gets "insufficient stock" error)

Result: 1 laptop sold to customer A, customer B gets proper error message
```

## 🏗️ Implementation Architecture

### Repository Layer: Data Access with Locking

The repository layer handles all database interactions and implements the atomic operations:

```python
class SQLModelProductRepository:
    """
    Repository implementation with atomic transaction support.
    
    Key responsibilities:
    - Database connection management
    - Row-level locking for concurrent safety
    - Transaction boundary management
    - Error handling and rollback logic
    """
    
    async def add_stock_atomic(self, sku: str, amount: int) -> Optional[Product]:
        """
        Atomic stock addition - simpler case since we're only adding.
        
        Even though addition doesn't risk negative values, we still use
        locking to ensure consistency and prevent lost updates.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Lock the row to prevent concurrent modifications
        stmt = select(Product).where(Product.sku == sku).with_for_update()
        result = await self.session.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            return None
        
        # Safe to add - no business logic constraints to check
        product.quantity += amount
        await self.session.commit()
        return product
    
    async def remove_stock_atomic(self, sku: str, amount: int) -> Optional[Product]:
        """
        Atomic stock removal - the critical operation that needs safety checks.
        
        This is where race conditions are most dangerous, so we implement
        the full read-check-update pattern with proper locking.
        """
        # Implementation shown above
        pass
```

### Service Layer: Business Logic and Error Handling

The service layer coordinates repository operations and handles business logic:

```python
class ProductService:
    """
    Service layer that orchestrates business operations.
    
    Responsibilities:
    - Business rule validation
    - Error handling and translation
    - Transaction coordination
    - Response formatting
    """
    
    async def remove_stock(self, sku: str, amount: int) -> ProductResponse:
        """
        Business logic for stock removal with comprehensive error handling.
        """
        # Validate business rules
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Delegate to repository for atomic operation
        product = await self.repository.remove_stock_atomic(sku, amount)
        
        if not product:
            # Check if product exists to provide specific error
            existing_product = await self.repository.get_product_by_sku(sku)
            if not existing_product:
                raise ProductNotFound(sku)
            else:
                # Product exists but insufficient stock
                raise InsufficientStock(sku, amount, existing_product.quantity)
        
        # Convert to response model
        return ProductResponse.model_validate(product)
```

## 🧪 Testing Atomic Operations

### Unit Tests for Race Conditions

We test atomic operations using concurrent execution:

```python
import asyncio
import pytest
from inventory_api.core.exceptions import InsufficientStock

@pytest.mark.asyncio
async def test_concurrent_stock_removal_prevents_overselling():
    """
    Test that concurrent stock removal operations don't cause race conditions.
    
    This test simulates the exact scenario described above:
    Two customers trying to buy the last item simultaneously.
    """
    # Setup: Create product with quantity 1
    await create_test_product(sku="RACE-TEST-001", quantity=1)
    
    async def attempt_purchase():
        """Simulate a customer attempting to purchase the item."""
        try:
            return await product_service.remove_stock("RACE-TEST-001", 1)
        except InsufficientStock:
            return None  # Purchase failed
    
    # Execute two purchase attempts concurrently
    results = await asyncio.gather(
        attempt_purchase(),
        attempt_purchase(),
        return_exceptions=True
    )
    
    # Verify: Exactly one purchase should succeed
    successful_purchases = [r for r in results if r is not None and not isinstance(r, Exception)]
    assert len(successful_purchases) == 1, "Only one purchase should succeed"
    
    # Verify final state: quantity should be 0, not negative
    final_product = await product_service.get_product_by_sku("RACE-TEST-001")
    assert final_product.quantity == 0, "Final quantity should be 0"

@pytest.mark.asyncio
async def test_high_concurrency_stock_operations():
    """
    Test atomic operations under high concurrency load.
    """
    # Setup: Create product with quantity 100
    await create_test_product(sku="STRESS-TEST-001", quantity=100)
    
    async def remove_random_stock():
        """Remove a random amount of stock (1-5 items)."""
        import random
        amount = random.randint(1, 5)
        try:
            return await product_service.remove_stock("STRESS-TEST-001", amount)
        except InsufficientStock:
            return None
    
    # Execute 50 concurrent operations
    tasks = [remove_random_stock() for _ in range(50)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify: Final quantity should never be negative
    final_product = await product_service.get_product_by_sku("STRESS-TEST-001")
    assert final_product.quantity >= 0, "Quantity should never go negative"
    
    # Verify: Total removed should equal initial - final
    successful_operations = [r for r in results if r is not None and not isinstance(r, Exception)]
    total_removed = sum(100 - r.quantity for r in successful_operations if hasattr(r, 'quantity'))
    expected_final = 100 - total_removed
    assert final_product.quantity == expected_final, "Stock accounting should be accurate"
```

### Integration Tests with Real Database

```python
@pytest.mark.asyncio
async def test_database_transaction_rollback():
    """
    Test that failed operations properly roll back database changes.
    """
    # Setup: Create product with quantity 5
    await create_test_product(sku="ROLLBACK-TEST-001", quantity=5)
    
    # Attempt to remove more stock than available
    with pytest.raises(InsufficientStock):
        await product_service.remove_stock("ROLLBACK-TEST-001", 10)
    
    # Verify: Quantity should be unchanged
    product = await product_service.get_product_by_sku("ROLLBACK-TEST-001")
    assert product.quantity == 5, "Quantity should be unchanged after failed operation"

@pytest.mark.asyncio
async def test_database_constraint_enforcement():
    """
    Test that database constraints prevent negative quantities.
    """
    # This test verifies our database-level safety net
    # Even if application logic fails, database constraints should prevent negative values
    
    # Setup: Create product with quantity 1
    product = await create_test_product(sku="CONSTRAINT-TEST-001", quantity=1)
    
    # Attempt to directly set negative quantity (bypassing business logic)
    with pytest.raises(Exception):  # Should raise constraint violation
        async with get_db_session() as session:
            stmt = select(Product).where(Product.sku == "CONSTRAINT-TEST-001")
            result = await session.execute(stmt)
            product = result.scalar_one()
            product.quantity = -1  # This should violate the CHECK constraint
            await session.commit()
```

## 🔍 Monitoring and Debugging

### Logging Atomic Operations

```python
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@asynccontextmanager
async def logged_transaction(session: AsyncSession, operation: str, sku: str):
    """
    Context manager for logging transaction operations.
    """
    transaction_id = f"{operation}-{sku}-{time.time()}"
    logger.info(f"Starting transaction {transaction_id}")
    
    try:
        async with session.begin():
            yield transaction_id
        logger.info(f"Transaction {transaction_id} committed successfully")
    except Exception as e:
        logger.error(f"Transaction {transaction_id} failed: {str(e)}")
        raise

async def remove_stock_atomic_with_logging(self, sku: str, amount: int) -> Optional[Product]:
    """
    Enhanced version with detailed logging for debugging.
    """
    async with logged_transaction(self.session, "remove_stock", sku) as tx_id:
        logger.debug(f"{tx_id}: Acquiring lock for product {sku}")
        
        stmt = select(Product).where(Product.sku == sku).with_for_update()
        result = await self.session.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            logger.warning(f"{tx_id}: Product {sku} not found")
            return None
        
        logger.debug(f"{tx_id}: Current quantity: {product.quantity}, requested: {amount}")
        
        if product.quantity < amount:
            logger.warning(f"{tx_id}: Insufficient stock - available: {product.quantity}, requested: {amount}")
            return None
        
        product.quantity -= amount
        logger.info(f"{tx_id}: Updated quantity from {product.quantity + amount} to {product.quantity}")
        
        return product
```

### Performance Monitoring

```python
import time
from functools import wraps

def monitor_transaction_time(func):
    """
    Decorator to monitor transaction execution time.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} completed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {str(e)}")
            raise
    return wrapper

@monitor_transaction_time
async def remove_stock_atomic(self, sku: str, amount: int) -> Optional[Product]:
    # Implementation here
    pass
```

## 🚀 Production Considerations

### Database Configuration

For production deployments, consider these database settings:

```sql
-- PostgreSQL example
-- Adjust lock timeout to prevent indefinite waiting
SET lock_timeout = '30s';

-- Configure deadlock detection
SET deadlock_timeout = '1s';

-- Monitor lock contention
SELECT * FROM pg_locks WHERE NOT granted;
```

### Connection Pooling

```python
from sqlalchemy.pool import QueuePool

# Configure connection pool for high concurrency
engine = create_async_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=20,          # Number of connections to maintain
    max_overflow=30,       # Additional connections under load
    pool_timeout=30,       # Timeout for getting connection
    pool_recycle=3600,     # Recycle connections every hour
)
```

### Monitoring and Alerting

```python
# Metrics collection for monitoring
class TransactionMetrics:
    def __init__(self):
        self.lock_wait_times = []
        self.transaction_durations = []
        self.failed_transactions = 0
        self.successful_transactions = 0
    
    def record_lock_wait(self, duration: float):
        self.lock_wait_times.append(duration)
    
    def record_transaction(self, duration: float, success: bool):
        self.transaction_durations.append(duration)
        if success:
            self.successful_transactions += 1
        else:
            self.failed_transactions += 1
    
    def get_stats(self):
        return {
            "avg_lock_wait": sum(self.lock_wait_times) / len(self.lock_wait_times) if self.lock_wait_times else 0,
            "avg_transaction_time": sum(self.transaction_durations) / len(self.transaction_durations) if self.transaction_durations else 0,
            "success_rate": self.successful_transactions / (self.successful_transactions + self.failed_transactions) if (self.successful_transactions + self.failed_transactions) > 0 else 0
        }
```

## 📚 Further Reading

### Database Concepts
- **ACID Properties:** Atomicity, Consistency, Isolation, Durability
- **Isolation Levels:** Read Uncommitted, Read Committed, Repeatable Read, Serializable
- **Lock Types:** Shared locks, Exclusive locks, Row-level vs Table-level
- **Deadlock Detection:** How databases detect and resolve deadlocks

### SQLAlchemy Documentation
- [Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [Transactions and Connection Management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
- [SELECT FOR UPDATE](https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.Select.with_for_update)

### Best Practices
- **Minimize Lock Duration:** Keep transactions as short as possible
- **Consistent Lock Ordering:** Always acquire locks in the same order to prevent deadlocks
- **Timeout Configuration:** Set appropriate timeouts for lock acquisition
- **Monitoring:** Track lock contention and transaction performance
- **Testing:** Thoroughly test concurrent scenarios

## 🎯 Summary

The atomic transaction implementation in this API provides:

1. **Race Condition Prevention:** SELECT FOR UPDATE ensures serialized access to critical data
2. **Data Integrity:** Read-check-update pattern prevents invalid state transitions
3. **Automatic Rollback:** Failed operations don't leave the database in an inconsistent state
4. **Scalability:** Row-level locking allows concurrent operations on different products
5. **Reliability:** Database constraints provide an additional safety net

This approach ensures that even under high concurrency, the inventory system maintains accurate stock levels and prevents overselling, making it suitable for production e-commerce applications.