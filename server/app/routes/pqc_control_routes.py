import os
import subprocess
from flask import Blueprint, request, jsonify, current_app
from app.extensions import app_state

pqc_control_bp = Blueprint("pqc_control", __name__)


# ======================================================
# PQC Key Generation Functions
# ======================================================
def generate_dilithium_keys():
    """Generate Dilithium5 key pair (sender's signature keys)"""
    pqc_key_folder = current_app.config["PQC_KEY_FOLDER"]
    os.makedirs(pqc_key_folder, exist_ok=True)

    dilithium_keygen_bin = os.path.join(
        current_app.root_path,
        "services", "PQC", "dilithium", "bin", "dilithium_keygen"
    )

    if not os.path.exists(dilithium_keygen_bin):
        raise FileNotFoundError(f"dilithium_keygen binary not found at {dilithium_keygen_bin}")

    print("Generating Dilithium5 key pair...")
    
    # Your C binary expects "server/pqc_keys/"
    # So we need to run it from the PARENT of server/ directory
    server_dir = os.path.dirname(current_app.root_path)  # This is server/
    project_root = os.path.dirname(server_dir)            # This is PQDocSec/
    
    print(f"Binary location: {dilithium_keygen_bin}")
    print(f"Running from: {project_root}")
    print(f"Keys will be written to: {os.path.join(project_root, 'server', 'pqc_keys')}")
    
    result = subprocess.run(
        [dilithium_keygen_bin],
        cwd=project_root,  # Run from PQDocSec/ so "server/pqc_keys/" works
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, dilithium_keygen_bin)
    
    print("✓ Dilithium5 keys generated successfully")
    
    # Verify keys were created in the right place
    pk_path = os.path.join(pqc_key_folder, "dilithium_pk.bin")
    sk_path = os.path.join(pqc_key_folder, "dilithium_sk.bin")
    
    if not os.path.exists(pk_path):
        raise FileNotFoundError(f"Public key not found at: {pk_path}")
    if not os.path.exists(sk_path):
        raise FileNotFoundError(f"Secret key not found at: {sk_path}")
    
    print(f"✓ Keys verified at: {pqc_key_folder}")


def generate_kyber_keys():
    """Generate Kyber1024 key pair (receiver's encryption keys)"""
    pqc_key_folder = current_app.config["PQC_KEY_FOLDER"]
    os.makedirs(pqc_key_folder, exist_ok=True)

    kyber_keygen_bin = os.path.join(
        current_app.root_path,
        "services", "PQC", "kyber", "bin", "kyber_keygen"
    )

    if not os.path.exists(kyber_keygen_bin):
        raise FileNotFoundError(f"kyber_keygen binary not found at {kyber_keygen_bin}")

    print("Generating Kyber1024 key pair...")
    
    # Same logic - run from parent directory
    server_dir = os.path.dirname(current_app.root_path)
    project_root = os.path.dirname(server_dir)
    
    print(f"Binary location: {kyber_keygen_bin}")
    print(f"Running from: {project_root}")
    
    result = subprocess.run(
        [kyber_keygen_bin],
        cwd=project_root,  # Run from PQDocSec/ so "server/pqc_keys/" works
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, kyber_keygen_bin)
    
    print("✓ Kyber1024 keys generated successfully")
    
    # Verify keys
    pk_path = os.path.join(pqc_key_folder, "kyber_pk.bin")
    sk_path = os.path.join(pqc_key_folder, "kyber_sk.bin")
    
    if not os.path.exists(pk_path):
        raise FileNotFoundError(f"Public key not found at: {pk_path}")
    if not os.path.exists(sk_path):
        raise FileNotFoundError(f"Secret key not found at: {sk_path}")
    
    print(f"✓ Keys verified at: {pqc_key_folder}")


# ======================================================
# Role Selection Endpoint
# ======================================================

