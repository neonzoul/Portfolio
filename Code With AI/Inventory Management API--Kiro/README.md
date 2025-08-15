# Inventory Management API

A robust, production-ready REST API for managing product inventory with atomic stock operations and race condition prevention.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip or uv package manager

### Installation & Setup

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd inventory-management-api
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python run.py
   ```

4. **Access the API:**
   - **API Documentation (Swagger UI):** http://localhost:8000/docs
   - **Alternative Documentation (ReDoc):** http://localhost:8000/redoc
   - **Health Check:** http://localhost:8000/health

## 📋 API Overview

The Inventory Management API provides endpoints for:

- **Product Management:** Create and retrieve products
- **Stock Operations:** Add and remove stock with atomic safety
- **Inventory Tracking:** Monitor stock levels across all products

### Key Features

- ✅ **Atomic Transactions:** Prevents race conditions in concurrent stock operations
- ✅ **Type Safety:** Comprehensive type hints and Pydantic validation
- ✅ **RESTful Design:** Follows HTTP semantics and status code conventions
- ✅ **Comprehensive Error Handling:** Detailed error responses with proper status codes
- ✅ **Auto-Generated Documentation:** OpenAPI/Swagger documentation
- ✅ **Production Ready:** Proper logging, CORS, and configuration management

## 🔒 Concurrency & Race Condition Prevention

### The Problem

In inventory systems, race conditions can occur when multiple requests attempt to modify the same product's stock simultaneously. For example:

1. Customer A tries to buy the last item (quantity: 1 → 0)
2. Customer B tries to buy the last item (quantity: 1 → 0) 
3. Both requests read quantity=1, both think they can proceed
4. Result: quantity becomes -1 (overselling)

### The Solution: Atomic Transactions

This API implements **atomic stock operations** using database-level locking:

```python
async def remove_stock_atomic(self, sku: str, amount: int) -> Optional[Product]:
    """
    Atomic stock removal with race condition prevention.
    
    Process:
    1. SELECT FOR UPDATE locks the product row
    2. Check if sufficient stock is available  
    3. Update quantity if check passes
    4. Commit transaction (releases lock)
    """
    # Lock the row until transaction completes
    stmt = select(Product).where(Product.sku == sku).with_for_update()
    result = await self.session.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product or product.quantity < amount:
        return None  # Insufficient stock or product not found
    
    # Safe to update - we have the lock and sufficient stock
    product.quantity -= amount
    await self.session.commit()  # Releases the lock
    return product
```

### Why This Works

- **SELECT FOR UPDATE:** Locks the database row until the transaction completes
- **Read-Check-Update Pattern:** All operations happen within a single transaction
- **Automatic Rollback:** Failed operations don't modify the database
- **Serialized Access:** Concurrent requests are processed one at a time per product


## 🏗️ Architecture

### Design Principles

This API follows **declarative, data-oriented design** with emphasis on:

1. **Separation of Concerns:** Clear layered architecture (API → Service → Repository → Database)
2. **Type Safety:** Comprehensive type hints throughout the codebase
3. **Protocol-Based Interfaces:** Dependency inversion using Python protocols
4. **Atomic Operations:** Database transactions ensure data consistency
5. **Immutable Data Flow:** Request → Validation → Business Logic → Database

### Project Structure

```
inventory_api/
├── main.py                 # FastAPI application entry point
├── models/
│   ├── database.py         # SQLModel entities (database schema)
│   └── api.py             # Pydantic request/response models
├── repositories/
│   ├── protocols.py        # Repository interfaces
│   └── sqlmodel.py        # SQLModel implementations with atomic operations
├── services/
│   ├── protocols.py        # Service interfaces
│   └── product.py         # Business logic implementation
├── api/
│   ├── dependencies.py     # FastAPI dependency injection
│   └── routes.py          # API endpoint definitions
├── core/
│   ├── config.py          # Application configuration
│   ├── database.py        # Database connection setup
│   ├── exceptions.py      # Custom exception definitions
│   └── db_utils.py        # Database utilities
└── tests/                 # Comprehensive test suite
    ├── test_repositories.py
    ├── test_services.py
    ├── test_api.py
    └── test_integration.py
