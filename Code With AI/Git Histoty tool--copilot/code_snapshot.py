# Gemini 2.5 pro
# Retrieves a clean snapshot of the code from a specific commit date and exports it to a new directory.

import subprocess
import csv
import os
import re
from datetime import datetime
import sys

# --- DYNAMIC CONFIGURATION ---
# Get the absolute path of the directory where the script is located (e.g., .../githistory-tools)
script_dir = os.path.dirname(os.path.realpath(__file__))

# The N8N_REPO_PATH is the parent directory of the script's directory (.../.n8n)
# This makes the script portable, as it no longer relies on a hardcoded path.
N8N_REPO_PATH = os.path.dirname(script_dir)

# The path to the CSV log file, built dynamically.
COMMIT_LOG_CSV_PATH = os.path.join(script_dir, 'n8n_full_commit_log.csv')
# --- END CONFIGURATION ---

def find_commit_by_date(target_date_str):
    """
    Searches the CSV log file for a commit matching the target date string.
    
    Returns:
        A dictionary with 'hash', 'date', and 'message' if found, otherwise None.
    """
    print(f"Searching for commit on date: {target_date_str}...")
    try:
        with open(COMMIT_LOG_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None) 
            for row in reader:
                # Ensure row has enough columns to avoid errors
                if len(row) >= 4 and row[1] == target_date_str:
                    commit_details = {
                        'hash': row[0],
                        'date': row[1],
                        'message': row[3]
                    }
                    print(f"✅ Found commit: {commit_details['hash']}")
                    return commit_details
    except FileNotFoundError:
        print(f"❌ ERROR: Log file not found at '{COMMIT_LOG_CSV_PATH}'")
        return None
    except Exception as e:
        print(f"❌ ERROR: An error occurred while reading the CSV file: {e}")
        return None
        
    print("❌ No commit found for the specified date.")
    return None

def create_snapshot_directory_name(commit_date_str, commit_message):
    """
    Creates a sanitized, file-system-safe directory name from commit details.
    """
    # Parse the date to reformat it
    dt_object = datetime.fromisoformat(commit_date_str)
    # UPDATED THIS LINE to include hours and minutes
    formatted_date = dt_object.strftime('%y_%m_%d__%H_%M') # yy_mm_dd__hh_mm format

    # Sanitize the commit message for use in a folder name
    # 1. Keep only letters, numbers, spaces, and hyphens
    sane_message = re.sub(r'[^\w\s-]', '', commit_message).strip()
    # 2. Replace spaces with a single hyphen
    sane_message = re.sub(r'\s+', '-', sane_message)
    # 3. Truncate to a reasonable length
    sane_message = sane_message[:50]

    return f"log-{formatted_date}-{sane_message}"

def export_commit_snapshot(commit_hash, target_dir):
    """
    Uses 'git archive' to export a clean snapshot of a commit to a target directory.
    This is much more efficient than re-cloning.
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"Created directory: {target_dir}")
    else:
        print(f"Directory already exists: {target_dir}")
        return False

    # Command to export the commit content into the new directory
    # 'git archive' creates a tarball, and 'tar -x' extracts it in the target directory.
    command = f'git archive {commit_hash} | tar -x -C "{target_dir}"'
    
    print(f"Exporting snapshot of commit {commit_hash}...")
    try:
        # We use shell=True because of the pipe (|) in the command
        subprocess.run(command, shell=True, check=True, cwd=N8N_REPO_PATH)
        print("✅ Snapshot exported successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to export snapshot. Git command failed: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred during export: {e}")
        return False

# --- Main Worker Logic ---
if __name__ == "__main__":
    # Check for command-line argument
    if len(sys.argv) < 2:
        print("Usage: python worker_snapshot.py \"<date-time-string>\"")
        print("Example: python worker_snapshot.py \"2019-06-24T10:28:18+02:00\"")
        sys.exit(1)

    target_date = sys.argv[1]
    
    commit_info = find_commit_by_date(target_date)

    if commit_info:
        dir_name = create_snapshot_directory_name(commit_info['date'], commit_info['message'])
        full_target_path = os.path.join(N8N_REPO_PATH, dir_name)
        
        export_commit_snapshot(commit_info['hash'], full_target_path)

