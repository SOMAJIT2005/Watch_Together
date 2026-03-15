import os
import random
import json
import urllib.request
from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- ADMIN NOTIFICATION SYSTEM (DISCORD) ---
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1482847532714299555/WYZFZghAG9uY4hfUngWJiVW8gP0r6TPsIbloNHFz7ejildt_l2Rur-dI89dlPh_Ct3CG"

def send_mobile_ping(name, pin):
    data = {
        "content": f"🚨 **New Access Request!**\n👤 **User:** `{name}`\n🔑 **PIN:** `{pin}`\n*Awaiting your approval.*"
    }
    
    # We add a User-Agent so Discord doesn't block the request
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL, 
        data=json.dumps(data).encode('utf-8'), 
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'WatchTogether-Server/1.0'
        }
    )
    
    try:
        urllib.request.urlopen(req)
        print("✅ Discord Ping Sent to Mobile!", flush=True)
    except Exception as e:
        print(f"❌ Discord Ping Failed: {e}", flush=True)

# State Management
unverified_requests = {}
users = {}
current_host_sid = None
current_host_name = None
global_hype = 0

# --- CLOUD PIN SECURITY ---
@socketio.on('request_cloud_pin')
def handle_pin_request(data):
    name = data.get('name', 'Anonymous')
    pin = str(random.randint(100000, 999999))
    unverified_requests[request.sid] = pin
    
    # 1. Print to Render Logs (Backup)
    print(f"\n🚨 ALERT: ACCESS REQUEST FROM [{name}] - PIN: {pin}\n", flush=True)
    
    # 2. Send Push Notification to your Phone!
    send_mobile_ping(name, pin)
    
    emit('pin_request_sent')

@socketio.on('verify_cloud_pin')
def handle_verification(data):
    guess = data.get('pin')
    actual = unverified_requests.get(request.sid)
    if guess and guess == actual:
        print(f"🔓 Access Granted for {request.sid}", flush=True)
        emit('auth_success')
        if request.sid in unverified_requests: del unverified_requests[request.sid]
    else:
        print(f"🚫 Access Denied for {request.sid}", flush=True)
        emit('auth_failed')

# --- CINEMA ROOM LOGIC ---
@socketio.on('join')
def on_join(data):
    global current_host_sid, current_host_name
    users[request.sid] = data
    if current_host_sid is None:
        current_host_sid = request.sid
        current_host_name = data['name']
    emit('host_update', {'host_sid': current_host_sid, 'host_name': current_host_name}, broadcast=True)
    emit('chat_event', {'sender': 'System', 'avatar': '🤖', 'color': '#ffffff', 'text': f"{data['name']} joined the cinema!"}, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    global current_host_sid, current_host_name
    if request.sid in unverified_requests:
        del unverified_requests[request.sid]
    if request.sid in users:
        name = users[request.sid]['name']
        del users[request.sid]
        emit('chat_event', {'sender': 'System', 'avatar': '🤖', 'color': '#ffffff', 'text': f"{name} left."}, broadcast=True)
        if request.sid == current_host_sid:
            if users:
                current_host_sid = list(users.keys())[0]
                current_host_name = users[current_host_sid]['name']
            else:
                current_host_sid, current_host_name = None, None
            emit('host_update', {'host_sid': current_host_sid, 'host_name': current_host_name}, broadcast=True)

@socketio.on('request_host')
def on_request_host():
    if current_host_sid and current_host_sid != request.sid:
        requester_name = users[request.sid]['name'] if request.sid in users else "Someone"
        emit('host_request_received', {'requester_sid': request.sid, 'requester_name': requester_name}, to=current_host_sid)

@socketio.on('grant_host')
def on_grant_host(data):
    global current_host_sid, current_host_name
    new_sid = data.get('new_host_sid')
    if new_sid in users and request.sid == current_host_sid:
        current_host_sid = new_sid
        current_host_name = users[new_sid]['name']
        emit('host_update', {'host_sid': current_host_sid, 'host_name': current_host_name}, broadcast=True)

# --- MULTIMEDIA SYNC & SOCIAL ---
@socketio.on('sync_event')
def on_sync(data): emit('sync_event', data, broadcast=True, include_self=False)

@socketio.on('chat_event')
def on_chat(msg):
    if request.sid in users:
        u = users[request.sid]
        emit('chat_event', {'sender': u['name'], 'avatar': u['avatar'], 'color': u['color'], 'text': msg}, broadcast=True, include_self=False)

@socketio.on('file_info')
def on_file(data): emit('file_info', data, broadcast=True, include_self=False)

@socketio.on('reaction_event')
def on_reaction(emoji):
    global global_hype
    global_hype = min(100, global_hype + 5)
    emit('reaction_event', {'emoji': emoji}, broadcast=True, include_self=False)
    emit('hype_update', global_hype, broadcast=True)

@socketio.on('laser_ping')
def on_laser(data):
    if request.sid in users:
        data['color'] = users[request.sid]['color']
        emit('laser_ping', data, broadcast=True, include_self=False)

@socketio.on('ping_server')
def on_ping(): emit('pong_client')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
