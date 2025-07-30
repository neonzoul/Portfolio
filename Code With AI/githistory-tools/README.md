# Git History Tools

This directory contains a set of Python scripts designed to interact with and analyze the Git history of the parent repository. These tools allow you to export the entire commit history to a searchable log and retrieve clean snapshots of the code from any point in time.

## Scripts

### 1. `log_generator.py`

-   **Purpose**: Scans the entire Git history across all branches and exports it to a single, comprehensive CSV log file (`n8n_full_commit_log.csv`).
-   **How to Use**: Run this script once to generate the initial log file. You only need to run it again if you want to update the log with new commits.
    ```bash
    python log_generator.py
    ```

### 2. `code_snapshot.py`

-   **Purpose**: Retrieves a clean snapshot of the code from a specific commit date and exports it to a new directory. It acts as a "code time machine."
-   **How to Use**: Pass the exact commit date and time (found in the CSV log) as a command-line argument. Remember to enclose the date string in double quotes.

    ```bash
    # Usage: python code_snapshot.py "<date-time-string>"

    # Example:
    python code_snapshot.py "2019-06-24T10:28:18+02:00"
    ```

-   **Output**: This will create a new folder in the `.n8n` directory named with the commit's date, time, and message (e.g., `log-19_06_24__10_28-Fix-link-to-README`), containing all the project files from that specific commit.

## Configuration

Both scripts are designed to be portable. They automatically detect their location and the root of the Git repository (`.n8n`), so no manual path configuration is needed as long as the directory structure is maintained.
