#!/usr/bin/env python3

import sys
import asyncio
from pathlib import Path
import traceback

from cli.common import load_graphrag_config, project_path
from cli.types import PreviewType, ArgConfig
from cli.generate_data import  generate_data
from cli.logger import get_logger
from cli.index_preview import index_preview
from cli.prompt_tuning import prompt_tuning
from cli.build_index import build_index, update_index
from cli.create_project import init_graphrag_project
from cli.upload_file import upload_files

import libs.config as config

from openai import AzureOpenAI

logger = get_logger('file_processor')

def process_a_project(config: ArgConfig):
    """process a project
    
    Args:
        project_name: project name
    """
    logger.info(f"process project: {config.project}")
    
    try:
        # step 1: upload files
        upload_files(config.project, config.input_dir)

        # step 2: generate data
        generate_data(config.project, config.pdf_vision_option)
        
        # step 3: prompt tuning
        asyncio.run(prompt_tuning(config.project))
        
        # step 4: build index
        build_index(config.project)
        
        # step 5: complete processing
        logger.info(f"project {config.project} processed successfully")
        return True
    
    except Exception as e:
        logger.error(f"process project {config.project} failed: {e}")
        logger.debug(traceback.format_exc())
        raise e
        return False

def process_all_projects(config: ArgConfig):
    process_a_project( config) 
    return True


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

        process_parser = subparsers.add_parser('generate_data', help='generate data for project')
        process_parser.add_argument('--project', help='specify project name', required=True)
        process_parser.add_argument('--input_dir', help='specify input directory', required=True)
        process_parser.add_argument('--pdf_vision_option', help='specify pdf vision option', required=False, default=config.generate_data_vision)

        process_parser = subparsers.add_parser('prompt_tuning', help='prompt tuning')
        process_parser.add_argument('--project', help='specify project name', required=True)

        process_parser = subparsers.add_parser('build_index', help='build index')
        process_parser.add_argument('--project', help='specify project name', required=True)

        process_parser = subparsers.add_parser('update_index', help='update index')
        process_parser.add_argument('--project', help='specify project name', required=True)

        process_parser = subparsers.add_parser('test_config', help='test config')
        process_parser.add_argument('--project', help='specify project name', required=True)

        process_parser = subparsers.add_parser('index_preview', help='index preview')
        process_parser.add_argument('--project', help='specify project name', required=True)
        process_parser.add_argument('--type', help='specify index type', required=True, choices=[e.value for e in PreviewType])

        process_parser = subparsers.add_parser('test_query', help='test query')
        process_parser.add_argument('--project', help='specify project name', required=True)
        process_parser.add_argument('--query', help='specify query', required=True)

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
            process_config = ArgConfig(project=args.project, input_dir=args.input_dir, pdf_vision_option=args.pdf_vision_option)
            if process_a_project(process_config):
                logger.info("=== automation processing completed ===")
                return 0
            else:
                logger.error("=== automation processing failed ===")
                return 1
        elif args.command == 'generate_data':
            logger.info("=== start generate data ===")
            if args.input_dir:
                upload_files(args.project, args.input_dir)
            generate_data(args.project, args.pdf_vision_option)
            logger.info("=== generate data completed ===")
            return 0
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
        elif args.command == 'update_index':
            logger.info("=== start update index ===")
            update_index(args.project)
            logger.info("=== update index completed ===")
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
        elif args.command == 'test_query':
            pass
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
