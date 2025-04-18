import os
import pandas as pd
from cli.logger import get_logger
from cli.types import PreviewType
from cli.common import project_path, load_graphrag_config

logger = get_logger('index_preview')

def index_preview(project_name: str, type: PreviewType):

    config = load_graphrag_config(project_name)

    artifacts_path = config.storage.base_dir

    if type == PreviewType.entities.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_entities.parquet", artifacts_path=artifacts_path)
    elif type == PreviewType.nodes.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_nodes.parquet", artifacts_path=artifacts_path)
    elif type == PreviewType.communities.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_communities.parquet", artifacts_path=artifacts_path)
    elif type == PreviewType.community_reports.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_community_reports.parquet", artifacts_path=artifacts_path)
    elif type == PreviewType.documents.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_documents.parquet", artifacts_path=artifacts_path)
    elif type == PreviewType.relationships.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_relationships.parquet", artifacts_path=artifacts_path)
    elif type == PreviewType.text_units.value:
        get_parquet_file(project_name=project_name, artifact_name="create_final_text_units.parquet", artifacts_path=artifacts_path)


def get_parquet_file(project_name:str, artifact_name: str, artifacts_path: str):
    parquet_path = f"{artifacts_path}/{artifact_name}"
    
    if not os.path.exists(parquet_path):
        logger.error(f"File not found: `{artifact_name}`")
        return
    
    pdc = pd.read_parquet(parquet_path)
    logger.info(f"Items: `{len(pdc)}`")
    logger.info(f"\n{pdc.head(n=20000)}")
        
