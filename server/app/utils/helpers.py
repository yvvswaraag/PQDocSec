from cryptography.hazmat.primitives import hashes
import base64

def bin_to_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")

def b64_to_bin(data: str) -> bytes:
    return base64.b64decode(data.encode("utf-8")) 

def sha256_hash_file(file_path):
    """
    Computes SHA-256 hash of a file.
    Returns hash bytes.
    """
    digest = hashes.Hash(hashes.SHA256())

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            digest.update(chunk)

    return digest.finalize()
