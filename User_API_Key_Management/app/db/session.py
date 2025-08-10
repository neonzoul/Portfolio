from sqlmodel import SQLModel, create_engine, Session
import re


# === Create Database File ===

# Provide db file name.
name: str = "app"

def validate_file_name(name: str) -> str:
    if re.search(r'[\\/:*?"<>|]', name):
        raise ValueError("A file name can't contain any of the following characters: \\ / : * ? \" < > |")
    return name
file_name: str = validate_file_name(name)

# Provide db directory. 
db_dir = "./app/db"

# Database URL {chage database here..}
DATABASE_URL = "sqlite:///{db_dir}/{file_name}.db"

# === Create engine ===
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session