@pqc_control_bp.route("/pqc/role/select", methods=["POST"])
def pqc_select_role():
    """
    Set role (SENDER or RECEIVER) and generate appropriate PQC keys
    
    SENDER needs:
    - Dilithium5 key pair (for signing)
    
    RECEIVER needs:
    - Kyber1024 key pair (for key encapsulation)
    """
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    role = data.get("role", "").strip().upper()
    
    if role not in ["SENDER", "RECEIVER"]:
        return jsonify({"error": "Invalid role. Must be 'sender' or 'receiver'"}), 400

    # Set role in app state
    app_state.role = role
    print(f"PQC Role selected: {role}")

    try:
        # Generate keys based on role
        if role == "SENDER":
            generate_dilithium_keys()
            return jsonify({
                "message": "Role set to SENDER",
                "role": "SENDER",
                "keys_generated": "Dilithium5 (signature keys)"
            }), 200
            
        elif role == "RECEIVER":
            generate_kyber_keys()
            return jsonify({
                "message": "Role set to RECEIVER",
                "role": "RECEIVER",
                "keys_generated": "Kyber1024 (encryption keys)"
            }), 200

    except FileNotFoundError as e:
        return jsonify({
            "error": "PQC binary not found",
            "details": str(e),
            "hint": "Make sure PQC binaries are compiled in services/PQC/*/bin/"
        }), 500
        
    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": "Key generation failed",
            "details": str(e),
            "hint": "Check console output for binary error messages"
        }), 500
        
    except Exception as e:
        return jsonify({
            "error": "Unexpected error during key generation",
            "details": str(e)
        }), 500


# ======================================================
# Optional: Get Current Role
# ======================================================

@pqc_control_bp.route("/pqc/role/current", methods=["GET"])
def pqc_get_current_role():
    """Get the currently selected role"""
    if not hasattr(app_state, 'role') or app_state.role is None:
        return jsonify({
            "role": None,
            "message": "No role selected yet"
        }), 200
    
    return jsonify({
        "role": app_state.role
    }), 200


# ======================================================
# Optional: Verify Keys Exist
# ======================================================

@pqc_control_bp.route("/pqc/keys/verify", methods=["GET"])
def pqc_verify_keys():
    """Check which PQC keys are present"""
    pqc_key_folder = current_app.config["PQC_KEY_FOLDER"]
    
    keys_status = {
        "kyber_public_key": os.path.exists(
            os.path.join(pqc_key_folder, "kyber_pk.bin")
        ),
        "kyber_private_key": os.path.exists(
            os.path.join(pqc_key_folder, "kyber_sk.bin")
        ),
        "dilithium_public_key": os.path.exists(
            os.path.join(pqc_key_folder, "dilithium_pk.bin")
        ),
        "dilithium_private_key": os.path.exists(
            os.path.join(pqc_key_folder, "dilithium_sk.bin")
        ),
        "receiver_kyber_public_key": os.path.exists(
            os.path.join(pqc_key_folder, "receiver_kyber_pk.bin")
        ),
        "sender_dilithium_public_key": os.path.exists(
            os.path.join(pqc_key_folder, "sender_dilithium_pk.bin")
        ),
    }
    
    return jsonify({
        "keys": keys_status,
        "pqc_key_folder": pqc_key_folder,
        "all_required_present": (
            (app_state.role == "SENDER" and keys_status["dilithium_public_key"]) or
            (app_state.role == "RECEIVER" and keys_status["kyber_public_key"])
        ) if hasattr(app_state, 'role') else False
    }), 200


# ======================================================
# Optional: Reset Role
# ======================================================

@pqc_control_bp.route("/pqc/role/reset", methods=["POST"])
def pqc_reset_role():
    """Reset the role and optionally clear keys"""
    clear_keys = request.json.get("clear_keys", False) if request.json else False
    
    if hasattr(app_state, 'role'):
        old_role = app_state.role
        app_state.role = None
    else:
        old_role = None
    
    if clear_keys:
        try:
            pqc_key_folder = current_app.config["PQC_KEY_FOLDER"]
            key_files = [
                "kyber_pk.bin",
                "kyber_sk.bin",
                "dilithium_pk.bin",
                "dilithium_sk.bin",
                "receiver_kyber_pk.bin",
                "sender_dilithium_pk.bin",
                "shared_secret_sender.bin",
                "shared_secret_receiver.bin",
                "kyber_ct.bin"
            ]
            
            for key_file in key_files:
                key_path = os.path.join(pqc_key_folder, key_file)
                if os.path.exists(key_path):
                    os.remove(key_path)
                    print(f"Deleted: {key_file}")
            
            return jsonify({
                "message": "Role reset and keys cleared",
                "previous_role": old_role
            }), 200
            
        except Exception as e:
            return jsonify({
                "error": "Failed to clear keys",
                "details": str(e)
            }), 500
    
    return jsonify({
        "message": "Role reset",
        "previous_role": old_role
    }), 200