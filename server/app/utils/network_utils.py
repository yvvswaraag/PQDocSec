import socket
import json
import time

DISCOVERY_PORT = 9999
BROADCAST_ADDR = "255.255.255.255"


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def broadcast_receiver(ip, port=5050,name="Reciver", interval=3):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    payload = {
        "type": "RECEIVER_AVAILABLE",
        "name": name,
        "ip": ip,
        "port": port
    }

    while True:
        sock.sendto(
            json.dumps(payload).encode(),
            (BROADCAST_ADDR, DISCOVERY_PORT)
        )
        time.sleep(interval)


def listen_for_receiver(timeout=10):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", DISCOVERY_PORT))
    sock.settimeout(timeout)

    try:
        data, _ = sock.recvfrom(4096)
        message = json.loads(data.decode())

        if message.get("type") == "RECEIVER_AVAILABLE":
            return message["ip"], message["port"], message["name"]

    except socket.timeout:
        return None, None, None
    finally:
        sock.close()
    return None, None, None