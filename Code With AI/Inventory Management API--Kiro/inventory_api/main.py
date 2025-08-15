"""
FastAPI application entry point for Inventory Management API.

This module creates and configures the FastAPI application instance
with proper middleware, exception handlers, and routing setup.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from inventory_api.core.config import get_settings
from inventory_api.core.exceptions import setup_exception_handlers
from inventory_api.core.database import initialize_database
from inventory_api.api.routes import router as products_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.api_title,
        description="""
        ## Overview
        
        A robust, production-ready REST API for managing product inventory with atomic stock operations and race condition prevention.
        
        ## Key Features
        
        - ✅ **Atomic Transactions:** Prevents race conditions in concurrent stock operations
        - ✅ **Type Safety:** Comprehensive type hints and Pydantic validation  
        - ✅ **RESTful Design:** Follows HTTP semantics and status code conventions
        - ✅ **Comprehensive Error Handling:** Detailed error responses with proper status codes
        - ✅ **Production Ready:** Proper logging, CORS, and configuration management
        
        ## Quick Start
        
        1. **Create a product:** `POST /products`
        2. **View inventory:** `GET /products`
        3. **Add stock:** `PATCH /products/{sku}/add`
        4. **Remove stock:** `PATCH /products/{sku}/remove`
        
        ## Race Condition Prevention
        
        This API uses atomic database transactions with row-level locking to prevent race conditions.
        Multiple customers can safely attempt to purchase the same item simultaneously without causing
        overselling or negative stock levels.
        
        ## Error Handling
        
        All endpoints return consistent error responses with appropriate HTTP status codes:
        - `400 Bad Request`: Business logic errors (insufficient stock, duplicate SKU)
        - `404 Not Found`: Resource not found
        - `422 Unprocessable Entity`: Request validation errors
        - `500 Internal Server Error`: Unexpected server errors
        
        ## Additional Resources
        
        - **GitHub Repository:** [View Source Code](https://github.com/your-repo/inventory-management-api)
        - **API Examples:** [Comprehensive Examples](./docs/api-examples.md)
        - **Technical Deep Dive:** [Atomic Transactions](./docs/atomic-transactions.md)
        """,
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        contact={
            "name": "API Support",
            "email": "support@inventory-api.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        servers=[
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            },
            {
                "url": "https://api.inventory-management.com",
                "description": "Production server"
            }
        ],
        tags_metadata=[
            {
                "name": "products",
                "description": "Product management operations including creation, retrieval, and stock management.",
                "externalDocs": {
                    "description": "Product management guide",
                    "url": "https://docs.inventory-api.com/products",
                },
            },
            {
                "name": "health",
                "description": "Health check and system status endpoints.",
            },
        ]
    )
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include API routes
    app.include_router(products_router)
    
    # Add startup event to initialize database
    @app.on_event("startup")
    async def startup_event():
        """Initialize database and perform startup tasks."""
        print("🚀 Starting Inventory Management API...")
        await initialize_database()
        print("✓ Application startup complete")
    
    return app


# Create the application instance
app = create_app()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "inventory-management-api"}


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "inventory_api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload and settings.environment == "development"
    )