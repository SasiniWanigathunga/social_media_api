import logging
from functools import lru_cache
import b2sdk.v1 as b2
from social_media_api.config import config

logger = logging.getLogger(__name__)

@lru_cache()
def b2_api():
    logger.info("Initializing and authorizing B2 API")
    info = b2.InMemoryAccountInfo()
    b2_api = b2.B2Api(info)
    b2_api.authorize_account("production", config.B2_KEY_ID, config.B2_APPLICATION_KEY)
    return b2_api

@lru_cache()
def get_b2_bucket(api: b2.B2Api):
    logger.info("Getting B2 bucket")
    return api.get_bucket_by_name(config.B2_BUCKET_NAME)

def upload_file_to_b2(local_file: str, file_name: str):
    api = b2_api()
    logger.info(f"Uploading file {local_file} to B2 bucket {config.B2_BUCKET_NAME} as {file_name}")
    
    upload_file = get_b2_bucket(api).upload_local_file(
        local_file=local_file,
        file_name=file_name,
    )

    download_url = api.get_download_url_for_fileid(upload_file.id_)
    logger.info(f"File uploaded successfully. Download URL: {download_url}")
    return download_url