import subprocess

def list_git_tags():
    try:
        tags = subprocess.check_output(["git", "tag"],stderr=subprocess.DEVNULL).strip().decode()
        if not tags:
            return []
        
        return tags.splitlines()
    except subprocess.CalledProcessError:
        return None
    
def get_stable_version(default: str = "unknown") -> str:
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags", "--always", "--dirty"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return default