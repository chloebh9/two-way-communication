import socket
import json
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox

online_users = []
sessions = {}

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat Client")
        self.master.geometry("700x400")
        self.username = None
        self.client_port = None
        self.server_ip = 'localhost'
        self.server_port = 5000
        self.session_id = None

        self.login_frame = tk.Frame(master)
        self.chat_frame = tk.Frame(master)

        self.create_login_frame()
        self.create_chat_frame()

    def create_login_frame(self):
        self.login_frame.pack(pady=20)

        tk.Label(self.login_frame, text="Username:", font=("Helvetica", 20)).pack(padx=5, pady=7)
        self.username_entry = tk.Entry(self.login_frame, width=30, font=("Helvetica", 20))
        self.username_entry.pack(padx=5, pady=10)

        tk.Label(self.login_frame, text="Port:", font=("Helvetica", 20)).pack(padx=5, pady=7)
        self.port_entry = tk.Entry(self.login_frame, width=30, font=("Helvetica", 20))
        self.port_entry.pack(padx=5, pady=20)

        tk.Button(self.login_frame, text="Login", font=("Helvetica", 20), command=self.login, height=2, width=16).pack(pady=50)

    def create_chat_frame(self):
        self.chat_frame.pack_forget()

        self.online_users_listbox = tk.Listbox(self.chat_frame, width=18, height=20, font=("Helvetica", 12))
        self.online_users_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=30)

        self.messages_text = tk.Text(self.chat_frame, state=tk.DISABLED, width=30, height=20, font=("Helvetica", 12))
        self.messages_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=30)

        self.message_entry = tk.Entry(self.chat_frame, width=14, font=("Helvetica", 12))
        self.message_entry.pack(side=tk.BOTTOM, fill=tk.X, expand=True, padx=2, pady=10)

        tk.Button(self.chat_frame, text="Send", command=self.send_message, width=8, height=2,
                  font=("Helvetica", 12)).pack(side=tk.BOTTOM, padx=2, pady=20, fill=tk.Y)
        tk.Button(self.chat_frame, text="Invite", command=self.invite_user, width=8, height=2,
                  font=("Helvetica", 12)).pack(side=tk.BOTTOM, padx=2, pady=20, fill=tk.Y)
        tk.Button(self.chat_frame, text="End Session", command=self.end_session, width=8, height=2,
                  font=("Helvetica", 12)).pack(side=tk.BOTTOM, padx=2, pady=20, fill=tk.Y)
        tk.Button(self.chat_frame, text="Logout", command=self.logout, width=8, height=2, font=("Helvetica", 12)).pack(
            side=tk.BOTTOM, padx=2, pady=20, fill=tk.Y)

    def login(self):
        self.username = self.username_entry.get()
        self.client_port = int(self.port_entry.get())

        online_users_list = connect_to_server(self.username, self.server_ip, self.server_port, self.client_port)
        if online_users_list is not None:
            self.login_frame.pack_forget()
            self.chat_frame.pack()
            self.master.geometry("600x480")
            threading.Thread(target=handle_incoming_messages, args=(self.client_port, self)).start()
            self.update_online_users(online_users_list)
        else:
            messagebox.showerror("Login Failed", "The username or port number you entered already exists.")

    def update_online_users(self, users):
        global online_users
        online_users = users
        self.online_users_listbox.delete(0, tk.END)
        for user in users:
            self.online_users_listbox.insert(tk.END, user)

    def append_message(self, message):
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.insert(tk.END, message + "\n")
        self.messages_text.config(state=tk.DISABLED)

    def send_message(self):
        message = self.message_entry.get()
        if self.session_id:
            self.append_message(f"Me: {message}")
            notice_message(self.session_id, message, self.username)
            self.message_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "You are not in a session")

    def invite_user(self):
        target_username = simpledialog.askstring("Invite User", "Enter the username to invite")
        if target_username not in [user.split()[0] for user in online_users]:
            messagebox.showerror("Error", "The username does not exist.")
            return

        if not self.session_id:
            self.session_id = simpledialog.askstring("Session name", "Enter the session name")
            if self.session_id not in sessions:
                sessions[self.session_id] = []
            sessions[self.session_id].append(self.username)
        if target_username not in sessions[self.session_id]:
            sessions[self.session_id].append(target_username)
        notice_invite(self.username, target_username, self.session_id)
        notice_session_update(self.session_id)

    def end_session(self):
        if self.session_id:
            notice_end_session(self.session_id, self.username)
            self.session_id = None
            self.append_message("Session ended")
        else:
            messagebox.showerror("Error", "You are not in a session")

    def logout(self):
        send_logout(self.server_ip, self.server_port, self.username)
        self.chat_frame.pack_forget()
        self.login_frame.pack()

