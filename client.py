import socket
import threading
import sys
import argparse
from socket import *


# TODO: Implement a client that connects to your server to chat with other clients here
def main():
    args = parseArgs()
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((args.host,args.port))
    # Send username and password to host  
    userAndPass = args.username + " " + args.passcode + "\n"
    clientSocket.send(userAndPass.encode())
    # Check for server response
    resp = clientSocket.recv(1024)
    resp_text = resp.decode().strip() if resp else ""
    if resp_text == "Incorrect passcode":
        print("Incorrect passcode")
        sys.stdout.flush()
        clientSocket.close()
        return
    if resp_text == "OK":
        print(f"Connected to {args.host} on port {args.port}")
        sys.stdout.flush()

    listener_thread = threading.Thread(target=listen_for_messages, args=(clientSocket,))
    listener_thread.daemon = True
    listener_thread.start()
    
    # Keep connection open and wait for user messages
    while True:
        message = input()
        if message == ":Exit":
            clientSocket.send(b":Exit\n")
            clientSocket.close()
            break
        # Temporary message to server
        clientSocket.send((message + "\n").encode())

def listen_for_messages(clientSocket):
    while True:
        message = clientSocket.recv(1024)
        if not message:
            break
        print(message.decode().strip())
        sys.stdout.flush()

def parseArgs():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('-join', action='store_true')
    p.add_argument('-host', type=str, required=True)
    p.add_argument('-port', type=int, required=True)
    p.add_argument('-username', type=str, required=True)
    p.add_argument('-passcode', type=str, required=True)
    args = p.parse_args()
    if not args.join:
        sys.exit(1)
    if args.host not in ("127.0.0.1", "localhost"):
        sys.exit(1)
    if not (1 <= args.port <= 65535):
        sys.exit(1)
    if len(args.username) > 8:
        sys.exit(1)
    # if not (args.passcode.isalnum() and len(args.passcode) <= 5):
    #     sys.exit(1)
    return args

if __name__ == '__main__':
    main()