import asyncio
import time

import graphrag.api as api
import streamlit as st

from libs.common import run_command, load_graphrag_config
from libs.print_progress import PrintProgressLogger
from theodoretools.fs import get_directory_size


def build_index(project_name: str):

    if st.button("Start Build", key="build_index_" + project_name, icon="🚀"):
        config = load_graphrag_config(project_name)
        st.info("Config:")
        st.json(config, expanded=False)

        with st.spinner("Building index..."):
            asyncio.run(
                api.build_index(
                    config=config,
                    run_id="",
                    is_resume_run=False,
                    memory_profile=True,
                    progress_logger=PrintProgressLogger(""),
                )
            )

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
