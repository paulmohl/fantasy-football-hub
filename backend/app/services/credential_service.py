import base64
import json
import os
from datetime import UTC, datetime

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credential import UserCredential
from app.models.user import User


class CredentialService:
    """Encrypt/decrypt and store platform credentials per user.

    All callers must use this class — never write credentials_encrypted directly.
    Encrypted blob format:
      Yahoo:        {"access_token": "...", "refresh_token": "...", "expires_at": 1234567890}
      ESPN private: {"swid": "{...}", "espn_s2": "...", "is_public": false}
      ESPN public:  {"league_id": "12345", "is_public": true}
    """

    def _get_fernet(self, user: User) -> Fernet:
        if user.envelope_key is None:
            user.envelope_key = os.urandom(32)
        return Fernet(base64.urlsafe_b64encode(user.envelope_key))

    def encrypt(self, user: User, plaintext: str) -> bytes:
        return self._get_fernet(user).encrypt(plaintext.encode())

    def decrypt(self, user: User, ciphertext: bytes) -> str:
        return self._get_fernet(user).decrypt(ciphertext).decode()

    async def store_credential(
        self,
        user: User,
        platform: str,
        credential_dict: dict,
        db: AsyncSession,
    ) -> UserCredential:
        """Encrypt credential_dict and upsert into user_credentials.

        platform: "yahoo" | "espn"
        """
        ciphertext = self.encrypt(user, json.dumps(credential_dict))

        result = await db.execute(
            select(UserCredential).where(
                UserCredential.user_id == user.id,
                UserCredential.platform == platform,
            )
        )
        credential = result.scalar_one_or_none()

        if credential is None:
            credential = UserCredential(
                user_id=user.id,
                platform=platform,
                credentials_encrypted=ciphertext,
                is_healthy=True,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            )
            db.add(credential)
        else:
            credential.credentials_encrypted = ciphertext
            credential.is_healthy = True

        await db.flush()
        return credential

    async def get_credential(
        self,
        user: User,
        platform: str,
        db: AsyncSession,
    ) -> dict | None:
        """Return decrypted credential dict or None if not stored."""
        result = await db.execute(
            select(UserCredential).where(
                UserCredential.user_id == user.id,
                UserCredential.platform == platform,
            )
        )
        credential = result.scalar_one_or_none()
        if credential is None:
            return None
        return json.loads(self.decrypt(user, credential.credentials_encrypted))

    async def mark_unhealthy(
        self,
        user_id,
        platform: str,
        db: AsyncSession,
    ) -> None:
        """Mark credential as unhealthy (called when 401 detected during sync)."""
        result = await db.execute(
            select(UserCredential).where(
                UserCredential.user_id == user_id,
                UserCredential.platform == platform,
            )
        )
        credential = result.scalar_one_or_none()
        if credential:
            credential.is_healthy = False
            credential.last_validated_at = datetime.now(UTC).replace(tzinfo=None)
            await db.flush()

    async def get_health(self, user_id, db: AsyncSession) -> list[dict]:
        """Return list of {platform, is_healthy} for all credentials belonging to user."""
        result = await db.execute(
            select(UserCredential).where(UserCredential.user_id == user_id)
        )
        rows = result.scalars().all()
        return [{"platform": r.platform, "is_healthy": r.is_healthy} for r in rows]
