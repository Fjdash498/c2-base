import socket
import threading
import time
#from flask import *
import datetime

#dynamically gets system IP.
#IP = socket.gethostbyname(socket.gethostname())
IP = "127.0.0.1"
PORT = 4444
SIZE = 2048
FORMAT = "utf-8"


class Server:
    threads = []
    clients = []

    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.bind((ip,port))
        self.sock.listen()
        print("[+] Server has Initialized")

    def set_thread(self,thread):
        #self.thread = thread
        self.threads.append(thread)

    #def remove_thread(self,thread):
        #self.threads.remove(thread)

    def find_thread(self, id):
        for x in self.threads:
            if x.name == id:
                return x

    def remove_client(self,thread,client):
        for t in self.threads:
            if t.name == thread.name:
                self.threads.remove(thread)
        #self.threads.remove(thread)
        self.clients.remove(client)

    def add_client(self,client):
        #self.threads.append(thread)
        self.clients.append(client)

class Connection:
    def __init__(self, socket, rAddr, id):
        self.socket = socket
        self.rAddr = rAddr
        self.id = str(id)
        self.frm_client = ""
        #self.to_send = ""

    #do our best to kill the socket any way we can if need be.
    def __del__(self):
        #self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
    #Can / should we define a client countdown in here?
    #perhaps using threading?
    def set_thread(self,thread):
        self.thread = thread

    def close_socket(self):
        print(f"[-] Cliend ID: {self.id} will now disconnect")
        #Send FIN / EOF to client, then close socket.
        #self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        #not sure if this is needed. Goal is to kill the thread too.
        #exit()

    def send(self, msg):
        try:
            self.socket.send(msg.encode("utf-8"))
        except ConnectionResetError as connReset:
            print(f"client init shutdown, closing.")
            self.close_socket()

    def recv(self, size):
        try:
            self.frm_client = self.socket.recv(size).decode("utf-8")
            return self.frm_client
        except ConnectionResetError as connReset:
            print(f"client init shutdown, closing.")
            self.close_socket()

#this function gets ran by every connection.
def handle_client(client,server):
    print(f"New client connected: {client.rAddr}")
    #TODO: include a counter to kill the connection
    # after N seconds of nothing. (HeartBeat?)
    #           #           #               #
    #starts a loop to handle the client's state:
    #connected = True
    while client.frm_client != "close":
        try:
        #basic echo server
            #print(f"received: {client.frm_client}")
            if client.frm_client == 'status':
                msg = f"{server.threads}\n{server.clients}"
                #when sending to client, must be inside a variable
                #does not accept strings
                #client.send(msg)
                print(msg)
                client.frm_client = ""
            else:
                msg = client.recv(1024)
                print(f"[{client.rAddr}]: {msg}")
                msg = f"Msg recieved: {msg}"
                client.send(msg)
                #client.frm_client = ""
        except ConnectionResetError as connReset:
            print(f"client {c.id} init shutdown, closing")
            for c in server.clients:
                if c.id == threading.current_thread().name:
                    t = server.find_thread(c.id)
                    server.remove_client(t,c)
        except BrokenPipeError as brkPipe:
            print(f"client {client.id} has disconnected")
            for c in server.clients:
                if c.id == threading.current_thread().name:
                    t = server.find_thread(c.id)
                    server.remove_client(t,c)
            client.frm_lient = "close"
        except OSError as oserror:
            print(f"client {client.id} has disconnected")
            for c in server.clients:
                if c.id == threading.current_thread().name:
                    t = server.find_thread(c.id)
                    server.remove_client(t,c)
            client.frm_client = "close"

    #Close out the connection, remove thread from list, and die.
    print(f"[-] Client {client.rAddr}:{client.id} has disconnected.")
    server.remove_client(threading.current_thread(), client)
    client.close_socket()
    exit()


def main():
    print("[+] Starting Server")
    s = Server(IP,PORT)
    id=1
    while True:
        try:
            sock_obj, addr = s.sock.accept()
            print(s.threads)
            print(s.clients)
            c = Connection(sock_obj, addr, id)
            #needs - 1.
            #thread = threading.Thread(name=id,target=handle_client, args=[c])
            thread = threading.Thread(name=id,target=handle_client, args=(c,s))

            thread.start()
            c.set_thread(thread)
            s.add_client(c)
            s.set_thread(thread)
            id += 1
            print(f"Active Connections: {threading.active_count() - 1}")

            #Need to include function to clean stale / closed
            #threads out of acitve_threads
            #for t in s.threads:
                #if t.is_alive() == False:
                #    s.find_thread(id)
                    #s.remove_thread(t)
            #shouldn't need above anymore, however will keep for now
        except KeyboardInterrupt:
            print(f"{datetime.datetime.now()} CAUGHT EXCEPTION, EXITING...")
            for x in s.clients:
                x.close_socket()
                del x
            s.threads.clear()
            print("!!!THREADS KILLED!!!")
            s.clients.clear()
            print("CLEANUP COMPLETE, GOODBYE..")

            exit()

if __name__ == "__main__":
    main()
