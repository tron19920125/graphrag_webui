import subprocess
from cli.logger import get_logger
import os
from pathlib import Path
from dotenv import load_dotenv
from graphrag.config.load_config import load_config

logger = get_logger('common')

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_project_env(project_name: str):
    load_dotenv(
        dotenv_path=f"{root_dir}/projects/{project_name}/.env", override=True)


def project_path(project_name: str):
    return Path(root_dir) / "projects" / project_name


def load_graphrag_config(project_name: str):
    return load_config(root_dir=project_path(project_name))

def run_command(command: str, output: bool = False):
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    while True:
        stdout = process.stdout.readline()
        stderr = process.stderr.readline()

        if output and stderr:
            logger.error(stderr)

        if stdout == "" and process.poll() is not None:
            break
        if stdout:
            s = stdout.strip()
            if output:
                logger.info(s)
            elif s.startswith("🚀"):
                logger.info(s)

    rc = process.poll()
    return rc