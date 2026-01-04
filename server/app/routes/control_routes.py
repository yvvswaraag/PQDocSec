from flask import Blueprint, request, jsonify, current_app
from app.services.key_service import (
    generate_signature_keys,
    generate_rsa_keys
)
from app.utils.network_utils import get_local_ip, broadcast_receiver, listen_for_receiver
import threading
from app.extensions import app_state

control_bp = Blueprint("control", __name__)

@control_bp.route("/role/select", methods=["POST"])
def select_role():
    role = request.json.get("role").lower()
    print(f"Role selected: {role}")
    if role not in ["sender", "receiver"]:
        return jsonify({"error": "Invalid role"}), 400

    app_state.role = role.upper()

    # Generate keys on demand
    if role == "sender":
        generate_signature_keys()
        print("Generated signature keys for sender")
    elif role == "receiver":
        generate_rsa_keys()
        print("Generated RSA keys for receiver")

    return jsonify({
        "message": f"Role set to {role}"
    })
    
@control_bp.route("/sender/discover", methods=["POST"])
def discover_receiver():
    print(app_state.role , "is the current role")
    if app_state.role != "SENDER":
        return jsonify({"error": "Not in sender mode"}), 403

    ip, port = listen_for_receiver()

    if not ip:
        return jsonify({"error": "No receiver found"}), 404
    print(f"Discovered receiver at {ip}:{port}")
    app_state.receiver_ip = ip
    app_state.receiver_port = port

    return jsonify({
        "message": "Receiver discovered",
        "receiver_ip": ip,
        "receiver_port": port
    })

@control_bp.route("/receiver/start", methods=["POST"])
def start_receiver():
    if app_state.role != "RECEIVER":
        return jsonify({"error": "Not in receiver mode"}), 403

    data = request.get_json() or {}
    name = data.get("name", "Receiver")
    ip = get_local_ip()

    thread = threading.Thread(
        target=broadcast_receiver,
        args=(ip,5050,name),
        daemon=True
    )
    thread.start()

    app_state.discovery_thread = thread

    return jsonify({
        "message": "Receiver broadcasting started",
        "ip": ip,
        "port": 5050
    })
