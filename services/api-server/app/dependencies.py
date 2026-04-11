from typing import AsyncGenerator
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
import jwt
import boto3
from botocore.config import Config
from redis.asyncio import Redis
from app.config import settings
from app.models.user import User
from app.services.storage_service import StorageService

engine = create_async_engine(settings.DATABASE_URL, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_storage_service() -> StorageService:
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    return StorageService(s3_client)


def get_redis_client() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        user = await db.scalar(select(User).where(User.id == UUID(user_id)))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")