---
plan: "03-02"
status: complete
completed_at: "2026-06-29"
---

# 03-02 Summary — CredentialService: Fernet encrypt/decrypt/store/rotate

## What was built

- `backend/app/services/credential_service.py` — `CredentialService` class:
  - `_get_fernet(user)` — generates `os.urandom(32)` envelope key on first use; derives Fernet key via base64 encoding
  - `encrypt(user, plaintext)` → bytes
  - `decrypt(user, ciphertext)` → str (raises `InvalidToken` on wrong key/tampered bytes)
  - `store_credential(user, platform, credential_dict, db)` — upserts `UserCredential` row
  - `get_credential(user, platform, db)` → dict | None
  - `mark_unhealthy(user_id, platform, db)` — sets `is_healthy=False`, stamps `last_validated_at`
  - `get_health(user_id, db)` → `[{platform, is_healthy}]`

## Tests

All 8 tests pass (`tests/test_credential_service.py`):
- Pure encrypt/decrypt (no DB) using `SimpleNamespace` stub users
- Round-trip store → get returns original dict
- Second store for same (user, platform) upserts, not duplicates
- `get_credential` returns None when no row exists
- `mark_unhealthy` sets `is_healthy=False` and `last_validated_at`
- Wrong key raises `InvalidToken`

## Notes

- `User.__new__(User)` fails SQLAlchemy InstrumentedAttribute — used `SimpleNamespace` for pure unit tests, real `User(...)` constructor for DB tests
