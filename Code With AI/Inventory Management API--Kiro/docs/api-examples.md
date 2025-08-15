# API Examples

This document provides comprehensive examples of all API endpoints with various scenarios including success cases, error cases, and edge cases.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. All endpoints are publicly accessible.

## Content Type

All requests that include a body should use:
```
Content-Type: application/json
```

---

## 📦 Product Management

### Create Product

Creates a new product with initial stock quantity.

**Endpoint:** `POST /products`

#### Success Case

**Request:**
```bash
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "LAPTOP-DELL-XPS13",
    "name": "Dell XPS 13 Laptop",
    "description": "13-inch ultrabook with Intel Core i7 processor",
    "quantity": 10
  }'
```

**Response (201 Created):**
```json
{
  "sku": "LAPTOP-DELL-XPS13",
  "name": "Dell XPS 13 Laptop",
  "description": "13-inch ultrabook with Intel Core i7 processor",
  "quantity": 10
}
```

#### Minimal Product (No Description)

**Request:**
```bash
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "MOUSE-WIRELESS",
    "name": "Wireless Mouse",
    "quantity": 50
  }'
```

**Response (201 Created):**
```json
{
  "sku": "MOUSE-WIRELESS",
  "name": "Wireless Mouse",
  "description": null,
  "quantity": 50
}
```

#### Error: Duplicate SKU

**Request:**
```bash
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "LAPTOP-DELL-XPS13",
    "name": "Another Laptop",
    "quantity": 5
  }'
```

**Response (400 Bad Request):**
```json
{
  "error": "Duplicate SKU",
  "message": "Product with SKU 'LAPTOP-DELL-XPS13' already exists",
  "details": "A product with SKU 'LAPTOP-DELL-XPS13' is already registered in the system",
  "sku": "LAPTOP-DELL-XPS13",
  "path": "/products"
}
```

#### Error: Validation Errors

**Request:**
```bash
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "invalid-sku",
    "name": "",
    "quantity": -5
  }'
```

**Response (422 Unprocessable Entity):**
```json
{
  "error": "Validation Error",
  "message": "Request validation failed",
  "details": "Found 3 validation error(s)",
  "validation_errors": [
    {
      "field": "sku",
      "message": "SKU format is invalid",
      "details": "SKU must contain only uppercase letters, numbers, and hyphens (e.g., 'PROD-001')",
      "provided_value": "invalid-sku"
    },
    {
      "field": "name",
      "message": "Product name cannot be empty or just whitespace",
      "details": "Name must be at least 1 character long",
      "provided_value": ""
    },
    {
      "field": "quantity",
      "message": "quantity must be greater than or equal to 0",
      "details": "Quantity cannot be negative",
      "provided_value": "-5"
    }
  ],
  "path": "/products"
}
```

---

## 📋 Product Retrieval

### Get All Products

Retrieves a list of all products in the inventory.

**Endpoint:** `GET /products`

#### Success Case

**Request:**
```bash
curl -X GET "http://localhost:8000/products"
```

**Response (200 OK):**
```json
{
  "products": [
    {
      "sku": "LAPTOP-DELL-XPS13",
      "name": "Dell XPS 13 Laptop",
      "description": "13-inch ultrabook with Intel Core i7 processor",
      "quantity": 10
    },
    {
      "sku": "MOUSE-WIRELESS",
      "name": "Wireless Mouse",
      "description": null,
      "quantity": 50
    },
    {
      "sku": "TSHIRT-RED-L",
      "name": "Red T-Shirt (Large)",
      "description": "Comfortable cotton t-shirt in red, size large",
      "quantity": 25
    }
  ]
}
```

#### Empty Inventory

**Request:**
```bash
curl -X GET "http://localhost:8000/products"
```

**Response (200 OK):**
```json
{
  "products": []
}
```

### Get Product by SKU

Retrieves a specific product by its Stock Keeping Unit (SKU).

**Endpoint:** `GET /products/{sku}`

#### Success Case

**Request:**
```bash
curl -X GET "http://localhost:8000/products/LAPTOP-DELL-XPS13"
```

**Response (200 OK):**
```json
{
  "sku": "LAPTOP-DELL-XPS13",
  "name": "Dell XPS 13 Laptop",
  "description": "13-inch ultrabook with Intel Core i7 processor",
  "quantity": 10
}
```

#### Error: Product Not Found

**Request:**
```bash
curl -X GET "http://localhost:8000/products/NONEXISTENT-SKU"
```

**Response (404 Not Found):**
```json
{
  "error": "Product Not Found",
  "message": "Product with SKU 'NONEXISTENT-SKU' not found",
  "details": "No product exists with the specified SKU: NONEXISTENT-SKU",
  "path": "/products/NONEXISTENT-SKU"
}
```

---

## 📈 Stock Operations

### Add Stock

Increases the stock quantity of a product. This operation is atomic and safe for concurrent access.

**Endpoint:** `PATCH /products/{sku}/add`

#### Success Case

**Request:**
```bash
curl -X PATCH "http://localhost:8000/products/LAPTOP-DELL-XPS13/add" \
  -H "Content-Type: application/json" \
  -d '{"amount": 5}'
```

