import boto3
import uuid
from src.config import Config
import mimetypes
from fastapi import UploadFile, HTTPException, status
from botocore.exceptions import NoCredentialsError, ClientError


ALLOWED_FILE_TYPES = {
    "image/jpeg", "image/png", "application/pdf", 
    "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
MAX_FILE_SIZE_MB = 10

s3_client = boto3.client(
    "s3",
    region_name=Config.AWS_S3_REGION,
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
)


async def upload_file_to_s3(file: UploadFile) -> str:
    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = f"File size exceeds the maximum limit of {MAX_FILE_SIZE_MB} MB."
        )
    await file.seek(0)  # Reset file pointer after reading

    # Validate file type
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Unsupported file type."
        )
    
    # Generate unique file key
    file_extension = mimetypes.guess_extension(file.content_type) or ""
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # Upload to S3
    try:
        s3_client.upload_fileobj(
            file.file,
            Config.AWS_S3_BUCKET_NAME,
            unique_filename,
            ExtraArgs={"ContentType": file.content_type}
        )
        file_url = f"https://{Config.AWS_S3_BUCKET_NAME}.s3.{Config.AWS_S3_REGION}.amazonaws.com/{unique_filename}"
        return file_url


    except (NoCredentialsError, ClientError) as e:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"S3 upload failed: {str(e)}"
        ) 