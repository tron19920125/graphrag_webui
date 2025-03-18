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
    """
    build index
    
    Args:
        project_name: project name
    """
    
    # load project environment variables
    load_dotenv(
        dotenv_path=Path(f"{project_path(project_name)}") / ".env",
        override=True,
    )
    
    target_dir = f"{project_path(project_name)}"
    settings_file = os.path.join(target_dir, 'settings.yaml')
    
    # backup settings.yaml
    backup_file = os.path.join(target_dir, 'settings.yaml.bak')
    shutil.copy2(settings_file, backup_file)
    
    try:
        # modify settings.yaml to avoid path loop
        with open(settings_file, 'r') as f:
            settings = yaml.safe_load(f)
        
        # use simple relative path
        if 'storage' in settings:
            settings['storage']['base_dir'] = 'output'
        if 'reporting' in settings:
            settings['reporting']['base_dir'] = 'logs'
        if 'cache' in settings:
            settings['cache']['base_dir'] = 'cache'
        if 'root_dir' in settings:
            del settings['root_dir']
        
        # save modified settings.yaml
        with open(settings_file, 'w') as f:
            yaml.dump(settings, f)
        
        # create necessary directories and execute command
        current_dir = os.getcwd()
        try:
            os.chdir(target_dir)
            
            # ensure directories exist
            for subdir in ['output', 'logs', 'cache']:
                os.makedirs(subdir, exist_ok=True)
            
            # execute index command
            index_cli(
                root_dir=Path(target_dir),
                verbose=True,
                memprofile=False,
                cache=True,
                logger=LoggerType.PRINT,
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
        logger.error(f"build index error: {e}")
        raise e
    
    finally:
        # restore original settings.yaml
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, settings_file)
            os.remove(backup_file)


def update_index(project_name: str):
    """
    update index
    
    Args:
        project_name: project name
    """
    
    load_dotenv(
        dotenv_path=Path(f"{project_path(project_name)}") / ".env",
        override=True,
    )
    
    target_dir = f"{project_path(project_name)}"
    settings_file = os.path.join(target_dir, 'settings.yaml')
    
    # backup settings.yaml
    backup_file = os.path.join(target_dir, 'settings.yaml.bak')
    shutil.copy2(settings_file, backup_file)
    
    try:
        # modify settings.yaml to avoid path loop
        with open(settings_file, 'r') as f:
            settings = yaml.safe_load(f)
        
        # use simple relative path
        if 'storage' in settings:
            settings['storage']['base_dir'] = 'output'
        if 'reporting' in settings:
            settings['reporting']['base_dir'] = 'logs'
        if 'cache' in settings:
            settings['cache']['base_dir'] = 'cache'
        if 'root_dir' in settings:
            del settings['root_dir']
        
        # save modified settings.yaml
        with open(settings_file, 'w') as f:
            yaml.dump(settings, f)
        
        # create necessary directories and execute command
        current_dir = os.getcwd()
        try:
            os.chdir(target_dir)
            
            # ensure directories exist
            for subdir in ['output', 'logs', 'cache']:
                os.makedirs(subdir, exist_ok=True)
            
            update_cli(
                root_dir=Path(target_dir),
                verbose=True,
                memprofile=False,
                cache=True,
                logger=LoggerType.PRINT,
                config_filepath=None,
                skip_validation=False,
                output_dir=None
            ) 
            return True
        finally:
            os.chdir(current_dir)
            
    except Exception as e:
        logger.error(f"update index error: {e}")
        raise e
    
    finally:
        # restore original settings.yaml
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, settings_file)
            os.remove(backup_file)