```

### Technology Stack

- **Web Framework:** FastAPI (async, type-safe, auto-documentation)
- **Database ORM:** SQLModel (combines SQLAlchemy + Pydantic)
- **Database:** SQLite (embedded, perfect for development and small deployments)
- **Validation:** Pydantic v2 (runtime type checking and serialization)
- **Testing:** pytest with async support

## 📚 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/products` | Create a new product |
| `GET` | `/products` | List all products |
| `GET` | `/products/{sku}` | Get product by SKU |
| `PATCH` | `/products/{sku}/add` | Add stock to product |
| `PATCH` | `/products/{sku}/remove` | Remove stock from product |
| `GET` | `/health` | Health check endpoint |

### Request/Response Examples

#### Create Product
```bash
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "TSHIRT-RED-L",
    "name": "Red T-Shirt (Large)",
    "description": "Comfortable cotton t-shirt in red, size large",
    "quantity": 25
  }'
```

**Response (201 Created):**
```json
{
  "sku": "TSHIRT-RED-L",
  "name": "Red T-Shirt (Large)", 
  "description": "Comfortable cotton t-shirt in red, size large",
  "quantity": 25
}
```

#### Remove Stock
```bash
curl -X PATCH "http://localhost:8000/products/TSHIRT-RED-L/remove" \
  -H "Content-Type: application/json" \
  -d '{"amount": 3}'
```

**Response (200 OK):**
```json
{
  "sku": "TSHIRT-RED-L",
  "name": "Red T-Shirt (Large)",
  "description": "Comfortable cotton t-shirt in red, size large", 
  "quantity": 22
}
```

#### Error Response (Insufficient Stock)
```bash
curl -X PATCH "http://localhost:8000/products/TSHIRT-RED-L/remove" \
  -H "Content-Type: application/json" \
  -d '{"amount": 50}'
```

**Response (400 Bad Request):**
```json
{
  "error": "Insufficient Stock",
  "message": "Insufficient stock for product 'TSHIRT-RED-L'",
  "details": "Requested: 50, Available: 22",
  "sku": "TSHIRT-RED-L",
  "requested": 50,
  "available": 22,
  "path": "/products/TSHIRT-RED-L/remove"
}
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=inventory_api

# Run specific test file
pytest tests/test_integration.py

# Run tests with verbose output
pytest -v
```

### Test Categories

- **Unit Tests:** Individual component testing (models, services, repositories)
- **Integration Tests:** End-to-end API workflow testing
- **Concurrency Tests:** Race condition and atomic operation verification
- **Error Handling Tests:** Comprehensive error scenario coverage

## 🔧 Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./inventory.db

# API Configuration  
API_TITLE=Inventory Management API
API_DESCRIPTION=A robust REST API for managing product inventory
API_VERSION=1.0.0

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true
ENVIRONMENT=development
```

### Production Considerations

For production deployment:

1. **Database:** Switch to PostgreSQL or MySQL
2. **Security:** Configure CORS origins appropriately
3. **Logging:** Implement structured logging
4. **Monitoring:** Add health checks and metrics
5. **Authentication:** Add API key or JWT authentication
6. **Rate Limiting:** Implement request rate limiting

## 🚀 Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run.py"]
```

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run with production server
pip install gunicorn
gunicorn inventory_api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📖 Additional Resources

- **Interactive API Documentation:** http://localhost:8000/docs
- **Alternative Documentation:** http://localhost:8000/redoc
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **SQLModel Documentation:** https://sqlmodel.tiangolo.com/
- **Pydantic Documentation:** https://docs.pydantic.dev/

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request