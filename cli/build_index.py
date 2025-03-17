import os
import shutil
import yaml
from dotenv import load_dotenv
from pathlib import Path
from cli.common import project_path, run_command
from cli.logger import get_logger
from graphrag.config.load_config import load_config
from graphrag.logger.factory import LoggerFactory, LoggerType
from graphrag.cli.index import update_cli, index_cli

import asyncio
import traceback


logger = get_logger('build_index_cli')

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
            index_cli(
                root_dir=Path(target_dir),
                verbose=True,
                memprofile=False,
                cache=True,
                logger=LoggerType.RICH,
                config_filepath=None,
                skip_validation=False,
                output_dir=None,
                dry_run=False,
                resume=None,
            )
            return True
        finally:
            os.chdir(current_dir)
            
    except Exception as e:
        logger.error(f"构建索引时出错: {e}")
        return False
    
    finally:
        # 恢复原配置
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, settings_file)
            os.remove(backup_file)


def update_index(project_name: str):
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
            
            update_cli(
                root_dir=Path(target_dir),
                verbose=True,
                memprofile=False,
                cache=True,
                logger=LoggerType.RICH,
                config_filepath=None,
                skip_validation=False,
                output_dir=None
            ) 
            return True
        finally:
            os.chdir(current_dir)
            
    except Exception as e:
        logger.error(f"更新索引时出错: {e}")
        raise e
    
    finally:
        # 恢复原配置
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, settings_file)
            os.remove(backup_file)