def handle_incoming_messages(port, client):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen()

    while True:
        client_socket, addr = server_socket.accept()
        data = client_socket.recv(1024).decode('utf-8')
        message = json.loads(data)
        if isinstance(message, list):
            client.update_online_users(message)
        else:
            if message['type'] == 'invite':
                session_id = message['session_id']
                from_user = message['from']
                target = message['target']
                if session_id not in sessions:
                    sessions[session_id] = []
                if from_user not in sessions[session_id]:
                    sessions[session_id].append(from_user)
                if target not in sessions[session_id]:
                    sessions[session_id].append(target)
                client.session_id = session_id
                client.append_message(f"Invited from {from_user} for session {session_id}")
            elif message['type'] == 'end_session':
                session_id = message['session_id']
                if session_id in sessions:
                    del sessions[session_id]
                client.session_id = None
                client.append_message(f"Session {session_id} has ended")
            elif message['type'] == 'message':
                if message['username'] != client.username:
                    client.append_message(f"{message['username']}: {message['message']}")
            elif message['type'] == 'session_update':
                session_id = message['session_id']
                updated_session = message['session']
                sessions[session_id] = updated_session
                client.append_message(f"Session updated: {', '.join(updated_session)}")
        client_socket.close()

def notice_message(session_id, message, username):
    if session_id in sessions:
        for participant in sessions[session_id]:
            target_user = next((user for user in online_users if user.startswith(participant)), None)
            if target_user:
                ip, port = target_user.split()[1:]
                try:
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect((ip, int(port)))
                    message_data = json.dumps({'type': 'message', 'username': username, 'message': message})
                    client_socket.send(message_data.encode('utf-8'))
                    client_socket.close()
                except Exception as e:
                    print(f"Failed to send message to {participant}: {e}")
    else:
        print(f"You are not in session {session_id}")

def notice_invite(username, target_username, session_id):
    if session_id in sessions:
        if target_username not in sessions[session_id]:
            sessions[session_id].append(target_username)
        for participant in sessions[session_id]:
            target_user = next((user for user in online_users if user.startswith(participant)), None)
            if target_user:
                ip, port = target_user.split()[1:]
                try:
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect((ip, int(port)))
                    invite_data = json.dumps({
                        'type': 'invite',
                        'from': username,
                        'session_id': session_id,
                        'target': target_username
                    })
                    client_socket.send(invite_data.encode('utf-8'))
                    client_socket.close()
                except Exception as e:
                    print(f"Failed to send invite to {participant}: {e}")

def notice_session_update(session_id):
    if session_id in sessions:
        session = sessions[session_id]
        for participant in session:
            target_user = next((user for user in online_users if user.startswith(participant)), None)
            if target_user:
                ip, port = target_user.split()[1:]
                try:
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect((ip, int(port)))
                    session_update_data = json.dumps({
                        'type': 'session_update',
                        'session_id': session_id,
                        'session': session
                    })
                    client_socket.send(session_update_data.encode('utf-8'))
                    client_socket.close()
                except Exception as e:
                    print(f"Failed to send session update to {participant}: {e}")

def notice_end_session(session_id, username):
    if session_id in sessions:
        participants = sessions[session_id]
        for participant in participants:
            target_user = next((user for user in online_users if user.startswith(participant)), None)
            if target_user:
                ip, port = target_user.split()[1:]
                try:
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect((ip, int(port)))
                    end_data = json.dumps({
                        'type': 'end_session',
                        'session_id': session_id
                    })
                    client_socket.send(end_data.encode('utf-8'))
                    client_socket.close()
                except Exception as e:
                    print(f"Failed to end session for {participant}: {e}")
        del sessions[session_id]

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
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()