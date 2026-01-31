import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os


# ======================================================
# AES key derivation (from Kyber shared secret)
# ======================================================

def derive_aes_key_from_shared_secret(shared_secret: bytes) -> bytes:
    """
    Deterministically derive AES-256 key from Kyber shared secret
    """

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,  # AES-256
        salt=None,
        info=b"pqc-document-encryption",
        backend=default_backend()
    )

    return hkdf.derive(shared_secret)




# ======================================================
# Binary-safe hashing for PQC workflow
# ======================================================

def compute_hash_from_encrypted_file_and_kyber_ct(
    encrypted_file_path: str,
    kyber_ct_path: str
) -> bytes:
    """
    Computes SHA-512 hash over:
    1. Encrypted document (.enc file)
    2. Kyber ciphertext (.bin)

    Returns:
        hash bytes (64 bytes)
    """

    if not os.path.exists(encrypted_file_path):
        raise FileNotFoundError(f"Encrypted file not found: {encrypted_file_path}")

    if not os.path.exists(kyber_ct_path):
        raise FileNotFoundError(f"Kyber ciphertext not found: {kyber_ct_path}")

    hasher = hashlib.sha512()

    # Read encrypted document (binary)
    with open(encrypted_file_path, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)

    # Read Kyber ciphertext (binary)
    with open(kyber_ct_path, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)

    return hasher.digest()