#!/usr/bin/env python3

import sys
import asyncio
from pathlib import Path
import traceback

from cli.common import load_graphrag_config, project_path
from cli.types import PreviewType, ArgConfig
from cli.logger import get_logger
from cli.create_project import init_graphrag_project

import libs.config as config

from openai import AzureOpenAI

logger = get_logger('file_processor')


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
