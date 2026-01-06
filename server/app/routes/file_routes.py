import uuid
from flask import Blueprint, request, jsonify, current_app
from app.services.file_service import save_uploaded_file
from app.services.encryption_service import aes_encrypt_file
from app.extensions import app_state
import os
import requests
import base64
from cryptography.hazmat.primitives import serialization
from app.services.workflow_service import decrypt_file_workflow
from app.services.key_service import load_rsa_private_key
from app.services.workflow_service import encrypt_file_workflow
from app.services.key_service import load_signature_private_key

file_bp = Blueprint("files", __name__)



@file_bp.route("/secureUpload", methods=["POST"])
def secureUpload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    # Save original file
    input_path = save_uploaded_file(
        file,
        current_app.config["UPLOAD_FOLDER"]
    )

    # Encrypt using AES
    encrypted_path, aes_key = aes_encrypt_file(
        input_path,
        current_app.config["ENCRYPTED_FOLDER"]
    )

    return jsonify({
        "message": "File encrypted using AES-256",
        "original_file": input_path,
        "encrypted_file": encrypted_path,
        "aes_key_hex": aes_key.hex()  # TEMP: for Phase-1 testing only
    })

@file_bp.route("/encrypt", methods=["POST"])
def encrypt_file():
    # Sender-only operation
    if app_state.role != "SENDER":
        return jsonify({"error": "Not in sender mode"}), 403
    print("Request files:", request.files)
    print(request.files)
    if "file" not in request.files:
        print("File not found in request")
        return jsonify({"error": "File missing"}), 400

    if app_state.peer_rsa_public_key is None:
        print("Peer RSA public key is None")
        return jsonify({"error": "Receiver public key not available"}), 400

    uploaded_file = request.files["file"]

    # Save original file
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    input_path = os.path.join(upload_dir, uploaded_file.filename)
    uploaded_file.save(input_path)

    # Load sender signature private key
    signature_private_key = load_signature_private_key()

    # Encrypt workflow
    result = encrypt_file_workflow(
        input_path=input_path,
        output_dir=current_app.config["ENCRYPTED_FOLDER"],
        rsa_public_key=app_state.peer_rsa_public_key,
        signing_private_key=signature_private_key
    )

    # Delete original file after encryption
    try:
        os.remove(input_path)
    except Exception as e:
        print(f"Failed to delete original file: {e}")

    # Read encrypted file and send as base64
    with open(result["encrypted_file_path"], 'rb') as f:
        encrypted_file_data = base64.b64encode(f.read()).decode('utf-8')

    return jsonify({
        "message": "File encrypted successfully",
        "encrypted_file": encrypted_file_data,
        "encrypted_file_name": os.path.basename(result["encrypted_file_path"]),
        "aes_key": result["aes_key"].hex(),
        "encrypted_aes_key": result["encrypted_aes_key"].hex(),
        "receiver_public_key": app_state.peer_rsa_public_key.hex() if isinstance(app_state.peer_rsa_public_key, bytes) else str(app_state.peer_rsa_public_key),
        "file_hash": result["file_hash"].hex(),
        "signature": result["signature"].hex(),
        "signature_private_key": signature_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).hex()
    })


@file_bp.route("/send-file", methods=["POST"])
def send_file():
    """
    Sender backend → Receiver backend
    Sends encrypted file + encrypted AES key + signature
    """

    # REQUIRED FIELDS
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    encrypted_file_name = data.get("encrypted_file_name")
    receiver_ip = data.get("receiver_api")
    # receiver_port = data.get("receiver_port", 5050)
    original_filename = data.get("original_filename")

    signature = data.get("signature")
    encrypted_aes_key = data.get("encrypted_aes_key")
   
    if not all([encrypted_file_name, encrypted_aes_key, signature, receiver_ip]):
        return jsonify({"error": "Missing required fields"}), 400

    # FULL PATH TO ENCRYPTED FILE
    encrypted_path = os.path.join(
        current_app.config["ENCRYPTED_FOLDER"],
        encrypted_file_name
    )

    if not os.path.exists(encrypted_path):
        return jsonify({"error": "Encrypted file not found"}), 404

    try:
        with open(encrypted_path, "rb") as f:
            files = {
                "file": (
                    encrypted_file_name,
                    f,
                    "application/octet-stream"
                )
            }

            data = {
                "encrypted_aes_key": encrypted_aes_key,  # already hex
                "signature": signature,                  # already hex
                "original_filename": original_filename
            }

            response = requests.post(
                f"{receiver_ip}/decrypt",
                files=files,
                data=data,
                timeout=15
            )

        # Forward receiver response to sender UI
        if response.status_code != 200:
            return jsonify({
                "error": "Receiver failed to decrypt",
                "receiver_status": response.status_code,
                "receiver_response": response.text
            }), 500

        return jsonify({
            "message": "File sent successfully",
            "receiver_response": response.json()
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Failed to contact receiver",
            "details": str(e)
        }), 500
