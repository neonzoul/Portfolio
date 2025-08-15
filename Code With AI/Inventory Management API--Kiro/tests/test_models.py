"""
Unit tests for data models validation and constraints.

These tests verify that our models properly validate input data,
enforce constraints, and handle edge cases correctly.
"""

import pytest
from pydantic import ValidationError
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.exc import IntegrityError

from inventory_api.models.database import Product
from inventory_api.models.api import (
    ProductCreate,
    ProductResponse,
    StockOperation,
    ErrorResponse,
    ProductListResponse
)


class TestProductDatabaseModel:
    """Test the SQLModel Product entity."""
    
    def test_product_creation_valid_data(self):
        """Test creating a product with valid data."""
        product = Product(
            sku="TEST-001",
            name="Test Product",
            description="A test product",
            quantity=10
        )
        
        assert product.sku == "TEST-001"
        assert product.name == "Test Product"
        assert product.description == "A test product"
        assert product.quantity == 10
        assert product.id is None  # Should be None until saved to DB
    
    def test_product_creation_minimal_data(self):
        """Test creating a product with minimal required data."""
        product = Product(
            sku="MIN-001",
            name="Minimal Product",
            quantity=0
        )
        
        assert product.sku == "MIN-001"
        assert product.name == "Minimal Product"
        assert product.description is None
        assert product.quantity == 0
    
    def test_product_validation_negative_quantity(self):
        """Test that negative quantities are rejected at the model level."""
        with pytest.raises(ValidationError) as exc_info:
            Product(
                sku="NEG-001",
                name="Negative Test",
                quantity=-1
            )
        
        error = exc_info.value.errors()[0]
        assert error['type'] == 'greater_than_equal'
        assert 'quantity' in error['loc']
    
    def test_product_validation_empty_sku(self):
        """Test that empty SKU is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Product(
                sku="",
                name="Empty SKU Test",
                quantity=5
            )
        
        error = exc_info.value.errors()[0]
        assert error['type'] == 'string_too_short'
        assert 'sku' in error['loc']
    
    def test_product_validation_empty_name(self):
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Product(
                sku="EMPTY-NAME",
                name="",
                quantity=5
            )
        
        error = exc_info.value.errors()[0]
        assert error['type'] == 'string_too_short'
        assert 'name' in error['loc']
    
    def test_product_validation_long_fields(self):
        """Test field length constraints."""
        # Test SKU too long
        with pytest.raises(ValidationError):
            Product(
                sku="A" * 51,  # Max is 50
                name="Test",
                quantity=5
            )
        
        # Test name too long
        with pytest.raises(ValidationError):
            Product(
                sku="LONG-NAME",
                name="A" * 256,  # Max is 255
                quantity=5
            )
        
        # Test description too long
        with pytest.raises(ValidationError):
            Product(
                sku="LONG-DESC",
                name="Test",
                description="A" * 1001,  # Max is 1000
                quantity=5
            )


class TestProductCreateModel:
    """Test the ProductCreate API model."""
    
    def test_product_create_valid_data(self):
        """Test creating ProductCreate with valid data."""
        product_data = ProductCreate(
            sku="CREATE-001",
            name="Create Test Product",
            description="Test description",
            quantity=15
        )
        
        assert product_data.sku == "CREATE-001"
        assert product_data.name == "Create Test Product"
        assert product_data.description == "Test description"
        assert product_data.quantity == 15
    
    def test_product_create_sku_validation(self):
        """Test SKU format validation."""
        # Valid SKUs
        valid_skus = ["ABC-123", "PRODUCT-001", "TEST123", "A1B2C3"]
        for sku in valid_skus:
            product = ProductCreate(
                sku=sku,
                name="Test Product",
                quantity=10
            )
            assert product.sku == sku
        
        # Invalid SKUs
        invalid_skus = ["abc-123", "product with spaces", "test@123", "test.123"]
        for sku in invalid_skus:
            with pytest.raises(ValidationError) as exc_info:
                ProductCreate(
                    sku=sku,
                    name="Test Product",
                    quantity=10
                )
            
            errors = exc_info.value.errors()
            assert any('SKU must contain only uppercase letters' in str(error) for error in errors)
    
    def test_product_create_name_validation(self):
        """Test name validation and whitespace handling."""
        # Valid name
        product = ProductCreate(
            sku="NAME-TEST",
            name="  Valid Product Name  ",
            quantity=10
        )
        assert product.name == "Valid Product Name"  # Should be stripped
        
        # Empty name after stripping
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                sku="EMPTY-NAME",
                name="   ",  # Just whitespace
                quantity=10
            )
        
        errors = exc_info.value.errors()
        assert any('cannot be empty or just whitespace' in str(error) for error in errors)
    
    def test_product_create_description_validation(self):
        """Test description validation and cleanup."""
        # Description with whitespace should be cleaned
        product = ProductCreate(
            sku="DESC-TEST",
            name="Test Product",
            description="  Test description  ",
            quantity=10
        )
        assert product.description == "Test description"
        
        # Empty description after stripping should become None
        product = ProductCreate(
            sku="EMPTY-DESC",
            name="Test Product",
            description="   ",  # Just whitespace
            quantity=10
        )
        assert product.description is None
    
    def test_product_create_quantity_validation(self):
        """Test quantity validation."""
        # Valid quantities
        for qty in [0, 1, 100, 9999]:
            product = ProductCreate(
                sku=f"QTY-{qty}",
                name="Quantity Test",
                quantity=qty
            )
            assert product.quantity == qty
        
        # Invalid quantities
        with pytest.raises(ValidationError):
            ProductCreate(
                sku="NEG-QTY",
                name="Negative Quantity",
                quantity=-1
            )


class TestStockOperationModel:
    """Test the StockOperation model."""
    
    def test_stock_operation_valid_amounts(self):
        """Test valid stock operation amounts."""
        for amount in [1, 5, 100, 9999]:
            operation = StockOperation(amount=amount)
            assert operation.amount == amount
    
    def test_stock_operation_invalid_amounts(self):
        """Test invalid stock operation amounts."""
        invalid_amounts = [0, -1, -100]
        
        for amount in invalid_amounts:
            with pytest.raises(ValidationError) as exc_info:
                StockOperation(amount=amount)
            
            error = exc_info.value.errors()[0]
            assert error['type'] == 'greater_than'
            assert 'amount' in error['loc']


class TestProductResponseModel:
    """Test the ProductResponse model."""
    
    def test_product_response_creation(self):
        """Test creating ProductResponse from data."""
        response = ProductResponse(
            sku="RESP-001",
            name="Response Test",
            description="Test description",
            quantity=25
        )
        
        assert response.sku == "RESP-001"
        assert response.name == "Response Test"
        assert response.description == "Test description"
        assert response.quantity == 25
    
    def test_product_response_from_database_model(self):
        """Test creating ProductResponse from database Product."""
        # Create a database product
        db_product = Product(
            id=1,
            sku="DB-001",
            name="Database Product",
            description="From database",
            quantity=30
        )
        
        # Convert to response model
        response = ProductResponse.model_validate(db_product)
        
        assert response.sku == "DB-001"
        assert response.name == "Database Product"
        assert response.description == "From database"
        assert response.quantity == 30


class TestProductListResponseModel:
    """Test the ProductListResponse model."""
    
    def test_product_list_response_creation(self):
        """Test creating ProductListResponse."""
        products = [
            ProductResponse(
                sku="LIST-001",
                name="Product 1",
                description="First product",
                quantity=10
            ),
            ProductResponse(
                sku="LIST-002",
                name="Product 2",
                description="Second product",
                quantity=20
            )
        ]
        
        response = ProductListResponse(products=products)
        
        assert len(response.products) == 2
        assert response.products[0].sku == "LIST-001"
        assert response.products[1].sku == "LIST-002"
    
    def test_product_list_response_empty(self):
        """Test creating empty ProductListResponse."""
        response = ProductListResponse(products=[])
        assert len(response.products) == 0


class TestErrorResponseModel:
    """Test the ErrorResponse model."""
    
    def test_error_response_creation(self):
        """Test creating ErrorResponse."""
        error = ErrorResponse(
            error="Validation Error",
            message="Request validation failed",
            details="SKU format is invalid",
            path="/products"
        )
        
        assert error.error == "Validation Error"
        assert error.message == "Request validation failed"
        assert error.details == "SKU format is invalid"
        assert error.path == "/products"


class TestDatabaseConstraints:
    """Test database-level constraints using an in-memory SQLite database."""
    
    @pytest.fixture
    def engine_and_session(self):
        """Create an in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(engine)
        
        with Session(engine) as session:
            yield engine, session
    
    def test_unique_sku_constraint(self, engine_and_session):
        """Test that duplicate SKUs are rejected at the database level."""
        engine, session = engine_and_session
        
        # Create first product
        product1 = Product(
            sku="UNIQUE-001",
            name="First Product",
            quantity=10
        )
        session.add(product1)
        session.commit()
        
        # Try to create second product with same SKU
        product2 = Product(
            sku="UNIQUE-001",  # Same SKU
            name="Second Product",
            quantity=5
        )
        session.add(product2)
        
        # Should raise IntegrityError due to unique constraint
        with pytest.raises(IntegrityError):
            session.commit()
    
    def test_positive_quantity_constraint(self, engine_and_session):
        """Test that negative quantities are rejected at the database level."""
        engine, session = engine_and_session
        
        # This should work at the Pydantic level, but let's test the database constraint
        # by bypassing Pydantic validation
        from sqlalchemy import text
        
        # Try to insert a product with negative quantity using raw SQL
        with pytest.raises(IntegrityError):
            session.execute(
                text("INSERT INTO product (sku, name, quantity) VALUES ('NEG-001', 'Negative Test', -1)")
            )
            session.commit()