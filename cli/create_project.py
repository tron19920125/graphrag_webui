from cli.common import run_command
import os
from cli.logger import get_logger
import libs.config as config
import time
from pathlib import Path
from graphrag.cli.initialize import initialize_project_at

logger = get_logger('create_project_cli')

def overwrite_settings_yaml(project_dir, new_project_name, create_db_type = "ai_search"):
    """重写 settings.yaml 文件，确保使用简单的相对路径，避免路径套娃问题"""
    settings_yaml = f"{project_dir}/settings.yaml"

    # 备份原始文件作为 settings_default.yaml
    run_command(f"cp {project_dir}/settings.yaml {project_dir}/settings_default.yaml")

    root_project_dir = os.path.dirname(os.path.dirname(__file__))

    template_settings_yaml = f"{root_project_dir}/template/setting_{create_db_type}.yaml"

    # 设置容器名称
    container_name = f"{config.app_name}_{new_project_name}"
    
    # 读取模板并进行替换
    with open(template_settings_yaml, "r") as t:
        with open(settings_yaml, "w") as f:
            new_settings_yaml = t.read().replace(
                "container_name: default", f"container_name: {container_name}"
            ).replace(
                'base_dir: "logs"', 'base_dir: "logs"'  # 保持相对路径不变
            ).replace(
                'base_dir: "output"', 'base_dir: "output"'  # 保持相对路径不变
            ).replace(
                "db_uri: 'lancedb'", "db_uri: 'lancedb'"  # 保持原样
            )
            
            # 确保没有项目名称出现在路径中
            new_settings_yaml = new_settings_yaml.replace(
                f'projects/{new_project_name}/', ''
            ).replace(
                f'projects\\{new_project_name}\\', ''
            )
            
            f.write(new_settings_yaml)
    
    logger.info(f"配置文件已创建: {settings_yaml}，使用简单相对路径")

def overwrite_settings_env(root):
    settings_env = f"{root}/.env"
    template_settings_env = f"{os.path.dirname(__file__)}/template/.env"
    with open(template_settings_env, "r") as t:
        with open(settings_env, "w") as f:
            f.write(t.read())

def init_graphrag_project(project_name: str):
    """ initialize graphrag project
    
    Args:
        project_name: project name, if empty, use default name
        
    Returns:
        bool: if initialize successfully
    """
    logger.info("initialize graphrag project")

    if not project_name:
        project_name = f"cli_{time.strftime('%Y%m%d')}"

    # create projects directory
    projects_dir = Path('projects')
    if not projects_dir.exists():
        logger.info("create projects directory")
        projects_dir.mkdir()

    # check if project directory exists
    project_dir = os.path.join(projects_dir, project_name)
    if os.path.exists(project_dir):
        logger.error(f"project {project_name} already exists")
        return False

    initialize_project_at(project_dir)

    overwrite_settings_yaml(project_dir, project_name, "ai_search")

    overwrite_settings_env(project_dir)

    return True