from src.database import create_db_and_tables
from src.crud import create_project, create_sprint, create_task, list_all_data_to_console

# === Main Execution block to run functions in a logical order. ===
if __name__ == "__main__":
    create_db_and_tables()

    # --Create Data--
    print("--- CREATING DATA ---")
    project1 = create_project(name="AutomateOs v0.1")

    # Sprint
    sprint1 = create_sprint(name="Week1: Foundations & Project Setup", project_id=project1.id)
    sprint2 = create_sprint(name="Week2: Workflow CRUD", project_id=project1.id)

    # Task
    create_task(title="Define User model", sprint_id=sprint1.id, status="In progress")
    create_task(title="Set up JWT authentication", sprint_id=sprint1.id)
    create_task(title="Create /workflows endpoint", sprint_id=sprint2.id, status="Done")

    print("--- DATA CREATED ---\n")

    # --- List All Data ---
    print("--- FULL PROJECT REPORT ---")
    list_all_data_to_console()
    print("--- END OF REPORT ---")

