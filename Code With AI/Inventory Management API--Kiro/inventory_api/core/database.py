"""
Database connection and session management.

This module provides SQLModel database engine and session management
with proper async support and connection pooling.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from inventory_api.core.config import get_settings


# Global engine instance
engine = None


def get_engine():
    """
    Get or create the database engine.
    
    Returns:
        AsyncEngine: SQLAlchemy async engine instance
    """
    global engine
    if engine is None:
        settings = get_settings()
        
        # Convert sqlite:// to sqlite+aiosqlite:// for async support
        database_url = settings.database_url
        if database_url.startswith("sqlite://"):
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
        
        engine = create_async_engine(
            database_url,
            echo=settings.database_echo,
            future=True
        )
    
    return engine


# Create async session factory
async_session_factory = sessionmaker(
    bind=get_engine(),
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session() -> AsyncSession:
    """
    Dependency function to get database session.
    
    This function is used with FastAPI's dependency injection system
    to provide database sessions to route handlers.
    
    Yields:
        AsyncSession: Database session instance
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """
    Create all database tables with proper constraints.
    
    This function should be called during application startup
    to ensure all tables exist with the correct schema and constraints.
    
    The function will:
    1. Import all models to ensure they're registered with SQLModel
    2. Create tables with all constraints (CHECK, UNIQUE, etc.)
    3. Create indexes for performance optimization
    """
    # Import models to ensure they're registered with SQLModel metadata
    from inventory_api.models.database import Product
    from sqlalchemy import text
    
    engine = get_engine()
    async with engine.begin() as conn:
        # Create all tables with constraints
        await conn.run_sync(SQLModel.metadata.create_all)
        
        # Verify table creation by checking if Product table exists
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
        )
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            raise RuntimeError("Failed to create product table")


async def initialize_database():
    """
    Complete database initialization sequence.
    
    This function performs all necessary database setup:
    1. Creates tables with constraints
    2. Verifies database connectivity
    3. Optionally seeds initial data (if needed)
    
    Raises:
        RuntimeError: If database initialization fails
    """
    try:
        # Test database connectivity
        from sqlalchemy import text
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        # Create tables
        await create_tables()
        
        print("✓ Database tables created successfully")
        print("✓ Database constraints applied")
        print("✓ Database indexes created")
        
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        raise RuntimeError(f"Database initialization failed: {e}")


async def drop_tables():
    """
    Drop all database tables.
    
    This function is primarily used for testing and development.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)