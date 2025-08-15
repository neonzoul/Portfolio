# Project Structure and Architectural Decisions

This document explains the project structure, architectural decisions, and design patterns used in the Inventory Management API.

## 📁 Project Structure Overview

```
inventory-management-api/
├── 📄 README.md                    # Main project documentation
├── 📄 requirements.txt             # Python dependencies
├── 📄 run.py                      # Application entry point
├── 📄 pytest.ini                 # Test configuration
├── 📄 .env.example               # Environment variables template
├── 📄 inventory.db               # SQLite database file (created at runtime)
│
├── 📁 inventory_api/             # Main application package
│   ├── 📄 __init__.py
│   ├── 📄 main.py               # FastAPI application factory
│   │
│   ├── 📁 models/               # Data models and schemas
│   │   ├── 📄 __init__.py
│   │   ├── 📄 database.py       # SQLModel entities (database schema)
│   │   └── 📄 api.py           # Pydantic request/response models
│   │
│   ├── 📁 repositories/         # Data access layer
│   │   ├── 📄 __init__.py
│   │   ├── 📄 protocols.py      # Repository interfaces (contracts)
│   │   └── 📄 sqlmodel.py      # SQLModel implementation with atomic operations
│   │
│   ├── 📁 services/            # Business logic layer
│   │   ├── 📄 __init__.py
│   │   ├── 📄 protocols.py      # Service interfaces (contracts)
│   │   └── 📄 product.py       # Product business logic implementation
│   │
│   ├── 📁 api/                 # API layer (HTTP interface)
│   │   ├── 📄 __init__.py
│   │   ├── 📄 dependencies.py   # FastAPI dependency injection
│   │   └── 📄 routes.py        # API endpoint definitions
│   │
│   └── 📁 core/                # Core utilities and configuration
│       ├── 📄 __init__.py
│       ├── 📄 config.py        # Application configuration
│       ├── 📄 database.py      # Database connection setup
│       ├── 📄 exceptions.py    # Custom exception definitions
│       └── 📄 db_utils.py      # Database utilities
│
├── 📁 tests/                   # Test suite
│   ├── 📄 __init__.py
│   ├── 📄 conftest.py          # Test configuration and fixtures
│   ├── 📄 test_models.py       # Model validation tests
│   ├── 📄 test_repositories.py # Repository layer tests
│   ├── 📄 test_services.py     # Service layer tests
│   ├── 📄 test_api.py          # API endpoint tests
│   ├── 📄 test_integration.py  # End-to-end integration tests
│   └── 📄 test_error_handling.py # Error handling tests
│
├── 📁 docs/                    # Documentation
│   ├── 📄 api-examples.md      # Comprehensive API examples
│   ├── 📄 atomic-transactions.md # Technical deep-dive on concurrency
│   └── 📄 project-structure.md # This file
│
└── 📁 .kiro/                   # Kiro IDE configuration
    └── 📁 specs/
        └── 📁 inventory-management-api/
            ├── 📄 requirements.md
            ├── 📄 design.md
            ├── 📄 tasks.md
            └── 📄 Implement-report.md
```

## 🏗️ Architectural Decisions

### 1. Layered Architecture

The application follows a **clean architecture** pattern with clear separation of concerns:

```
┌─────────────────┐
│   API Layer     │  ← HTTP interface, routing, serialization
├─────────────────┤
│ Service Layer   │  ← Business logic, validation, orchestration
├─────────────────┤
│Repository Layer │  ← Data access, atomic operations, persistence
├─────────────────┤
│ Database Layer  │  ← SQLite/SQLModel, constraints, transactions
└─────────────────┘
```

**Benefits:**
- **Testability:** Each layer can be tested in isolation
- **Maintainability:** Changes in one layer don't affect others
- **Flexibility:** Easy to swap implementations (e.g., database providers)
- **Clarity:** Clear responsibilities for each component

### 2. Protocol-Based Interfaces

We use Python's `typing.Protocol` for defining interfaces:

```python
# repositories/protocols.py
class ProductRepositoryProtocol(Protocol):
    async def create_product(self, product_data: ProductCreate) -> Product: ...
    async def get_product_by_sku(self, sku: str) -> Product | None: ...
    async def add_stock_atomic(self, sku: str, amount: int) -> Product | None: ...
    async def remove_stock_atomic(self, sku: str, amount: int) -> Product | None: ...
```

**Benefits:**
- **Dependency Inversion:** High-level modules don't depend on low-level modules
- **Testability:** Easy to create mock implementations for testing
- **Flexibility:** Can swap implementations without changing business logic
- **Type Safety:** Static type checking ensures interface compliance

### 3. Dependency Injection with FastAPI

FastAPI's dependency injection system manages object creation and lifecycle:

