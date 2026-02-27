"""
Credentials Encryption Service
Secure encryption/decryption of sensitive data using Fernet (symmetric encryption)
"""

import logging
import threading
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
import secrets, hashlib

from app.core.config import settings

logger = logging.getLogger(__name__)

# Thread lock for singleton initialization
_encryption_lock = threading.Lock()


class EncryptionError(Exception):
    """Raised when encryption/decryption fails"""
    pass


class CredentialsEncryption:
    """
    Handles encryption and decryption of sensitive credentials

    Uses Fernet (symmetric encryption) which is:
    - Built on AES-128-CBC with HMAC authentication
    - Secure and industry-standard
    - Fast and simple to use

    Key Management:
    - Encryption key should be stored in environment variable
    - DO NOT hardcode the key in source code
    - Rotate keys periodically in production
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption service

        Args:
            encryption_key: Base64-encoded Fernet key (32 bytes)
                           If not provided, uses ENCRYPTION_KEY from settings
        """
        # Get encryption key from settings or parameter
        key = getattr(settings, 'ENCRYPTION_KEY', None)

        # if not key:
            # logger.warning(
            #     "ENCRYPTION_KEY not set! Using a temporary key. "
            #     "SET THIS IN PRODUCTION via environment variable!"
            # )
            # Generate a temporary key (NOT FOR PRODUCTION!)
            # key = Fernet.generate_key().decode()
            # logger.warning(f"Generated temporary key: {key}")
            # logger.warning("Add this to your .env file as ENCRYPTION_KEY")

        # Ensure key is bytes
        if isinstance(key, str):
            key = key.encode()

        try:
            self.cipher = Fernet(key)
            logger.info("Encryption service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise EncryptionError(f"Invalid encryption key: {e}")

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string

        Raises:
            EncryptionError: If encryption fails
        """
        if not plaintext:
            return ""

        try:
            # Convert to bytes
            plaintext_bytes = plaintext.encode('utf-8')

            # Encrypt
            encrypted_bytes = self.cipher.encrypt(plaintext_bytes)

            # Return as base64 string
            encrypted_string = encrypted_bytes.decode('utf-8')

            logger.debug(f"Encrypted {len(plaintext)} characters")
            return encrypted_string

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data: {e}")

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string

        Args:
            encrypted_text: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            EncryptionError: If decryption fails (wrong key, corrupted data, etc.)
        """
        if not encrypted_text:
            return ""

        try:
            # Convert to bytes
            encrypted_bytes = encrypted_text.encode('utf-8')
            print("ENCRYPTED BYTES: ", encrypted_bytes)

            # Decrypt
            plaintext_bytes = self.cipher.decrypt(encrypted_bytes)
            print("PLAINTEXT BYTES: ",plaintext_bytes)

            # Return as string
            plaintext = plaintext_bytes.decode('utf-8')

            logger.debug(f"Decrypted {len(plaintext)} characters")
            return plaintext

        except InvalidToken:
            logger.error("Decryption failed: Invalid token (wrong key or corrupted data)")
            raise EncryptionError(
                "Failed to decrypt: Invalid encryption key or data corrupted. "
                "This may happen if the ENCRYPTION_KEY was changed."
            )
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt data: {e}")

    def encrypt_credentials(self, credentials: dict) -> dict:
        """
        Encrypt all sensitive fields in a credentials dictionary

        Args:
            credentials: Dictionary with sensitive fields

        Returns:
            Dictionary with encrypted values
        """
        encrypted = {}

        # Define which fields should be encrypted
        sensitive_fields = {'app_key', 'app_secret', 'access_token', 'api_key', 'password'}

        for key, value in credentials.items():
            if key in sensitive_fields and value:
                encrypted[key] = self.encrypt(str(value))
            else:
                encrypted[key] = value

        return encrypted

    def decrypt_credentials(self, credentials: dict) -> dict:
        """
        Decrypt all encrypted fields in a credentials dictionary

        Args:
            credentials: Dictionary with encrypted fields

        Returns:
            Dictionary with decrypted values
        """
        decrypted = {}

        # Define which fields should be decrypted
        sensitive_fields = {'app_key', 'app_secret', 'access_token', 'api_key', 'password'}

        for key, value in credentials.items():
            if key in sensitive_fields and value:
                try:
                    decrypted[key] = self.decrypt(str(value))
                except EncryptionError:
                    # If decryption fails, value might be unencrypted (legacy data)
                    logger.warning(f"Failed to decrypt {key}, assuming unencrypted")
                    decrypted[key] = value
            else:
                decrypted[key] = value

        return decrypted


# Singleton instance (thread-safe)
_encryption_service: Optional[CredentialsEncryption] = None


def get_encryption_service() -> CredentialsEncryption:
    """Get thread-safe encryption service singleton"""
    global _encryption_service
    if _encryption_service is None:
        with _encryption_lock:
            # Double-check locking pattern
            if _encryption_service is None:
                _encryption_service = CredentialsEncryption()
    return _encryption_service


def generate_new_key() -> str:
    """
    Generate a new Fernet encryption key

    Use this to generate a key for your .env file:

    ```python
    from app.utils.encryption import generate_new_key
    key = generate_new_key()
    print(f"Add this to your .env file:\nENCRYPTION_KEY={key}")
    ```

    Returns:
        Base64-encoded Fernet key
    """
    key = Fernet.generate_key()
    return key.decode('utf-8')

def generate_api_key():
    raw_key = "client_" + secrets.token_urlsafe(48)
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, hashed_key

if __name__ == "__main__":
    # Generate a new key when run directly
    print("=" * 70)
    print("FERNET ENCRYPTION KEY GENERATOR")
    print("=" * 70)
    key = generate_new_key()
    print("\nGenerated new encryption key:")
    print(f"\nENCRYPTION_KEY={key}")
    print("\n⚠️  IMPORTANT:")
    print("1. Add this to your .env file")
    print("2. NEVER commit this key to git")
    print("3. Use different keys for dev/staging/production")
    print("4. Store production key in a secrets manager (AWS Secrets Manager, etc.)")
    print("=" * 70)
