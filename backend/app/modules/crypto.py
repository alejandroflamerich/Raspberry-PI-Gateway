from pathlib import Path
import os
from cryptography.fernet import Fernet


def _backend_root() -> Path:
    # backend/app/modules/crypto.py -> backend (parents[2])
    return Path(__file__).resolve().parents[2]


def secrets_dir() -> Path:
    # allow overriding via env var
    p = os.environ.get('BACKEND_SECRETS_DIR')
    if p:
        return Path(p)
    return _backend_root() / '.secrets'


def ensure_secrets_dir() -> Path:
    d = secrets_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _key_path() -> Path:
    return ensure_secrets_dir() / 'secret.key'


def _cred_path() -> Path:
    return ensure_secrets_dir() / 'credentials.enc'


def generate_key() -> bytes:
    key = Fernet.generate_key()
    kp = _key_path()
    with open(kp, 'wb') as f:
        f.write(key)
    try:
        os.chmod(kp, 0o600)
    except Exception:
        pass
    return key


def load_key() -> bytes | None:
    kp = _key_path()
    if not kp.exists():
        return None
    return kp.read_bytes()


def encrypt_password(password: str) -> None:
    key = load_key()
    if key is None:
        key = generate_key()
    f = Fernet(key)
    token = f.encrypt(password.encode('utf-8'))
    cp = _cred_path()
    with open(cp, 'wb') as fh:
        fh.write(token)
    try:
        os.chmod(cp, 0o600)
    except Exception:
        pass


def decrypt_password() -> str | None:
    key = load_key()
    cp = _cred_path()
    if key is None or not cp.exists():
        return None
    try:
        f = Fernet(key)
        data = cp.read_bytes()
        return f.decrypt(data).decode('utf-8')
    except Exception:
        return None


def has_encrypted_password() -> bool:
    return _cred_path().exists() and _key_path().exists()


def delete_encrypted_password() -> None:
    kp = _key_path()
    cp = _cred_path()
    try:
        if cp.exists():
            cp.unlink()
    except Exception:
        pass
    try:
        if kp.exists():
            kp.unlink()
    except Exception:
        pass
