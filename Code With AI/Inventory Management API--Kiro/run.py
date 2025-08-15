#!/usr/bin/env python3
"""
Enhanced startup script for the Inventory Management API.

This script provides CLI commands for database initialization and server startup
with proper configuration management and error handling.

Usage:
    python run.py                    # Initialize DB and start server
    python run.py --init-db-only     # Only initialize database
    python run.py --help             # Show help
"""

import argparse
import asyncio
import sys
import uvicorn

from inventory_api.core.database import initialize_database, drop_tables
from inventory_api.core.config import get_settings


async def init_database_only():
    """Initialize database tables only (no server start)."""
    try:
        print("🔧 Initializing database...")
        await initialize_database()
        print("✅ Database initialization completed successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


async def reset_database():
    """Reset database by dropping and recreating all tables."""
    try:
        print("⚠️  Resetting database (dropping all tables)...")
        await drop_tables()
        print("🔧 Recreating database tables...")
        await initialize_database()
        print("✅ Database reset completed successfully")
        return True
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        return False


def start_server():
    """Start the FastAPI server with proper configuration."""
    settings = get_settings()
    
    print(f"🚀 Starting Inventory Management API")
    
    # Show user-friendly URLs
    if settings.host == "0.0.0.0":
        display_host = "localhost"
    else:
        display_host = settings.host
        
    print(f"📍 Server: http://{display_host}:{settings.port}")
    print(f"📚 API Docs: http://{display_host}:{settings.port}/docs")
    print(f"🔧 Environment: {settings.environment}")
    print(f"💾 Database: {settings.database_url}")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "inventory_api.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.reload and settings.environment == "development",
            log_level="info" if settings.environment == "production" else "debug"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Inventory Management API startup script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                    # Initialize DB and start server
  python run.py --init-db-only     # Only initialize database
  python run.py --reset-db         # Reset database and start server
  python run.py --help             # Show this help message

Environment Variables:
  INVENTORY_DATABASE_URL           # Database connection string
  INVENTORY_HOST                   # Server host (default: 0.0.0.0)
  INVENTORY_PORT                   # Server port (default: 8000)
  INVENTORY_ENVIRONMENT            # Environment (development/production)
        """
    )
    
    parser.add_argument(
        "--init-db-only",
        action="store_true",
        help="Initialize database tables only (don't start server)"
    )
    
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Reset database by dropping and recreating all tables"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Inventory Management API v1.0.0"
    )
    
    args = parser.parse_args()
    
    # Handle database-only initialization
    if args.init_db_only:
        success = asyncio.run(init_database_only())
        sys.exit(0 if success else 1)
    
    # Handle database reset
    if args.reset_db:
        success = asyncio.run(reset_database())
        if not success:
            sys.exit(1)
        # Continue to start server after reset
    
    # Default behavior: initialize database and start server
    # Note: The FastAPI app will handle database initialization on startup
    # but we can also do it here for explicit control
    if not args.reset_db:  # Skip if we already initialized above
        print("🔧 Pre-startup database check...")
        success = asyncio.run(init_database_only())
        if not success:
            print("❌ Cannot start server due to database initialization failure")
            sys.exit(1)
    
    # Start the server
    start_server()


if __name__ == "__main__":
    main()