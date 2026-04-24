import boto3

from app.config import settings


class S3Client:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name="us-east-1",
        )

    def download(self, file_key: str) -> bytes:
        response = self.client.get_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=file_key,
        )
        return response["Body"].read()
