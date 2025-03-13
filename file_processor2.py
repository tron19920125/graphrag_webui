#!/usr/bin/env python3

import os
import sys
import yaml
import shutil
import asyncio
import subprocess
from pathlib import Path
import importlib.util
import traceback
from graphrag.cli.initialize import initialize_project_at
import time
import graphrag.api as api
from dotenv import load_dotenv

from cli.common import  run_command, load_graphrag_config, project_path
from cli.generate_data import  prepare_file, convert_file
from cli.logger import get_logger
from cli.index_preview import index_preview
from cli.types import PreviewType

import libs.config as config

from graphrag.config.load_config import load_config
from openai import AzureOpenAI

class ArgConfig:
    def __init__(self, project, input_dir, pdf_vision_option):
        self.project = project
        self.input_dir = input_dir
        self.pdf_vision_option = pdf_vision_option


logger = get_logger('file_processor')

# 确保libs目录可导入
sys.path.append(os.path.abspath('.'))

# 动态导入libs中的模块
def import_from_libs(module_name):
    """动态导入libs目录下的模块"""
    try:
        # 检查模块是否已经加载
        if module_name in sys.modules:
            return sys.modules[module_name]
        
        # 构建完整模块路径
        full_module_name = f"libs.{module_name}"
        module_path = f"libs/{module_name}.py"
        
        # 检查模块文件是否存在
        if not os.path.exists(module_path):
            logger.warning(f"模块文件不存在: {module_path}")
            return None
        
        # 加载模块
        spec = importlib.util.spec_from_file_location(full_module_name, module_path)
        if spec is None:
            logger.warning(f"无法加载模块规范: {module_path}")
            return None
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 将模块添加到sys.modules
        sys.modules[full_module_name] = module
        
        logger.info(f"成功导入模块: {module_name}")
        return module
    except Exception as e:
        logger.error(f"导入模块 {module_name} 失败: {e}")
        logger.debug(traceback.format_exc())
        return None

# def load_config():
#     """加载配置文件"""
#     config_path = Path('config.yaml')
#     if not config_path.exists():
#         logger.error("找不到config.yaml文件")
#         sys.exit(1)
    
#     with open(config_path, 'r', encoding='utf-8') as f:
#         try:
#             return yaml.safe_load(f)
#         except yaml.YAMLError as e:
#             logger.error(f"读取配置文件失败: {e}")
#             sys.exit(1)

def check_graphrag_settings(project_name):
    """检查GraphRAG Settings必要文件是否存在"""
    logger.info(f"检查项目 {project_name} 的GraphRAG Settings必要文件")
    
    try:
        project_dir = os.path.join('projects', project_name)
        if not os.path.exists(project_dir):
            logger.error(f"项目目录不存在: {project_dir}")
            return False
        
        # 检查必要文件
        required_files = [
            os.path.join(project_dir, '.env'),
            os.path.join(project_dir, 'settings.yaml'),
            os.path.join(project_dir, 'settings_default.yaml')
        ]
        
        for req_file in required_files:
            if not os.path.exists(req_file):
                logger.error(f"必要的配置文件不存在: {req_file}")
                return False
        
        # 检查必要目录
        required_dirs = [
            os.path.join(project_dir, 'prompts'),
            os.path.join(project_dir, 'input'),
            os.path.join(project_dir, 'original')
        ]
        
        for req_dir in required_dirs:
            if not os.path.exists(req_dir):
                logger.error(f"必要的目录不存在: {req_dir}")
                return False
        
        logger.info(f"项目 {project_name} 的GraphRAG Settings检查通过")
        return True
    except Exception as e:
        logger.error(f"检查GraphRAG Settings时出错: {e}")
        logger.debug(traceback.format_exc())
        return False


def handle_input_files(config: ArgConfig):
    """upload files"""
    project_name = config.project
    input_dir = config.input_dir

    Path(f"{os.getcwd()}/projects/{project_name}/original").mkdir(
        parents=True, exist_ok=True)
    Path(f"{os.getcwd()}/projects/{project_name}/input").mkdir(
        parents=True, exist_ok=True)

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


def generate_data(config: ArgConfig):
    logger.info(f"generate data for project: {config.project}")
    # 1. copy original files to input
    for root, dirs, files in os.walk(
        f"{project_path(config.project)}/original"
    ):
        for file in files:
            file_path = os.path.join(root, file)
            prepare_file(file_path, file, config.project)

    # 2. convert files to txt
    for root, dirs, files in os.walk(f"{project_path(config.project)}/input"):
        for file in files:
            file_path = os.path.join(root, file)
            convert_file(file_path, file,
                     config.project, config.pdf_vision_option)

    #  3. make file permissions to another user can write
    for root, dirs, files in os.walk(f"{project_path(config.project)}/input"):
        for file in files:
            file_path = os.path.join(root, file)
            os.chmod(file_path, 0o666)


