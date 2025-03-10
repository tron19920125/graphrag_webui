#!/usr/bin/env python3

import os
import sys
import yaml
import shutil
import logging
import asyncio
import subprocess
from pathlib import Path
import importlib.util
import traceback
from graphrag.cli.initialize import initialize_project_at
import time

import pandas as pd

from cli.common import  run_command
import libs.config as config
from cli.generate_data import  prepare_file, convert_file
from cli.logger import get_logger

class ArgConfig:
    def __init__(self, project, input_dir, pdf_vision_option):
        self.project = project
        self.input_dir = input_dir
        self.pdf_vision_option = pdf_vision_option


root_dir = os.path.dirname(os.path.abspath(__file__))


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

def load_config():
    """加载配置文件"""
    config_path = Path('config.yaml')
    if not config_path.exists():
        logger.error("找不到config.yaml文件")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"读取配置文件失败: {e}")
            sys.exit(1)

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


async def run_prompt_tuning(project_name):
    """执行Prompt Tuning步骤"""
    logger.info(f"为项目 {project_name} 执行Prompt Tuning步骤")
    
    try:
        # 从libs导入prompt_tuning模块
        prompt_tuning_module = import_from_libs('prompt_tuning')
        
        if prompt_tuning_module and hasattr(prompt_tuning_module, 'start'):
            # 构建项目路径
            base_path = os.path.join(os.getcwd(), 'projects', project_name)
            
            # 直接调用start函数进行prompt tuning
            logger.info("开始执行prompt tuning...")
            await prompt_tuning_module.start(base_path)
            logger.info("prompt tuning完成")
        else:
            logger.error("无法导入prompt_tuning模块或模块缺少start函数")
    except Exception as e:
        logger.error(f"Prompt Tuning步骤出错: {e}")
        logger.debug(traceback.format_exc())

def run_build_index(project_name):
    """执行Build Index步骤"""
    logger.info(f"为项目 {project_name} 执行Build Index步骤")
    
    try:
        # 直接执行graphrag命令行工具
        project_dir = os.path.join(os.getcwd(), 'projects', project_name)
        
        # 设置环境变量
        env_file = os.path.join(project_dir, '.env')
        env_vars = {}
        
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
        
        # 构建环境变量
        cmd_env = os.environ.copy()
        cmd_env.update(env_vars)
        
        # 执行graphrag命令
        cmd = ['graphrag', 'index']
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            cwd=project_dir,
            env=cmd_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 读取输出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(output.strip())
        
        # 检查执行结果
        return_code = process.wait()
        
        if return_code == 0:
            logger.info("Build Index步骤完成")
        else:
            stderr = process.stderr.read()
            logger.error(f"Build Index失败，返回代码: {return_code}")
            logger.error(f"错误信息: {stderr}")
            
    except Exception as e:
        logger.error(f"Build Index步骤出错: {e}")
        logger.debug(traceback.format_exc())

def run_index_preview(project_name):
    """执行Index Preview步骤"""
    logger.info(f"为项目 {project_name} 执行Index Preview步骤")
    
    try:
        # 检查输出文件是否存在
        artifacts_path = os.path.join('projects', project_name, 'output')
        
        if not os.path.exists(artifacts_path):
            logger.warning(f"项目 {project_name} 的output目录不存在，跳过Index Preview")
            return
        
        # 检查关键Parquet文件是否存在
        parquet_files = [
            "create_final_entities.parquet",
            "create_final_nodes.parquet",
            "create_final_communities.parquet",
            "create_final_community_reports.parquet",
            "create_final_documents.parquet",
            "create_final_relationships.parquet",
            "create_final_text_units.parquet"
        ]
        
        missing_files = []
        existing_files = []
        
        for file in parquet_files:
            file_path = os.path.join(artifacts_path, file)
            if not os.path.exists(file_path):
                missing_files.append(file)
            else:
                existing_files.append(file)
        
        if missing_files:
            logger.warning(f"以下索引文件不存在: {', '.join(missing_files)}")
        
        if existing_files:
            logger.info(f"以下索引文件存在: {', '.join(existing_files)}")
        else:
            logger.warning(f"项目 {project_name} 没有任何索引文件")
        
    except Exception as e:
        logger.error(f"Index Preview步骤出错: {e}")
        logger.debug(traceback.format_exc())

# ./file_processor.py process --input_dir ./projects/test/original

def handle_input_files(config: ArgConfig):
    """upload files"""
    project_name = config.project
    input_dir = config.input_dir

    Path(f"{os.getcwd()}/projects/{project_name}/original").mkdir(
        parents=True, exist_ok=True)

    if os.path.isdir(input_dir):
        for file in os.listdir(input_dir):
            # copy file to /app/projects/{project_name}/original
            shutil.copy(os.path.join(input_dir, file), os.path.join(f"{root_dir}/projects/{project_name}/original", file))
            # make file permissions to another user can write
            os.chmod(
                f"{root_dir}/projects/{project_name}/original/{file}", 0o666
            )


    return True


def generate_data(config: ArgConfig):
    logger.info(f"generate data for project: {config.project}")
    # 1. copy original files to input
    for root, dirs, files in os.walk(
        f"{root_dir}/projects/{config.project}/original"
    ):
        for file in files:
            file_path = os.path.join(root, file)
            prepare_file(file_path, file, config.project)

    # 2. convert files to txt
    for root, dirs, files in os.walk(f"{root_dir}/projects/{config.project}/input"):
        for file in files:
            file_path = os.path.join(root, file)
            convert_file(file_path, file,
                     config.project, config.pdf_vision_option)

    #  3. make file permissions to another user can write
    for root, dirs, files in os.walk(f"{root_dir}/projects/{config.project}/input"):
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
        # asyncio.run(run_prompt_tuning(config.project))
        
        # # 步骤5: Build Index
        # run_build_index(config.project)
        
        # # 步骤6: Index Preview
        # run_index_preview(config.project)
        
        # 步骤7: 完成处理
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
    settings_yaml = f"{root}/settings.yaml"

    run_command(f"cp {root}/settings.yaml {root}/settings_default.yaml")

    template_settings_yaml = f"{os.path.dirname(__file__)}/template/setting_{create_db_type}.yaml"

    container_name = f"{config.app_name}_{new_project_name}"
    with open(template_settings_yaml, "r") as t:
        with open(settings_yaml, "w") as f:
            new_settings_yaml = t.read().replace(
                "container_name: default", f"container_name: {container_name}"
            ).replace(
                'base_dir: "logs"', f'base_dir: "{root}/logs"'
            ).replace(
                'base_dir: "output"', f'base_dir: "{root}/output"'
            ).replace(
                "db_uri: 'lancedb'", f"db_uri: '{root}/lancedb'"
            )
            f.write(new_settings_yaml)

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
        process_parser.add_argument('--project', help='specify project name', required=False)
        process_parser.add_argument('--input_dir', help='specify input directory', required=False)
        process_parser.add_argument('--pdf_vision_option', help='specify pdf vision option', required=False, default=config.generate_data_vision)
        args = parser.parse_args()

        # process subcommand
        if args.command == 'init':
            if init_graphrag_project(args.project):
                logger.info(f"project {args.project} initialized successfully")
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
