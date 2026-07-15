import subprocess

def list_git_tags():
    try:
        tags = subprocess.check_output(["git", "tag"],stderr=subprocess.DEVNULL).strip().decode()
        if not tags:
            return []
        
        return tags.splitlines()
    except subprocess.CalledProcessError:
        return None
    
def get_stable_version(default: str = "dev") -> str:

    tags = list_git_tags()
    if len(tags) >= 2: return tags[-2].replace(".","_")
        
    if len(tags) == 1: return tags[-1].replace(".","_")
    


    return default