import os
from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

connected_users = {}
current_host_sid = None

@socketio.on('join')
def handle_join(data):
    global current_host_sid
    user_name = data.get('name', f"User {request.sid[:4]}")
    connected_users[request.sid] = user_name
    print(f"🟢 {user_name} connected.")

    if current_host_sid is None:
        current_host_sid = request.sid
        
    emit('host_update', {'host_sid': current_host_sid, 'host_name': connected_users[current_host_sid]}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    global current_host_sid
    user_name = connected_users.pop(request.sid, "Unknown User")
    print(f"🔴 {user_name} disconnected.")

    if request.sid == current_host_sid:
        current_host_sid = next(iter(connected_users)) if connected_users else None
        if current_host_sid:
            new_host_name = connected_users[current_host_sid]
            emit('host_update', {'host_sid': current_host_sid, 'host_name': new_host_name}, broadcast=True)

@socketio.on('sync_event')
def handle_sync(data):
    if request.sid == current_host_sid:
        emit('sync_event', data, broadcast=True, include_self=False)

@socketio.on('chat_event')
def handle_chat(text):
    sender_name = connected_users.get(request.sid, "Unknown")
    emit('chat_event', {'text': text, 'sender': sender_name}, broadcast=True, include_self=False)

@socketio.on('file_info')
def handle_file_info(data):
    sender_name = connected_users.get(request.sid, "Unknown")
    emit('file_info', {'filename': data['filename'], 'sender': sender_name}, broadcast=True, include_self=False)

@socketio.on('request_host')
def handle_host_request():
    requester_name = connected_users.get(request.sid, "Unknown")
    if current_host_sid:
        emit('host_request_received', {'requester_sid': request.sid, 'requester_name': requester_name}, room=current_host_sid)

@socketio.on('grant_host')
def handle_grant_host(data):
    global current_host_sid
    if request.sid == current_host_sid:
        new_host_sid = data.get('new_host_sid')
        if new_host_sid in connected_users:
            current_host_sid = new_host_sid
            emit('host_update', {'host_sid': current_host_sid, 'host_name': connected_users[current_host_sid]}, broadcast=True)

# --- NEW PRESENTATION FEATURES ---
@socketio.on('reaction_event')
def handle_reaction(emoji):
    sender_name = connected_users.get(request.sid, "Unknown")
    emit('reaction_event', {'emoji': emoji, 'sender': sender_name}, broadcast=True)

@socketio.on('ping_server')
def handle_ping():
    # Instantly bounce the packet back to calculate latency
    emit('pong_client', room=request.sid)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
