# Database(tables) Models Modules

from typing import List
from sqlmodel import Field, Relationship, SQLModel

# === Projects Database Model ===
class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    sprints: List["Sprint"] = Relationship(back_populates="project")

# === Sprints Database Model ===
class Sprint(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    project_id: int | None = Field(foreign_key="project.id")
    project: "Project" = Relationship(back_populates="sprints")
    tasks: List["Task"] = Relationship(back_populates="sprint")

# === Tasks Database Model ===
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    status: str = Field(default="Not Started")

    sprint_id: int | None = Field(default=None, foreign_key="sprint.id")
    sprint: "Sprint" = Relationship(back_populates="tasks")
