import time
from dotenv import load_dotenv
import streamlit as st
from pathlib import Path
from libs.common import is_admin, run_command
from theodoretools.fs import get_directory_size
from theodoretools.st import run_shell_command


def build_index(project_name: str):

    if st.button("Start Build", key="build_index_" + project_name, icon="🚀"):

        load_dotenv(
            dotenv_path=Path("/app/projects") / project_name / ".env",
            override=True,
        )

        with st.spinner("Building index..."):

            target_dir = f"/app/projects/{project_name}"

            run_shell_command(['graphrag', 'index'], target_dir)

    cache_size_mb = get_directory_size(f"/app/projects/{project_name}/cache")
    if cache_size_mb > 0:
        st.write(f"Cache size: {cache_size_mb} MB")

    output_size_mb = get_directory_size(
        f"/app/projects/{project_name}/output", [".log"]
    )
    if output_size_mb > 0 and st.button(
        f"Clear index files ({output_size_mb} MB)",
        key="clear_index_" + project_name,
        icon="🗑️",
    ):
        run_command(f"rm -rf /app/projects/{project_name}/output/*")
        st.success("All files deleted.")
        time.sleep(3)
