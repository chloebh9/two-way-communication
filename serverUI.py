import socket
import threading
import json

def handle_client(client_socket, addr):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            data = json.loads(data.decode('utf-8'))
            if data['type'] == 'login':
                if not is_unique_login(data['username'], data['port']):
                    client_socket.send(json.dumps({'type': 'error', 'message': 'Username or port already in use'}).encode('utf-8'))
                else:
                    with open('online_users.txt', 'a+') as f:
                        f.write(f"{data['username']} {addr[0]} {data['port']}\n")
                    send_online_users(client_socket)
                    update_online_users()
            elif data['type'] == 'logout':
                handle_logout(data['username'])
                update_online_users()
                break
        except Exception as e:
            print(e)
            break

    client_socket.close()

def is_unique_login(username, port):
    with open('online_users.txt', 'r') as f:
        online_users = f.readlines()
    for user in online_users:
        existing_username, ip, existing_port = user.strip().split()
        if existing_username == username or int(existing_port) == port:
            return False
    return True

def send_online_users(client_socket):
    with open('online_users.txt', 'r') as f:
        online_users = [user.strip() for user in f.readlines()]
    client_socket.sendall(json.dumps(online_users).encode('utf-8'))

def update_online_users():
    with open('online_users.txt', 'r') as f:
        online_users = [user.strip() for user in f.readlines()]
    for user in online_users:
        username, ip, port = user.split()
        try:
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((ip, int(port)))
            target_socket.sendall(json.dumps(online_users).encode('utf-8'))
            target_socket.close()
        except Exception as e:
            print(f"Failed to update user {username}: {e}")

def handle_logout(username):
    try:
        with open('online_users.txt', 'r') as f:
            online_users = f.readlines()
        with open('online_users.txt', 'w') as f:
            for user in online_users:
                if user.split()[0] != username:
                    f.write(user)
    except Exception as e:
        print(f"Failed to handle logout: {e}")

def start_server():
    open('online_users.txt', 'w').close()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 5000))
    server_socket.listen()
    print("Server listening on port 5000")

    while True:
        client_socket, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()

if __name__ == '__main__':
    start_server()