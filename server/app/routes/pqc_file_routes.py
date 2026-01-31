import os
import uuid
import base64
import requests
from flask import Blueprint, request, jsonify, current_app
from app.extensions import app_state

# PQC workflow services
from app.services.pqc_workflow_service import (
    pqc_encrypt_file_workflow,
    pqc_decrypt_file_workflow
)

# Key storage helpers (used during handshake elsewhere)
from app.services.pqc_key_service import (
    store_receiver_kyber_public_key,
    store_sender_dilithium_public_key
)

# ------------------------------------------------------
# Blueprint
# ------------------------------------------------------

file_pqc_bp = Blueprint("file_pqc", __name__)


# ======================================================
# SENDER: Encrypt file using PQC
# ======================================================

@file_pqc_bp.route("/pqc/encrypt", methods=["POST"])
def pqc_encrypt_file():

    # if app_state.role != "SENDER":
    #     return jsonify({"error": "Not in sender mode"}), 403

    if "file" not in request.files:
        return jsonify({"error": "File missing"}), 400

    uploaded_file = request.files["file"]

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    input_path = os.path.join(upload_dir, uploaded_file.filename)
    uploaded_file.save(input_path)

    try:
        # Full PQC encryption workflow
        result = pqc_encrypt_file_workflow(input_path)
    except Exception as e:
        print(f"Error during PQC encryption: {e}")
        return jsonify({"error": str(e)}), 500

    # Read encrypted file → base64
    with open(result["encrypted_file_path"], "rb") as f:
        encrypted_b64 = base64.b64encode(f.read()).decode("utf-8")

    return jsonify({
        "message": "File encrypted using PQC",
        "encrypted_file": encrypted_b64,
        "encrypted_file_name": os.path.basename(result["encrypted_file_path"]),
        "kyber_ciphertext": base64.b64encode(
            result["kyber_ciphertext"]
        ).decode("utf-8"),
        "signature": base64.b64encode(
            result["signature"]
        ).decode("utf-8"),
        "original_filename": uploaded_file.filename
    }), 200


# ======================================================
# SENDER → RECEIVER: Send encrypted file
# ======================================================

@file_pqc_bp.route("/pqc/send-file", methods=["POST"])
def pqc_send_file():

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    receiver_api = data.get("receiver_api")
    encrypted_file_name = data.get("encrypted_file_name")
    signature = data.get("signature")
    kyber_ciphertext = data.get("kyber_ciphertext")
    original_filename = data.get("original_filename")

    if not all([
        receiver_api,
        encrypted_file_name,
        signature,
        kyber_ciphertext,
        original_filename
    ]):
        return jsonify({"error": "Missing required fields"}), 400

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

            form_data = {
                "signature": signature,
                "kyber_ciphertext": kyber_ciphertext,
                "original_filename": original_filename
            }

            response = requests.post(
                f"{receiver_api}/pqc/decrypt",
                files=files,
                data=form_data,
                timeout=20
            )

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


# ======================================================
# RECEIVER: Decrypt file using PQC
# ======================================================

@file_pqc_bp.route("/pqc/decrypt", methods=["POST"])
def pqc_decrypt_file():

    # if app_state.role != "RECEIVER":
    #     return jsonify({"error": "Not in receiver mode"}), 403

    if "file" not in request.files:
        return jsonify({"error": "Encrypted file missing"}), 400

    encrypted_file = request.files["file"]
    signature_b64 = request.form.get("signature")
    kyber_ct_b64 = request.form.get("kyber_ciphertext")
    original_filename = request.form.get(
        "original_filename", "received_file"
    )

    if not signature_b64 or not kyber_ct_b64:
        return jsonify({"error": "Missing signature or Kyber ciphertext"}), 400

    # Decode Base64 inputs
    try:
        signature = base64.b64decode(signature_b64)
        kyber_ct = base64.b64decode(kyber_ct_b64)
    except Exception:
        return jsonify({"error": "Invalid Base64 encoding"}), 400

    # Save encrypted file exactly as received
    encrypted_dir = current_app.config["ENCRYPTED_FOLDER"]
    os.makedirs(encrypted_dir, exist_ok=True)

    encrypted_path = os.path.join(
        encrypted_dir,
        f"recv_{uuid.uuid4().hex}.enc"
    )

    with open(encrypted_path, "wb") as f:
        f.write(encrypted_file.read())

    # Store Kyber ciphertext for decapsulation
    kyber_ct_path = os.path.join(
        current_app.config["PQC_KEY_FOLDER"],
        "kyber_ct.bin"
    )

    with open(kyber_ct_path, "wb") as f:
        f.write(kyber_ct)

    try:
        decrypted_path = pqc_decrypt_file_workflow(
            encrypted_file_path=encrypted_path,
            signature=signature,
            original_filename=original_filename
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # Return decrypted file (UI/demo use)
    with open(decrypted_path, "rb") as f:
        decrypted_b64 = base64.b64encode(f.read()).decode("utf-8")

    return jsonify({
        "message": "File decrypted successfully",
        "filename": original_filename,
        "file_data": decrypted_b64
    }), 200