import secrets
from passlib.context import CryptContext

# Configure passlib for hashing API keys
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Non-secret namespace used in the visible prefix (helps users identify keys)
PREFIX_NAMESPACE = "amos"
KEY_SEPARATOR = "."


def generate_api_key() -> tuple[str, str]:
    """
    Generate a new API key.
    Returns:
        - plaintext_key: The full key to show once to the user.
        - key_prefix: A short, non-secret prefix safe to store/display.
    """
    prefix_suffix = secrets.token_hex(4)  # 8 hex chars
    key_prefix = f"{PREFIX_NAMESPACE}_{prefix_suffix}"
    random_part = secrets.token_urlsafe(32)
    plaintext_key = f"{key_prefix}{KEY_SEPARATOR}{random_part}"
    return plaintext_key, key_prefix

def hash_api_key(plain_key: str) -> str:
    """
    Securely hash the plaintext API key for storage.
    """
    return pwd_context.hash(plain_key)

def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Verify a plaintext API key against a stored hash.
    """
    return pwd_context.verify(plain_key, hashed_key)