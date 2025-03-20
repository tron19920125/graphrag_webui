
from enum import Enum
from pydantic import BaseModel

class ArgConfig(BaseModel):
    project: str
    input_dir: str
    pdf_vision_option: str

class PreviewType(Enum):
    entities = "entities"
    nodes = "nodes"
    communities = "communities"
    community_reports = "community_reports"
    documents = "documents"
    relationships = "relationships"
    text_units = "text_units"