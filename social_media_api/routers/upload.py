import logging
import tempfile
from fastapi import APIRouter, UploadFile, HTTPException, status
import aiofiles
from social_media_api.libs.b2 import upload_file_to_b2

logger = logging.getLogger(__name__)

router = APIRouter()

CHUNK_SIZE = 1024 * 1024  # 1MB

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile):
    try:
        with tempfile.NamedTemporaryFile() as temp_file:
            filename = temp_file.name
            logger.info(f"Saving uploaded file to temporary location: {filename}")
            async with aiofiles.open(filename, 'wb') as f:
                while chunk := await file.read(CHUNK_SIZE):
                    await f.write(chunk)

            file_url = upload_file_to_b2(local_file=filename, file_name=file.filename)
    except Exception:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while uploading the file.",
        )
    return {"detail": f"Successfully uploaded {file.filename} to B2.", "file_url": file_url}