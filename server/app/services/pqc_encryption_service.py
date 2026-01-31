import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend


# ======================================================
# AES-256-CBC encryption (PQC version)
# ======================================================

def encrypt_file_with_aes_key(input_path: str, output_dir: str, aes_key: bytes):
    """
    Encrypts a file using AES-256-CBC.
    AES key is PROVIDED (derived from Kyber).
    
    Returns:
        encrypted_file_path
    """

    os.makedirs(output_dir, exist_ok=True)

    # Read plaintext
    with open(input_path, "rb") as f:
        plaintext = f.read()

    # Generate IV
    iv = os.urandom(16)  # 128-bit IV

    # Pad plaintext
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()

    # Encrypt
    cipher = Cipher(
        algorithms.AES(aes_key),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # Save encrypted file (IV + ciphertext)
    encrypted_filename = os.path.basename(input_path) + ".enc"
    encrypted_path = os.path.join(output_dir, encrypted_filename)

    with open(encrypted_path, "wb") as f:
        f.write(iv + ciphertext)

    return encrypted_path


# ======================================================
# AES-256-CBC decryption (PQC version)
# ======================================================

def decrypt_file_with_aes_key(
    encrypted_path: str,
    output_dir: str,
    aes_key: bytes,
    original_filename: str
):
    """
    Decrypts AES-256-CBC encrypted file using PROVIDED AES key.
    
    Returns:
        decrypted_file_path
    """

    os.makedirs(output_dir, exist_ok=True)

    # Read encrypted file
    with open(encrypted_path, "rb") as f:
        data = f.read()

    iv = data[:16]
    ciphertext = data[16:]

    # Decrypt
    cipher = Cipher(
        algorithms.AES(aes_key),
        modes.CBC(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    # Unpad
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

    # Save decrypted file
    decrypted_path = os.path.join(output_dir, original_filename)

    with open(decrypted_path, "wb") as f:
        f.write(plaintext)

    return decrypted_path