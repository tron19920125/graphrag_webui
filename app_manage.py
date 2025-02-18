import logging
import sys
import streamlit as st
import os
from dotenv import load_dotenv
from app_test import test_page
from libs import config
from libs.common import is_admin
from libs.create_project import create_project
from libs.projects_manage import project_show, projects_manage
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

notebook_dir = os.path.abspath("")
parent_dir = os.path.dirname(notebook_dir)
grandparent_dir = os.path.dirname(parent_dir)

sys.path.append(grandparent_dir)


def page():
    project_name = st.query_params.get("project_name", None)
    action = st.query_params.get("action", None)
    if project_name is not None:
        if action == 'test':
            test_page()
            return
        if action == 'manage':
            project_show(project_name)
            return
        st.error("Invalid action")
        return

    if is_admin():
        create_project()

    projects_manage()


if __name__ == "__main__":

    page_title = "GraphRAG WebUI"
    st.set_page_config(
        page_title=page_title,
        page_icon="avatars/favicon.ico",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.image("avatars/logo.svg", width=100)
    st.title(page_title)

    if not os.path.exists("./config.yaml"):
        page()
    else:
        with open("./config.yaml") as file:
            yaml_config = yaml.load(file, Loader=SafeLoader)
            authenticator = stauth.Authenticate(
                yaml_config["credentials"],
                yaml_config["cookie"]["name"],
                yaml_config["cookie"]["key"],
                yaml_config["cookie"]["expiry_days"],
            )

            authenticator.login()

            if st.session_state["authentication_status"]:
                st.write(
                    f'Welcome `{st.session_state["name"]}`, [GraphRAG WebUI](https://github.com/TheodoreNiu/graphrag_webui):`{config.app_version}` [GraphRAG](https://github.com/microsoft/graphrag):`{config.graphrag_version}` App started at: `{config.app_started_at}`')

                authenticator.logout()

                if is_admin() and st.button("Restart Server"):
                    st.success("You need to refresh page later.")
                    os._exit(1)
                    sys.exit(1)
                    os.kill(os.getpid(), signal.SIGTERM)
                    st.stop()
                    sys.exit()

                page()
            elif st.session_state["authentication_status"] is False:
                st.error("Username/password is incorrect")
            elif st.session_state["authentication_status"] is None:
                st.warning("Please enter your username and password")
