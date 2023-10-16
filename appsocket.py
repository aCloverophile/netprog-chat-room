import enum
import json
import flask
import base64
import asyncio
import hashlib
import secrets
from database import Database
from cryptography.hazmat.primitives import hashes, serialization

MAGIC_BYTES = 4096

def checkKeyValidity(public_key_data):
    try:
        public_key = serialization.load_pem_public_key(public_key_data)
        return True
    except (ValueError, TypeError):
        return False

class AppSocket:
    def __init__(self, host, port, database: Database):
        self.host = host
        self.port = port
        self.database = database

        self.sockets = []
        self.clients = {}

        self.loop = asyncio.get_event_loop()

    async def handle_client(self, reader, writer, client_id):
        data = await reader.read(MAGIC_BYTES)
        client_json = data.decode()

        try:
            client_data = json.loads(client_json)

            if 'operation' in client_data: 
                operation = client_data['operation']

                # if the client wants to register
                if operation == "/register":
                    username = client_data['username']
                    public_key = client_data['public_key']
                    public_key_data = base64.urlsafe_b64decode(public_key + '=' * (4 - len(public_key) % 4))

                    if not username or not public_key:
                        writer.write(json.dumps({
                            'result':'error',
                            'error': 'Username and public key are required!',
                            'operation': '/register'
                        }).encode())
                        await writer.drain()
                        writer.close()
                        await writer.wait_closed()
                        return
                    
                    if self.database.doesUsernameExist(username):
                        writer.write(json.dumps({
                            'result':'error',
                            'error': 'Username already exists!',
                            'operation': '/register'
                        }).encode())
                        await writer.drain()
                        writer.close()
                        await writer.wait_closed()
                        return
                    
                    if not checkKeyValidity(public_key_data):
                        writer.write(json.dumps({
                            'result':'error',
                            'error': 'Invalid public key!',
                            'operation': '/register'
                        }).encode())
                        await writer.drain()
                        writer.close()
                        await writer.wait_closed()
                        return
                    
                    self.database.addUser(username, public_key)
                    self.clients[client_id] = writer
                    user = self.database.getUser(username)
                    writer.write(json.dumps({
                        'result':'ok',
                        'operation': '/register',
                        'username': username,
                        'user_id': client_id
                    }).encode())
                    await writer.drain()

                # if the client wants to login
                elif operation == "/login":
                    if 'username' in client_data:
                        user = self.database.getUser(client_data['username'])

                        if user:
                            self.clients[client_id] = writer
                            writer.write(json.dumps({
                                'result':'ok',
                                'user_id': user[0],
                                'operation': '/login',
                                'username': user[1]
                            }).encode())
                            client_id = user[0]
                            username = user[1]
                            await writer.drain()
                        
                        else:
                            writer.write(json.dumps({
                                'result':'error',
                                'operation': '/login',
                                'error': 'User not found!'
                            }).encode())
                            await writer.drain()
                            writer.close()
                            await writer.wait_closed()
                            return
            
                    else:
                        writer.write(json.dumps({
                            'result':'error',
                            'operation': '/login',
                            'error': 'No username provided!'
                        }).encode())
                        await writer.drain()
                        writer.close()
                        await writer.wait_closed()
                        return
                
                # If the operation is not valid
                else:
                    writer.write(json.dumps({
                        'result':'error',
                        'error': 'Invalid operation!'
                    }).encode())
                    await writer.drain()
                    writer.close()
                    await writer.wait_closed()
                    return

            # If the operation is not provided  
            else: 
                writer.write(json.dumps({
                    'result':'error',
                    'error': 'No operation provided!'
                }).encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                return

        except json.JSONDecodeError:
            writer.write(json.dumps({
                'result':'error',
                'error': 'Invalid JSON!'
            }).encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
        
        except Exception as e:
            print(e)
            writer.close()
            await writer.wait_close()

        self.clients[client_id] = writer

        try:
            data = await reader.read(MAGIC_BYTES)
            client_json = data.decode()
            client_data = json.loads(client_json)

            if 'operation2' in client_data:
                operation2 = client_data['operation2']
                if operation2 == "/create_chat":
                    chat_name = client_data['chat_name']
                    if not chat_name:
                        writer.write(json.dumps({
                            'result':'error',
                            'operation2': '/create_chat',
                            'error': 'Chat name is required!'
                        }).encode())
                        await writer.drain()
                        writer.close()
                        await writer.wait_closed()
                        return
                    else:
                        chat_id = self.database.createChat(chat_name, [client_id])
                        writer.write(json.dumps({
                            'result':'ok',
                            'chat_id': chat_id,
                            'operation2': '/create_chat',
                            'chat_name': chat_name
                        }).encode())
                        await writer.drain()
                    
                elif operation2 == "/join_chat":
                    chat_name = client_data['chat_name']
                    chat = self.database.getChat(chat_name)
                    if not chat:
                        writer.write(json.dumps({
                            'result':'error',
                            'error': 'Chat not found!',
                            'operation2': '/join_chat'
                        }).encode())
                        await writer.drain()
                        writer.close()
                        await writer.wait_closed()
                        return
                    
                    if client_id in chat[2]:
                        writer.write(json.dumps({
                            'result':'error',
                            'error': 'You are already in this chat!',
                            'operation2': '/join_chat'
                        }).encode())
                        await writer.drain()
                        writer.close()
                        await writer.wait_closed()
                        return
                    
                    self.database.addUserToChat(chat_name, client_id)
                    participants = self.database.getParticipantsUsername(chat_name)
                    writer.write(json.dumps({
                        'result':'ok',
                        'operation2': '/join_chat',
                        'participants': participants,
                        'chat_name': chat_name
                    }).encode())
                    await writer.drain()

                else:
                    writer.write(json.dumps({
                        'result':'error',
                        'error': 'Invalid operation!'
                    }).encode())
                    await writer.drain()
                    writer.close()
                    await writer.wait_closed()
                    return
                    
            else:
                writer.write(json.dumps({
                    'result':'error',
                    'error': 'No operation provided!'
                }).encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                return

        except Exception as e:
            print(e)
            writer.close()
            await writer.wait_close()
            return
        

        try:
            while True:
                data = await reader.read(MAGIC_BYTES)
                if not data: break
                client_json = data.decode()
                client_data = json.loads(client_json)

                if 'operation3' in client_data:
                    operation3 = client_data['operation3']

                    if operation3 == '/leave_chat':
                        chat_name = client_data['chat_name']
                        self.database.removeUserFromChat(chat_name, client_id)
                        writer.write(json.dumps({
                            'result':'ok',
                            'operation3': '/leave_chat'
                        }).encode())

                    elif operation3 == '/send_message':
                        # print(client_data)
                        messages = client_data['messages']
                        chat_name = client_data['chat_name']

                        for message1 in messages:
                            message = message1['message']
                            user_id = message1['user_id']
                            # print('before if')
                            if user_id in self.clients:
                                # print('in if')
                                self.clients[user_id].write(json.dumps({
                                    'operation3': '/receive_message',
                                    'result': 'ok',
                                    'from': {
                                        'user_id': client_id,
                                        'username': user[1]
                                    },
                                    'message': message
                                }).encode())
                            else:
                                writer.write(json.dumps({
                                    'result': 'error',
                                    'operation3': '/send_message',
                                    'error': f'User {user_id} not connected'}).encode())
                                await writer.drain()
                                continue

                        writer.write(json.dumps({
                            'result': 'ok',
                            'operation3': '/send_message'
                        }).encode())

                    else:
                        writer.write(json.dumps({
                            'result':'error',
                            'error': 'Invalid operation!'
                        }).encode())
                        await writer.drain()
                        writer.close()
                        await writer.wait_closed()
                        return
                
                else:
                    writer.write(json.dumps({
                        'result':'error',
                        'error': 'No operation provided!'
                    }).encode())
                    await writer.drain()
                    writer.close()
                    await writer.wait_closed()
                    return
                

        except json.JSONDecodeError:
            writer.write(json.dumps({
                'result':'error',
                'error': 'Invalid JSON!'
            }).encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
        
        except Exception as e:
            print(e)
            writer.close()
            await writer.wait_closed()
            return

        finally:
            del self.clients[client_id]
            writer.close()
            await writer.wait_closed()

    async def start(self):
        server = await asyncio.start_server(
            lambda r, w: self.handle_client(r, w, len(self.clients) + 1),
            self.host, self.port)

        async with server:
            await server.serve_forever()





    