@file_bp.route("/decrypt", methods=["POST"])
def decrypt_file():

    if "file" not in request.files:
        return jsonify({"error": "Encrypted file missing"}), 400

    encrypted_file = request.files["file"]
    encrypted_aes_key = request.form.get("encrypted_aes_key")
    signature = request.form.get("signature")
    original_filename = request.form.get("original_filename", "received_file.pdf")

    if not encrypted_aes_key or not signature:
        return jsonify({"error": "Missing key or signature"}), 400

    # 🔑 READ RAW ENCRYPTED BYTES (NO BASE64)
    encrypted_file.stream.seek(0)
    encrypted_file_data = encrypted_file.read()

    # Save encrypted file exactly as received
    encrypted_dir = current_app.config["ENCRYPTED_FOLDER"]
    os.makedirs(encrypted_dir, exist_ok=True)
    encrypted_path = os.path.join(
        encrypted_dir, f"encrypted_{uuid.uuid4().hex}.enc"
    )

    with open(encrypted_path, "wb") as f:
        f.write(encrypted_file_data)

    rsa_private_key = load_rsa_private_key()
    sender_signature_public_key = app_state.peer_signature_public_key

    if sender_signature_public_key is None:
        print("key error")
        return jsonify({"error": "Sender public key not available"}), 400

    try: 
        decrypted_path = decrypt_file_workflow(
            encrypted_file_path=encrypted_path,
            encrypted_aes_key=bytes.fromhex(encrypted_aes_key),
            signature=bytes.fromhex(signature),
            rsa_private_key=rsa_private_key,
            signer_public_key=sender_signature_public_key,
            decrypted_output_dir=current_app.config["DECRYPTED_FOLDER"],
            original_filename = original_filename
        )

        os.remove(encrypted_path)

    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 400

    # (Optional UI demo)
    with open(decrypted_path, "rb") as f:
        decrypted_file_data = base64.b64encode(f.read()).decode("utf-8")

    file_size = os.path.getsize(decrypted_path)

    file_id = str(uuid.uuid4())
    app_state.received_files_queue = getattr(
        app_state, "received_files_queue", []
    )

    app_state.received_files_queue.append({
        "id": file_id,
        "filename": original_filename,
        "decrypted_file": decrypted_file_data,
        "file_size": file_size,
        "path": decrypted_path,
        "status": "READY"
    })

    return jsonify({
        "message": "File decrypted and stored",
        "file_id": file_id
    }), 200

@file_bp.route("/next-file", methods=["POST"])
def next_file():
    """Get next file from queue and delete from backend"""
    if app_state.role != "RECEIVER":
        return jsonify({"error": "Not in receiver mode"}), 403

    if not hasattr(app_state, 'received_files_queue') or not app_state.received_files_queue:
        return jsonify({"message": "No files available"}), 204  # No Content

    # Get first file from queue
    file_entry = app_state.received_files_queue.pop(0)
    
    # Delete file from disk
    try:
        if os.path.exists(file_entry["path"]):
            os.remove(file_entry["path"])
    except Exception as e:
        print(f"Failed to delete file from disk: {e}")
    
    # Return entire file data
    return jsonify({
        "id": file_entry["id"],
        "filename": file_entry["filename"],
        "file_data": file_entry["decrypted_file"],
        "file_size": file_entry["file_size"]
    }), 200