```python
# api/dependencies.py
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session with automatic cleanup."""
    async with AsyncSessionLocal() as session:
        yield session

async def get_product_repository(
    session: AsyncSession = Depends(get_db_session)
) -> ProductRepositoryProtocol:
    """Provide product repository instance."""
    return SQLModelProductRepository(session)

async def get_product_service(
    repository: ProductRepositoryProtocol = Depends(get_product_repository)
) -> ProductServiceProtocol:
    """Provide product service instance."""
    return ProductService(repository)
```

**Benefits:**
- **Automatic Lifecycle Management:** Sessions are created and cleaned up automatically
- **Easy Testing:** Dependencies can be overridden for testing
- **Loose Coupling:** Components don't create their own dependencies
- **Configuration:** Easy to configure different implementations for different environments

## 📦 Layer-by-Layer Breakdown

### API Layer (`inventory_api/api/`)

**Purpose:** HTTP interface and request/response handling

**Key Files:**
- `routes.py`: FastAPI endpoint definitions with OpenAPI documentation
- `dependencies.py`: Dependency injection configuration

**Responsibilities:**
- HTTP request parsing and validation
- Response serialization
- Error handling and status code mapping
- API documentation generation
- CORS and middleware configuration

**Design Decisions:**
- **RESTful URLs:** `/products`, `/products/{sku}`, `/products/{sku}/add`
- **HTTP Semantics:** POST for creation, GET for retrieval, PATCH for updates
- **Comprehensive Documentation:** Every endpoint has detailed docstrings and examples
- **Error Response Consistency:** Standardized error response format across all endpoints

### Service Layer (`inventory_api/services/`)

**Purpose:** Business logic and orchestration

**Key Files:**
- `protocols.py`: Service interface definitions
- `product.py`: Product business logic implementation

**Responsibilities:**
- Business rule validation
- Error handling and translation
- Transaction coordination
- Data transformation between layers

**Design Decisions:**
- **Single Responsibility:** Each service handles one business domain
- **Error Translation:** Converts repository errors to business-meaningful exceptions
- **Validation:** Business rule validation separate from data validation
- **Stateless:** Services don't maintain state between requests

### Repository Layer (`inventory_api/repositories/`)

**Purpose:** Data access and persistence

**Key Files:**
- `protocols.py`: Repository interface definitions
- `sqlmodel.py`: SQLModel implementation with atomic operations

**Responsibilities:**
- Database operations (CRUD)
- Transaction management
- Atomic operations with locking
- Data integrity enforcement

**Design Decisions:**
- **Atomic Operations:** All stock operations use SELECT FOR UPDATE
- **Error Handling:** Database errors are caught and translated
- **Session Management:** Repository receives session from dependency injection
- **Query Optimization:** Efficient queries with proper indexing

### Models (`inventory_api/models/`)

**Purpose:** Data structures and validation

**Key Files:**
- `database.py`: SQLModel entities (database schema)
- `api.py`: Pydantic request/response models

**Responsibilities:**
- Data validation and serialization
- Database schema definition
- Type safety and documentation

**Design Decisions:**
- **Separation of Concerns:** Database models separate from API models
- **Comprehensive Validation:** Field-level and model-level validation
- **Type Safety:** Full type hints throughout
- **Documentation:** Models serve as living documentation

### Core (`inventory_api/core/`)

**Purpose:** Shared utilities and configuration

**Key Files:**
- `config.py`: Application configuration management
- `database.py`: Database connection and session setup
- `exceptions.py`: Custom exception definitions
- `db_utils.py`: Database utilities and initialization

**Responsibilities:**
- Configuration management
- Database connection setup
- Custom exception definitions
- Shared utilities

**Design Decisions:**
- **Environment-Based Configuration:** Different settings for dev/test/prod
- **Async Database Operations:** Full async support throughout
- **Custom Exceptions:** Business-meaningful exception hierarchy
- **Database Initialization:** Automatic table creation and setup

## 🧪 Testing Strategy

### Test Structure

```
tests/
├── conftest.py              # Shared test fixtures and configuration
├── test_models.py           # Model validation and serialization tests
├── test_repositories.py     # Data access layer tests
├── test_services.py         # Business logic tests
├── test_api.py             # HTTP endpoint tests
├── test_integration.py     # End-to-end workflow tests
└── test_error_handling.py  # Error scenario tests
```

### Testing Approach

1. **Unit Tests:** Test individual components in isolation
2. **Integration Tests:** Test component interactions
3. **End-to-End Tests:** Test complete user workflows
4. **Concurrency Tests:** Test atomic operations under load

### Test Fixtures

```python
# conftest.py
@pytest.fixture
async def db_session():
    """Provide clean database session for each test."""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()  # Clean up after test

@pytest.fixture
async def product_repository(db_session):
    """Provide repository instance for testing."""
    return SQLModelProductRepository(db_session)

@pytest.fixture
async def product_service(product_repository):
    """Provide service instance for testing."""
    return ProductService(product_repository)
```

## 🔧 Configuration Management

### Environment-Based Configuration

