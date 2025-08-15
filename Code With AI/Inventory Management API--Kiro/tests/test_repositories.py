"""
Unit tests for repository layer operations.

This module tests the repository implementations, focusing on:
- Basic CRUD operations
- Atomic transaction behavior
- Concurrent access scenarios
- Error handling and edge cases
"""

import pytest
import pytest_asyncio

# Configure pytest-asyncio to automatically handle async tests
pytest_asyncio.asyncio_mode = "auto"
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from inventory_api.models.database import Product
from inventory_api.models.api import ProductCreate
from inventory_api.repositories.sqlmodel import SQLModelProductRepository
from inventory_api.core.exceptions import DuplicateSKU


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
async def session(engine):
    """Create test database session."""
    async_session_factory = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def repository(session):
    """Create repository instance for testing."""
    return SQLModelProductRepository(session)


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return ProductCreate(
        sku="TEST-001",
        name="Test Product",
        description="A test product",
        quantity=10
    )


class TestProductRepositoryBasicOperations:
    """Test basic CRUD operations."""
    
    async def test_create_product_success(self, repository, sample_product_data):
        """Test successful product creation."""
        product = await repository.create_product(sample_product_data)
        
        assert product.id is not None
        assert product.sku == sample_product_data.sku
        assert product.name == sample_product_data.name
        assert product.description == sample_product_data.description
        assert product.quantity == sample_product_data.quantity
    
    async def test_create_product_duplicate_sku(self, repository, sample_product_data):
        """Test that creating a product with duplicate SKU raises exception."""
        # Create first product
        await repository.create_product(sample_product_data)
        
        # Attempt to create duplicate should raise exception
        with pytest.raises(DuplicateSKU) as exc_info:
            await repository.create_product(sample_product_data)
        
        assert sample_product_data.sku in str(exc_info.value)
    
    async def test_get_all_products_empty(self, repository):
        """Test getting all products when none exist."""
        products = await repository.get_all_products()
        assert products == []
    
    async def test_get_all_products_with_data(self, repository):
        """Test getting all products when some exist."""
        # Create test products
        product1_data = ProductCreate(sku="TEST-001", name="Product 1", quantity=5)
        product2_data = ProductCreate(sku="TEST-002", name="Product 2", quantity=10)
        
        await repository.create_product(product1_data)
        await repository.create_product(product2_data)
        
        products = await repository.get_all_products()
        
        assert len(products) == 2
        # Should be ordered by SKU
        assert products[0].sku == "TEST-001"
        assert products[1].sku == "TEST-002"
    
    async def test_get_product_by_sku_exists(self, repository, sample_product_data):
        """Test getting a product by SKU when it exists."""
        created_product = await repository.create_product(sample_product_data)
        
        found_product = await repository.get_product_by_sku(sample_product_data.sku)
        
        assert found_product is not None
        assert found_product.id == created_product.id
        assert found_product.sku == sample_product_data.sku
    
    async def test_get_product_by_sku_not_exists(self, repository):
        """Test getting a product by SKU when it doesn't exist."""
        product = await repository.get_product_by_sku("NONEXISTENT")
        assert product is None


