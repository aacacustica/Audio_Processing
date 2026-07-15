import subprocess

def list_git_tags():
    try:
        tags = tags = subprocess.check_output(["git", "tag"]).strip().decode()
        return tags.split('\n')
    except subprocess.CalledProcessError:
        return None
    
def get_stable_version():

    tags = list_git_tags()
    tag_selected = tags[-2]
    tag_selected = tag_selected.replace(".", "_")

    return tag_selected