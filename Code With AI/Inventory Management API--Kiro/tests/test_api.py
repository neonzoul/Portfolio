"""
Integration tests for the FastAPI endpoints.

These tests verify that the API endpoints work correctly with proper HTTP semantics,
request/response handling, and error scenarios.
"""

import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient
from fastapi.testclient import TestClient

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


class TestProductCreation:
    """Test product creation endpoint (POST /products)."""
    
    @pytest.mark.asyncio
    async def test_create_product_success(self, client: AsyncClient):
        """Test successful product creation."""
        # Arrange
        product_data = {
            "sku": "TSHIRT-RED-L",
            "name": "Red T-Shirt (Large)",
            "description": "Comfortable cotton t-shirt in red, size large",
            "quantity": 25
        }
        
        # Act
        response = await client.post("/products", json=product_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["sku"] == "TSHIRT-RED-L"
        assert data["name"] == "Red T-Shirt (Large)"
        assert data["description"] == "Comfortable cotton t-shirt in red, size large"
        assert data["quantity"] == 25
    
    @pytest.mark.asyncio
    async def test_create_product_minimal_data(self, client: AsyncClient):
        """Test product creation with minimal required data."""
        # Arrange
        product_data = {
            "sku": "MINIMAL-001",
            "name": "Minimal Product",
            "quantity": 0
        }
        
        # Act
        response = await client.post("/products", json=product_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["sku"] == "MINIMAL-001"
        assert data["name"] == "Minimal Product"
        assert data["description"] is None
        assert data["quantity"] == 0
    
    @pytest.mark.asyncio
    async def test_create_product_duplicate_sku(self, client: AsyncClient):
        """Test product creation with duplicate SKU."""
        # Arrange
        product_data = {
            "sku": "DUPLICATE-001",
            "name": "First Product",
            "quantity": 10
        }
        
        # Act - Create first product
        response1 = await client.post("/products", json=product_data)
        assert response1.status_code == 201
        
        # Act - Try to create duplicate
        duplicate_data = {
            "sku": "DUPLICATE-001",
            "name": "Second Product",
            "quantity": 5
        }
        response2 = await client.post("/products", json=duplicate_data)
        
        # Assert
        assert response2.status_code == 400
        data = response2.json()
        assert data["error"] == "Duplicate SKU"
        assert "already exists" in data["message"]
    
    @pytest.mark.asyncio
    async def test_create_product_invalid_sku_format(self, client: AsyncClient):
        """Test product creation with invalid SKU format."""
        # Arrange
        product_data = {
            "sku": "invalid-sku-lowercase",
            "name": "Invalid SKU Product",
            "quantity": 10
        }
        
        # Act
        response = await client.post("/products", json=product_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert data["error"] == "Validation Error"
        # Check that SKU validation error is present
        sku_error = next(
            (error for error in data["validation_errors"] if error["field"] == "sku"),
            None
        )
        assert sku_error is not None
        assert "SKU format is invalid" in sku_error["message"]
    
    @pytest.mark.asyncio
    async def test_create_product_negative_quantity(self, client: AsyncClient):
        """Test product creation with negative quantity."""
        # Arrange
        product_data = {
            "sku": "NEGATIVE-001",
            "name": "Negative Quantity Product",
            "quantity": -5
        }
        
        # Act
        response = await client.post("/products", json=product_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert data["error"] == "Validation Error"
        # Check that quantity validation error is present
        quantity_error = next(
            (error for error in data["validation_errors"] if error["field"] == "quantity"),
            None
        )
        assert quantity_error is not None
        assert "greater than or equal to" in quantity_error["message"]
    
    @pytest.mark.asyncio
    async def test_create_product_missing_required_fields(self, client: AsyncClient):
        """Test product creation with missing required fields."""
        # Arrange
        product_data = {
            "sku": "MISSING-001"
            # Missing name and quantity
        }
        
        # Act
        response = await client.post("/products", json=product_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert data["error"] == "Validation Error"
        missing_fields = [error["field"] for error in data["validation_errors"]]
        assert "name" in missing_fields
        assert "quantity" in missing_fields


class TestProductRetrieval:
    """Test product retrieval endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_all_products_empty(self, client: AsyncClient):
        """Test retrieving all products when none exist."""
        # Act
        response = await client.get("/products")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["products"] == []
    
    @pytest.mark.asyncio
    async def test_get_all_products_with_data(self, client: AsyncClient):
        """Test retrieving all products with existing data."""
        # Arrange - Create test products
        products = [
            {"sku": "PROD-001", "name": "Product 1", "quantity": 10},
            {"sku": "PROD-002", "name": "Product 2", "quantity": 20}
        ]
        
        for product in products:
            await client.post("/products", json=product)
        
        # Act
        response = await client.get("/products")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) == 2
        
        # Verify products are returned (order may vary)
        skus = [p["sku"] for p in data["products"]]
        assert "PROD-001" in skus
        assert "PROD-002" in skus
    
    @pytest.mark.asyncio
    async def test_get_product_by_sku_success(self, client: AsyncClient):
        """Test retrieving a product by SKU."""
        # Arrange
        product_data = {
            "sku": "GET-TEST-001",
            "name": "Get Test Product",
            "description": "Product for testing retrieval",
            "quantity": 15
        }
        await client.post("/products", json=product_data)
        
        # Act
        response = await client.get("/products/GET-TEST-001")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == "GET-TEST-001"
        assert data["name"] == "Get Test Product"
        assert data["description"] == "Product for testing retrieval"
        assert data["quantity"] == 15
    
    @pytest.mark.asyncio
    async def test_get_product_by_sku_not_found(self, client: AsyncClient):
        """Test retrieving a non-existent product."""
        # Act
        response = await client.get("/products/NONEXISTENT-001")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Product Not Found"
        assert "not found" in data["message"]


class TestStockOperations:
    """Test stock addition and removal endpoints."""
    
    @pytest.mark.asyncio
    async def test_add_stock_success(self, client: AsyncClient):
        """Test successful stock addition."""
        # Arrange
        product_data = {
            "sku": "STOCK-ADD-001",
            "name": "Stock Addition Test",
            "quantity": 10
        }
        await client.post("/products", json=product_data)
        
        # Act
        response = await client.patch("/products/STOCK-ADD-001/add", json={"amount": 5})
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == "STOCK-ADD-001"
        assert data["quantity"] == 15  # 10 + 5
    
    @pytest.mark.asyncio
    async def test_add_stock_product_not_found(self, client: AsyncClient):
        """Test stock addition for non-existent product."""
        # Act
        response = await client.patch("/products/NONEXISTENT-001/add", json={"amount": 5})
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Product Not Found"
        assert "not found" in data["message"]
    
    @pytest.mark.asyncio
    async def test_add_stock_invalid_amount(self, client: AsyncClient):
        """Test stock addition with invalid amount."""
        # Arrange
        product_data = {
            "sku": "STOCK-INVALID-001",
            "name": "Invalid Stock Test",
            "quantity": 10
        }
        await client.post("/products", json=product_data)
        
        # Act
        response = await client.patch("/products/STOCK-INVALID-001/add", json={"amount": 0})
        
        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert data["error"] == "Validation Error"
        # Check that amount validation error is present
        amount_error = next(
            (error for error in data["validation_errors"] if error["field"] == "amount"),
            None
        )
        assert amount_error is not None
        assert "greater than" in amount_error["message"]
    
    @pytest.mark.asyncio
    async def test_remove_stock_success(self, client: AsyncClient):
        """Test successful stock removal."""
        # Arrange
        product_data = {
            "sku": "STOCK-REMOVE-001",
            "name": "Stock Removal Test",
            "quantity": 10
        }
        await client.post("/products", json=product_data)
        
        # Act
        response = await client.patch("/products/STOCK-REMOVE-001/remove", json={"amount": 3})
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == "STOCK-REMOVE-001"
        assert data["quantity"] == 7  # 10 - 3
    
    @pytest.mark.asyncio
    async def test_remove_stock_insufficient(self, client: AsyncClient):
        """Test stock removal with insufficient stock."""
        # Arrange
        product_data = {
            "sku": "STOCK-INSUFFICIENT-001",
            "name": "Insufficient Stock Test",
            "quantity": 5
        }
        await client.post("/products", json=product_data)
        
        # Act
        response = await client.patch("/products/STOCK-INSUFFICIENT-001/remove", json={"amount": 10})
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Insufficient Stock"
        assert "Insufficient stock" in data["message"]
        assert data["requested"] == 10
        assert data["available"] == 5
    
    @pytest.mark.asyncio
    async def test_remove_stock_product_not_found(self, client: AsyncClient):
        """Test stock removal for non-existent product."""
        # Act
        response = await client.patch("/products/NONEXISTENT-001/remove", json={"amount": 5})
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Product Not Found"
        assert "not found" in data["message"]
    
    @pytest.mark.asyncio
    async def test_remove_stock_invalid_amount(self, client: AsyncClient):
        """Test stock removal with invalid amount."""
        # Arrange
        product_data = {
            "sku": "STOCK-INVALID-REMOVE-001",
            "name": "Invalid Remove Test",
            "quantity": 10
        }
        await client.post("/products", json=product_data)
        
        # Act
        response = await client.patch("/products/STOCK-INVALID-REMOVE-001/remove", json={"amount": -1})
        
        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert data["error"] == "Validation Error"
        # Check that amount validation error is present
        amount_error = next(
            (error for error in data["validation_errors"] if error["field"] == "amount"),
            None
        )
        assert amount_error is not None
        assert "greater than" in amount_error["message"]


class TestCompleteWorkflow:
    """Test complete API workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_product_lifecycle(self, client: AsyncClient):
        """Test complete product lifecycle: create, retrieve, modify stock."""
        # 1. Create product
        product_data = {
            "sku": "LIFECYCLE-001",
            "name": "Lifecycle Test Product",
            "description": "Testing complete lifecycle",
            "quantity": 20
        }
        
        create_response = await client.post("/products", json=product_data)
        assert create_response.status_code == 201
        
        # 2. Retrieve product
        get_response = await client.get("/products/LIFECYCLE-001")
        assert get_response.status_code == 200
        assert get_response.json()["quantity"] == 20
        
        # 3. Add stock
        add_response = await client.patch("/products/LIFECYCLE-001/add", json={"amount": 10})
        assert add_response.status_code == 200
        assert add_response.json()["quantity"] == 30
        
        # 4. Remove stock
        remove_response = await client.patch("/products/LIFECYCLE-001/remove", json={"amount": 5})
        assert remove_response.status_code == 200
        assert remove_response.json()["quantity"] == 25
        
        # 5. Verify final state
        final_response = await client.get("/products/LIFECYCLE-001")
        assert final_response.status_code == 200
        assert final_response.json()["quantity"] == 25
    
    @pytest.mark.asyncio
    async def test_multiple_products_management(self, client: AsyncClient):
        """Test managing multiple products simultaneously."""
        # Create multiple products
        products = [
            {"sku": "MULTI-001", "name": "Multi Product 1", "quantity": 10},
            {"sku": "MULTI-002", "name": "Multi Product 2", "quantity": 20},
            {"sku": "MULTI-003", "name": "Multi Product 3", "quantity": 30}
        ]
        
        for product in products:
            response = await client.post("/products", json=product)
            assert response.status_code == 201
        
        # Retrieve all products
        all_response = await client.get("/products")
        assert all_response.status_code == 200
        assert len(all_response.json()["products"]) == 3
        
        # Modify stock for different products
        await client.patch("/products/MULTI-001/add", json={"amount": 5})
        await client.patch("/products/MULTI-002/remove", json={"amount": 3})
        
        # Verify individual states
        product1 = await client.get("/products/MULTI-001")
        assert product1.json()["quantity"] == 15
        
        product2 = await client.get("/products/MULTI-002")
        assert product2.json()["quantity"] == 17
        
        product3 = await client.get("/products/MULTI-003")
        assert product3.json()["quantity"] == 30  # Unchanged


class TestHTTPSemantics:
    """Test proper HTTP semantics and status codes."""
    
    @pytest.mark.asyncio
    async def test_http_methods_and_status_codes(self, client: AsyncClient):
        """Test that endpoints use correct HTTP methods and return proper status codes."""
        # POST for creation returns 201
        create_response = await client.post("/products", json={
            "sku": "HTTP-TEST-001",
            "name": "HTTP Test Product",
            "quantity": 10
        })
        assert create_response.status_code == 201
        
        # GET for retrieval returns 200
        get_response = await client.get("/products/HTTP-TEST-001")
        assert get_response.status_code == 200
        
        # GET for list returns 200
        list_response = await client.get("/products")
        assert list_response.status_code == 200
        
        # PATCH for updates returns 200
        patch_response = await client.patch("/products/HTTP-TEST-001/add", json={"amount": 5})
        assert patch_response.status_code == 200
        
        # 404 for non-existent resources
        not_found_response = await client.get("/products/NONEXISTENT")
        assert not_found_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_content_type_headers(self, client: AsyncClient):
        """Test that responses have correct content-type headers."""
        # Create a product
        response = await client.post("/products", json={
            "sku": "CONTENT-TYPE-001",
            "name": "Content Type Test",
            "quantity": 10
        })
        
        assert response.headers["content-type"] == "application/json"
        assert response.status_code == 201
        
        # Get product
        get_response = await client.get("/products/CONTENT-TYPE-001")
        assert get_response.headers["content-type"] == "application/json"
        assert get_response.status_code == 200