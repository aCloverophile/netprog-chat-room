from threading import Thread

import sys
import appsocket
import dotenv
import config

from database import Database
from http_handler import FlaskApp

host = "localhost"
port = 8000

def start_flask(host, port, db: Database):
    flask_app = FlaskApp(__name__, db)
    flask_app.start(host, port)

if __name__ == '__main__':
    dotenv.load_dotenv()
    db = Database()
    Thread(target=start_flask, args=(host, port, db)).start()
    server = appsocket.AppSocket(config.host, config.port, db)
    try:
        print(f"Server started at {config.host}:{config.port}")
        server.loop.run_until_complete(server.start())
    except KeyboardInterrupt:
        print("Server stopped!")
        sys.exit()