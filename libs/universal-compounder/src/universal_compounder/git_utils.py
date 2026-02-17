import subprocess
from typing import List

def get_recent_changes(hours: int = 24) -> str:
    """Gets the git log and diff for the last N hours."""
    try:
        # Get commit hashes
        cmd = ["git", "log", f"--since={hours} hours ago", "--pretty=format:%H"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        hashes = result.stdout.strip().splitlines()

        if not hashes:
            return "No changes found in the last 24 hours."

        # Get diffs
        full_diff = ""
        for commit_hash in hashes:
            log_cmd = ["git", "show", "--stat", "--patch", commit_hash]
            log_res = subprocess.run(log_cmd, capture_output=True, text=True)
            full_diff += f"\n\n=== Commit {commit_hash} ===\n{log_res.stdout}"
        
        return full_diff
    except subprocess.CalledProcessError as e:
        return f"Error running git command: {e}"
    except Exception as e:
        return f"Error: {e}"
