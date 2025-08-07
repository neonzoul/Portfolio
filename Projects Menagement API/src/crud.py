# :Modules: CRUD Modules

from sqlmodel import Session, select
from typing import Literal, List
from .models import Project, Sprint, Task
from .database import engine

# === Create Operations ===
# -Creates a new project instance and saves it to the database.-
def create_project(name: str) -> Project:
    with Session(engine) as session:
        project = Project(name=name)
        session.add(project)
        session.commit()
        session.refresh(project)
    return project

# --Creates a new sprint can link to a project.--
def create_sprint(name: str, project_id: int | None) -> Sprint:
    with Session(engine) as session:
        if project_id is not None:
            sprint = Sprint(name=name, project_id=project_id)
        else:
            sprint = Sprint(name=name, project_id=None)
        session.add(sprint)
        session.commit()
        session.refresh(sprint)
    return sprint

# --Creates a new task can link to a sprint.--
def create_task(
    title: str,
    sprint_id: int | None = None,
    status: Literal["Not Started", "In progress", "Done"] = "Not Started"
) -> Task:
    with Session(engine) as session:
        task = Task(title=title, sprint_id=sprint_id, status=status)
        session.add(task)
        session.commit()
        session.refresh(task)
    return task

# === Read Operations ===
# Get All Project return as List
def get_all_projects() -> List[Project]:
    with Session(engine) as session:
        statement = select(Project)     
        results = session.exec(statement).all()
        projects = list(results)
        return projects

# Display Database Hierarchy
def list_all_data_to_console() -> None:
    with Session(engine) as session:
        # Query all projects
        statement = select(Project)
        projects = session.exec(statement).all()

        # [Loop through each project]
        for project in projects:
            print(f'📁 Project: {project.name} (ID: {project.id})')

            # [Loop through the sprints linked to this project.]
            for sprint in project.sprints:
                print(f' Sprint: {sprint.name} (ID: {sprint.id})')

                # [Loop though the tasks linked to this sprint.]
                for task in sprint.tasks:
                    print(f'    - Task: {task.title} (Status: {task.status})')
        print()
# [[ Test function. -> $ pyton -c "from src.crud import list_all_data_to_console; list_all_data_to_console()" ]]

# Get Project Details 
def get_project_details(project_id: int) -> Project | None:
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if project is None:
            return None
        return project
    
# Get Sprint Details
def get_sprint_details(sprint_id: int) -> tuple[Sprint | None, int]:
    with Session(engine) as session:
        sprint = session.get(Sprint, sprint_id)
        if sprint is None:
            return None, 404
        return sprint, 200
    
# Get Task Details
def get_task_details(task_id: int) -> tuple[Task | None, int]:
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if task is None:
            return None, 404
        return task, 200

# === Update Operations ===
# Update Task Status
def update_task_status(
        task_id: int, 
        new_status: Literal["Not Started", "In progress", "Done"]
        ) -> tuple[Task | None, int]:

        with Session(engine) as session:
            task = session.get(Task, task_id)
            if task is None:
                print(f'Error 404: Task id{task_id} not found.')
                return None, 404

            task.status = new_status

            session.add(task)
            session.commit()
            session.refresh(task)

            return task, 200

# === Delete Oprerations ===
# Delete Sprint
def delete_sprint(sprint_id: int) -> tuple[Sprint | None, int]:

    with Session(engine) as session:
        sprint = session.get(Sprint, sprint_id)
        if sprint is None:
            print(f'Error 404: Task id{sprint_id} not found.')
            return None, 404
    
        session.delete(sprint)
        session.commit()

        return sprint, 204

