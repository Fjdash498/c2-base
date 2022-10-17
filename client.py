import socket
import time

IP = "127.0.0.1"
PORT = 4444
SIZE = 2048
FORMAT = "utf-8"

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((IP,PORT))
    print(f"CONNECTED: client connect to server at {IP}:{PORT}")

    connected = True
    while connected:
        #time.sleep(1)
        msg = input("> ")
        if msg == "close":
            client.send(msg.encode(FORMAT))
            connected = False
        elif msg == "status":
            client.send(msg.encode(FORMAT))
            resp = client.recv(SIZE).decode(FORMAT)
            #time.sleep(1)
            print(f"{msg}")
        else:
            client.send(msg.encode(FORMAT))
            msg = client.recv(SIZE).decode(FORMAT)
            print(f"Server send: {msg}.")



if __name__ == "__main__":
    main()