def process_a_project(config: ArgConfig):
    """process a project
    
    Args:
        project_name: project name
    """
    logger.info(f"process project: {config.project}")
    
    try:
        # 步骤1: 上传文件
        handle_input_files(config)

        # 步骤2: Generate Data - 使用参考项目的配置生成数据
        generate_data(config)
        
        # # 步骤4: Prompt Tuning
        asyncio.run(prompt_tuning(config.project))
        
        # # 步骤5: Build Index
        build_index(config.project)
        
        # 步骤6: 完成处理
        logger.info(f"项目 {config.project} 处理完成")
        return True
    
    except Exception as e:
        logger.error(f"处理项目 {config.project} 流程出错: {e}")
        logger.debug(traceback.format_exc())
        raise e
        return False

def process_all_projects(config: ArgConfig):
    process_a_project( config) 
    return True

def overwrite_settings_yaml(root, new_project_name, create_db_type = "ai_search"):
    """重写 settings.yaml 文件，确保使用简单的相对路径，避免路径套娃问题"""
    settings_yaml = f"{root}/settings.yaml"

    # 备份原始文件作为 settings_default.yaml
    run_command(f"cp {root}/settings.yaml {root}/settings_default.yaml")

    template_settings_yaml = f"{os.path.dirname(__file__)}/template/setting_{create_db_type}.yaml"

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



async def write_prompt_file(path: str, content: str):
    """Write prompt content to file asynchronously"""
    with open(path, "wb") as file:
        file.write(content.encode(encoding="utf-8", errors="strict"))
    return True

async def prompt_tuning(project_name: str):
    base_path = f"{project_path(project_name)}"
    
    logger.info("This operation will overwrite your following files, please proceed with caution: \n\n - prompts/entity_extraction.txt \n\n - prompts/summarize_descriptions.txt \n\n - prompts/community_report.txt")
    
    logger.info(f'Start Tuning {project_name}')
    
    # Generate prompts
    (
        entity_extraction_prompt,
        entity_summarization_prompt,
        community_summarization_prompt,
    ) = await api.generate_indexing_prompts(
            config=load_config(root_dir=Path(base_path)),
            root=base_path)
    
    # Define file paths
    entity_extraction_prompt_path = f"{base_path}/prompts/entity_extraction.txt"
    entity_summarization_prompt_path = f"{base_path}/prompts/summarize_descriptions.txt" 
    community_summarization_prompt_path = f"{base_path}/prompts/community_report.txt"

    # Write files concurrently
    await asyncio.gather(
        write_prompt_file(entity_extraction_prompt_path, entity_extraction_prompt),
        write_prompt_file(entity_summarization_prompt_path, entity_summarization_prompt),
        write_prompt_file(community_summarization_prompt_path, community_summarization_prompt)
    )
    
    return True # Add return value to avoid coroutine warning


def run_shell_command(command, cwd):
    asyncio.run(
        run_subprocess(command, cwd)
    )


async def run_subprocess(command, cwd):
    # Create placeholder for live output
    accumulated_output = []

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )

    # Read stdout stream
    while True:
        line = await process.stdout.readline()
        if not line:
            break

        line = line.decode().strip()
        accumulated_output.append(line)

        # Log accumulated output
        logger.info('\n'.join(accumulated_output))

    # Get any remaining output and errors
    stdout, stderr = await process.communicate()
    if stderr:
        logger.error("Subprocess errors:")
        logger.error(stderr.decode())

