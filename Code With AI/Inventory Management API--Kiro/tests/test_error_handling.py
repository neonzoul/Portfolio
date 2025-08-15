"""
Comprehensive tests for error handling and HTTP status codes.

These tests verify that the API properly handles all error scenarios
with correct HTTP status codes and detailed error messages.
"""

import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient

from inventory_api.main import app
from inventory_api.core.database import create_tables, drop_tables


@pytest_asyncio.fixture
async def client():
    """Create test client with database setup and teardown."""
    # Setup: Create tables
    await create_tables()
    
    # Use httpx AsyncClient with the app's ASGI interface
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    # Teardown: Drop tables
    await drop_tables()


class TestValidationErrors:
    """Test request validation error handling (422 status codes)."""
    
    @pytest.mark.asyncio
    async def test_create_product_missing_required_fields(self, client: AsyncClient):
        """Test product creation with missing required fields."""
        # Test completely empty request
        response = await client.post("/products", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"
        assert data["message"] == "Request validation failed"
        assert "validation_errors" in data
        assert len(data["validation_errors"]) >= 2  # At least sku and name missing
        
        # Check that required fields are identified
        missing_fields = [error["field"] for error in data["validation_errors"]]
        assert "sku" in missing_fields
        assert "name" in missing_fields
        assert "quantity" in missing_fields
    
    @pytest.mark.asyncio
    async def test_create_product_invalid_sku_format(self, client: AsyncClient):
        """Test product creation with invalid SKU format."""
        product_data = {
            "sku": "invalid-lowercase-sku",
            "name": "Test Product",
            "quantity": 10
        }
        
        response = await client.post("/products", json=product_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"
        assert "validation_errors" in data
        
        # Find the SKU validation error
        sku_error = next(
            (error for error in data["validation_errors"] if error["field"] == "sku"),
            None
        )
        assert sku_error is not None
        assert "SKU format is invalid" in sku_error["message"]
        assert "uppercase letters, numbers, and hyphens" in sku_error["details"]
    
    @pytest.mark.asyncio
    async def test_create_product_negative_quantity(self, client: AsyncClient):
        """Test product creation with negative quantity."""
        product_data = {
            "sku": "NEGATIVE-001",
            "name": "Negative Test",
            "quantity": -5
        }
        
        response = await client.post("/products", json=product_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"
        
        # Find the quantity validation error
        quantity_error = next(
            (error for error in data["validation_errors"] if error["field"] == "quantity"),
            None
        )
        assert quantity_error is not None
        assert "greater than or equal to" in quantity_error["message"]
        assert "cannot be negative" in quantity_error["details"]
    
    @pytest.mark.asyncio
    async def test_create_product_string_too_long(self, client: AsyncClient):
        """Test product creation with strings that are too long."""
        product_data = {
            "sku": "A" * 51,  # Max is 50
            "name": "B" * 256,  # Max is 255
            "description": "C" * 1001,  # Max is 1000
            "quantity": 10
        }
        
        response = await client.post("/products", json=product_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"
        assert len(data["validation_errors"]) == 3  # All three fields should fail
        
        # Check each field has appropriate error
        field_errors = {error["field"]: error for error in data["validation_errors"]}
        
        assert "sku" in field_errors
        assert "too long" in field_errors["sku"]["message"]
        
        assert "name" in field_errors
        assert "too long" in field_errors["name"]["message"]
        
        assert "description" in field_errors
        assert "too long" in field_errors["description"]["message"]
    
    @pytest.mark.asyncio
    async def test_create_product_string_too_short(self, client: AsyncClient):
        """Test product creation with strings that are too short."""
        product_data = {
            "sku": "",  # Min is 1
            "name": "",  # Min is 1
            "quantity": 10
        }
        
        response = await client.post("/products", json=product_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"
        
        # Should have errors for both sku and name
        field_errors = {error["field"]: error for error in data["validation_errors"]}
        assert "sku" in field_errors
        assert "name" in field_errors
    
    @pytest.mark.asyncio
    async def test_stock_operation_invalid_amount(self, client: AsyncClient):
        """Test stock operations with invalid amounts."""
        # First create a product
        await client.post("/products", json={
            "sku": "STOCK-TEST-001",
            "name": "Stock Test",
            "quantity": 10
        })
        
        # Test zero amount
        response = await client.patch("/products/STOCK-TEST-001/add", json={"amount": 0})
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"
        
        amount_error = next(
            (error for error in data["validation_errors"] if error["field"] == "amount"),
            None
        )
        assert amount_error is not None
        assert "greater than" in amount_error["message"]
        
        # Test negative amount
        response = await client.patch("/products/STOCK-TEST-001/remove", json={"amount": -5})
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"
    
    @pytest.mark.asyncio
    async def test_stock_operation_missing_amount(self, client: AsyncClient):
        """Test stock operations with missing amount field."""
        # First create a product
        await client.post("/products", json={
            "sku": "STOCK-MISSING-001",
            "name": "Stock Missing Test",
            "quantity": 10
        })
        
        # Test missing amount field
        response = await client.patch("/products/STOCK-MISSING-001/add", json={})
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"
        
        # Should have error for missing amount
        missing_fields = [error["field"] for error in data["validation_errors"]]
        assert "amount" in missing_fields


class TestBusinessLogicErrors:
    """Test business logic error handling (400 status codes)."""
    
    @pytest.mark.asyncio
    async def test_duplicate_sku_error(self, client: AsyncClient):
        """Test creating product with duplicate SKU."""
        # Create first product
        product_data = {
            "sku": "DUPLICATE-TEST-001",
            "name": "First Product",
            "quantity": 10
        }
        response1 = await client.post("/products", json=product_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        duplicate_data = {
            "sku": "DUPLICATE-TEST-001",
            "name": "Second Product",
            "quantity": 5
        }
        response2 = await client.post("/products", json=duplicate_data)
        
        assert response2.status_code == 400
        data = response2.json()
        assert data["error"] == "Duplicate SKU"
        assert "DUPLICATE-TEST-001" in data["message"]
        assert "already exists" in data["message"]
        assert data["sku"] == "DUPLICATE-TEST-001"
        assert data["path"] == "/products"
    
    @pytest.mark.asyncio
    async def test_insufficient_stock_error(self, client: AsyncClient):
        """Test removing more stock than available."""
        # Create product with limited stock
        await client.post("/products", json={
            "sku": "INSUFFICIENT-001",
            "name": "Insufficient Stock Test",
            "quantity": 5
        })
        
        # Try to remove more than available
        response = await client.patch("/products/INSUFFICIENT-001/remove", json={"amount": 10})
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Insufficient Stock"
        assert "INSUFFICIENT-001" in data["message"]
        assert data["sku"] == "INSUFFICIENT-001"
        assert data["requested"] == 10
        assert data["available"] == 5
        assert data["path"] == "/products/INSUFFICIENT-001/remove"
    
    @pytest.mark.asyncio
    async def test_insufficient_stock_exact_boundary(self, client: AsyncClient):
        """Test removing exactly the available stock (should succeed)."""
        # Create product with specific stock
        await client.post("/products", json={
            "sku": "BOUNDARY-001",
            "name": "Boundary Test",
            "quantity": 5
        })
        
        # Remove exactly the available amount (should work)
        response = await client.patch("/products/BOUNDARY-001/remove", json={"amount": 5})
        
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 0
        
        # Now try to remove one more (should fail)
        response = await client.patch("/products/BOUNDARY-001/remove", json={"amount": 1})
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Insufficient Stock"
        assert data["available"] == 0


class TestNotFoundErrors:
    """Test resource not found error handling (404 status codes)."""
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_product(self, client: AsyncClient):
        """Test retrieving a product that doesn't exist."""
        response = await client.get("/products/NONEXISTENT-001")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Product Not Found"
        assert "NONEXISTENT-001" in data["message"]
        assert data["sku"] == "NONEXISTENT-001"
        assert data["path"] == "/products/NONEXISTENT-001"
    
    @pytest.mark.asyncio
    async def test_add_stock_nonexistent_product(self, client: AsyncClient):
        """Test adding stock to a product that doesn't exist."""
        response = await client.patch("/products/NONEXISTENT-002/add", json={"amount": 5})
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Product Not Found"
        assert "NONEXISTENT-002" in data["message"]
        assert data["sku"] == "NONEXISTENT-002"
        assert data["path"] == "/products/NONEXISTENT-002/add"
    
    @pytest.mark.asyncio
    async def test_remove_stock_nonexistent_product(self, client: AsyncClient):
        """Test removing stock from a product that doesn't exist."""
        response = await client.patch("/products/NONEXISTENT-003/remove", json={"amount": 3})
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Product Not Found"
        assert "NONEXISTENT-003" in data["message"]
        assert data["sku"] == "NONEXISTENT-003"
        assert data["path"] == "/products/NONEXISTENT-003/remove"


class TestHTTPStatusCodeConsistency:
    """Test that all endpoints return consistent HTTP status codes."""
    
    @pytest.mark.asyncio
    async def test_successful_operations_status_codes(self, client: AsyncClient):
        """Test that successful operations return correct status codes."""
        # POST for creation should return 201
        create_response = await client.post("/products", json={
            "sku": "STATUS-TEST-001",
            "name": "Status Test Product",
            "quantity": 10
        })
        assert create_response.status_code == 201
        
        # GET for individual resource should return 200
        get_response = await client.get("/products/STATUS-TEST-001")
        assert get_response.status_code == 200
        
        # GET for collection should return 200
        list_response = await client.get("/products")
        assert list_response.status_code == 200
        
        # PATCH for updates should return 200
        add_response = await client.patch("/products/STATUS-TEST-001/add", json={"amount": 5})
        assert add_response.status_code == 200
        
        remove_response = await client.patch("/products/STATUS-TEST-001/remove", json={"amount": 3})
        assert remove_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_error_status_code_consistency(self, client: AsyncClient):
        """Test that error scenarios consistently return appropriate status codes."""
        # 404 for all non-existent resource operations
        assert (await client.get("/products/MISSING-001")).status_code == 404
        assert (await client.patch("/products/MISSING-001/add", json={"amount": 1})).status_code == 404
        assert (await client.patch("/products/MISSING-001/remove", json={"amount": 1})).status_code == 404
        
        # 422 for all validation errors
        assert (await client.post("/products", json={})).status_code == 422
        assert (await client.post("/products", json={"sku": "", "name": "", "quantity": -1})).status_code == 422
        
        # Create a product for business logic error tests
        await client.post("/products", json={
            "sku": "ERROR-TEST-001",
            "name": "Error Test",
            "quantity": 1
        })
        
        # 400 for business logic errors
        assert (await client.post("/products", json={
            "sku": "ERROR-TEST-001",
            "name": "Duplicate",
            "quantity": 1
        })).status_code == 400
        
        assert (await client.patch("/products/ERROR-TEST-001/remove", json={"amount": 5})).status_code == 400


class TestErrorResponseFormat:
    """Test that error responses have consistent format and required fields."""
    
    @pytest.mark.asyncio
    async def test_error_response_structure(self, client: AsyncClient):
        """Test that all error responses have consistent structure."""
        # Test 404 error structure
        response = await client.get("/products/MISSING-001")
        assert response.status_code == 404
        
        data = response.json()
        required_fields = ["error", "message", "details", "path"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert data["path"] == "/products/MISSING-001"
        assert isinstance(data["error"], str)
        assert isinstance(data["message"], str)
        assert isinstance(data["details"], str)
    
    @pytest.mark.asyncio
    async def test_validation_error_response_structure(self, client: AsyncClient):
        """Test validation error response structure."""
        response = await client.post("/products", json={"sku": "invalid"})
        assert response.status_code == 422
        
        data = response.json()
        required_fields = ["error", "message", "details", "validation_errors", "path"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert isinstance(data["validation_errors"], list)
        assert len(data["validation_errors"]) > 0
        
        # Check validation error detail structure
        validation_error = data["validation_errors"][0]
        validation_fields = ["field", "message", "details"]
        for field in validation_fields:
            assert field in validation_error, f"Missing validation error field: {field}"
    
    @pytest.mark.asyncio
    async def test_insufficient_stock_error_structure(self, client: AsyncClient):
        """Test insufficient stock error response structure."""
        # Create product
        await client.post("/products", json={
            "sku": "STOCK-STRUCTURE-001",
            "name": "Stock Structure Test",
            "quantity": 3
        })
        
        # Try to remove too much
        response = await client.patch("/products/STOCK-STRUCTURE-001/remove", json={"amount": 10})
        assert response.status_code == 400
        
        data = response.json()
        required_fields = ["error", "message", "details", "sku", "requested", "available", "path"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert data["sku"] == "STOCK-STRUCTURE-001"
        assert data["requested"] == 10
        assert data["available"] == 3
        assert isinstance(data["requested"], int)
        assert isinstance(data["available"], int)


class TestContentTypeHeaders:
    """Test that responses have correct content-type headers."""
    
    @pytest.mark.asyncio
    async def test_success_response_headers(self, client: AsyncClient):
        """Test that successful responses have correct headers."""
        response = await client.post("/products", json={
            "sku": "HEADER-TEST-001",
            "name": "Header Test",
            "quantity": 10
        })
        
        assert response.status_code == 201
        assert response.headers["content-type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_error_response_headers(self, client: AsyncClient):
        """Test that error responses have correct headers."""
        # Test 404 error
        response = await client.get("/products/MISSING-HEADER-001")
        assert response.status_code == 404
        assert response.headers["content-type"] == "application/json"
        
        # Test 422 validation error
        response = await client.post("/products", json={})
        assert response.status_code == 422
        assert response.headers["content-type"] == "application/json"
        
        # Test 400 business logic error
        await client.post("/products", json={
            "sku": "HEADER-DUPLICATE-001",
            "name": "Header Duplicate Test",
            "quantity": 5
        })
        
        response = await client.post("/products", json={
            "sku": "HEADER-DUPLICATE-001",
            "name": "Another Product",
            "quantity": 3
        })
        assert response.status_code == 400
        assert response.headers["content-type"] == "application/json"


class TestErrorMessageQuality:
    """Test that error messages are helpful and user-friendly."""
    
    @pytest.mark.asyncio
    async def test_validation_error_messages_are_helpful(self, client: AsyncClient):
        """Test that validation error messages provide helpful guidance."""
        response = await client.post("/products", json={
            "sku": "invalid-sku",
            "name": "",
            "quantity": -1
        })
        
        assert response.status_code == 422
        data = response.json()
        
        # Check that error messages are helpful
        for validation_error in data["validation_errors"]:
            assert len(validation_error["message"]) > 0
            assert len(validation_error["details"]) > 0
            # Details should provide guidance - check for helpful words
            details_lower = validation_error["details"].lower()
            assert any(word in details_lower 
                      for word in ["must", "should", "cannot", "required", "format", "check", "minimum", "maximum", "positive", "negative"])
    
    @pytest.mark.asyncio
    async def test_business_error_messages_are_specific(self, client: AsyncClient):
        """Test that business logic error messages are specific and actionable."""
        # Create product for testing
        await client.post("/products", json={
            "sku": "SPECIFIC-ERROR-001",
            "name": "Specific Error Test",
            "quantity": 2
        })
        
        # Test insufficient stock error
        response = await client.patch("/products/SPECIFIC-ERROR-001/remove", json={"amount": 5})
        assert response.status_code == 400
        
        data = response.json()
        # Message should include specific numbers
        assert "2" in data["details"]  # Available amount
        assert "5" in data["details"]  # Requested amount
        assert data["requested"] == 5
        assert data["available"] == 2
    
    @pytest.mark.asyncio
    async def test_not_found_messages_include_sku(self, client: AsyncClient):
        """Test that not found error messages include the specific SKU."""
        response = await client.get("/products/SPECIFIC-MISSING-SKU")
        assert response.status_code == 404
        
        data = response.json()
        assert "SPECIFIC-MISSING-SKU" in data["message"]
        assert data["sku"] == "SPECIFIC-MISSING-SKU"