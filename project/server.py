import socket
import threading

HOST = '127.0.0.1'
PORT = 1234
active_clients = []  # (username, socket)

def listen_for_messages(client, username):
    while True:
        try:
            message = client.recv(2048).decode('utf-8')
            if message:
                receiver, msg = message.split("~", 1)
                send_to_user(username, receiver, msg)
        except:
            break

def send_to_user(sender, receiver, message):
    for user, conn in active_clients:
        if user == receiver:
            conn.send(f"{sender}~{message}".encode())
            break

def client_handler(client):
    username = client.recv(2048).decode('utf-8')
    active_clients.append((username, client))
    threading.Thread(target=listen_for_messages, args=(client, username)).start()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server running on {HOST}:{PORT}")
    while True:
        client, _ = server.accept()
        threading.Thread(target=client_handler, args=(client,)).start()

if __name__ == '__main__':
    main()