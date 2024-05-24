import socket
import json
import threading

online_users = []

def handle_incoming_messages(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen()
    print(f"Listening for incoming messages on port {port}")

    while True:
        client_socket, addr = server_socket.accept()
        data = client_socket.recv(1024).decode('utf-8')
        message = json.loads(data)
        if isinstance(message, list):
            global online_users
            online_users = message  # 업데이트된 사용자 목록 저장
            print("Updated online users:")
            for user in message:
                print(user)  # 각 사용자 정보를 줄 바꿈 없이 출력
        else:
            print(f"Message from {message['username']}: {message['message']}")
        client_socket.close()

def send_message(target_ip, target_port, message, username):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((target_ip, target_port))
        message_data = json.dumps({'type': 'message', 'username': username, 'message': message})
        client_socket.send(message_data.encode('utf-8'))
        client_socket.close()
    except Exception as e:
        print(f"Failed to send message: {e}")

def connect_to_server(username, server_ip, server_port, client_port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))

    login_data = json.dumps({'type': 'login', 'username': username, 'port': client_port})
    client_socket.send(login_data.encode('utf-8'))

    response = client_socket.recv(1024)
    response_data = json.loads(response.decode('utf-8'))
    if isinstance(response_data, dict) and response_data.get('type') == 'error':
        print(response_data['message'])
        client_socket.close()
        return None
    else:
        client_socket.close()
        return response_data

def send_logout(server_ip, server_port, username):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    logout_data = json.dumps({'type': 'logout', 'username': username})
    client_socket.send(logout_data.encode('utf-8'))
    client_socket.close()

if __name__ == '__main__':
    server_ip = 'localhost'
    server_port = 5000

    while True:
        username = input("Enter your username: ")
        client_port = int(input("Enter your port number: "))

        online_users = connect_to_server(username, server_ip, server_port, client_port)
        if online_users is not None:
            break
        else:
            print("Failed to connect to server with the provided username and port. Please try again.")

    threading.Thread(target=handle_incoming_messages, args=(client_port,)).start()

    while True:
        target_username = input("Enter the username to send a message to (or type 'logout' to quit): ")
        if target_username == 'logout':
            send_logout(server_ip, server_port, username)
            break

        target_user = None
        for user in online_users:
            if user.startswith(target_username):
                target_user = user.strip().split()
                break

        if target_user:
            target_ip = target_user[1]
            target_port = int(target_user[2])
            message = input("Enter your message: ")
            send_message(target_ip, target_port, message, username)
        else:
            print("User not found. Please try again.")

    print("Exiting the client.")
