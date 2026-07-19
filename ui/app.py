import os

import requests
from flask import Flask, jsonify, request, send_from_directory

NGROK_API = "http://ngrok-minecraft:4041/api/tunnels"
TARGET_HOST = os.environ.get("MC_HOST", "big-bear-crafty")
CRAFTY_BASE = os.environ.get("CRAFTY_BASE_URL", "https://big-bear-crafty:8443/api/v2")
CRAFTY_TOKEN = os.environ["CRAFTY_API_TOKEN"]
TUNNEL_NAME = "mc-active"

app = Flask(__name__)


def crafty(method, path, **kw):
    r = requests.request(
        method,
        f"{CRAFTY_BASE}{path}",
        headers={"Authorization": f"Bearer {CRAFTY_TOKEN}"},
        verify=False,  # self-signed cert, same as nginx.conf's proxy_ssl_verify off
        timeout=10,
        **kw,
    )
    r.raise_for_status()
    return r.json()["data"]


@app.get("/")
def index():
    return send_from_directory(os.path.dirname(__file__), "index.html")


def active_tunnel():
    r = requests.get(NGROK_API, timeout=5)
    r.raise_for_status()
    for t in r.json().get("tunnels", []):
        if t["proto"] == "tcp":
            return t
    return None


@app.get("/api/servers")
def servers():
    # ponytail: field names (server_id/id, server_name/name, server_port/port, running)
    # are unconfirmed against a live Crafty instance - adjust the .get() fallbacks below
    # once you see the real payload shape.
    raw = crafty("GET", "/servers")
    out = []
    for s in raw:
        out.append({
            "id": s.get("server_id") or s.get("id"),
            "name": s.get("server_name") or s.get("name"),
            "port": s.get("server_port") or s.get("port"),
            "running": bool(s.get("running")),
        })
    return jsonify(out)


@app.get("/api/status")
def status():
    t = active_tunnel()
    if not t:
        return jsonify({"connected": None, "address": None})
    return jsonify({"connected": t["config"]["addr"], "address": t["public_url"].replace("tcp://", "")})


@app.post("/api/servers/<server_id>/<action>")
def server_action(server_id, action):
    if action not in ("start_server", "stop_server"):
        return jsonify({"error": "unsupported action"}), 400
    crafty("POST", f"/servers/{server_id}/action/{action}")
    return jsonify({"ok": True})


@app.post("/api/connect")
def connect():
    port = request.json["port"]

    # ponytail: free ngrok allows one tcp tunnel; tear down before swapping
    existing = active_tunnel()
    if existing:
        requests.delete(f"{NGROK_API}/{existing['name']}", timeout=5)

    r = requests.post(
        NGROK_API,
        json={"name": TUNNEL_NAME, "proto": "tcp", "addr": f"{TARGET_HOST}:{port}"},
        timeout=10,
    )
    r.raise_for_status()
    return jsonify({"address": r.json()["public_url"].replace("tcp://", "")})


@app.post("/api/disconnect")
def disconnect():
    existing = active_tunnel()
    if existing:
        requests.delete(f"{NGROK_API}/{existing['name']}", timeout=5)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
