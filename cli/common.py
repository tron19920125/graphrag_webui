import subprocess
from cli.logger import get_logger
logger = get_logger('common')

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