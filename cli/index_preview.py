import os
import pandas as pd
from cli.logger import get_logger
from cli.types import PreviewType
from cli.common import project_path

logger = get_logger('index_preview')

def index_preview(project_name: str, type: PreviewType):
    if type == PreviewType.entities.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_entities.parquet")
    elif type == PreviewType.nodes.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_nodes.parquet")
    elif type == PreviewType.communities.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_communities.parquet")
    elif type == PreviewType.community_reports.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_community_reports.parquet")
    elif type == PreviewType.documents.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_documents.parquet")
    elif type == PreviewType.relationships.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_relationships.parquet")
    elif type == PreviewType.text_units.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_text_units.parquet")


def get_parquet_file(project_name:str, artifact_name: str):
    parquet_path = f"{project_path(project_name)}/output/{artifact_name}"
    
    if not os.path.exists(parquet_path):
        logger.error(f"File not found: `{artifact_name}`")
        return
    
    pdc = pd.read_parquet(parquet_path)
    logger.info(f"Items: `{len(pdc)}`")
    logger.info(f"\n{pdc.head(n=20000)}")
        