```python
# core/config.py
class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./inventory.db"
    
    # API Configuration
    api_title: str = "Inventory Management API"
    api_description: str = "A robust REST API for managing product inventory"
    api_version: str = "1.0.0"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

### Environment Files

```bash
# .env.example
DATABASE_URL=sqlite+aiosqlite:///./inventory.db
API_TITLE=Inventory Management API
API_DESCRIPTION=A robust REST API for managing product inventory
API_VERSION=1.0.0
HOST=0.0.0.0
PORT=8000
RELOAD=true
ENVIRONMENT=development
```

## 🚀 Deployment Considerations

### Production Structure

For production deployment, consider this enhanced structure:

```
inventory-management-api/
├── 📁 docker/                  # Docker configuration
│   ├── 📄 Dockerfile
│   ├── 📄 docker-compose.yml
│   └── 📄 docker-compose.prod.yml
│
├── 📁 scripts/                # Deployment and utility scripts
│   ├── 📄 deploy.sh
│   ├── 📄 migrate.py
│   └── 📄 health_check.py
│
├── 📁 monitoring/             # Monitoring and observability
│   ├── 📄 prometheus.yml
│   ├── 📄 grafana-dashboard.json
│   └── 📄 alerts.yml
│
└── 📁 k8s/                   # Kubernetes manifests
    ├── 📄 deployment.yaml
    ├── 📄 service.yaml
    ├── 📄 configmap.yaml
    └── 📄 ingress.yaml
```

### Scalability Considerations

1. **Database:** Switch to PostgreSQL or MySQL for production
2. **Caching:** Add Redis for caching frequently accessed data
3. **Load Balancing:** Multiple API instances behind a load balancer
4. **Monitoring:** Prometheus metrics and Grafana dashboards
5. **Logging:** Structured logging with ELK stack or similar

## 📋 Design Patterns Used

### 1. Repository Pattern
- **Purpose:** Encapsulate data access logic
- **Implementation:** `ProductRepositoryProtocol` and `SQLModelProductRepository`
- **Benefits:** Testability, flexibility, separation of concerns

### 2. Service Layer Pattern
- **Purpose:** Encapsulate business logic
- **Implementation:** `ProductServiceProtocol` and `ProductService`
- **Benefits:** Reusability, testability, clear business boundaries

### 3. Dependency Injection
- **Purpose:** Manage object dependencies and lifecycle
- **Implementation:** FastAPI's `Depends()` system
- **Benefits:** Loose coupling, testability, configuration flexibility

### 4. Factory Pattern
- **Purpose:** Create configured application instances
- **Implementation:** `create_app()` function in `main.py`
- **Benefits:** Consistent configuration, easy testing, environment-specific setup

### 5. Protocol Pattern (Interface Segregation)
- **Purpose:** Define contracts without implementation
- **Implementation:** `typing.Protocol` for repository and service interfaces
- **Benefits:** Type safety, flexibility, dependency inversion

## 🎯 Key Architectural Benefits

### 1. Maintainability
- **Clear Structure:** Each component has a single responsibility
- **Loose Coupling:** Components interact through well-defined interfaces
- **Consistent Patterns:** Same patterns used throughout the codebase

### 2. Testability
- **Isolated Testing:** Each layer can be tested independently
- **Mock-Friendly:** Protocol-based interfaces make mocking easy
- **Comprehensive Coverage:** Unit, integration, and end-to-end tests

### 3. Scalability
- **Stateless Design:** No shared state between requests
- **Async Operations:** Full async support for high concurrency
- **Database Optimization:** Proper indexing and atomic operations

### 4. Type Safety
- **Comprehensive Types:** Type hints throughout the codebase
- **Runtime Validation:** Pydantic models validate data at runtime
- **IDE Support:** Full IntelliSense and error detection

### 5. Documentation
- **Self-Documenting:** Code structure and types serve as documentation
- **API Documentation:** Automatic OpenAPI/Swagger generation
- **Comprehensive Examples:** Real-world usage examples and scenarios

## 🔄 Future Enhancements

### Potential Improvements

1. **Caching Layer:** Add Redis for frequently accessed products
2. **Event Sourcing:** Track all inventory changes for audit trails
3. **Message Queues:** Async processing for bulk operations
4. **Multi-tenancy:** Support for multiple organizations
5. **Advanced Querying:** Search, filtering, and pagination
6. **Batch Operations:** Bulk product creation and updates
7. **Webhooks:** Notify external systems of inventory changes
8. **Rate Limiting:** Protect against abuse and ensure fair usage

### Migration Path

The current architecture supports these enhancements without major refactoring:

- **New layers** can be added without affecting existing ones
- **Protocol-based interfaces** make it easy to add new implementations
- **Dependency injection** allows easy configuration of new components
- **Comprehensive testing** ensures changes don't break existing functionality

This architecture provides a solid foundation for both current requirements and future growth.