"""
Unit tests for the service layer.

These tests verify business logic, error handling, and the interaction
between services and repositories using mocks to isolate the service layer.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from inventory_api.services.product import ProductService
from inventory_api.models.api import ProductCreate, ProductResponse
from inventory_api.models.database import Product
from inventory_api.core.exceptions import (
    ProductNotFound,
    InsufficientStock,
    DuplicateSKU,
    DatabaseError
)


# Global fixtures for all test classes
@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    return AsyncMock()

@pytest.fixture
def service(mock_repository):
    """Create a ProductService instance with mocked repository."""
    return ProductService(mock_repository)

@pytest.fixture
def sample_product_create():
    """Sample product creation data."""
    return ProductCreate(
        sku="TEST-001",
        name="Test Product",
        description="A test product",
        quantity=10
    )

@pytest.fixture
def sample_product_entity():
    """Sample product database entity."""
    return Product(
        id=1,
        sku="TEST-001",
        name="Test Product",
        description="A test product",
        quantity=10
    )

@pytest.fixture
def sample_product_response():
    """Sample product response model."""
    return ProductResponse(
        sku="TEST-001",
        name="Test Product",
        description="A test product",
        quantity=10
    )


class TestProductService:
    """Test suite for ProductService business logic."""
    pass


class TestCreateProduct:
    """Tests for product creation business logic."""
    
    @pytest.mark.asyncio
    async def test_create_product_success(self, service, mock_repository, 
                                        sample_product_create, sample_product_entity):
        """Test successful product creation."""
        # Arrange
        mock_repository.create_product.return_value = sample_product_entity
        
        # Act
        result = await service.create_product(sample_product_create)
        
        # Assert
        assert isinstance(result, ProductResponse)
        assert result.sku == "TEST-001"
        assert result.name == "Test Product"
        assert result.description == "A test product"
        assert result.quantity == 10
        mock_repository.create_product.assert_called_once_with(sample_product_create)
    
    @pytest.mark.asyncio
    async def test_create_product_duplicate_sku(self, service, mock_repository, 
                                              sample_product_create):
        """Test product creation with duplicate SKU."""
        # Arrange
        orig_error = Mock()
        orig_error.__str__ = Mock(return_value="UNIQUE constraint failed: product.sku")
        integrity_error = IntegrityError("statement", "params", orig_error)
        mock_repository.create_product.side_effect = integrity_error
        
        # Act & Assert
        with pytest.raises(DuplicateSKU) as exc_info:
            await service.create_product(sample_product_create)
        
        assert exc_info.value.sku == "TEST-001"
        mock_repository.create_product.assert_called_once_with(sample_product_create)
    
    @pytest.mark.asyncio
    async def test_create_product_other_integrity_error(self, service, mock_repository, 
                                                      sample_product_create):
        """Test product creation with non-duplicate integrity error."""
        # Arrange
        orig_error = Mock()
        orig_error.__str__ = Mock(return_value="CHECK constraint failed")
        integrity_error = IntegrityError("statement", "params", orig_error)
        mock_repository.create_product.side_effect = integrity_error
        
        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await service.create_product(sample_product_create)
        
        assert exc_info.value.operation == "product creation"
        mock_repository.create_product.assert_called_once_with(sample_product_create)
    
    @pytest.mark.asyncio
    async def test_create_product_database_error(self, service, mock_repository, 
                                                sample_product_create):
        """Test product creation with general database error."""
        # Arrange
        db_error = SQLAlchemyError("Database connection failed")
        mock_repository.create_product.side_effect = db_error
        
        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await service.create_product(sample_product_create)
        
        assert exc_info.value.operation == "product creation"
        mock_repository.create_product.assert_called_once_with(sample_product_create)


class TestGetAllProducts:
    """Tests for retrieving all products."""
    
    @pytest.mark.asyncio
    async def test_get_all_products_success(self, service, mock_repository):
        """Test successful retrieval of all products."""
        # Arrange
        products = [
            Product(id=1, sku="TEST-001", name="Product 1", description="Desc 1", quantity=10),
            Product(id=2, sku="TEST-002", name="Product 2", description=None, quantity=5)
        ]
        mock_repository.get_all_products.return_value = products
        
        # Act
        result = await service.get_all_products()
        
        # Assert
        assert len(result) == 2
        assert all(isinstance(p, ProductResponse) for p in result)
        assert result[0].sku == "TEST-001"
        assert result[1].sku == "TEST-002"
        mock_repository.get_all_products.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_products_empty(self, service, mock_repository):
        """Test retrieval when no products exist."""
        # Arrange
        mock_repository.get_all_products.return_value = []
        
        # Act
        result = await service.get_all_products()
        
        # Assert
        assert result == []
        mock_repository.get_all_products.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_products_database_error(self, service, mock_repository):
        """Test retrieval with database error."""
        # Arrange
        db_error = SQLAlchemyError("Connection timeout")
        mock_repository.get_all_products.side_effect = db_error
        
        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await service.get_all_products()
        
        assert exc_info.value.operation == "product retrieval"


class TestGetProductBySku:
    """Tests for retrieving a product by SKU."""
    
    @pytest.mark.asyncio
    async def test_get_product_by_sku_success(self, service, mock_repository, 
                                            sample_product_entity):
        """Test successful product retrieval by SKU."""
        # Arrange
        mock_repository.get_product_by_sku.return_value = sample_product_entity
        
        # Act
        result = await service.get_product_by_sku("TEST-001")
        
        # Assert
        assert isinstance(result, ProductResponse)
        assert result.sku == "TEST-001"
        mock_repository.get_product_by_sku.assert_called_once_with("TEST-001")
    
    @pytest.mark.asyncio
    async def test_get_product_by_sku_not_found(self, service, mock_repository):
        """Test product retrieval when product doesn't exist."""
        # Arrange
        mock_repository.get_product_by_sku.return_value = None
        
        # Act & Assert
        with pytest.raises(ProductNotFound) as exc_info:
            await service.get_product_by_sku("NONEXISTENT")
        
        assert exc_info.value.sku == "NONEXISTENT"
        mock_repository.get_product_by_sku.assert_called_once_with("NONEXISTENT")
    
    @pytest.mark.asyncio
    async def test_get_product_by_sku_database_error(self, service, mock_repository):
        """Test product retrieval with database error."""
        # Arrange
        db_error = SQLAlchemyError("Query failed")
        mock_repository.get_product_by_sku.side_effect = db_error
        
        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await service.get_product_by_sku("TEST-001")
        
        assert exc_info.value.operation == "product retrieval"


