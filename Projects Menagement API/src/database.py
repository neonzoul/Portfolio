# :Modules: Database Connector

from .models import Project, Sprint, Task
from sqlmodel import create_engine, SQLModel
import re # Regular Expression for validate file name.
import os # For directory operations

# === Create Database File ===
# file name validator.
def validate_file_name(name: str) -> str:
    if re.search(r'[\\/:*?"<>|]', name):
        raise ValueError("A file name can't contain any of the following characters: \\ / : * ? \" < > |")
    return name

name: str = "task_manager"
file_name: str = validate_file_name(name)

# Create db directory if it doesn't exist
db_dir = "./db"
os.makedirs(db_dir, exist_ok=True)

DATABASE_URL = f'sqlite:///{db_dir}/{file_name}.db'

# === Create engine ===
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    print("Creating database and table...")
    print(f"Creating tables for models: {Project.__name__}, {Sprint.__name__}, {Task.__name__}")
    SQLModel.metadata.create_all(engine)
    print("Done. ")