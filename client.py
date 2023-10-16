import json
import enum
import base64
import socket
import requests
import threading 
import key_generator as keygen

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding

MAGIC_BYTES = 4096

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.username = None
        self.public_key = None
        self.client_id = None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    # function to send messages to the server
    def send_messages(self, message):
        self.socket.send(message.encode())

    # function to receive messages from the server
    def receive_messages(self):
        while True:
            data = self.socket.recv(MAGIC_BYTES)
            if not data: break
            server_json = data.decode()
            try:
                server_data = json.loads(server_json)
                if 'username' in server_data:
                    self.username = server_data['username']

                if 'user_id' in server_data:
                    self.client_id = server_data['user_id']
                
                if 'operation' in server_data:
                    if 'result' in server_data:
                        result = server_data['result']
                        if result == 'ok':
                            operation = server_data['operation']
                            if operation == "/register":
                                print("\nRegistration successful!\n")
                                # print(f"DEBUG: {server_data['client_id']}")
                            elif operation == "/login":
                                print("\nLogin successful!\n")
                        else:
                            print(f"Operation failed: {server_data['error']}")
                
                elif 'operation2' in server_data:
                    if 'result' in server_data:
                        result = server_data['result']
                        if result == 'ok':
                            operation2 = server_data['operation2']
                            if operation2 == "/create_chat":
                                chat_name = server_data['chat_name']
                                print("\nChat created successfully!\n")
                            elif operation2 == "/join_chat":
                                participants = server_data['participants']
                                chat_name = server_data['chat_name']
                                print("\nYou have joined the chat!\n")
                                print(f"\nParticipants: {','.join(participants)}\n")
                        else:
                            print(f"Operation failed: {server_data['error']}")

                elif 'operation3' in server_data:
                    print(server_data)
                    if 'result' in server_data:
                        result = server_data['result']
                        if result == 'ok':
                            operation3 = server_data['operation3']
                            if operation3 == "/send_message":
                                print("\nMessage sent successfully!\n")
                            elif operation3 == "/leave_chat":
                                print("\nYou have left the chat!\n")
                            elif operation3 == "/receive_message":
                                # print(1)
                                encrypted_message = base64.urlsafe_b64decode(server_data['message'] + '=' * (4 - len(server_data['message']) % 4))
                                private_key = serialization.load_pem_private_key(
                                    open(f'./{self.username}/private_key.pem', 'rb').read(),
                                    password=None
                                )
                                # print(2)
                                decrypted_message = private_key.decrypt(
                                    encrypted_message,
                                    padding.OAEP(
                                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                        algorithm=hashes.SHA256(),
                                        label=None)
                                )
                                # print(3)
                                print(f'Received message from {server_data["from"]["username"]} (ID {server_data["from"]["user_id"]}): '
                                    f'{decrypted_message.decode()}')


            except Exception as e:
                print(e)
                continue



async def main():
    host = "localhost"
    port = 8888
    client = Client(host, port)

    receiver = threading.Thread(target = client.receive_messages)
    receiver.start()

    
    try:
        print('''
        Welcome to the Chat889 Application!\n
        Created by Elv 💜 and Clover 🍀\n
        For chatting, you just need to follow 
        the instructions. Have fun!\n
        For registration, type: "/register".\n
        For login, type: "/login".\n
        ''')

        operation = input("What do you want to do? ")

        # if the user wants to register
        if operation == "/register":
            username = input("Enter your username: ")
            if username: 
                keygen.key_generator(username)
                with open(f"./{username}/public_key.pem", "rb") as f:
                    if f:
                        public_key = f.read()
                        # print(public_key)
                        public_key = base64.urlsafe_b64encode(public_key).decode()
                        client.send_messages(json.dumps({
                            'operation': '/register',
                            'username': username,
                            'public_key': public_key
                        }))
                    else:
                        print("Error in key generation! Try again please...")
                        exit()
            else: 
                print("Username is required!")
                exit()
            
        # if the user wants to login
        elif operation == "/login":
            username = input("Enter your username: ")
            if username:
                client.send_messages(json.dumps({
                    'operation': '/login',
                    'username': username
                }))
            else:
                print("Username is required!")
                exit()
            
        else:
            print("Invalid operation!")
            exit()
        
    except KeyboardInterrupt:
        print("Exiting...")
        exit()
    
    except Exception as e:
        print(e)
        exit()
    
    
    try:
        print('''
        Would you like to create a new chat room or join an existing one?\n
        For creating a new chat room, type: "/create_chat".\n
        To join a chat, type: "/join_chat".\n
        ''')

        operation2 = input("What do you want to do? ")

        # if the user wants to create a new chat room
        if operation2 == "/create_chat":
            chat_name = input("Enter the chat name: ")
            if chat_name:
                client.send_messages(json.dumps({
                    'operation2': '/create_chat',
                    'chat_name': chat_name
                }))
            else:
                print("Chat name is required!")
                exit()
            
        # if the user wants to join a chat room
        elif operation2 == "/join_chat":
            chat_name = input("Enter the chat name: ")
            if chat_name:
                client.send_messages(json.dumps({
                    'operation2': '/join_chat',
                    'chat_name': chat_name
                }))
            else:
                print("Chat name is required!")
                exit()
            
        else:
            print("Invalid operation!")
            exit()
        
    except KeyboardInterrupt:
        print("Exiting...")
        exit()
    
    except Exception as e:
        print(e)
        exit()
    
    
    try:
        print('''
        Chat889 is ready to use!\n
        If you want to leave the chat, type: "/leave_chat".\n      
        ''')

        while True:
            try:
                message = input(f"[{username}] > ")
                if not message:
                    continue
                if message == "/leave_chat":
                    client.send_messages(json.dumps({
                        'operation3': '/leave_chat',
                        'chat_name': chat_name
                    }))
                    break
                else:
                    response = requests.get(
                        f'http://{host}:8000/api/chat/participants?client_id={client.client_id}&chat_name={chat_name}')
                    response_json = response.json()
                    participants = response_json['participants']
                    # print(participants)
                    encrypted_messages = []
                    for participant in participants:
                        public_key = participant['public_key']
                        public_key_data = base64.urlsafe_b64decode(public_key + '=' * (4 - len(public_key) % 4))
                        public_key = serialization.load_pem_public_key(public_key_data)
                        
                        encrypted_message = public_key.encrypt(
                            message.encode(),
                            padding.OAEP(
                                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                algorithm=hashes.SHA256(),
                                label=None)
                        )

                        encrypted_messages.append({
                            'user_id': participant['user_id'],
                            'message': base64.urlsafe_b64encode(encrypted_message).decode()
                        })
                    # print('chat_name', chat_name)
                    # print('messages', encrypted_messages)
                    client.send_messages(json.dumps({
                        'operation3': '/send_message',
                        'chat_name': chat_name,
                        'messages': encrypted_messages
                    }))
                        
            except KeyboardInterrupt:
                print("Exiting...")
                break       

    except KeyboardInterrupt:
        print("Exiting...")
        receiver.join()
        client.socket.close()
        exit()
    
    except Exception as e:
        print(e)
        exit()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 
    
    

    

            

            
        

