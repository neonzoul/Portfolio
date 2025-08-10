from sqlmodel import SQLModel, create_engine, Session
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

# Database URL {chage database here..}
DATABASE_URL = f"sqlite:///{os.path.join(db_dir, file_name + '.db')}"

# === Create engine ===
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session