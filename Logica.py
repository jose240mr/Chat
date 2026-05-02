"""
💬 Chat en Tiempo Real - Python Backend
========================================
Ejecuta: python chat_server.py
Puerto: 8080
URL: http://localhost:8080

Características:
- Chat en tiempo real
- Contador de usuarios conectados
- Nombres de usuario personalizados
- Historial de mensajes
- Sin dependencias externas
"""

import http.server
import json
import time
import threading
import urllib.parse
from datetime import datetime
from collections import defaultdict

class ChatServer(http.server.BaseHTTPRequestHandler):
    """Servidor de Chat con Polling"""
    
    # Almacenamiento compartido entre todos los clientes
    messages = []  # Historial de mensajes
    users = {}     # Usuarios conectados {id: {name, last_seen}}
    max_messages = 100  # Máximo de mensajes en memoria
    
    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(200)
        self._send_cors()
        self.end_headers()
    
    def do_GET(self):
        """Manejar GET"""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        
        if path == '/':
            self._serve_html()
        elif path == '/messages':
            self._get_messages(params)
        elif path == '/users':
            self._get_users()
        elif path == '/ping':
            self._ping_user(params)
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Manejar POST - Enviar mensaje"""
        if self.path == '/send':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body)
                self._add_message(data)
                self._send_json({'status': 'ok'})
            except:
                self.send_error(400)
        else:
            self.send_error(404)
    
    def _serve_html(self):
        """Sirve la interfaz del chat"""
        html = self._get_html()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def _get_messages(self, params):
        """Retorna mensajes nuevos"""
        last_id = int(params.get('last_id', [0])[0])
        
        # Filtrar mensajes nuevos
        new_messages = [msg for msg in self.messages if msg['id'] > last_id]
        
        self._send_json({
            'messages': new_messages,
            'count': len(new_messages)
        })
    
    def _get_users(self):
        """Retorna usuarios conectados"""
        # Limpiar usuarios inactivos (más de 30 segundos)
        current_time = time.time()
        active_users = {
            uid: user for uid, user in self.users.items()
            if current_time - user['last_seen'] < 30
        }
        self.users = active_users
        
        self._send_json({
            'users': list(active_users.values()),
            'count': len(active_users)
        })
    
    def _ping_user(self, params):
        """Mantener usuario activo"""
        user_id = params.get('id', ['unknown'])[0]
        user_name = params.get('name', ['Anónimo'])[0]
        
        self.users[user_id] = {
            'id': user_id,
            'name': user_name,
            'last_seen': time.time()
        }
        
        self._send_json({'status': 'ok', 'users': len(self.users)})
    
    def _add_message(self, data):
        """Añade un mensaje al historial"""
        message = {
            'id': len(self.messages) + 1,
            'user': data.get('user', 'Anónimo'),
            'text': data.get('text', ''),
            'color': data.get('color', '#667eea'),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        
        self.messages.append(message)
        
        # Limitar historial
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def _send_json(self, data, status=200):
        """Envía respuesta JSON"""
        self.send_response(status)
        self._send_cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_cors(self):
        """Headers CORS"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-cache')
    
    def _get_html(self):
        """HTML del chat"""
        return '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>💬 Chat en Vivo - Python</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chat-container {
            width: 100%;
            max-width: 800px;
            height: 90vh;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 25px 45px rgba(0, 0, 0, 0.3);
        }
        
        .chat-header {
            padding: 20px 30px;
            background: rgba(0, 0, 0, 0.3);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-header h1 {
            font-size: 1.5em;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .online-counter {
            background: rgba(0, 184, 148, 0.2);
            border: 1px solid rgba(0, 184, 148, 0.3);
            padding: 8px 15px;
            border-radius: 20px;
            color: #00b894;
            font-size: 0.9em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .online-dot {
            width: 8px;
            height: 8px;
            background: #00b894;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        
        .user-setup {
            padding: 20px 30px;
            background: rgba(0, 0, 0, 0.2);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .user-setup input {
            flex: 1;
            padding: 10px 15px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            color: #e0e0e0;
            font-size: 0.9em;
        }
        
        .user-setup input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .color-picker {
            width: 40px;
            height: 40px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            background: #667eea;
        }
        
        .messages-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px 30px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .message {
            display: flex;
            gap: 10px;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message-avatar {
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.8em;
            flex-shrink: 0;
        }
        
        .message-content {
            flex: 1;
        }
        
        .message-header {
            display: flex;
            gap: 10px;
            align-items: baseline;
            margin-bottom: 5px;
        }
        
        .message-user {
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .message-time {
            font-size: 0.7em;
            color: #a0a0b0;
        }
        
        .message-text {
            color: #e0e0e0;
            font-size: 0.95em;
            line-height: 1.4;
            word-break: break-word;
        }
        
        .input-area {
            padding: 20px 30px;
            background: rgba(0, 0, 0, 0.3);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            gap: 10px;
        }
        
        .input-area input {
            flex: 1;
            padding: 15px 20px;
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 25px;
            color: #e0e0e0;
            font-size: 1em;
            transition: all 0.3s;
        }
        
        .input-area input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 15px rgba(102, 126, 234, 0.3);
        }
        
        .send-btn {
            padding: 15px 25px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .send-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .empty-chat {
            text-align: center;
            color: #a0a0b0;
            padding: 40px;
        }
        
        .empty-chat .icon {
            font-size: 3em;
            margin-bottom: 10px;
        }
        
        /* Scrollbar personalizado */
        .messages-area::-webkit-scrollbar {
            width: 6px;
        }
        
        .messages-area::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.1);
        }
        
        .messages-area::-webkit-scrollbar-thumb {
            background: rgba(102, 126, 234, 0.3);
            border-radius: 3px;
        }
        
        @media (max-width: 600px) {
            .chat-container {
                height: 100vh;
                border-radius: 0;
            }
            .user-setup {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>💬 Chat en Vivo</h1>
            <div class="online-counter">
                <div class="online-dot"></div>
                <span id="online-count">0</span> en línea
            </div>
        </div>
        
        <div class="user-setup">
            <input 
                type="text" 
                id="username-input" 
                placeholder="Tu nombre..." 
                maxlength="20"
                value="Usuario"
            >
            <input 
                type="color" 
                id="color-picker" 
                class="color-picker" 
                value="#667eea"
                title="Color de tu nombre"
            >
        </div>
        
        <div class="messages-area" id="messages-area">
            <div class="empty-chat">
                <div class="icon">👋</div>
                <p>¡Sé el primero en escribir!</p>
            </div>
        </div>
        
        <div class="input-area">
            <input 
                type="text" 
                id="message-input" 
                placeholder="Escribe un mensaje..." 
                maxlength="500"
            >
            <button class="send-btn" onclick="sendMessage()">Enviar</button>
        </div>
    </div>

    <script>
        // Configuración
        const API = window.location.origin;
        const USER_ID = 'user_' + Math.random().toString(36).substr(2, 9);
        let lastMessageId = 0;
        let username = 'Usuario';
        let userColor = '#667eea';
        
        // Elementos DOM
        const messagesArea = document.getElementById('messages-area');
        const messageInput = document.getElementById('message-input');
        const usernameInput = document.getElementById('username-input');
        const colorPicker = document.getElementById('color-picker');
        const onlineCount = document.getElementById('online-count');
        
        // Inicializar
        function init() {
            username = localStorage.getItem('chat_username') || 'Usuario';
            userColor = localStorage.getItem('chat_color') || '#667eea';
            
            usernameInput.value = username;
            colorPicker.value = userColor;
            
            // Eventos
            usernameInput.addEventListener('change', updateUserInfo);
            colorPicker.addEventListener('change', updateUserInfo);
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });
            
            // Iniciar polling
            loadMessages();
            pingServer();
            countUsers();
            
            // Intervalos
            setInterval(loadMessages, 1000);  // Cargar mensajes cada segundo
            setInterval(pingServer, 10000);   // Ping cada 10 segundos
            setInterval(countUsers, 5000);    // Contar usuarios cada 5 segundos
        }
        
        function updateUserInfo() {
            username = usernameInput.value || 'Anónimo';
            userColor = colorPicker.value;
            
            localStorage.setItem('chat_username', username);
            localStorage.setItem('chat_color', userColor);
        }
        
        async function pingServer() {
            try {
                await fetch(`${API}/ping?id=${USER_ID}&name=${encodeURIComponent(username)}`);
            } catch (e) {
                console.log('Ping error:', e);
            }
        }
        
        async function countUsers() {
            try {
                const response = await fetch(`${API}/users`);
                const data = await response.json();
                onlineCount.textContent = data.count || 0;
            } catch (e) {
                onlineCount.textContent = '?';
            }
        }
        
        async function loadMessages() {
            try {
                const response = await fetch(`${API}/messages?last_id=${lastMessageId}`);
                const data = await response.json();
                
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(msg => {
                        addMessageToChat(msg);
                        lastMessageId = Math.max(lastMessageId, msg.id);
                    });
                    
                    // Scroll al final
                    messagesArea.scrollTop = messagesArea.scrollHeight;
                }
            } catch (e) {
                console.log('Load error:', e);
            }
        }
        
        async function sendMessage() {
            const text = messageInput.value.trim();
            if (!text) return;
            
            updateUserInfo();
            
            try {
                await fetch(`${API}/send`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user: username,
                        text: text,
                        color: userColor
                    })
                });
                
                messageInput.value = '';
                messageInput.focus();
                
                // Cargar inmediatamente
                loadMessages();
                
            } catch (e) {
                alert('Error al enviar mensaje');
            }
        }
        
        function addMessageToChat(msg) {
            // Eliminar mensaje de "vacío" si existe
            const emptyMsg = messagesArea.querySelector('.empty-chat');
            if (emptyMsg) emptyMsg.remove();
            
            // Crear elemento de mensaje
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message';
            
            const initial = (msg.user || 'A')[0].toUpperCase();
            const color = msg.color || '#667eea';
            
            msgDiv.innerHTML = `
                <div class="message-avatar" style="background: ${color}20; color: ${color}; border: 2px solid ${color}40;">
                    ${initial}
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-user" style="color: ${color};">${escapeHtml(msg.user)}</span>
                        <span class="message-time">${msg.timestamp || ''}</span>
                    </div>
                    <div class="message-text">${escapeHtml(msg.text)}</div>
                </div>
            `;
            
            messagesArea.appendChild(msgDiv);
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Iniciar
        init();
    </script>
</body>
</html>
'''
    
    def log_message(self, format, *args):
        """Log con timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {args[0]}")


if __name__ == '__main__':
    PORT = 8080
    
    print(f"""
╔══════════════════════════════════════════╗
║   💬 Chat en Tiempo Real - Python        ║
║   Puerto: {PORT}                            ║
║   URL: http://localhost:{PORT}              ║
║                                          ║
║   📱 Abre en varias pestañas para probar ║
║   👥 Contador de usuarios en tiempo real ║
║   🎨 Personaliza nombre y color          ║
║                                          ║
║   Presiona Ctrl+C para detener          ║
╚══════════════════════════════════════════╝
    """)
    
    server = http.server.HTTPServer(('0.0.0.0', PORT), ChatServer)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Chat detenido")
        server.shutdown()