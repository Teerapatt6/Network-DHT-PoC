import socket
import threading
import json
import sys
import hashlib
import time

HOST = "127.0.0.1"
PORT = int(sys.argv[1])
NODE_ID = int(sys.argv[2])
last_batch_id = None
put_round_num = 1
get_round_num = 1

PORT_RANGE = range(6000, 6010)

data_store = {}
known_nodes = {}
lock = threading.Lock()


def hash_key(key):
    return int(hashlib.sha1(key.encode()).hexdigest(), 16) % 1000


def responsible_node(key_hash):
    with lock:
        ring = sorted(known_nodes.keys())

    if not ring:
        return NODE_ID

    for nid in ring:
        if key_hash <= nid:
            return nid
    return ring[0]


def scan_nodes_once():
    alive = {}

    alive[NODE_ID] = PORT

    for p in PORT_RANGE:
        if p == PORT:
            continue
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            s.connect((HOST, p))
            s.send(json.dumps({"type": "HELLO"}).encode())
            res = json.loads(s.recv(1024).decode())
            alive[res["node_id"]] = p
            s.close()
        except:
            pass

    with lock:
        known_nodes.clear()
        known_nodes.update(alive)


def discover_nodes():
    while True:
        scan_nodes_once()
        time.sleep(2)


def forward(node_id, req):
    with lock:
        port = known_nodes.get(node_id)

    if port is None:
        raise ConnectionError("Node not found")

    key = req.get("key")
    print(f"[Node {NODE_ID}] Forwarded key='{key}' to node {node_id}")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)

    try:
        s.connect((HOST, port))
        s.send(json.dumps(req).encode())
        res = s.recv(4096)
        s.close()
        return res
    except:
        s.close()
        raise


def handle(conn):
    req = json.loads(conn.recv(4096).decode())
    global get_round_num

    if req["type"] == "HELLO":
        conn.send(json.dumps({"node_id": NODE_ID}).encode())
        conn.close()
        return

    if req["type"] == "GET":
        print()
        print(f"===== GET ROUND {get_round_num} =====")
        get_round_num += 1

    key = req["key"]

    if req["type"] == "PUT":
        global last_batch_id
        global put_round_num

        batch_id = req.get("batch_id")

        if batch_id != last_batch_id:
            print()
            print(f"===== PUT ROUND {put_round_num} =====")
            last_batch_id = batch_id
            put_round_num = put_round_num + 1

        scan_nodes_once()

    h = hash_key(key)

    while True:
        owner = responsible_node(h)

        if owner == NODE_ID:
            break

        try:
            res = forward(owner, req)
            conn.send(res)
            conn.close()
            return
        except:
            with lock:
                known_nodes.pop(owner, None)

    if req["type"] == "PUT":
        data_store[key] = req["value"]
        print(f"[Node {NODE_ID}] STORED key='{key}' hash_key='{h}'")
        conn.send(b"STORED")

    elif req["type"] == "GET":
        value = data_store.get(key)
        print(f"[Node {NODE_ID}] GET key='{key}' -> {value}")
        conn.send(json.dumps(value).encode())

    conn.close()


def start():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()

    print(f"[Node {NODE_ID}] Listening on port {PORT}")

    threading.Thread(target=discover_nodes, daemon=True).start()

    while True:
        conn, _ = s.accept()
        threading.Thread(target=handle, args=(conn,)).start()


if __name__ == "__main__":
    try:
        start()
    except KeyboardInterrupt:
        print(f"\n[Node {NODE_ID}] Shutdown")
        sys.exit(0)