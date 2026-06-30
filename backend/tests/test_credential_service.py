"""Tests for CredentialService (03-02)."""
import json
import types
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from cryptography.fernet import InvalidToken

from app.models.credential import UserCredential
from app.models.user import User
from app.services.credential_service import CredentialService


def make_stub_user(**kwargs):
    """Return a plain namespace acting like a User for encrypt/decrypt unit tests.

    Does NOT involve SQLAlchemy — avoids InstrumentedAttribute issues for pure unit tests.
    """
    ns = types.SimpleNamespace()
    ns.id = kwargs.get("id", uuid4())
    ns.email = kwargs.get("email", "test@example.com")
    ns.envelope_key = kwargs.get("envelope_key", None)
    return ns


# ── Pure encrypt / decrypt (no DB) ────────────────────────────────────────────

def test_encrypt_decrypt():
    svc = CredentialService()
    user = make_stub_user()
    plaintext = '{"access_token": "abc"}'
    ciphertext = svc.encrypt(user, plaintext)
    assert svc.decrypt(user, ciphertext) == plaintext


def test_encrypt_different_per_call():
    """Fernet uses a random IV so same plaintext produces different ciphertext each call."""
    svc = CredentialService()
    user = make_stub_user()
    c1 = svc.encrypt(user, "same input")
    c2 = svc.encrypt(user, "same input")
    assert c1 != c2


def test_envelope_key_generated_if_none():
    svc = CredentialService()
    user = make_stub_user(envelope_key=None)
    assert user.envelope_key is None
    svc.encrypt(user, "test")
    assert user.envelope_key is not None
    assert len(user.envelope_key) == 32


def test_wrong_key_raises():
    svc = CredentialService()
    user_a = make_stub_user()
    user_b = make_stub_user()
    ciphertext = svc.encrypt(user_a, "secret")
    with pytest.raises(InvalidToken):
        svc.decrypt(user_b, ciphertext)


# ── DB-backed tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_store_and_get_credential(test_db):
    svc = CredentialService()
    uid = uuid4()
    db_user = User(id=uid, email="u1@test.com", password_hash=None, is_verified=False)
    test_db.add(db_user)
    await test_db.flush()

    cred_dict = {"access_token": "tok123", "refresh_token": "ref456"}
    await svc.store_credential(db_user, "yahoo", cred_dict, test_db)
    await test_db.flush()

    result = await svc.get_credential(db_user, "yahoo", test_db)
    assert result == cred_dict


@pytest.mark.asyncio
async def test_store_upsert(test_db):
    """Calling store_credential twice for same (user, platform) upserts — no duplicate rows."""
    from sqlalchemy import func, select as sa_select
    svc = CredentialService()
    uid = uuid4()
    db_user = User(id=uid, email="u2@test.com", password_hash=None, is_verified=False)
    test_db.add(db_user)
    await test_db.flush()

    await svc.store_credential(db_user, "yahoo", {"access_token": "v1"}, test_db)
    await test_db.flush()
    await svc.store_credential(db_user, "yahoo", {"access_token": "v2"}, test_db)
    await test_db.flush()

    count_result = await test_db.execute(
        sa_select(func.count()).select_from(UserCredential).where(
            UserCredential.user_id == uid,
            UserCredential.platform == "yahoo",
        )
    )
    assert count_result.scalar() == 1

    result = await svc.get_credential(db_user, "yahoo", test_db)
    assert result == {"access_token": "v2"}


@pytest.mark.asyncio
async def test_get_returns_none(test_db):
    svc = CredentialService()
    uid = uuid4()
    db_user = User(id=uid, email="u3@test.com", password_hash=None, is_verified=False)
    test_db.add(db_user)
    await test_db.flush()

    result = await svc.get_credential(db_user, "espn", test_db)
    assert result is None


@pytest.mark.asyncio
async def test_mark_unhealthy(test_db):
    from sqlalchemy import select as sa_select
    svc = CredentialService()
    uid = uuid4()
    db_user = User(id=uid, email="u4@test.com", password_hash=None, is_verified=False)
    test_db.add(db_user)
    await test_db.flush()

    await svc.store_credential(db_user, "espn", {"swid": "x", "is_public": False}, test_db)
    await test_db.flush()

    await svc.mark_unhealthy(uid, "espn", test_db)
    await test_db.flush()

    row_result = await test_db.execute(
        sa_select(UserCredential).where(
            UserCredential.user_id == uid,
            UserCredential.platform == "espn",
        )
    )
    row = row_result.scalar_one()
    assert row.is_healthy is False
    assert row.last_validated_at is not None