**Response (200 OK):**
```json
{
  "sku": "LAPTOP-DELL-XPS13",
  "name": "Dell XPS 13 Laptop",
  "description": "13-inch ultrabook with Intel Core i7 processor",
  "quantity": 15
}
```

#### Large Stock Addition

**Request:**
```bash
curl -X PATCH "http://localhost:8000/products/MOUSE-WIRELESS/add" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100}'
```

**Response (200 OK):**
```json
{
  "sku": "MOUSE-WIRELESS",
  "name": "Wireless Mouse",
  "description": null,
  "quantity": 150
}
```

#### Error: Product Not Found

**Request:**
```bash
curl -X PATCH "http://localhost:8000/products/NONEXISTENT-SKU/add" \
  -H "Content-Type: application/json" \
  -d '{"amount": 10}'
```

**Response (404 Not Found):**
```json
{
  "error": "Product Not Found",
  "message": "Product with SKU 'NONEXISTENT-SKU' not found",
  "details": "No product exists with the specified SKU: NONEXISTENT-SKU",
  "path": "/products/NONEXISTENT-SKU/add"
}
```

#### Error: Invalid Amount

**Request:**
```bash
curl -X PATCH "http://localhost:8000/products/LAPTOP-DELL-XPS13/add" \
  -H "Content-Type: application/json" \
  -d '{"amount": 0}'
```

**Response (422 Unprocessable Entity):**
```json
{
  "error": "Validation Error",
  "message": "Request validation failed",
  "details": "Found 1 validation error(s)",
  "validation_errors": [
    {
      "field": "amount",
      "message": "amount must be greater than 0",
      "details": "Amount must be a positive integer",
      "provided_value": "0"
    }
  ],
  "path": "/products/LAPTOP-DELL-XPS13/add"
}
```

### Remove Stock

Decreases the stock quantity of a product with safety checks to prevent negative stock levels. This operation is atomic and handles concurrent access safely.

**Endpoint:** `PATCH /products/{sku}/remove`

#### Success Case

**Request:**
```bash
curl -X PATCH "http://localhost:8000/products/LAPTOP-DELL-XPS13/remove" \
  -H "Content-Type: application/json" \
  -d '{"amount": 3}'
```

**Response (200 OK):**
```json
{
  "sku": "LAPTOP-DELL-XPS13",
  "name": "Dell XPS 13 Laptop",
  "description": "13-inch ultrabook with Intel Core i7 processor",
  "quantity": 12
}
```

#### Remove All Stock

**Request:**
```bash
curl -X PATCH "http://localhost:8000/products/TSHIRT-RED-L/remove" \
  -H "Content-Type: application/json" \
  -d '{"amount": 25}'
```

**Response (200 OK):**
```json
{
  "sku": "TSHIRT-RED-L",
  "name": "Red T-Shirt (Large)",
  "description": "Comfortable cotton t-shirt in red, size large",
  "quantity": 0
}
```

#### Error: Insufficient Stock

**Request:**
```bash
curl -X PATCH "http://localhost:8000/products/LAPTOP-DELL-XPS13/remove" \
  -H "Content-Type: application/json" \
  -d '{"amount": 20}'
```

**Response (400 Bad Request):**
```json
{
  "error": "Insufficient Stock",
  "message": "Insufficient stock for product 'LAPTOP-DELL-XPS13'",
  "details": "Requested: 20, Available: 12",
  "sku": "LAPTOP-DELL-XPS13",
  "requested": 20,
  "available": 12,
  "path": "/products/LAPTOP-DELL-XPS13/remove"
}
```

#### Error: Product Not Found

**Request:**
```bash
curl -X PATCH "http://localhost:8000/products/NONEXISTENT-SKU/remove" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1}'
```

**Response (404 Not Found):**
```json
{
  "error": "Product Not Found",
  "message": "Product with SKU 'NONEXISTENT-SKU' not found",
  "details": "No product exists with the specified SKU: NONEXISTENT-SKU",
  "path": "/products/NONEXISTENT-SKU/remove"
}
```

#### Error: Invalid Amount

**Request:**
```bash
curl -X PATCH "http://localhost:8000/products/LAPTOP-DELL-XPS13/remove" \
  -H "Content-Type: application/json" \
  -d '{"amount": -5}'
```

**Response (422 Unprocessable Entity):**
```json
{
  "error": "Validation Error",
  "message": "Request validation failed",
  "details": "Found 1 validation error(s)",
  "validation_errors": [
    {
      "field": "amount",
      "message": "amount must be greater than 0",
      "details": "Amount must be a positive integer",
      "provided_value": "-5"
    }
  ],
  "path": "/products/LAPTOP-DELL-XPS13/remove"
}
```

---

## 🏥 Health Check

### Health Check Endpoint

Simple endpoint to verify the API is running and responsive.

**Endpoint:** `GET /health`

#### Success Case

**Request:**
```bash
curl -X GET "http://localhost:8000/health"
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "inventory-management-api"
}
```

