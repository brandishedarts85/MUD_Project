import socket

HOST = "127.0.0.1"
PORT = 4000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    while True:
        data = s.recv(1024).decode()
        print(data, end="")

        msg = input("> ")
        s.sendall((msg + "\n").encode())

        if msg.lower() == "quit":
            break
