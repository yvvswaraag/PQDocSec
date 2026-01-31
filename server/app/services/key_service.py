import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

KEY_DIR = "keys"


def ensure_key_dir():
    os.makedirs(KEY_DIR, exist_ok=True)


# ---------------- RSA (Receiver) ----------------

def generate_rsa_keys():
    ensure_key_dir()

    private_key_path = os.path.join(KEY_DIR, "rsa_private.pem")
    public_key_path = os.path.join(KEY_DIR, "rsa_public.pem")
    #print(public_key_path)
    # if os.path.exists(private_key_path) and os.path.exists(public_key_path):
    #     print("Keys already exist")
    #     return

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    public_key = private_key.public_key()

    with open(private_key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    with open(public_key_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )


def load_rsa_private_key():
    with open(os.path.join(KEY_DIR, "rsa_private.pem"), "rb") as f:
        return serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )


def load_rsa_public_key():
    with open(os.path.join(KEY_DIR, "rsa_public.pem"), "rb") as f:
        return serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )





def generate_signature_keys():
    ensure_key_dir()

    private_key_path = os.path.join(KEY_DIR, "sign_private.pem")
    public_key_path = os.path.join(KEY_DIR, "sign_public.pem")

    # if os.path.exists(private_key_path) and os.path.exists(public_key_path):
    #     return

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    public_key = private_key.public_key()

    with open(private_key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    with open(public_key_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )


def load_signature_private_key():
    with open(os.path.join(KEY_DIR, "sign_private.pem"), "rb") as f:
        return serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )


def load_signature_public_key():
    with open(os.path.join(KEY_DIR, "sign_public.pem"), "rb") as f:
        return serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )
    