def build_index(project_name: str):
    """执行构建索引，确保不会出现路径套娃问题"""
    # 加载项目环境变量
    load_dotenv(
        dotenv_path=Path(f"{project_path(project_name)}") / ".env",
        override=True,
    )
    
    target_dir = f"{project_path(project_name)}"
    settings_file = os.path.join(target_dir, 'settings.yaml')
    
    # 备份配置文件
    backup_file = os.path.join(target_dir, 'settings.yaml.bak')
    shutil.copy2(settings_file, backup_file)
    
    try:
        # 修改配置以避免路径套娃
        with open(settings_file, 'r') as f:
            settings = yaml.safe_load(f)
        
        # 使用简单相对路径
        if 'storage' in settings:
            settings['storage']['base_dir'] = 'output'
        if 'reporting' in settings:
            settings['reporting']['base_dir'] = 'logs'
        if 'cache' in settings:
            settings['cache']['base_dir'] = 'cache'
        if 'root_dir' in settings:
            del settings['root_dir']
        
        # 保存修改后的配置
        with open(settings_file, 'w') as f:
            yaml.dump(settings, f)
        
        # 创建必要目录并执行命令
        current_dir = os.getcwd()
        try:
            os.chdir(target_dir)
            
            # 确保目录存在
            for subdir in ['output', 'logs', 'cache']:
                os.makedirs(subdir, exist_ok=True)
            
            # 执行索引命令
            run_shell_command(['graphrag', 'index'], ".")
            return True
        finally:
            os.chdir(current_dir)
            
    except Exception as e:
        logger.error(f"构建索引时出错: {e}")
        logger.debug(traceback.format_exc())
        return False
    
    finally:
        # 恢复原配置
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, settings_file)
            os.remove(backup_file)

def test_config(project_name: str):
    """测试配置文件"""
    logger.info("=== start test config ===")
    # 加载项目环境变量
    config = load_graphrag_config(project_name)
    client = AzureOpenAI(
        api_version=config.llm.api_version,
        azure_endpoint=config.llm.api_base,
        azure_deployment=config.llm.deployment_name,
        api_key=config.llm.api_key,
    )
    completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "你好"},
                    ],
                }
            ],
            model=config.llm.model,
        )
    ai_txt = completion.choices[0].message.content
    logger.info(ai_txt)



def main():
    try:
        # parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description='GraphRAG WebUI file processor')
        
        # create subcommand parser
        subparsers = parser.add_subparsers(dest='command', help='available commands')
        
        # create init subcommand
        init_parser = subparsers.add_parser('init', help='initialize graphrag project')
        init_parser.add_argument('--project', help='specify project name', required=False)
        
        # create process subcommand (default command)
        process_parser = subparsers.add_parser('process', help='process specified project or all projects')
        process_parser.add_argument('--project', help='specify project name', required=True)
        process_parser.add_argument('--input_dir', help='specify input directory', required=True)
        process_parser.add_argument('--pdf_vision_option', help='specify pdf vision option', required=False, default=config.generate_data_vision)

        process_parser = subparsers.add_parser('prompt_tuning', help='prompt tuning')
        process_parser.add_argument('--project', help='specify project name', required=False)

        process_parser = subparsers.add_parser('build_index', help='build index')
        process_parser.add_argument('--project', help='specify project name', required=False)

        process_parser = subparsers.add_parser('test_config', help='test config')
        process_parser.add_argument('--project', help='specify project name', required=False)

        process_parser = subparsers.add_parser('index_preview', help='index preview')
        process_parser.add_argument('--project', help='specify project name', required=False)
        process_parser.add_argument('--type', help='specify index type', required=True, choices=[e.value for e in PreviewType])

        args = parser.parse_args()

        # process subcommand
        if args.command == 'init':
            if init_graphrag_project(args.project):
                logger.info(f"project {args.project} initialized successfully")
                logger.info(f"please visit {project_path(args.project)} and config settings.yaml and .env")
                return 0
            else:
                logger.error(f"project {args.project} initialization failed")
                return 1
        elif args.command == 'process':
            # process is default command
            logger.info("=== start automation processing ===")
            process_config = ArgConfig(args.project, args.input_dir, args.pdf_vision_option)
            if process_a_project(process_config):
                logger.info("=== automation processing completed ===")
                return 0
            else:
                logger.error("=== automation processing failed ===")
                return 1
        elif args.command == 'prompt_tuning':
            logger.info("=== start prompt tuning ===")
            asyncio.run(prompt_tuning(args.project))
            logger.info("=== prompt tuning completed ===")
            return 0
        elif args.command == 'build_index':
            logger.info("=== start build index ===")
            build_index(args.project)
            logger.info("=== build index completed ===")
            return 0
        elif args.command == 'test_config':
            logger.info("=== start test config ===")
            test_config(args.project)
            logger.info("=== test config completed ===")
            return 0
        elif args.command == 'index_preview':
            logger.info("=== start index preview ===")
            index_preview(args.project, args.type)
            logger.info("=== index preview completed ===")
            return 0
        else:
            parser.print_help()
            return 1
    except Exception as e:
        logger.error(f"error occurred during processing: {e}")
        logger.debug(traceback.format_exc())
        raise e
        return 1

if __name__ == "__main__":
    sys.exit(main())
