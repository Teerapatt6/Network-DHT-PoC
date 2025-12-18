import socket, json, time

HOST = "127.0.0.1"
PORT = 6000

data = {
    "numbers": [10,20,30],
    "users": ["alice","bob"],
    "files": [10,20],
    "scores": [90,80],
    "temps": [36.5],
    "key54": ["A","B","C"]
}

batch_id = int(time.time())

def send(req):
    s = socket.socket()
    s.connect((HOST, PORT))
    s.send(json.dumps(req).encode())
    s.recv(4096)
    s.close()

for k,v in data.items():
    print(f"PUT {k}")
    send({
        "type": "PUT",
        "key": k,
        "value": v,
        "batch_id": batch_id
    })