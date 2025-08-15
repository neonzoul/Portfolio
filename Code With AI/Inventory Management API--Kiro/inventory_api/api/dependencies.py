"""
FastAPI dependency injection configuration.

This module provides dependency functions for injecting services and repositories
into API route handlers, following the Dependency Inversion Principle.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from inventory_api.core.database import get_session
from inventory_api.repositories.protocols import ProductRepositoryProtocol
from inventory_api.repositories.sqlmodel import SQLModelProductRepository
from inventory_api.services.protocols import ProductServiceProtocol
from inventory_api.services.product import ProductService


async def get_product_repository(
    session: AsyncSession = Depends(get_session)
) -> ProductRepositoryProtocol:
    """
    Dependency function to provide product repository instance.
    
    This function creates a repository instance with the database session
    injected through FastAPI's dependency system.
    
    Args:
        session: Database session from dependency injection
        
    Returns:
        ProductRepositoryProtocol: Repository instance for data access
    """
    return SQLModelProductRepository(session)


async def get_product_service(
    repository: ProductRepositoryProtocol = Depends(get_product_repository)
) -> ProductServiceProtocol:
    """
    Dependency function to provide product service instance.
    
    This function creates a service instance with the repository
    injected through FastAPI's dependency system, enabling
    proper separation of concerns and testability.
    
    Args:
        repository: Repository instance from dependency injection
        
    Returns:
        ProductServiceProtocol: Service instance for business logic
    """
    return ProductService(repository)