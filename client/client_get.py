import socket, json

HOST = "127.0.0.1"
PORT = 6000

def send(req):
    s = socket.socket()
    s.connect((HOST, PORT))
    s.send(json.dumps(req).encode())
    res = s.recv(4096)
    s.close()
    return res

while True:
    key = input("\nGET key (or exit): ")
    if key == "exit":
        break
    res = json.loads(send({
            "type":"GET",
            "key":key
        }).decode())
    print("Result:", res)