class TestStockOperationsAtomic:
    """Test atomic stock operations."""
    
    async def test_add_stock_success(self, repository, sample_product_data):
        """Test successful stock addition."""
        # Create product with initial stock
        created_product = await repository.create_product(sample_product_data)
        initial_quantity = created_product.quantity
        
        # Add stock
        updated_product = await repository.add_stock_atomic(sample_product_data.sku, 5)
        
        assert updated_product is not None
        assert updated_product.quantity == initial_quantity + 5
    
    async def test_add_stock_product_not_found(self, repository):
        """Test adding stock to non-existent product."""
        result = await repository.add_stock_atomic("NONEXISTENT", 5)
        assert result is None
    
    async def test_add_stock_invalid_amount(self, repository, sample_product_data):
        """Test adding invalid (non-positive) stock amount."""
        await repository.create_product(sample_product_data)
        
        with pytest.raises(ValueError, match="Amount must be positive"):
            await repository.add_stock_atomic(sample_product_data.sku, 0)
        
        with pytest.raises(ValueError, match="Amount must be positive"):
            await repository.add_stock_atomic(sample_product_data.sku, -5)
    
    async def test_remove_stock_success(self, repository, sample_product_data):
        """Test successful stock removal."""
        # Create product with initial stock
        created_product = await repository.create_product(sample_product_data)
        initial_quantity = created_product.quantity
        
        # Remove stock
        updated_product = await repository.remove_stock_atomic(sample_product_data.sku, 3)
        
        assert updated_product is not None
        assert updated_product.quantity == initial_quantity - 3
    
    async def test_remove_stock_insufficient(self, repository, sample_product_data):
        """Test removing more stock than available."""
        # Create product with limited stock
        sample_product_data.quantity = 5
        await repository.create_product(sample_product_data)
        
        # Try to remove more than available
        result = await repository.remove_stock_atomic(sample_product_data.sku, 10)
        
        # Should return None (insufficient stock)
        assert result is None
        
        # Verify original quantity unchanged
        product = await repository.get_product_by_sku(sample_product_data.sku)
        assert product.quantity == 5
    
    async def test_remove_stock_exact_amount(self, repository, sample_product_data):
        """Test removing exact available stock amount."""
        # Create product with specific stock
        sample_product_data.quantity = 5
        await repository.create_product(sample_product_data)
        
        # Remove exact amount
        updated_product = await repository.remove_stock_atomic(sample_product_data.sku, 5)
        
        assert updated_product is not None
        assert updated_product.quantity == 0
    
    async def test_remove_stock_product_not_found(self, repository):
        """Test removing stock from non-existent product."""
        result = await repository.remove_stock_atomic("NONEXISTENT", 5)
        assert result is None
    
    async def test_remove_stock_invalid_amount(self, repository, sample_product_data):
        """Test removing invalid (non-positive) stock amount."""
        await repository.create_product(sample_product_data)
        
        with pytest.raises(ValueError, match="Amount must be positive"):
            await repository.remove_stock_atomic(sample_product_data.sku, 0)
        
        with pytest.raises(ValueError, match="Amount must be positive"):
            await repository.remove_stock_atomic(sample_product_data.sku, -5)


