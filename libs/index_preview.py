import os
import pandas as pd
import streamlit as st
from libs.common import load_graphrag_config, project_path
from pathlib import Path

def index_preview(project_name: str):
    if st.button('Preview Index', key=f"index_preview_{project_name}", icon="🔍"):

        config = load_graphrag_config(project_name)

        artifacts_path = config.storage.base_dir

        with st.spinner(f'Reading ...'):
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "👤 entities",
                "🔗 nodes",
                "👥 communities",
                "🪄 community_reports",
                "📄 documents",
                "🔗 relationships",
                "🔗 text_units",
                ])
            with tab1:
                get_parquet_file(project_name=project_name, artifact_name="create_final_entities.parquet", artifacts_path=artifacts_path)
            with tab2:
                get_parquet_file(project_name=project_name, artifact_name="create_final_nodes.parquet", artifacts_path=artifacts_path)
            with tab3:
                get_parquet_file(project_name=project_name, artifact_name="create_final_communities.parquet", artifacts_path=artifacts_path)
            with tab4:
                get_parquet_file(project_name=project_name, artifact_name="create_final_community_reports.parquet", artifacts_path=artifacts_path)
            with tab5:
                get_parquet_file(project_name=project_name, artifact_name="create_final_documents.parquet", artifacts_path=artifacts_path)
            with tab6:
                get_parquet_file(project_name=project_name, artifact_name="create_final_relationships.parquet", artifacts_path=artifacts_path)
            with tab7:
                get_parquet_file(project_name=project_name, artifact_name="create_final_text_units.parquet", artifacts_path=artifacts_path)


def get_parquet_file(project_name:str, artifact_name: str, artifacts_path: str):
    parquet_path = Path(project_path(project_name)) / artifacts_path / artifact_name
    
    if not os.path.exists(parquet_path):
        st.write(f"File not found: `{artifact_name}`")
        return
    
    pdc = pd.read_parquet(parquet_path)
    st.write(f"Items: `{len(pdc)}`")
    st.write(pdc.head(n=20000))
        