class TestAddStock:
    """Tests for adding stock to products."""
    
    @pytest.mark.asyncio
    async def test_add_stock_success(self, service, mock_repository):
        """Test successful stock addition."""
        # Arrange
        updated_product = Product(id=1, sku="TEST-001", name="Test Product", 
                                description="A test product", quantity=15)
        mock_repository.add_stock_atomic.return_value = updated_product
        
        # Act
        result = await service.add_stock("TEST-001", 5)
        
        # Assert
        assert isinstance(result, ProductResponse)
        assert result.quantity == 15
        mock_repository.add_stock_atomic.assert_called_once_with("TEST-001", 5)
    
    @pytest.mark.asyncio
    async def test_add_stock_product_not_found(self, service, mock_repository):
        """Test stock addition when product doesn't exist."""
        # Arrange
        mock_repository.add_stock_atomic.return_value = None
        
        # Act & Assert
        with pytest.raises(ProductNotFound) as exc_info:
            await service.add_stock("NONEXISTENT", 5)
        
        assert exc_info.value.sku == "NONEXISTENT"
    
    @pytest.mark.asyncio
    async def test_add_stock_invalid_amount_zero(self, service, mock_repository):
        """Test stock addition with zero amount."""
        # Act & Assert
        with pytest.raises(ValueError, match="Amount must be positive"):
            await service.add_stock("TEST-001", 0)
        
        # Repository should not be called
        mock_repository.add_stock_atomic.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_add_stock_invalid_amount_negative(self, service, mock_repository):
        """Test stock addition with negative amount."""
        # Act & Assert
        with pytest.raises(ValueError, match="Amount must be positive"):
            await service.add_stock("TEST-001", -5)
        
        # Repository should not be called
        mock_repository.add_stock_atomic.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_add_stock_database_error(self, service, mock_repository):
        """Test stock addition with database error."""
        # Arrange
        db_error = SQLAlchemyError("Transaction failed")
        mock_repository.add_stock_atomic.side_effect = db_error
        
        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await service.add_stock("TEST-001", 5)
        
        assert exc_info.value.operation == "stock addition"


