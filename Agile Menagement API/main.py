from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Literal

from src.crud import (
    create_project,
    get_all_projects,
    get_project_details,

    create_sprint,
    get_sprint_details,
    delete_sprint,

    create_task,
    get_task_details,
    update_task_status,
)
from src.database import create_db_and_tables
from src.models import Project, Sprint, Task

# Request Body Expects
class ProjectCreate(BaseModel):
    name: str

class SprintCreate(BaseModel):
    name: str
    project_id: int

class TaskCreate(BaseModel):
    title: str
    sprint_id: int | None = None 

class TaskUpdateStatus(BaseModel):
    status: Literal["Not Started", "In progress", "Done"]

# ===  Lifespan Management ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up... creating database and tables.")
    create_db_and_tables()
    print("🌍 Server is running!")
    print("🕹️  API Documentation: http://127.0.0.1:8000/docs")
    print("🕳️  Alternative docs: http://127.0.0.1:8000/redoc")
    yield
    print("Shutting down...")

# == FastAPI Application Setup ==
app = FastAPI(
    title="Project Management API",
    description="API for managing Projects, Sprints, and Tasks.",
    version="0.1.0",
    lifespan=lifespan
)

# === Routes ===

# --- Project Enpoints ---
# Create Project
@app.post("/projects/", response_model=Project, status_code=201, tags=["Projects"])
def api_create_project(project_data: ProjectCreate):
    new_project = create_project(name=project_data.name)
    return new_project

# List All Projects
@app.get("/projects/", response_model=List[Project], tags=["Projects"])
def api_get_all_projects():
    projects = get_all_projects()
    return projects

# Get the Project Details
@app.get("/projects/{project_id}", response_model=Project, tags=["Projects"])
def api_get_project(project_id: int):
    project = get_project_details(project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# --- Sprint Endpoints ---

@app.post("/sprints/", response_model=Sprint, status_code=201, tags=["Sprints"])
def api_create_sprint(sprint_data: SprintCreate):
    # Best practice: Check if the parent project exists before creating a child.
    project = get_project_details(project_id=sprint_data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with id {sprint_data.project_id} not found.")
    
    return create_sprint(name=sprint_data.name, project_id=sprint_data.project_id)

@app.get("/sprints/{sprint_id}", response_model=Sprint, tags=["Sprints"])
def api_get_sprint(sprint_id: int):
    sprint, status_code = get_sprint_details(sprint_id)
    if status_code == 404:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return sprint

@app.delete("/sprints/{sprint_id}", status_code=204, tags=["Sprints"])
def api_delete_sprint(sprint_id: int):
    _, status_code = delete_sprint(sprint_id) # [[ _, to ignore unused value for return nothing]]
    if status_code == 404:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return

# --- Task Endpoints ---

@app.post("/tasks/", response_model=Task, status_code=201, tags=["Tasks"])
def api_create_task(task_data: TaskCreate):
    # If a sprint_id is provided, check if it exists.
    if task_data.sprint_id:
        _, status_code = get_sprint_details(task_data.sprint_id) #[[ _, to ignore sprint ]]
        if status_code == 404:
            raise HTTPException(status_code=404, detail=f"Sprint with id {task_data.sprint_id} not found.")

    return create_task(title=task_data.title, sprint_id=task_data.sprint_id)

@app.put("/tasks/{task_id}/status", response_model=Task, tags=["Tasks"])
def api_update_task_status(task_id: int, status_data: TaskUpdateStatus):
    updated_task, status_code = update_task_status(task_id=task_id, new_status=status_data.status)
    if status_code == 404:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task

@app.get("/tasks/{task_id}", response_model=Task, tags=["Tasks"])
def api_get_task(task_id: int):
    task, status_code = get_task_details(task_id)
    if status_code == 404:
        raise HTTPException(status_code=404, detail="Task not found")
    return task