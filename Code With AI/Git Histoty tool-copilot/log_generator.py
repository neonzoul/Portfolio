# Gemini 2.5 pro
# Scans the entire Git history and exports it to a single, comprehensive CSV log file.
# Using Python to full all the logs and create a CSV file as requested.

import subprocess
import csv
import os

# --- Configuration ---
# 1. Edit the path to match where you cloned the n8n repository
REPO_PATH = 'F:/Coding-Area/Learn/Deconstruction_training/n8n'
# 2. The name of the CSV file to be created
OUTPUT_CSV_FILE = 'n8n_full_commit_log.csv'
# --------------------

def export_git_log_to_csv(repo_path, output_file):
    """
    Fetches the entire Git log from all branches, sorts it from oldest to newest,
    and saves it to a CSV file.
    """
    if not os.path.isdir(repo_path):
        print(f"Error: Git repository not found at path: {repo_path}")
        return

    print(f"Fetching logs from: {repo_path}...")

    # git log command
    # --all: Fetch logs from all branches
    # --reverse: Sort from the very first commit to the most recent
    # --pretty=format: Define the output format using a unique separator
    separator = "_|-" # field separator
    git_command = [
        'git', 'log', '--all', '--reverse',
        f'--pretty=format:%H{separator}%cI{separator}%an{separator}%s' # Hash | Date | Author | Subject
    ]

    try:
        # Run the git command via subprocess
        result = subprocess.run(
            git_command,
            cwd=repo_path,          # Run the command in the repo's directory
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )

        # Process the output to create the CSV file
        commits = result.stdout.strip().split('\n')

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write the Header - CORRECTED
            writer.writerow(['Commit Hash', 'Commit Date', 'Author', 'Message'])
            
            # Write commit data line by line
            for line in commits:
                # Split each part using the defined separator - CORRECTED
                parts = line.split(separator, 3)
                writer.writerow(parts)
        
        print(f"✅ Success! All logs have been saved to the file '{output_file}'.")

    except FileNotFoundError:
        print("Error: 'git' command not found. Please ensure Git is installed correctly.")
    except subprocess.CalledProcessError as e:
        print(f"Error while running git command: {e.stderr}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Start the script execution
if __name__ == "__main__":
    # Check if the user has modified the REPO_PATH yet
    if 'path/to/your' in REPO_PATH:
        print("🚨 Please edit the REPO_PATH variable in the script to the correct path of your n8n repository before running.")
    else:
        export_git_log_to_csv(REPO_PATH, OUTPUT_CSV_FILE)