class TestRemoveStock:
    """Tests for removing stock from products."""
    
    @pytest.mark.asyncio
    async def test_remove_stock_success(self, service, mock_repository):
        """Test successful stock removal."""
        # Arrange
        current_product = Product(id=1, sku="TEST-001", name="Test Product", 
                                description="A test product", quantity=10)
        updated_product = Product(id=1, sku="TEST-001", name="Test Product", 
                                description="A test product", quantity=7)
        
        mock_repository.get_product_by_sku.return_value = current_product
        mock_repository.remove_stock_atomic.return_value = updated_product
        
        # Act
        result = await service.remove_stock("TEST-001", 3)
        
        # Assert
        assert isinstance(result, ProductResponse)
        assert result.quantity == 7
        mock_repository.get_product_by_sku.assert_called_once_with("TEST-001")
        mock_repository.remove_stock_atomic.assert_called_once_with("TEST-001", 3)
    
    @pytest.mark.asyncio
    async def test_remove_stock_product_not_found(self, service, mock_repository):
        """Test stock removal when product doesn't exist."""
        # Arrange
        mock_repository.get_product_by_sku.return_value = None
        
        # Act & Assert
        with pytest.raises(ProductNotFound) as exc_info:
            await service.remove_stock("NONEXISTENT", 3)
        
        assert exc_info.value.sku == "NONEXISTENT"
        mock_repository.get_product_by_sku.assert_called_once_with("NONEXISTENT")
        mock_repository.remove_stock_atomic.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_remove_stock_insufficient_stock(self, service, mock_repository):
        """Test stock removal with insufficient stock."""
        # Arrange
        current_product = Product(id=1, sku="TEST-001", name="Test Product", 
                                description="A test product", quantity=5)
        
        mock_repository.get_product_by_sku.return_value = current_product
        mock_repository.remove_stock_atomic.return_value = None  # Insufficient stock
        
        # Act & Assert
        with pytest.raises(InsufficientStock) as exc_info:
            await service.remove_stock("TEST-001", 10)
        
        assert exc_info.value.sku == "TEST-001"
        assert exc_info.value.requested_amount == 10
        assert exc_info.value.available_amount == 5
    
    @pytest.mark.asyncio
    async def test_remove_stock_invalid_amount_zero(self, service, mock_repository):
        """Test stock removal with zero amount."""
        # Act & Assert
        with pytest.raises(ValueError, match="Amount must be positive"):
            await service.remove_stock("TEST-001", 0)
        
        # Repository should not be called
        mock_repository.get_product_by_sku.assert_not_called()
        mock_repository.remove_stock_atomic.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_remove_stock_invalid_amount_negative(self, service, mock_repository):
        """Test stock removal with negative amount."""
        # Act & Assert
        with pytest.raises(ValueError, match="Amount must be positive"):
            await service.remove_stock("TEST-001", -3)
        
        # Repository should not be called
        mock_repository.get_product_by_sku.assert_not_called()
        mock_repository.remove_stock_atomic.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_remove_stock_database_error_on_get(self, service, mock_repository):
        """Test stock removal with database error during product retrieval."""
        # Arrange
        db_error = SQLAlchemyError("Query failed")
        mock_repository.get_product_by_sku.side_effect = db_error
        
        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await service.remove_stock("TEST-001", 3)
        
        assert exc_info.value.operation == "stock removal"
    
    @pytest.mark.asyncio
    async def test_remove_stock_database_error_on_remove(self, service, mock_repository):
        """Test stock removal with database error during atomic removal."""
        # Arrange
        current_product = Product(id=1, sku="TEST-001", name="Test Product", 
                                description="A test product", quantity=10)
        db_error = SQLAlchemyError("Transaction failed")
        
        mock_repository.get_product_by_sku.return_value = current_product
        mock_repository.remove_stock_atomic.side_effect = db_error
        
        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await service.remove_stock("TEST-001", 3)
        
        assert exc_info.value.operation == "stock removal"


class TestConvertToResponse:
    """Tests for the helper conversion method."""
    
    def test_convert_to_response(self, service, sample_product_entity):
        """Test conversion from database entity to response model."""
        # Act
        result = service._convert_to_response(sample_product_entity)
        
        # Assert
        assert isinstance(result, ProductResponse)
        assert result.sku == sample_product_entity.sku
        assert result.name == sample_product_entity.name
        assert result.description == sample_product_entity.description
        assert result.quantity == sample_product_entity.quantity
    
    def test_convert_to_response_none_description(self, service):
        """Test conversion with None description."""
        # Arrange
        product = Product(id=1, sku="TEST-001", name="Test Product", 
                         description=None, quantity=10)
        
        # Act
        result = service._convert_to_response(product)
        
        # Assert
        assert result.description is None