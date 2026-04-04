from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from app.config import settings
from app.models.user import User
from app.schemas.auth import UserRegister
from app.services.workspace_service import WorkspaceService


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )

    def create_token(self, user_id: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS)
        payload = {"sub": str(user_id), "exp": expire}
        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    async def register(self, data: UserRegister) -> User:
        existing = await self.db.scalar(select(User).where(User.email == data.email))
        if existing:
            raise ValueError("User already exists")

        hashed_password = self.hash_password(data.password)
        user = User(
            email=data.email,
            name=data.name,
            password_hash=hashed_password,
        )
        self.db.add(user)
        try:
            await self.db.flush()

            workspace_service = WorkspaceService(self.db)
            await workspace_service._create_workspace(
                user=user,
                name="Personal Workspace",
                is_personal=True,
            )

            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("User already exists")
        await self.db.refresh(user)
        return user

    async def login(self, email: str, password: str) -> tuple[User, str]:
        user = await self.db.scalar(select(User).where(User.email == email))
        if not user:
            raise ValueError("Invalid credentials")

        if not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")
            
        token = self.create_token(user.id)
        return user, token
