import os
import psycopg2 as postgresql

class Database:

    def __init__(self):
        self.connection = postgresql.connect(
            host = os.getenv('DB_HOST'),
            port = os.getenv('DB_PORT'),
            database = os.getenv('DB_NAME'),
            user = os.getenv('DB_USER'),
            password = os.getenv('DB_PASSWORD')
        )
        self.cursor = self.connection.cursor()

        self.cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGSERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                public_key TEXT NOT NULL UNIQUE           
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatrooms (
                chat_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
                chat_name VARCHAR(255) NOT NULL UNIQUE,
                participants INTEGER[] NOT NULL,
                state BOOLEAN NOT NULL DEFAULT TRUE
            )
        ''')

        self.connection.commit()

    def addUser(self, username, publicKey):
        self.cursor.execute('''
            INSERT INTO users (username, public_key) VALUES (%s, %s)
        ''', (username, publicKey))
        self.connection.commit()

    def getUser(self, username):
        self.cursor.execute('''
            SELECT * FROM users WHERE username = %s
        ''', (username,))
        return self.cursor.fetchone()
    
    def doesUsernameExist(self, username):
        self.cursor.execute('''
            SELECT * FROM users WHERE username = %s
        ''', (username,))
        if self.cursor.fetchone(): return True
        return False

    def createChat(self, chat_name, participants):
        self.cursor.execute('''
            INSERT INTO chatrooms (chat_name, participants) VALUES (%s, %s) RETURNING chat_id
        ''', (chat_name, participants))
        self.connection.commit()
        # returning chat_id
        return self.cursor.fetchone()[0]
    
    def getChat(self, chat_name):
        self.cursor.execute('''
            SELECT * FROM chatrooms WHERE chat_name = %s
        ''', (chat_name,))
        return self.cursor.fetchone()
    
    def addUserToChat(self, chat_name, user_id):
        self.cursor.execute('''
            UPDATE chatrooms SET participants = array_append(participants, %s) WHERE chat_name = %s
        ''', (user_id, chat_name))
        self.connection.commit()

    def getParticipantsUsername(self, chat_name):
        self.cursor.execute('''
            SELECT participants FROM chatrooms WHERE chat_name = %s
        ''', (chat_name,))
        participants = self.cursor.fetchone()[0]
        usernames = []
        for participant in participants:
            self.cursor.execute('''
                SELECT username FROM users WHERE user_id = %s
            ''', (participant,))
            usernames.append(self.cursor.fetchone()[0])
        return usernames
    
    def removeUserFromChat(self, chat_name, user_id):
        self.cursor.execute('''
            UPDATE chatrooms SET participants = array_remove(participants, %s) WHERE chat_name = %s RETURNING array_length(participants, 1)
        ''', (user_id, chat_name))
        self.connection.commit()
        if self.cursor.fetchone()[0] is None:
            self.cursor.execute('''
                UPDATE chatrooms SET state = FALSE WHERE chat_name = %s
            ''', (chat_name,))
            self.connection.commit()

    def getParticipantsInfo(self, chat_name, user_id):
        self.cursor.execute('''
            SELECT user_id, public_key 
            FROM users 
            WHERE user_id IN (
                    SELECT unnest(participants) 
                    FROM chatrooms 
                    WHERE chat_name = %s AND state = TRUE
                ) AND user_id != %s
        ''', (chat_name, user_id))
        return self.cursor.fetchall()
    
    def __del__(self):
        self.cursor.close()
        self.connection.close()
    

    