---

## 🔄 Complete Workflow Examples

### Example 1: E-commerce Order Processing

This example demonstrates a typical e-commerce workflow:

1. **Create products:**
```bash
# Add a laptop
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "LAPTOP-GAMING-001",
    "name": "Gaming Laptop RTX 4070",
    "description": "High-performance gaming laptop with RTX 4070",
    "quantity": 5
  }'

# Add accessories
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "MOUSE-GAMING-RGB",
    "name": "RGB Gaming Mouse",
    "description": "Wireless gaming mouse with RGB lighting",
    "quantity": 20
  }'
```

2. **Check inventory:**
```bash
curl -X GET "http://localhost:8000/products"
```

3. **Process customer orders:**
```bash
# Customer 1 buys 1 laptop and 1 mouse
curl -X PATCH "http://localhost:8000/products/LAPTOP-GAMING-001/remove" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1}'

curl -X PATCH "http://localhost:8000/products/MOUSE-GAMING-RGB/remove" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1}'

# Customer 2 buys 2 laptops
curl -X PATCH "http://localhost:8000/products/LAPTOP-GAMING-001/remove" \
  -H "Content-Type: application/json" \
  -d '{"amount": 2}'
```

4. **Restock inventory:**
```bash
# Receive new shipment
curl -X PATCH "http://localhost:8000/products/LAPTOP-GAMING-001/add" \
  -H "Content-Type: application/json" \
  -d '{"amount": 10}'
```

### Example 2: Concurrent Access Simulation

This example shows how the API handles concurrent requests safely:

```bash
# Create a product with limited stock
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "LIMITED-EDITION-001",
    "name": "Limited Edition Item",
    "quantity": 1
  }'

# Simulate two customers trying to buy the last item simultaneously
# In practice, only one of these would succeed
curl -X PATCH "http://localhost:8000/products/LIMITED-EDITION-001/remove" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1}' &

curl -X PATCH "http://localhost:8000/products/LIMITED-EDITION-001/remove" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1}' &

wait

# Check final state - should be 0, not negative
curl -X GET "http://localhost:8000/products/LIMITED-EDITION-001"
```

---

## 📊 HTTP Status Codes

| Status Code | Meaning | When Used |
|-------------|---------|-----------|
| `200 OK` | Success | Successful GET, PATCH operations |
| `201 Created` | Resource Created | Successful POST operations |
| `400 Bad Request` | Client Error | Business logic errors (insufficient stock, duplicate SKU) |
| `404 Not Found` | Resource Not Found | Product with specified SKU doesn't exist |
| `422 Unprocessable Entity` | Validation Error | Request format/validation errors |
| `500 Internal Server Error` | Server Error | Unexpected server or database errors |

---

## 🔧 Testing with Different Tools

### Using HTTPie

```bash
# Install HTTPie
pip install httpie

# Create product
http POST localhost:8000/products sku=TEST-001 name="Test Product" quantity:=10

# Get product
http GET localhost:8000/products/TEST-001

# Remove stock
http PATCH localhost:8000/products/TEST-001/remove amount:=3
```

### Using Python requests

```python
import requests

base_url = "http://localhost:8000"

# Create product
response = requests.post(f"{base_url}/products", json={
    "sku": "PYTHON-TEST-001",
    "name": "Python Test Product",
    "quantity": 15
})
print(f"Created: {response.status_code} - {response.json()}")

# Get product
response = requests.get(f"{base_url}/products/PYTHON-TEST-001")
print(f"Retrieved: {response.status_code} - {response.json()}")

# Remove stock
response = requests.patch(f"{base_url}/products/PYTHON-TEST-001/remove", json={
    "amount": 5
})
print(f"Updated: {response.status_code} - {response.json()}")
```

### Using JavaScript/Node.js

```javascript
const axios = require('axios');

const baseURL = 'http://localhost:8000';

async function testAPI() {
  try {
    // Create product
    const createResponse = await axios.post(`${baseURL}/products`, {
      sku: 'JS-TEST-001',
      name: 'JavaScript Test Product',
      quantity: 20
    });
    console.log('Created:', createResponse.status, createResponse.data);

    // Get product
    const getResponse = await axios.get(`${baseURL}/products/JS-TEST-001`);
    console.log('Retrieved:', getResponse.status, getResponse.data);

    // Remove stock
    const updateResponse = await axios.patch(`${baseURL}/products/JS-TEST-001/remove`, {
      amount: 7
    });
    console.log('Updated:', updateResponse.status, updateResponse.data);

  } catch (error) {
    console.error('Error:', error.response?.status, error.response?.data);
  }
}

testAPI();
```

---

## 🚀 Next Steps

After exploring these examples:

1. **Visit the Interactive Documentation:** http://localhost:8000/docs
2. **Try the ReDoc Documentation:** http://localhost:8000/redoc
3. **Run the Test Suite:** `pytest tests/`
4. **Explore the Source Code:** Check out the repository structure
5. **Build Your Own Client:** Use these examples as a reference

For more advanced usage and deployment options, see the main [README.md](../README.md) file.