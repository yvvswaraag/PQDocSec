import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

def encrypt_file(input_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    with open(input_path, "rb") as f:
        data = f.read()

    key = os.urandom(32)   # AES-256
    iv = os.urandom(16)

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    output_path = os.path.join(
        output_dir,
        os.path.basename(input_path) + ".enc"
    )

    with open(output_path, "wb") as f:
        f.write(iv + ciphertext)

    return output_path

def aes_encrypt_file(input_path, output_dir):
    """
    Encrypts a file using AES-256-CBC
    Returns: (encrypted_file_path, aes_key, iv)
    """

    # Read file as bytes
    with open(input_path, "rb") as f:
        plaintext = f.read()

    # Generate AES-256 key and IV
    aes_key = os.urandom(32)   # 256-bit key
    iv = os.urandom(16)        # 128-bit IV

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

    # Save encrypted file
    encrypted_filename = os.path.basename(input_path) + ".enc"
    encrypted_path = os.path.join(output_dir, encrypted_filename)

    with open(encrypted_path, "wb") as f:
        # prepend IV for later decryption
        f.write(iv + ciphertext)

    return encrypted_path, aes_key

def aes_decrypt_file(encrypted_path, output_dir, aes_key,original_filename):
    """
    Decrypts AES-encrypted file
    """

    with open(encrypted_path, "rb") as f:
        data = f.read()

    iv = data[:16]
    ciphertext = data[16:]

    cipher = Cipher(
        algorithms.AES(aes_key),
        modes.CBC(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

    decrypted_filename = original_filename
    decrypted_path = os.path.join(output_dir,  decrypted_filename)

    with open(decrypted_path, "wb") as f:
        f.write(plaintext)

    return decrypted_path
