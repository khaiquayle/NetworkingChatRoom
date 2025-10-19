import socket
import threading
import sys
import argparse
from datetime import datetime, timedelta
from socket import *

#TODO: Implement all code for your server here

# GLOBAL VARS
client_sockets = list()
client_lock = threading.Lock()

def parseArgs():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('-start', action='store_true')
    p.add_argument('-port', type=int, required=True)
    p.add_argument('-passcode', type=str, required=True)
    args = p.parse_args()
    if (not args.start) or (not (args.passcode.isalnum() and len(args.passcode) <= 5)):
        # either command line input was wrong, or password was invalid
        sys.exit(1)
    return args

def handle_client(connectionSocket, addr, server_passcode):
    global client_sockets
    # Read username and passcode and determine validity
    data = connectionSocket.recv(1024)
    if not data:
        connectionSocket.close()
        return
    line = data.decode().strip()
    parts = line.split(' ', 1)
    username = parts[0] if parts else ""
    client_pass = parts[1] if len(parts) == 2 else ""
    if client_pass != server_passcode:
        # Inform client passcode is incorrect and close
        connectionSocket.send(b"Incorrect passcode\n")
        connectionSocket.close()
        return
    if username:
        output_message = f"{username} joined the chatroom"
        print(output_message)
        sys.stdout.flush()
        # Send success response to client
        connectionSocket.send(b"OK\n")
        with client_lock:
            client_sockets.append((connectionSocket, username)) # add clients to list for broadcasting
        broadcast_message(output_message, connectionSocket)
        
        # Keep connection open and handle messages
        while True:
            data = connectionSocket.recv(1024)
            if not data:
                # if received data is none - client disconnected unexpectedly
                with client_lock:
                    client_sockets = [(s, u) for (s, u) in client_sockets if s != connectionSocket]
                connectionSocket.close()
                break
            message = data.decode().strip()
            if message == ":Exit":
                output_message = f"{username} left the chatroom"
                print(output_message)
                broadcast_message(output_message, connectionSocket)
                sys.stdout.flush()
                with client_lock:
                    # Remove the specific (socket, username) tuple
                    client_sockets = [(s, u) for (s, u) in client_sockets if s != connectionSocket]
                connectionSocket.close()
                break
            elif message == ":)":
                output_message = f"{username}: [feeling happy]"
                print(output_message)
                broadcast_message(output_message, connectionSocket)
                sys.stdout.flush()
            elif message == ":(":
                output_message = f"{username}: [feeling sad]"
                print(output_message)
                broadcast_message(output_message, connectionSocket)
                sys.stdout.flush()
            elif message == ":mytime":
                current_time = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
                output_message = f"{username}: {current_time}"
                print(output_message)
                broadcast_message(output_message, connectionSocket)
                sys.stdout.flush()
            elif message == ":+1hr":
                future_time = (datetime.now() + timedelta(hours=1)).strftime("%a %b %d %H:%M:%S %Y")
                output_message = f"{username}: {future_time}"
                print(output_message)
                broadcast_message(output_message, connectionSocket)
                sys.stdout.flush()
            elif message == ":Users":
                # get list of all connected users
                with client_lock:
                    usernames = [u for (s, u) in client_sockets]
                if usernames:
                    users_list = ", ".join(usernames) # creates a comma separated list
                    output_message = f"Active Users: {users_list}"
                else:
                    output_message = "Active Users: "
                print(f"{username}: searched up active users")
                sys.stdout.flush()
                try:
                    connectionSocket.send(f"{output_message}\n".encode())
                except:
                    pass
            elif message.split(' ')[0] == ":Msg":
                parts = message.split(' ', 2)
                if len(parts) >= 3:
                    target_username, private_message = parts[1], parts[2]
                    private_output = f"[Message from {username}]: {private_message}"
                    print(f"{username}: send message to {target_username}")
                    sys.stdout.flush()
                    
                    with client_lock:
                        for socket, u in client_sockets:
                            if u == target_username:
                                try:
                                    socket.send(f"{private_output}\n".encode())
                                except:
                                    client_sockets.remove((socket, u))
                                break
            else:
                # For now, just print the message
                output_message = f"{username}: {message}"
                print(output_message)
                broadcast_message(output_message, connectionSocket)
                sys.stdout.flush()

def main():
    args = parseArgs()
    serverSocket = socket(AF_INET,SOCK_STREAM)
    serverSocket.bind(('127.0.0.1',args.port))
    serverSocket.listen(10)
    print(f"Server started on port {args.port}. Accepting connections")
    sys.stdout.flush()
    while True:
        connectionSocket, addr = serverSocket.accept()
        # Read username and passcode and determine validity
        data = connectionSocket.recv(1024)
        if not data:
            connectionSocket.close()
            continue
        line = data.decode().strip()
        parts = line.split(' ', 1)
        username = parts[0] if parts else ""
        client_pass = parts[1] if len(parts) == 2 else ""
        if client_pass != args.passcode:
            # Inform client passcode is incorrect and close
            connectionSocket.send(b"Incorrect passcode\n")
            connectionSocket.close()
            continue
        if username:
            print(f"{username} joined the chatroom")
            sys.stdout.flush()
            # Send success response to client
            connectionSocket.send(b"OK\n")
            
            # Keep connection open and handle messages
            while True:
                data = connectionSocket.recv(1024)
                if not data:
                    # if recieved data is none
                    break
                message = data.decode().strip()
                if message == ":Exit":
                    print(f"{username} left the chatroom")
                    sys.stdout.flush()
                    connectionSocket.close()
                    break
                else:
                    # For now, just print the message
                    print(f"{username}: {message}")
                    sys.stdout.flush()

def accept_connections():
    """
    meant to accept concurrent connections to allow for multiple users
    """
    args = parseArgs()
    serverSocket = socket(AF_INET,SOCK_STREAM)
    serverSocket.bind(('127.0.0.1',args.port))
    serverSocket.listen(10)
    print(f"Server started on port {args.port}. Accepting connections")
    sys.stdout.flush()
    while True:
        # waits for a new client to connect
        connectionSocket, addr = serverSocket.accept()

        # start a new thread for new client
        client_thread = threading.Thread(target=handle_client, args=(connectionSocket, addr, args.passcode))
        client_thread.start()
    

def broadcast_message(message, sender):
    """
    sends message to all clients
    removes sockets that have gone bad/disconnected
    without explicity exiting
    """
    with client_lock:
        bad_sockets = []
        for socket, username in client_sockets:
            if socket != sender:
                try:
                    socket.send(f"{message}\n".encode())
                except:
                    bad_sockets.append((socket, username))
        
        for bad_socket in bad_sockets:
            client_sockets.remove(bad_socket)

if __name__ == "__main__":
    accept_connections()