import os
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from cli.logger import get_logger

logger = get_logger('blob')

load_dotenv()

connection_string = os.getenv("DATA_AZURE_CONNECTION_STRING", "")


def get_container_name(project_name):
    container_name = "graphrag" + project_name + "cache"
    container_name = container_name.replace("_", "")
    container_name = container_name.replace("-", "")
    return container_name


def upload_file(project_name, file_path):
    
    if not connection_string:
        return
        
    try:
        container_name = get_container_name(project_name)

        file_name = os.path.basename(file_path)

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        container_client = blob_service_client.get_container_client(container_name)

        if not container_client.exists():
            container_client.create_container()

        blob_client = container_client.get_blob_client(file_name)
        
        content_settings = None
        if file_path.endswith(".png"):
            content_settings = ContentSettings(content_type="image/png", content_disposition="inline")

        if file_path.endswith(".pdf"):
            content_settings = ContentSettings(content_type="application/pdf", content_disposition="inline")
        
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True, content_settings=content_settings)
            container_client.set_container_access_policy(signed_identifiers=None, public_access="container")
    except Exception as e:
        logger.error(f"Error uploading file {file_name}: {e}")


def get_sas_url(project_name, blob_name):
    try:
        container_name = get_container_name(project_name)

        expiry_time = datetime.now(timezone.utc) + timedelta(hours=1)

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        sas_token = generate_blob_sas(
            connection_string=connection_string,
            container_name=container_name,
            account_name=blob_service_client.account_name,
            blob_name=blob_name,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
            account_key=blob_service_client.credential.account_key
        )
        
        sas_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"

        return sas_url, ""
    except Exception as e:
        print(f"Error generating SAS URL for {blob_name}: {e}")
        return "", str(e)
