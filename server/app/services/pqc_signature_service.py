import os
import subprocess
from flask import current_app


# ======================================================
# Helper: write / read binary files
# ======================================================

def _write_binary(path: str, data: bytes):
    with open(path, "wb") as f:
        f.write(data)


def _read_binary(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


# ======================================================
# SIGNATURE GENERATION (Sender side)
# ======================================================

def sign_hash_with_dilithium(hash_bytes: bytes) -> bytes:
    """
    Signs a hash using Dilithium (ML-DSA) private key.

    Input:
        hash_bytes → hash of encrypted file + Kyber ciphertext

    Output:
        signature bytes
    """

    pqc_key_folder = current_app.config["PQC_KEY_FOLDER"]

    hash_path = os.path.join(pqc_key_folder, "data_to_sign.bin")
    sig_path = os.path.join(pqc_key_folder, "signature.bin")

    # Write hash to file (input for C binary)
    _write_binary(hash_path, hash_bytes)

    dilithium_sign_bin = os.path.join(
        current_app.root_path,
        "services", "PQC", "dilithium", "bin", "dilithium_sign"
    )

    if not os.path.exists(dilithium_sign_bin):
        raise FileNotFoundError("Dilithium sign binary not found")

    # Run Dilithium signing binary
    subprocess.run(
        [dilithium_sign_bin],
        check=True
    )

    # Read generated signature
    return _read_binary(sig_path)


# ======================================================
# SIGNATURE VERIFICATION (Receiver side)
# ======================================================

def verify_dilithium_signature(hash_bytes: bytes, signature: bytes) -> bool:
    """
    Verifies Dilithium (ML-DSA) signature.

    Returns:
        True  → signature valid
        False → signature invalid
    """

    pqc_key_folder = current_app.config["PQC_KEY_FOLDER"]

    hash_path = os.path.join(pqc_key_folder, "data_to_verify.bin")
    sig_path = os.path.join(pqc_key_folder, "signature.bin")

    # Write verification inputs
    _write_binary(hash_path, hash_bytes)
    _write_binary(sig_path, signature)

    dilithium_verify_bin = os.path.join(
        current_app.root_path,
        "services", "PQC", "dilithium", "bin", "dilithium_verify"
    )

    if not os.path.exists(dilithium_verify_bin):
        raise FileNotFoundError("Dilithium verify binary not found")

    # Run verification binary
    result = subprocess.run(
        [dilithium_verify_bin],
        capture_output=True
    )

    # Convention: exit code 0 → valid signature
    return result.returncode == 0