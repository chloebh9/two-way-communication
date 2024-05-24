import socket
import threading
import json

# client 소켓에서 들어오는 데이터를 처리
def handle_client(client_socket, addr):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            data = json.loads(data.decode('utf-8'))
            if data['type'] == 'login': 
                # 아이디, 포트 중복 아닐 때만 받음
                if not is_unique_login(data['username'], data['port']):
                    client_socket.send(json.dumps({'type': 'error', 'message': 'Username or port already in use'}).encode('utf-8'))
                else:
                    with open('online_users.txt', 'a+') as f:
                        f.write(f"{data['username']} {addr[0]} {data['port']}\n")
                    send_online_users(client_socket)  # 새로 로그인한 사용자에게 현재 사용자 목록을 전송
                    update_online_users()  # 모든 사용자에게 업데이트된 사용자 목록을 전송
            elif data['type'] == 'message':
                send_direct_message(data)
            elif data['type'] == 'logout':
                handle_logout(data['username'])
                update_online_users()  # 모든 사용자에게 업데이트된 사용자 목록을 전송
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

# 처음 로그인할 때 현재 온라인 사용자 목록 확인
def send_online_users(client_socket):
    with open('online_users.txt', 'r') as f:
        online_users = [user.strip() for user in f.readlines()]  # 줄 바꿈 문자 제거
    client_socket.sendall(json.dumps(online_users).encode('utf-8'))

# 새로운 사용자가 로그인하거나 기존 사용자가 로그아웃할 때, 전체 사용자에게 업데이트된 온라인 사용자 목록을 보냄
def update_online_users():
    with open('online_users.txt', 'r') as f:
        online_users = [user.strip() for user in f.readlines()]  # 줄 바꿈 문자 제거
    for user in online_users:
        username, ip, port = user.split()
        try:
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((ip, int(port)))
            target_socket.sendall(json.dumps(online_users).encode('utf-8'))
            target_socket.close()
        except Exception as e:
            print(f"Failed to update user {username}: {e}")

def send_direct_message(data):
    try:
        with open('online_users.txt', 'r') as f:
            online_users = f.readlines()
        for user in online_users:
            username, ip, port = user.strip().split()
            if username == data['target']:
                target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target_socket.connect((ip, int(port)))
                target_socket.sendall(json.dumps(data).encode('utf-8'))
                target_socket.close()
                break
    except Exception as e:
        print(f"Failed to send message: {e}")

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
    # online_users.txt 내용 초기화
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
