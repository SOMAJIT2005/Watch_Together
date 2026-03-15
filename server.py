import os
from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

connected_users = {}
current_host_sid = None
global_hype = 0  # NEW: Tracks the shared Hype Meter!

@socketio.on('join')
def handle_join(data):
    global current_host_sid
    # NEW: We now save the user's name, avatar, and color in the server!
    user_data = {
        'name': data.get('name', f"User {request.sid[:4]}"),
        'avatar': data.get('avatar', '👤'),
        'color': data.get('color', '#ffffff')
    }
    connected_users[request.sid] = user_data
    print(f"🟢 {user_data['name']} connected.")

    if current_host_sid is None:
        current_host_sid = request.sid
        
    emit('host_update', {'host_sid': current_host_sid, 'host_name': connected_users[current_host_sid]['name']}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    global current_host_sid
    user_data = connected_users.pop(request.sid, {'name': 'Unknown User'})
    print(f"🔴 {user_data['name']} disconnected.")

    if request.sid == current_host_sid:
        current_host_sid = next(iter(connected_users)) if connected_users else None
        if current_host_sid:
            new_host_name = connected_users[current_host_sid]['name']
            emit('host_update', {'host_sid': current_host_sid, 'host_name': new_host_name}, broadcast=True)

@socketio.on('sync_event')
def handle_sync(data):
    if request.sid == current_host_sid:
        emit('sync_event', data, broadcast=True, include_self=False)

@socketio.on('chat_event')
def handle_chat(text):
    user = connected_users.get(request.sid, {})
    emit('chat_event', {
        'text': text, 
        'sender': user.get('name', 'Unknown'),
        'avatar': user.get('avatar', '👤'),
        'color': user.get('color', '#ffffff')
    }, broadcast=True, include_self=False)

@socketio.on('file_info')
def handle_file_info(data):
    user = connected_users.get(request.sid, {})
    emit('file_info', {'filename': data['filename'], 'sender': user.get('name', 'Unknown')}, broadcast=True, include_self=False)

@socketio.on('request_host')
def handle_host_request():
    user = connected_users.get(request.sid, {})
    if current_host_sid:
        emit('host_request_received', {'requester_sid': request.sid, 'requester_name': user.get('name', 'Unknown')}, room=current_host_sid)

@socketio.on('grant_host')
def handle_grant_host(data):
    global current_host_sid
    if request.sid == current_host_sid:
        new_host_sid = data.get('new_host_sid')
        if new_host_sid in connected_users:
            current_host_sid = new_host_sid
            emit('host_update', {'host_sid': current_host_sid, 'host_name': connected_users[current_host_sid]['name']}, broadcast=True)

# --- NEW: INTERACTIVE FEATURES ---
@socketio.on('laser_ping')
def handle_laser(data):
    # Pass the spatial coordinates and the user's color to everyone else
    user = connected_users.get(request.sid, {})
    data['color'] = user.get('color', '#ff0000')
    emit('laser_ping', data, broadcast=True, include_self=False)

@socketio.on('reaction_event')
def handle_reaction(emoji):
    global global_hype
    user = connected_users.get(request.sid, {})
    emit('reaction_event', {'emoji': emoji, 'sender': user.get('name', 'Unknown')}, broadcast=True)

    # Calculate global hype! 10% per click.
    global_hype += 10
    if global_hype >= 100:
        emit('hype_update', 100, broadcast=True)
        emit('confetti_event', broadcast=True) # BOOM!
        global_hype = 0 # Reset
    else:
        emit('hype_update', global_hype, broadcast=True)

@socketio.on('ping_server')
def handle_ping():
    emit('pong_client', room=request.sid)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
