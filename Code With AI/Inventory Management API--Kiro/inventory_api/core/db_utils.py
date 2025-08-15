"""
Database utility functions for management and maintenance.

This module provides utility functions for database operations
that are useful for development, testing, and maintenance.
"""

import asyncio
from typing import Dict, Any

from sqlalchemy import text
from inventory_api.core.database import get_engine, initialize_database, drop_tables
from inventory_api.models.database import Product


async def get_database_info() -> Dict[str, Any]:
    """
    Get information about the database and tables.
    
    Returns:
        Dict containing database information
    """
    engine = get_engine()
    info = {
        "database_url": str(engine.url),
        "tables": [],
        "product_count": 0
    }
    
    try:
        async with engine.begin() as conn:
            # Get table information
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = [row[0] for row in result.fetchall()]
            info["tables"] = tables
            
            # Get product count if table exists
            if "product" in tables:
                result = await conn.execute(text("SELECT COUNT(*) FROM product"))
                info["product_count"] = result.scalar()
                
    except Exception as e:
        info["error"] = str(e)
    
    return info


async def verify_database_constraints():
    """
    Verify that database constraints are properly applied.
    
    Returns:
        Dict containing constraint verification results
    """
    engine = get_engine()
    results = {
        "constraints_verified": False,
        "checks": []
    }
    
    try:
        async with engine.begin() as conn:
            # Check if positive_quantity constraint exists
            result = await conn.execute(
                text("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='product'
                """)
            )
            
            table_sql = result.scalar()
            if table_sql and "positive_quantity" in table_sql:
                results["checks"].append({
                    "constraint": "positive_quantity",
                    "status": "present",
                    "description": "CHECK constraint preventing negative quantities"
                })
            else:
                results["checks"].append({
                    "constraint": "positive_quantity", 
                    "status": "missing",
                    "description": "CHECK constraint for positive quantities not found"
                })
            
            # Check unique constraint on SKU
            result = await conn.execute(
                text("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='index' AND name LIKE '%sku%'
                """)
            )
            
            sku_indexes = result.scalar()
            if sku_indexes > 0:
                results["checks"].append({
                    "constraint": "unique_sku",
                    "status": "present", 
                    "description": "UNIQUE constraint on SKU field"
                })
            else:
                results["checks"].append({
                    "constraint": "unique_sku",
                    "status": "missing",
                    "description": "UNIQUE constraint on SKU not found"
                })
            
            # Overall verification
            results["constraints_verified"] = all(
                check["status"] == "present" for check in results["checks"]
            )
            
    except Exception as e:
        results["error"] = str(e)
    
    return results


async def create_sample_data():
    """
    Create sample product data for testing and development.
    
    This function creates a few sample products that can be used
    for testing the API functionality.
    """
    from inventory_api.repositories.sqlmodel import SQLModelProductRepository
    from inventory_api.core.database import async_session_factory
    from inventory_api.models.api import ProductCreate
    
    sample_products = [
        ProductCreate(
            sku="TSHIRT-RED-L",
            name="Red T-Shirt (Large)",
            description="Comfortable cotton t-shirt in red, size large",
            quantity=25
        ),
        ProductCreate(
            sku="JEANS-BLUE-32",
            name="Blue Jeans (32 waist)",
            description="Classic blue denim jeans, 32 inch waist",
            quantity=15
        ),
        ProductCreate(
            sku="SNEAKERS-WHITE-10",
            name="White Sneakers (Size 10)",
            description="Comfortable white sneakers, size 10",
            quantity=8
        )
    ]
    
    async with async_session_factory() as session:
        repository = SQLModelProductRepository(session)
        
        created_count = 0
        for product_data in sample_products:
            try:
                await repository.create_product(product_data)
                created_count += 1
                print(f"✓ Created sample product: {product_data.sku}")
            except Exception as e:
                print(f"⚠ Skipped {product_data.sku} (may already exist): {e}")
        
        print(f"✅ Sample data creation complete. Created {created_count} products.")


if __name__ == "__main__":
    # Simple CLI for database utilities
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m inventory_api.core.db_utils <command>")
        print("Commands: info, verify, sample-data")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "info":
        info = asyncio.run(get_database_info())
        print("Database Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    
    elif command == "verify":
        results = asyncio.run(verify_database_constraints())
        print("Constraint Verification:")
        print(f"  Overall Status: {'✅ PASS' if results['constraints_verified'] else '❌ FAIL'}")
        for check in results.get("checks", []):
            status_icon = "✅" if check["status"] == "present" else "❌"
            print(f"  {status_icon} {check['constraint']}: {check['description']}")
    
    elif command == "sample-data":
        asyncio.run(initialize_database())
        asyncio.run(create_sample_data())
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)