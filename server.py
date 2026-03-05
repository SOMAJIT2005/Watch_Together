import os
from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Global State ---
connected_users = {}  # Map SID to a username/label
current_host_sid = None
# --------------------

@socketio.on('connect')
def handle_connect():
    global current_host_sid
    # Store the user. We'll use their SID as a temporary name.
    connected_users[request.sid] = f"User {request.sid[:4]}"
    print(f"🟢 {connected_users[request.sid]} connected.")

    # The first person to connect becomes the host.
    if current_host_sid is None:
        current_host_sid = request.sid
        print(f"👑 {connected_users[request.sid]} is now the Host.")
    
    # Tell everyone (including the new user) who the current host is.
    emit('host_update', {'host_sid': current_host_sid, 'host_name': connected_users[current_host_sid]}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    global current_host_sid
    user_name = connected_users.pop(request.sid, "Unknown User")
    print(f"🔴 {user_name} disconnected.")

    # If the host disconnected, pass the crown to someone else.
    if request.sid == current_host_sid:
        current_host_sid = next(iter(connected_users)) if connected_users else None
        if current_host_sid:
            new_host_name = connected_users[current_host_sid]
            print(f"👑 Host disconnected. New Host is {new_host_name}.")
            emit('host_update', {'host_sid': current_host_sid, 'host_name': new_host_name}, broadcast=True)
        else:
            print("Please close the server and start again")

@socketio.on('sync_event')
def handle_sync(data):
    # --- THE ENFORCER ---
    # Only process the command if it comes from the current host.
    if request.sid == current_host_sid:
        print(f"📩 Sync Action from Host: {data}")
        emit('sync_event', data, broadcast=True, include_self=False)
    else:
        print(f"⛔ Ignored sync command from non-host: {request.sid}")
        # Optionally, send a message back to the user telling them they aren't the host.
        emit('chat_event', "<i>⚠️ Only the Host can control playback. Use 'Request Host' to ask for control.</i>", room=request.sid)

@socketio.on('chat_event')
def handle_chat(message_data):
    sender_name = connected_users.get(request.sid, "Unknown")
    print(f"💬 Chat from {sender_name}: {message_data}")
    # Broadcast the message with the sender's name
    emit('chat_event', {'text': message_data, 'sender': sender_name, 'sid': request.sid}, broadcast=True, include_self=False)

@socketio.on('file_info')
def handle_file_info(data):
    sender_name = connected_users.get(request.sid, "Unknown")
    print(f"📁 File info from {sender_name}: {data['filename']}")
    emit('file_info', {'filename': data['filename'], 'sender': sender_name}, broadcast=True, include_self=False)

# --- NEW: HOST PASSING LOGIC ---

@socketio.on('request_host')
def handle_host_request():
    requester_sid = request.sid
    requester_name = connected_users.get(requester_sid, "Unknown")
    print(f"🙋 {requester_name} is requesting to be Host.")
    
    # Forward the request ONLY to the current host.
    if current_host_sid:
        emit('host_request_received', {'requester_sid': requester_sid, 'requester_name': requester_name}, room=current_host_sid)

@socketio.on('grant_host')
def handle_grant_host(data):
    global current_host_sid
    # Only the current host can grant the role.
    if request.sid == current_host_sid:
        new_host_sid = data.get('new_host_sid')
        if new_host_sid in connected_users:
            current_host_sid = new_host_sid
            new_host_name = connected_users[current_host_sid]
            print(f"👑 Host role granted to {new_host_name}.")
            # Announce the new host to everyone.
            emit('host_update', {'host_sid': current_host_sid, 'host_name': new_host_name}, broadcast=True)

# -------------------------------

if __name__ == '__main__':
    print("🚀 Starting Watch Together Server in the Cloud...")
    # Ask the cloud environment what port to use, default to 5000 if running locally
    port = int(os.environ.get('PORT', 5000))
    # 0.0.0.0 tells the server to listen to the public internet, not just localhost
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)