class TestConcurrentOperations:
    """Test concurrent access scenarios to verify atomic behavior."""
    
    async def test_concurrent_stock_addition(self, repository, sample_product_data):
        """Test concurrent stock additions are handled atomically."""
        # Create product with initial stock
        await repository.create_product(sample_product_data)
        initial_quantity = sample_product_data.quantity
        
        # Define concurrent add operations
        async def add_stock_task(amount):
            return await repository.add_stock_atomic(sample_product_data.sku, amount)
        
        # Run multiple add operations concurrently
        tasks = [add_stock_task(2) for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        assert all(result is not None for result in results)
        
        # Verify final quantity is correct
        final_product = await repository.get_product_by_sku(sample_product_data.sku)
        expected_quantity = initial_quantity + (2 * 5)  # 5 operations adding 2 each
        assert final_product.quantity == expected_quantity
    
    async def test_concurrent_stock_removal_success(self, repository, sample_product_data):
        """Test concurrent stock removals when sufficient stock exists."""
        # Create product with enough stock for all operations
        sample_product_data.quantity = 20
        await repository.create_product(sample_product_data)
        
        # Define concurrent remove operations
        async def remove_stock_task(amount):
            return await repository.remove_stock_atomic(sample_product_data.sku, amount)
        
        # Run multiple remove operations concurrently (total: 10)
        tasks = [remove_stock_task(2) for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        assert all(result is not None for result in results)
        
        # Verify final quantity is correct
        final_product = await repository.get_product_by_sku(sample_product_data.sku)
        expected_quantity = 20 - (2 * 5)  # 5 operations removing 2 each
        assert final_product.quantity == expected_quantity
    
    async def test_concurrent_stock_removal_race_condition(self, repository, sample_product_data):
        """
        Test the critical race condition scenario: multiple requests trying to buy the last item.
        
        This test simulates the scenario where two customers try to buy the last item
        simultaneously. Only one should succeed, preventing overselling.
        """
        # Create product with only 1 item in stock
        sample_product_data.quantity = 1
        await repository.create_product(sample_product_data)
        
        # Define concurrent remove operations trying to remove 1 item each
        async def remove_last_item():
            return await repository.remove_stock_atomic(sample_product_data.sku, 1)
        
        # Run two operations concurrently trying to get the last item
        results = await asyncio.gather(
            remove_last_item(),
            remove_last_item(),
            return_exceptions=True
        )
        
        # Count successful operations (should be exactly 1)
        successful_operations = [r for r in results if r is not None and not isinstance(r, Exception)]
        failed_operations = [r for r in results if r is None or isinstance(r, Exception)]
        
        assert len(successful_operations) == 1, "Only one operation should succeed"
        assert len(failed_operations) == 1, "One operation should fail"
        
        # Verify final state: quantity should be 0
        final_product = await repository.get_product_by_sku(sample_product_data.sku)
        assert final_product.quantity == 0, "Final quantity should be 0"
    
    async def test_mixed_concurrent_operations(self, repository, sample_product_data):
        """Test concurrent mix of add and remove operations."""
        # Create product with initial stock
        sample_product_data.quantity = 10
        await repository.create_product(sample_product_data)
        
        # Define mixed operations
        async def add_stock():
            return await repository.add_stock_atomic(sample_product_data.sku, 3)
        
        async def remove_stock():
            return await repository.remove_stock_atomic(sample_product_data.sku, 2)
        
        # Run mixed operations concurrently
        tasks = [add_stock(), remove_stock(), add_stock(), remove_stock()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should succeed (we have enough stock)
        successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        assert len(successful_results) == 4
        
        # Verify final quantity: 10 + 3 - 2 + 3 - 2 = 12
        final_product = await repository.get_product_by_sku(sample_product_data.sku)
        assert final_product.quantity == 12


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    async def test_create_product_minimal_data(self, repository):
        """Test creating product with minimal required data."""
        minimal_data = ProductCreate(
            sku="MIN-001",
            name="Minimal Product",
            quantity=0  # Zero stock is valid
        )
        
        product = await repository.create_product(minimal_data)
        
        assert product.sku == "MIN-001"
        assert product.name == "Minimal Product"
        assert product.description is None
        assert product.quantity == 0
    
    async def test_stock_operations_with_zero_quantity(self, repository):
        """Test stock operations on product with zero quantity."""
        # Create product with zero stock
        product_data = ProductCreate(sku="ZERO-001", name="Zero Stock", quantity=0)
        await repository.create_product(product_data)
        
        # Adding to zero stock should work
        result = await repository.add_stock_atomic("ZERO-001", 5)
        assert result is not None
        assert result.quantity == 5
        
        # Removing from zero stock should fail
        result = await repository.remove_stock_atomic("ZERO-001", 1)
        assert result is None  # Should fail due to insufficient stock
    
    async def test_large_quantity_operations(self, repository):
        """Test operations with large quantities."""
        # Create product with large initial quantity
        large_quantity = 1000000
        product_data = ProductCreate(
            sku="LARGE-001", 
            name="Large Quantity Product", 
            quantity=large_quantity
        )
        await repository.create_product(product_data)
        
        # Add large amount
        result = await repository.add_stock_atomic("LARGE-001", 500000)
        assert result is not None
        assert result.quantity == 1500000
        
        # Remove large amount
        result = await repository.remove_stock_atomic("LARGE-001", 750000)
        assert result is not None
        assert result.quantity == 750000