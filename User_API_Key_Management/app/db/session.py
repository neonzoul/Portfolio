# :Modules: Database Session & Engine
# === Purpose ===
# Create SQLite engine, ensure tables, and provide request-scoped sessions.

from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import inspect, text
import re
import os


# === Create Database File ===

# Provide db file name.
name: str = "app"

def validate_file_name(name: str) -> str:
    if re.search(r'[\\/:*?"<>|]', name):
        raise ValueError("A file name can't contain any of the following characters: \\ / : * ? \" < > |")
    return name
file_name: str = validate_file_name(name)

# Provide db directory as absolute path (avoid sqlite open errors on relative CWD)
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
db_dir = os.path.join(workspace_root, "db")
os.makedirs(db_dir, exist_ok=True)

# Database URL {change database here if needed}
DATABASE_URL = f"sqlite:///{os.path.join(db_dir, file_name + '.db')}"

# === Create engine ===
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    # Lightweight migration: ensure 'hashed_password' exists on 'user' table
    with engine.begin() as conn:
        inspector = inspect(conn)
        if 'user' in inspector.get_table_names():
            try:
                # Probe for column; will error if missing
                conn.execute(text("SELECT hashed_password FROM user LIMIT 1"))
            except Exception:
                conn.execute(text("ALTER TABLE user ADD COLUMN hashed_password VARCHAR(255) NOT NULL DEFAULT ''"))

def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session