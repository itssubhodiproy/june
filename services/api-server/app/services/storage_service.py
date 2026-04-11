from botocore.client import BaseClient

from app.config import settings


class StorageService:
    def __init__(self, client: BaseClient) -> None:
        self.client = client

    def object_exists(self, *, file_key: str) -> bool:
        try:
            self.client.head_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=file_key,
            )
            return True
        except self.client.exceptions.NoSuchKey:
            return False
        except Exception as exc:
            error_code = getattr(exc, "response", {}).get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise

    def create_presigned_upload_url(self, *, file_key: str, file_type: str) -> str:
        return self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": file_key,
                "ContentType": file_type,
            },
            ExpiresIn=settings.S3_PRESIGNED_EXPIRY,
        )
