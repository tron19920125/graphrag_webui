from cli.common import project_path
import os
from pathlib import Path
import shutil

def upload_files(project_name, input_dir):
    """upload files"""

    Path(f"{os.getcwd()}/projects/{project_name}/original").mkdir(
        parents=True, exist_ok=True)
    Path(f"{os.getcwd()}/projects/{project_name}/input").mkdir(
        parents=True, exist_ok=True)
    
    # clear original and input directory
    for file in os.listdir(f"{os.getcwd()}/projects/{project_name}/original"):
        os.remove(os.path.join(f"{os.getcwd()}/projects/{project_name}/original", file))
    for file in os.listdir(f"{os.getcwd()}/projects/{project_name}/input"):
        os.remove(os.path.join(f"{os.getcwd()}/projects/{project_name}/input", file))

    if os.path.isdir(input_dir):
        for file in os.listdir(input_dir):
            # copy file to /app/projects/{project_name}/original
            shutil.copy(os.path.join(input_dir, file), os.path.join(project_path(project_name), "original", file))
            shutil.copy(os.path.join(input_dir, file), os.path.join(project_path(project_name), "input", file))
            # make file permissions to another user can write
            os.chmod(
                f"{project_path(project_name)}/original/{file}", 0o666
            )
            os.chmod(
                f"{project_path(project_name)}/input/{file}", 0o666
            )

    return True