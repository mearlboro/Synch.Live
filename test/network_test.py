import socket

HOST = '192.168.1.101'  # Server address in the local network
PORT = 65432            # Server port

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
s.connect((HOST, PORT))
while True:
    data = s.recv(1024)
    print(data)

