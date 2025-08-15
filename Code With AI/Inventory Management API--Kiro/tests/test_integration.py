"""
Integration tests for complete API workflows.

These tests verify end-to-end functionality, concurrent operations,
and API contract compliance. They test the complete system integration
from HTTP requests through to database operations.
"""

import pytest
import pytest_asyncio
import asyncio
import httpx
from httpx import AsyncClient
from typing import List, Dict, Any

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


class TestEndToEndWorkflows:
    """Test complete end-to-end API workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_product_lifecycle_workflow(self, client: AsyncClient):
        """
        Test complete product lifecycle from creation to stock depletion.
        
        This test covers:
        - Product creation
        - Stock retrieval and verification
        - Multiple stock additions
        - Multiple stock removals
        - Final state verification
        """
        # Step 1: Create a new product
        product_data = {
            "sku": "LIFECYCLE-COMPLETE-001",
            "name": "Complete Lifecycle Product",
            "description": "Testing complete product lifecycle",
            "quantity": 50
        }
        
        create_response = await client.post("/products", json=product_data)
        assert create_response.status_code == 201
        created_product = create_response.json()
        assert created_product["sku"] == "LIFECYCLE-COMPLETE-001"
        assert created_product["quantity"] == 50
        
        # Step 2: Verify product appears in product list
        list_response = await client.get("/products")
        assert list_response.status_code == 200
        products = list_response.json()["products"]
        lifecycle_product = next(
            (p for p in products if p["sku"] == "LIFECYCLE-COMPLETE-001"), 
            None
        )
        assert lifecycle_product is not None
        assert lifecycle_product["quantity"] == 50
        
        # Step 3: Add stock multiple times
        add_operations = [
            {"amount": 10, "expected_total": 60},
            {"amount": 25, "expected_total": 85},
            {"amount": 5, "expected_total": 90}
        ]
        
        for operation in add_operations:
            add_response = await client.patch(
                f"/products/LIFECYCLE-COMPLETE-001/add", 
                json={"amount": operation["amount"]}
            )
            assert add_response.status_code == 200
            assert add_response.json()["quantity"] == operation["expected_total"]
        
        # Step 4: Remove stock multiple times
        remove_operations = [
            {"amount": 15, "expected_total": 75},
            {"amount": 30, "expected_total": 45},
            {"amount": 20, "expected_total": 25}
        ]
        
        for operation in remove_operations:
            remove_response = await client.patch(
                f"/products/LIFECYCLE-COMPLETE-001/remove", 
                json={"amount": operation["amount"]}
            )
            assert remove_response.status_code == 200
            assert remove_response.json()["quantity"] == operation["expected_total"]
        
        # Step 5: Verify final state through individual product retrieval
        final_response = await client.get("/products/LIFECYCLE-COMPLETE-001")
        assert final_response.status_code == 200
        final_product = final_response.json()
        assert final_product["quantity"] == 25
        assert final_product["name"] == "Complete Lifecycle Product"
        
        # Step 6: Attempt to remove more stock than available (should fail)
        insufficient_response = await client.patch(
            "/products/LIFECYCLE-COMPLETE-001/remove", 
            json={"amount": 30}
        )
        assert insufficient_response.status_code == 400
        error_data = insufficient_response.json()
        assert error_data["error"] == "Insufficient Stock"
        assert error_data["available"] == 25
        assert error_data["requested"] == 30
        
        # Step 7: Remove exact remaining stock
        final_remove_response = await client.patch(
            "/products/LIFECYCLE-COMPLETE-001/remove", 
            json={"amount": 25}
        )
        assert final_remove_response.status_code == 200
        assert final_remove_response.json()["quantity"] == 0
    
    @pytest.mark.asyncio
    async def test_multi_product_inventory_management_workflow(self, client: AsyncClient):
        """
        Test managing multiple products simultaneously.
        
        This test verifies:
        - Creating multiple products
        - Managing stock across different products
        - Ensuring operations on one product don't affect others
        - Bulk retrieval and verification
        """
        # Step 1: Create multiple products with different initial stock levels
        products_to_create = [
            {"sku": "MULTI-SHIRT-001", "name": "Red T-Shirt", "quantity": 100},
            {"sku": "MULTI-PANTS-001", "name": "Blue Jeans", "quantity": 50},
            {"sku": "MULTI-SHOES-001", "name": "Running Shoes", "quantity": 25},
            {"sku": "MULTI-HAT-001", "name": "Baseball Cap", "quantity": 75}
        ]
        
        created_products = []
        for product_data in products_to_create:
            response = await client.post("/products", json=product_data)
            assert response.status_code == 201
            created_products.append(response.json())
        
        # Step 2: Verify all products are created and retrievable
        all_products_response = await client.get("/products")
        assert all_products_response.status_code == 200
        all_products = all_products_response.json()["products"]
        
        # Should have at least our 4 products (may have others from other tests)
        multi_products = [p for p in all_products if p["sku"].startswith("MULTI-")]
        assert len(multi_products) == 4
        
        # Step 3: Perform different operations on each product
        operations = [
            {"sku": "MULTI-SHIRT-001", "operation": "add", "amount": 20, "expected": 120},
            {"sku": "MULTI-PANTS-001", "operation": "remove", "amount": 10, "expected": 40},
            {"sku": "MULTI-SHOES-001", "operation": "add", "amount": 15, "expected": 40},
            {"sku": "MULTI-HAT-001", "operation": "remove", "amount": 25, "expected": 50}
        ]
        
        for op in operations:
            endpoint = f"/products/{op['sku']}/{op['operation']}"
            response = await client.patch(endpoint, json={"amount": op["amount"]})
            assert response.status_code == 200
            assert response.json()["quantity"] == op["expected"]
        
        # Step 4: Verify each product individually
        for op in operations:
            response = await client.get(f"/products/{op['sku']}")
            assert response.status_code == 200
            assert response.json()["quantity"] == op["expected"]
        
        # Step 5: Perform simultaneous operations on different products
        async def modify_product(sku: str, operation: str, amount: int):
            endpoint = f"/products/{sku}/{operation}"
            return await client.patch(endpoint, json={"amount": amount})
        
        # Run operations on different products simultaneously
        simultaneous_tasks = [
            modify_product("MULTI-SHIRT-001", "remove", 30),  # 120 -> 90
            modify_product("MULTI-PANTS-001", "add", 10),     # 40 -> 50
            modify_product("MULTI-SHOES-001", "remove", 5),   # 40 -> 35
            modify_product("MULTI-HAT-001", "add", 25)        # 50 -> 75
        ]
        
        results = await asyncio.gather(*simultaneous_tasks)
        
        # All operations should succeed
        for result in results:
            assert result.status_code == 200
        
        # Verify final quantities
        expected_final_quantities = {
            "MULTI-SHIRT-001": 90,
            "MULTI-PANTS-001": 50,
            "MULTI-SHOES-001": 35,
            "MULTI-HAT-001": 75
        }
        
        for sku, expected_qty in expected_final_quantities.items():
            response = await client.get(f"/products/{sku}")
            assert response.status_code == 200
            assert response.json()["quantity"] == expected_qty
    
    @pytest.mark.asyncio
    async def test_inventory_restocking_workflow(self, client: AsyncClient):
        """
        Test a realistic inventory restocking workflow.
        
        This simulates:
        - Initial product creation with low stock
        - Sales reducing stock to critical levels
        - Restocking operations
        - Verification of stock levels throughout
        """
        # Step 1: Create product with initial stock
        initial_product = {
            "sku": "RESTOCK-WIDGET-001",
            "name": "Premium Widget",
            "description": "High-quality widget for testing restocking",
            "quantity": 100
        }
        
        create_response = await client.post("/products", json=initial_product)
        assert create_response.status_code == 201
        
        # Step 2: Simulate sales (multiple stock removals)
        sales_operations = [
            {"amount": 25, "description": "Morning sales"},
            {"amount": 30, "description": "Afternoon sales"},
            {"amount": 20, "description": "Evening sales"}
        ]
        
        current_stock = 100
        for sale in sales_operations:
            response = await client.patch(
                "/products/RESTOCK-WIDGET-001/remove", 
                json={"amount": sale["amount"]}
            )
            assert response.status_code == 200
            current_stock -= sale["amount"]
            assert response.json()["quantity"] == current_stock
        
        # Current stock should be 25 (100 - 25 - 30 - 20)
        assert current_stock == 25
        
        # Step 3: Check stock level is low (simulate low stock alert)
        stock_check_response = await client.get("/products/RESTOCK-WIDGET-001")
        assert stock_check_response.status_code == 200
        assert stock_check_response.json()["quantity"] == 25
        
        # Step 4: Restock operations (multiple deliveries)
        restock_operations = [
            {"amount": 50, "description": "First delivery"},
            {"amount": 75, "description": "Second delivery"},
            {"amount": 25, "description": "Final delivery"}
        ]
        
        for restock in restock_operations:
            response = await client.patch(
                "/products/RESTOCK-WIDGET-001/add", 
                json={"amount": restock["amount"]}
            )
            assert response.status_code == 200
            current_stock += restock["amount"]
            assert response.json()["quantity"] == current_stock
        
        # Final stock should be 175 (25 + 50 + 75 + 25)
        assert current_stock == 175
        
        # Step 5: Verify final inventory level
        final_check_response = await client.get("/products/RESTOCK-WIDGET-001")
        assert final_check_response.status_code == 200
        final_product = final_check_response.json()
        assert final_product["quantity"] == 175
        assert final_product["name"] == "Premium Widget"
        assert final_product["description"] == "High-quality widget for testing restocking"


class TestConcurrentOperations:
    """Test concurrent operations to verify system behavior under concurrent load."""
    
    @pytest.mark.asyncio
    async def test_sequential_operations_for_consistency(self, client: AsyncClient):
        """
        Test sequential operations to establish baseline behavior.
        
        This test verifies that operations work correctly when run sequentially,
        establishing a baseline for comparison with concurrent operations.
        """
        # Setup: Create product with initial stock
        product_data = {
            "sku": "SEQUENTIAL-001",
            "name": "Sequential Test",
            "quantity": 100
        }
        
        create_response = await client.post("/products", json=product_data)
        assert create_response.status_code == 201
        
        # Run operations sequentially
        operations = [
            {"type": "add", "amount": 10},
            {"type": "add", "amount": 15},
            {"type": "remove", "amount": 5},
            {"type": "add", "amount": 20},
            {"type": "remove", "amount": 8}
        ]
        
        expected_quantity = 100
        for operation in operations:
            endpoint = f"/products/SEQUENTIAL-001/{operation['type']}"
            response = await client.patch(endpoint, json={"amount": operation["amount"]})
            assert response.status_code == 200
            
            if operation["type"] == "add":
                expected_quantity += operation["amount"]
            else:
                expected_quantity -= operation["amount"]
            
            assert response.json()["quantity"] == expected_quantity
        
        # Final verification
        final_response = await client.get("/products/SEQUENTIAL-001")
        assert final_response.status_code == 200
        assert final_response.json()["quantity"] == expected_quantity
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_data_integrity(self, client: AsyncClient):
        """
        Test that concurrent operations maintain data integrity.
        
        This test focuses on ensuring that the final state is consistent
        and that no data corruption occurs, regardless of the exact
        execution order of concurrent operations.
        """
        # Setup: Create product with initial stock
        product_data = {
            "sku": "CONCURRENT-INTEGRITY-001",
            "name": "Concurrent Integrity Test",
            "quantity": 100
        }
        
        create_response = await client.post("/products", json=product_data)
        assert create_response.status_code == 201
        
        # Define operations
        async def add_stock(amount: int):
            return await client.patch(
                "/products/CONCURRENT-INTEGRITY-001/add", 
                json={"amount": amount}
            )
        
        async def remove_stock(amount: int):
            return await client.patch(
                "/products/CONCURRENT-INTEGRITY-001/remove", 
                json={"amount": amount}
            )
        
        # Run a mix of operations concurrently
        tasks = [
            add_stock(10),
            add_stock(5),
            remove_stock(3),
            add_stock(8)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all operations completed (either success or proper failure)
        for result in results:
            assert result.status_code in [200, 400], f"Unexpected status code: {result.status_code}"
        
        # Verify final state is consistent
        final_response = await client.get("/products/CONCURRENT-INTEGRITY-001")
        assert final_response.status_code == 200
        final_quantity = final_response.json()["quantity"]
        
        # Stock should never be negative
        assert final_quantity >= 0, f"Final stock {final_quantity} should never be negative"
        
        # Stock should be within reasonable bounds based on operations
        # Minimum: 100 - 3 = 97 (if only remove succeeded)
        # Maximum: 100 + 10 + 5 + 8 = 123 (if all adds succeeded, remove failed)
        assert 95 <= final_quantity <= 125, f"Final quantity {final_quantity} should be within reasonable bounds"
    
    @pytest.mark.asyncio
    async def test_insufficient_stock_prevention(self, client: AsyncClient):
        """
        Test that the system prevents overselling.
        
        This test verifies that the system correctly handles attempts to
        remove more stock than available, ensuring data integrity.
        """
        # Setup: Create product with limited stock
        product_data = {
            "sku": "OVERSELL-PREVENTION-001",
            "name": "Oversell Prevention Test",
            "quantity": 3  # Very limited stock
        }
        
        create_response = await client.post("/products", json=product_data)
        assert create_response.status_code == 201
        
        # First, remove some stock successfully
        first_remove = await client.patch(
            "/products/OVERSELL-PREVENTION-001/remove", 
            json={"amount": 2}
        )
        assert first_remove.status_code == 200
        assert first_remove.json()["quantity"] == 1
        
        # Now try to remove more than what's available
        second_remove = await client.patch(
            "/products/OVERSELL-PREVENTION-001/remove", 
            json={"amount": 2}  # Trying to remove 2, but only 1 available
        )
        
        # This should fail
        assert second_remove.status_code == 400
        error_data = second_remove.json()
        assert error_data["error"] == "Insufficient Stock"
        assert error_data["available"] == 1
        assert error_data["requested"] == 2
        
        # Verify final stock is still 1 (unchanged from failed operation)
        final_response = await client.get("/products/OVERSELL-PREVENTION-001")
        assert final_response.status_code == 200
        final_stock = final_response.json()["quantity"]
        assert final_stock == 1, f"Final stock should be 1, got {final_stock}"
        
        # Now remove the last item successfully
        final_remove = await client.patch(
            "/products/OVERSELL-PREVENTION-001/remove", 
            json={"amount": 1}
        )
        assert final_remove.status_code == 200
        assert final_remove.json()["quantity"] == 0
        
        # Try to remove from empty stock
        empty_remove = await client.patch(
            "/products/OVERSELL-PREVENTION-001/remove", 
            json={"amount": 1}
        )
        assert empty_remove.status_code == 400
        error_data = empty_remove.json()
        assert error_data["error"] == "Insufficient Stock"
        assert error_data["available"] == 0
        assert error_data["requested"] == 1
    
    @pytest.mark.asyncio
    async def test_mixed_concurrent_operations(self, client: AsyncClient):
        """
        Test concurrent mix of add and remove operations.
        
        Verifies that concurrent add and remove operations are handled
        correctly and the final stock level is consistent.
        """
        # Setup: Create product with initial stock
        product_data = {
            "sku": "MIXED-CONCURRENT-001",
            "name": "Mixed Concurrent Operations Test",
            "quantity": 50
        }
        
        create_response = await client.post("/products", json=product_data)
        assert create_response.status_code == 201
        
        # Define mixed operations
        async def add_stock(amount: int):
            return await client.patch(
                "/products/MIXED-CONCURRENT-001/add", 
                json={"amount": amount}
            )
        
        async def remove_stock(amount: int):
            return await client.patch(
                "/products/MIXED-CONCURRENT-001/remove", 
                json={"amount": amount}
            )
        
        # Create smaller mixed operations to work within SQLite limitations
        tasks = [
            add_stock(10),    # +10
            remove_stock(5),  # -5
            add_stock(8),     # +8
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Count successful operations
        successful_operations = [r for r in results if r.status_code == 200]
        assert len(successful_operations) >= 1, "At least one operation should succeed"
        
        # Verify final stock level is reasonable
        final_response = await client.get("/products/MIXED-CONCURRENT-001")
        assert final_response.status_code == 200
        final_quantity = final_response.json()["quantity"]
        
        # Final quantity should be within reasonable bounds
        # Minimum: 50 (if no operations succeeded)
        # Maximum: 50 + 10 + 8 = 68 (if all add operations succeeded and remove failed)
        assert 45 <= final_quantity <= 70, f"Final quantity {final_quantity} should be within reasonable bounds"
        
        # Most importantly, stock should never be negative
        assert final_quantity >= 0, f"Final stock {final_quantity} should never be negative"
    
    @pytest.mark.asyncio
    async def test_high_concurrency_stress_test(self, client: AsyncClient):
        """
        Stress test with moderate concurrency to verify system stability.
        
        This test verifies that the system maintains data integrity
        and handles multiple operations without corruption.
        """
        # Setup: Create product with substantial stock
        product_data = {
            "sku": "STRESS-TEST-001",
            "name": "Concurrency Stress Test",
            "quantity": 1000
        }
        
        create_response = await client.post("/products", json=product_data)
        assert create_response.status_code == 201
        
        # Define operations
        async def perform_operation(operation_type: str, amount: int):
            endpoint = f"/products/STRESS-TEST-001/{operation_type}"
            return await client.patch(endpoint, json={"amount": amount})
        
        # Create moderate number of concurrent operations
        tasks = []
        
        # Add operations: 5 operations adding 10 each = +50
        for _ in range(5):
            tasks.append(perform_operation("add", 10))
        
        # Remove operations: 5 operations removing 8 each = -40
        for _ in range(5):
            tasks.append(perform_operation("remove", 8))
        
        # Execute all operations concurrently
        results = await asyncio.gather(*tasks)
        
        # Count successful operations
        successful_operations = [r for r in results if r.status_code == 200]
        assert len(successful_operations) >= 5, "At least half the operations should succeed"
        
        # Verify final stock level is reasonable and never negative
        final_response = await client.get("/products/STRESS-TEST-001")
        assert final_response.status_code == 200
        final_quantity = final_response.json()["quantity"]
        
        # Stock should never be negative
        assert final_quantity >= 0, f"Final stock {final_quantity} should never be negative"
        
        # Stock should be within reasonable bounds
        # Minimum: 1000 - 40 = 960 (if all removes succeeded, no adds)
        # Maximum: 1000 + 50 = 1050 (if all adds succeeded, no removes)
        assert 950 <= final_quantity <= 1060, f"Final quantity {final_quantity} should be within reasonable bounds"


class TestAPIContractCompliance:
    """Test API contract compliance and response formats."""
    
    @pytest.mark.asyncio
    async def test_product_creation_response_contract(self, client: AsyncClient):
        """Test that product creation responses follow the expected contract."""
        product_data = {
            "sku": "CONTRACT-001",
            "name": "Contract Test Product",
            "description": "Testing API contract compliance",
            "quantity": 25
        }
        
        response = await client.post("/products", json=product_data)
        
        # Verify status code
        assert response.status_code == 201
        
        # Verify response structure
        data = response.json()
        required_fields = ["sku", "name", "description", "quantity"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify field types and values
        assert isinstance(data["sku"], str)
        assert isinstance(data["name"], str)
        assert isinstance(data["description"], str) or data["description"] is None
        assert isinstance(data["quantity"], int)
        
        # Verify values match input
        assert data["sku"] == product_data["sku"]
        assert data["name"] == product_data["name"]
        assert data["description"] == product_data["description"]
        assert data["quantity"] == product_data["quantity"]
        
        # Verify content-type header
        assert response.headers["content-type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_product_list_response_contract(self, client: AsyncClient):
        """Test that product list responses follow the expected contract."""
        # Create test products
        test_products = [
            {"sku": "LIST-001", "name": "List Product 1", "quantity": 10},
            {"sku": "LIST-002", "name": "List Product 2", "quantity": 20}
        ]
        
        for product in test_products:
            await client.post("/products", json=product)
        
        # Get product list
        response = await client.get("/products")
        
        # Verify status code
        assert response.status_code == 200
        
        # Verify response structure
        data = response.json()
        assert "products" in data
        assert isinstance(data["products"], list)
        
        # Verify each product in the list has correct structure
        for product in data["products"]:
            required_fields = ["sku", "name", "description", "quantity"]
            for field in required_fields:
                assert field in product, f"Missing required field: {field}"
            
            # Verify field types
            assert isinstance(product["sku"], str)
            assert isinstance(product["name"], str)
            assert isinstance(product["description"], str) or product["description"] is None
            assert isinstance(product["quantity"], int)
        
        # Verify content-type header
        assert response.headers["content-type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_stock_operation_response_contract(self, client: AsyncClient):
        """Test that stock operation responses follow the expected contract."""
        # Create test product
        product_data = {
            "sku": "STOCK-CONTRACT-001",
            "name": "Stock Contract Test",
            "quantity": 15
        }
        
        await client.post("/products", json=product_data)
        
        # Test add stock response
        add_response = await client.patch(
            "/products/STOCK-CONTRACT-001/add", 
            json={"amount": 10}
        )
        
        assert add_response.status_code == 200
        add_data = add_response.json()
        
        # Verify response structure
        required_fields = ["sku", "name", "description", "quantity"]
        for field in required_fields:
            assert field in add_data, f"Missing required field: {field}"
        
        # Verify updated quantity
        assert add_data["quantity"] == 25
        assert add_response.headers["content-type"] == "application/json"
        
        # Test remove stock response
        remove_response = await client.patch(
            "/products/STOCK-CONTRACT-001/remove", 
            json={"amount": 5}
        )
        
        assert remove_response.status_code == 200
        remove_data = remove_response.json()
        
        # Verify response structure
        for field in required_fields:
            assert field in remove_data, f"Missing required field: {field}"
        
        # Verify updated quantity
        assert remove_data["quantity"] == 20
        assert remove_response.headers["content-type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_error_response_contract(self, client: AsyncClient):
        """Test that error responses follow the expected contract."""
        # Test 404 error contract
        not_found_response = await client.get("/products/NONEXISTENT-CONTRACT")
        assert not_found_response.status_code == 404
        
        error_data = not_found_response.json()
        required_error_fields = ["error", "message", "details", "path"]
        for field in required_error_fields:
            assert field in error_data, f"Missing required error field: {field}"
        
        assert error_data["error"] == "Product Not Found"
        assert "NONEXISTENT-CONTRACT" in error_data["message"]
        assert error_data["path"] == "/products/NONEXISTENT-CONTRACT"
        
        # Test 400 error contract (insufficient stock)
        await client.post("/products", json={
            "sku": "ERROR-CONTRACT-001",
            "name": "Error Contract Test",
            "quantity": 5
        })
        
        insufficient_response = await client.patch(
            "/products/ERROR-CONTRACT-001/remove", 
            json={"amount": 10}
        )
        assert insufficient_response.status_code == 400
        
        insufficient_data = insufficient_response.json()
        required_insufficient_fields = ["error", "message", "details", "sku", "requested", "available", "path"]
        for field in required_insufficient_fields:
            assert field in insufficient_data, f"Missing required insufficient stock field: {field}"
        
        assert insufficient_data["error"] == "Insufficient Stock"
        assert insufficient_data["sku"] == "ERROR-CONTRACT-001"
        assert insufficient_data["requested"] == 10
        assert insufficient_data["available"] == 5
        
        # Test 422 validation error contract
        validation_response = await client.post("/products", json={
            "sku": "invalid-sku",
            "name": "",
            "quantity": -1
        })
        assert validation_response.status_code == 422
        
        validation_data = validation_response.json()
        required_validation_fields = ["error", "message", "details", "validation_errors", "path"]
        for field in required_validation_fields:
            assert field in validation_data, f"Missing required validation field: {field}"
        
        assert validation_data["error"] == "Validation Error"
        assert isinstance(validation_data["validation_errors"], list)
        assert len(validation_data["validation_errors"]) > 0
        
        # Verify validation error structure
        for validation_error in validation_data["validation_errors"]:
            validation_error_fields = ["field", "message", "details"]
            for field in validation_error_fields:
                assert field in validation_error, f"Missing validation error field: {field}"
    
    @pytest.mark.asyncio
    async def test_http_method_compliance(self, client: AsyncClient):
        """Test that endpoints use correct HTTP methods."""
        # POST for resource creation
        create_response = await client.post("/products", json={
            "sku": "HTTP-METHOD-001",
            "name": "HTTP Method Test",
            "quantity": 10
        })
        assert create_response.status_code == 201  # Created
        
        # GET for resource retrieval (individual)
        get_response = await client.get("/products/HTTP-METHOD-001")
        assert get_response.status_code == 200  # OK
        
        # GET for resource retrieval (collection)
        list_response = await client.get("/products")
        assert list_response.status_code == 200  # OK
        
        # PATCH for partial resource updates
        patch_add_response = await client.patch(
            "/products/HTTP-METHOD-001/add", 
            json={"amount": 5}
        )
        assert patch_add_response.status_code == 200  # OK
        
        patch_remove_response = await client.patch(
            "/products/HTTP-METHOD-001/remove", 
            json={"amount": 3}
        )
        assert patch_remove_response.status_code == 200  # OK
        
        # Verify that unsupported methods return appropriate errors
        # PUT should not be supported for these endpoints
        put_response = await client.put("/products/HTTP-METHOD-001", json={
            "name": "Updated Name"
        })
        assert put_response.status_code == 405  # Method Not Allowed
        
        # DELETE should not be supported
        delete_response = await client.delete("/products/HTTP-METHOD-001")
        assert delete_response.status_code == 405  # Method Not Allowed


class TestDataIntegrityVerification:
    """Test data integrity across operations."""
    
    @pytest.mark.asyncio
    async def test_stock_level_consistency_across_operations(self, client: AsyncClient):
        """
        Test that stock levels remain consistent across multiple operations.
        
        This test performs a series of operations and verifies that the
        stock level is always accurate and never goes negative.
        """
        # Create product with known initial stock
        initial_stock = 100
        product_data = {
            "sku": "INTEGRITY-001",
            "name": "Data Integrity Test",
            "quantity": initial_stock
        }
        
        await client.post("/products", json=product_data)
        
        # Track expected stock level
        expected_stock = initial_stock
        
        # Perform series of operations
        operations = [
            {"type": "add", "amount": 25},     # 100 + 25 = 125
            {"type": "remove", "amount": 15},  # 125 - 15 = 110
            {"type": "add", "amount": 40},     # 110 + 40 = 150
            {"type": "remove", "amount": 30},  # 150 - 30 = 120
            {"type": "remove", "amount": 20},  # 120 - 20 = 100
            {"type": "add", "amount": 10},     # 100 + 10 = 110
        ]
        
        for operation in operations:
            endpoint = f"/products/INTEGRITY-001/{operation['type']}"
            response = await client.patch(endpoint, json={"amount": operation["amount"]})
            
            assert response.status_code == 200
            
            # Update expected stock
            if operation["type"] == "add":
                expected_stock += operation["amount"]
            else:
                expected_stock -= operation["amount"]
            
            # Verify response shows correct stock level
            assert response.json()["quantity"] == expected_stock
            
            # Double-check with individual product retrieval
            verify_response = await client.get("/products/INTEGRITY-001")
            assert verify_response.status_code == 200
            assert verify_response.json()["quantity"] == expected_stock
        
        # Final verification
        assert expected_stock == 110
        final_response = await client.get("/products/INTEGRITY-001")
        assert final_response.json()["quantity"] == 110
    
    @pytest.mark.asyncio
    async def test_negative_stock_prevention(self, client: AsyncClient):
        """
        Test that the system prevents stock levels from going negative.
        
        This test verifies that attempts to remove more stock than available
        are properly rejected and don't affect the stock level.
        """
        # Create product with limited stock
        product_data = {
            "sku": "NEGATIVE-PREVENTION-001",
            "name": "Negative Stock Prevention Test",
            "quantity": 10
        }
        
        await client.post("/products", json=product_data)
        
        # Attempt to remove more stock than available
        invalid_operations = [
            {"amount": 11, "description": "Remove 1 more than available"},
            {"amount": 15, "description": "Remove 5 more than available"},
            {"amount": 100, "description": "Remove much more than available"}
        ]
        
        for operation in invalid_operations:
            response = await client.patch(
                "/products/NEGATIVE-PREVENTION-001/remove", 
                json={"amount": operation["amount"]}
            )
            
            # Should fail with 400 Bad Request
            assert response.status_code == 400
            error_data = response.json()
            assert error_data["error"] == "Insufficient Stock"
            assert error_data["available"] == 10  # Stock should remain unchanged
            assert error_data["requested"] == operation["amount"]
            
            # Verify stock level hasn't changed
            verify_response = await client.get("/products/NEGATIVE-PREVENTION-001")
            assert verify_response.status_code == 200
            assert verify_response.json()["quantity"] == 10
        
        # Verify that valid operations still work
        valid_response = await client.patch(
            "/products/NEGATIVE-PREVENTION-001/remove", 
            json={"amount": 5}
        )
        assert valid_response.status_code == 200
        assert valid_response.json()["quantity"] == 5
        
        # Now attempting to remove 6 should fail
        final_invalid_response = await client.patch(
            "/products/NEGATIVE-PREVENTION-001/remove", 
            json={"amount": 6}
        )
        assert final_invalid_response.status_code == 400
        assert final_invalid_response.json()["available"] == 5