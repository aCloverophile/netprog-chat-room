# create flask app class
import base64
import secrets

from flask import Flask, request, jsonify
from cryptography.hazmat.primitives import serialization
from database import Database
from hashlib import sha256


class FlaskApp(Flask):

    def __init__(self, name, db: Database):
        super().__init__(name)
        self._init_routes()
        self.db = db

    def _init_routes(self):
        @self.route('/', methods=['GET'])
        def hello_page():
            return 'Chat889'

        @self.route('/api/chat/participants', methods=['GET'])
        def get_chat_participants():
            client_id = request.args.get('client_id')
            chat_name = request.args.get('chat_name')
            if not chat_name:
                return jsonify({'result': 'error', 'error': 'Chat name is required'}), 400
            chat = self.db.getChat(chat_name)
            if not chat:
                return jsonify({'result': 'error', 'error': 'Chat not found'}), 404
            participants = self.db.getParticipantsInfo(chat_name, client_id)
            participants = [{
                'user_id': participant[0],
                'public_key': participant[1]
            } for participant in participants]
            # print(participants)
            return jsonify({'result': 'ok', 'participants': participants})


    def start(self, host, port, debug=False, **options):
        super().run(host, port, debug, **options)

