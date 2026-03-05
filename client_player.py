import sys
import os
import time
import random
import socketio

from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                               QHBoxLayout, QWidget, QFileDialog, QTextEdit, 
                               QLineEdit, QLabel, QMessageBox, 
                               QInputDialog, QSlider)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import QUrl, Signal, Slot, Qt, QTimer, QEvent, QPropertyAnimation, QPoint, QEasingCurve

sio = socketio.Client()

class VideoPlayer(QMainWindow):
    sync_signal = Signal(dict)
    chat_signal = Signal(dict)  
    file_signal = Signal(dict)
    host_update_signal = Signal(dict)
    host_request_signal = Signal(dict)
    reaction_signal = Signal(dict)

    def __init__(self, username):
        super().__init__()
        
        # 🔴 YOUR RENDER URL
        self.server_url = 'https://watch-together-6kuy.onrender.com' 
        
        self.username = username
        self.setWindowTitle(f"Watch Together - {self.username} | CSE 2100 Project")
        self.resize(1100, 650) 

        self.my_filename = None       
        self.friend_filename = None   
        self.is_host = False
        self.my_sid = None
        self.active_animations = [] # Stores floating emojis
        self.last_ping_time = 0

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # ================= LEFT PANEL (MEDIA) =================
        self.media_layout = QVBoxLayout()
        
        # --- Top Bar ---
        self.top_bar = QHBoxLayout()
        self.host_status_label = QLabel("👑 Host: Connecting...")
        self.host_status_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        
        # NEW: The Ping/Latency Tracker
        self.ping_label = QLabel("📶 Ping: -- ms")
        self.ping_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; color: gray;")

        self.request_host_btn = QPushButton("🙋 Request Host")
        self.request_host_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.request_host_btn.clicked.connect(self.request_host_clicked)
        self.request_host_btn.hide()

        self.fullscreen_btn = QPushButton("⛶ Fullscreen")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)

        self.top_bar.addWidget(self.host_status_label)
        self.top_bar.addStretch()
        self.top_bar.addWidget(self.ping_label)
        self.top_bar.addWidget(self.request_host_btn)
        self.top_bar.addWidget(self.fullscreen_btn)
        self.media_layout.addLayout(self.top_bar)

        # --- Native Video Player ---
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.media_layout.addWidget(self.video_widget, stretch=1)

        # --- Progress Bar (Seeker) ---
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)
        self.slider.setEnabled(False) 
        self.media_layout.addWidget(self.slider)

        # --- Bottom Controls ---
        self.controls_layout = QHBoxLayout()

        self.open_btn = QPushButton("📁 Open Local Movie File (.mp4)")
        self.open_btn.setStyleSheet("padding: 10px; font-weight: bold;")
        self.open_btn.clicked.connect(self.open_file)
        self.controls_layout.addWidget(self.open_btn)

        self.play_btn = QPushButton("⏯️ Play / Pause")
        self.play_btn.setStyleSheet("padding: 10px; font-weight: bold;")
        self.play_btn.clicked.connect(self.play_pause_clicked)
        self.play_btn.setEnabled(False) 
        self.controls_layout.addWidget(self.play_btn)

        self.media_layout.addLayout(self.controls_layout)
        self.main_layout.addLayout(self.media_layout, stretch=3)

        # ================= RIGHT PANEL (SOCIAL) =================
        self.chat_layout = QVBoxLayout()
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True) 
        self.chat_layout.addWidget(self.chat_history)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type a message and hit Enter...")
        self.chat_input.returnPressed.connect(self.send_chat_message) 
        self.chat_layout.addWidget(self.chat_input)

        # NEW: Live Floating Reaction Toolbar
        self.reaction_toolbar = QHBoxLayout()
        emojis = ["❤️", "😂", "😲", "🔥", "🎉"]
        for e in emojis:
            btn = QPushButton(e)
            btn.setStyleSheet("font-size: 20px; padding: 5px; border-radius: 5px; background-color: #f0f0f0;")
            btn.clicked.connect(lambda checked, emoji=e: self.send_reaction(emoji))
            self.reaction_toolbar.addWidget(btn)
            
        self.chat_layout.addLayout(self.reaction_toolbar)
        self.main_layout.addLayout(self.chat_layout, stretch=1)

        # --- Media Engine Setup ---
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.8)

        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

        # --- Networking Setup ---
        self.sync_signal.connect(self.handle_network_sync)
        self.chat_signal.connect(self.handle_network_chat) 
        self.file_signal.connect(self.handle_network_file)
        self.host_update_signal.connect(self.handle_host_update)
        self.host_request_signal.connect(self.handle_host_request_dialog)
        self.reaction_signal.connect(self.handle_incoming_reaction)
        self.connect_to_server()

        # Start the Background Ping Tracker (Fires every 2 seconds)
        self.ping_timer = QTimer(self)
        self.ping_timer.timeout.connect(self.send_ping)
        self.ping_timer.start(2000)

    # ================= OS DISTRACTION MONITOR =================
    # This automatically detects if the user minimizes or clicks away from the app
    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange:
            if not self.isActiveWindow(): # App lost focus!
                if self.is_host and self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    # Auto-pause to protect the watch party
                    self.play_pause_clicked()
                    sio.emit('chat_event', "⚠️ <b>System Alert:</b> Host tabbed out! Video auto-paused to keep sync.")
                elif not self.is_host:
                    # Snitch on the guest!
                    sio.emit('chat_event', "👀 <b>System Alert:</b> I just tabbed out of the watch party!")
        super().changeEvent(event)
    # ==========================================================

    # --- UI & MEDIA LOGIC ---
    def toggle_fullscreen(self):
        if self.isFullScreen(): self.showNormal()
        else: self.showFullScreen()

    def position_changed(self, position):
        self.slider.setValue(position)

    def duration_changed(self, duration):
        self.slider.setRange(0, duration)

    def set_position(self, position):
        if self.is_host:
            self.media_player.setPosition(position)
            sio.emit('sync_event', {'action': 'seek', 'time': position})

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.avi *.mkv)")
        if file_path:
            filename = os.path.basename(file_path)
            self.my_filename = filename 
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.media_player.pause()
            
            if self.friend_filename and self.my_filename != self.friend_filename:
                 self.chat_history.append(f"<b style='color: red;'>❌ MISMATCH: Load '{self.friend_filename}' to unlock!</b>")
            else:
                 self.chat_history.append(f"<i>🎬 Loaded Local File: {filename}. Ready.</i>")
            sio.emit('file_info', {'filename': filename})

    def play_pause_clicked(self):
        if not self.is_host: return 
        if self.friend_filename and self.my_filename != self.friend_filename:
            self.chat_history.append("<b style='color: red;'>⛔ Play Blocked: Video mismatch. Both users must load the same file.</b>")
            return 

        current_time = self.media_player.position() 
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            sio.emit('sync_event', {'action': 'pause', 'time': current_time})
            self.media_player.pause()
        else:
            sio.emit('sync_event', {'action': 'play', 'time': current_time})
            self.media_player.play()

    # --- SOCIAL FEATURES (PINGS & REACTIONS) ---
    def send_ping(self):
        self.last_ping_time = time.time()
        sio.emit('ping_server')

    def send_reaction(self, emoji):
        sio.emit('reaction_event', emoji)
        # Show it on our own screen immediately
        self.trigger_floating_emoji(emoji)

    @Slot(dict)
    def handle_incoming_reaction(self, data):
        emoji = data.get('emoji')
        sender = data.get('sender')
        self.chat_history.append(f"<span style='color: gray; font-size: 10px;'><i>{sender} reacted {emoji}</i></span>")
        self.trigger_floating_emoji(emoji)

    def trigger_floating_emoji(self, emoji):
        # Creates a temporary label that physically floats over the video player
        label = QLabel(emoji, self.video_widget)
        label.setStyleSheet("font-size: 48px; background: transparent;")
        label.setAttribute(Qt.WA_TransparentForMouseEvents) # So it doesn't block mouse clicks
        label.show()
        
        # Pick a random starting point at the bottom of the video
        start_x = random.randint(20, max(20, self.video_widget.width() - 80))
        start_y = self.video_widget.height() - 60
        label.move(start_x, start_y)
        
        # Animate it upwards
        anim = QPropertyAnimation(label, b"pos")
        anim.setEndValue(QPoint(start_x, start_y - 250))
        anim.setDuration(2500)
        anim.setEasingCurve(QEasingCurve.OutExpo)
        anim.finished.connect(label.deleteLater)
        anim.start()
        
        # Prevent Python from deleting the animation too early
        self.active_animations.append(anim)
        self.active_animations = [a for a in self.active_animations if a.state() == QPropertyAnimation.State.Running]

    # --- NETWORKING & HOSTING LOGIC ---
    def connect_to_server(self):
        @sio.on('connect')
        def on_connect():
            self.my_sid = sio.get_sid()
            self.chat_history.append("<i>✅ Connected to Global Server!</i>")
            sio.emit('join', {'name': self.username})

        @sio.on('sync_event')
        def on_sync(data): self.sync_signal.emit(data)
        @sio.on('chat_event')
        def on_chat(data): self.chat_signal.emit(data)
        @sio.on('file_info')
        def on_file_info(data): self.file_signal.emit(data)
        @sio.on('host_update')
        def on_host_update(data): self.host_update_signal.emit(data)
        @sio.on('host_request_received')
        def on_host_request(data): self.host_request_signal.emit(data)
        @sio.on('reaction_event')
        def on_reaction(data): self.reaction_signal.emit(data)
        
        @sio.on('pong_client')
        def on_pong():
            latency = int((time.time() - self.last_ping_time) * 1000)
            self.ping_label.setText(f"📶 Ping: {latency}ms")
            if latency < 100: self.ping_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; color: green;")
            elif latency < 250: self.ping_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; color: orange;")
            else: self.ping_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; color: red;")

        try: sio.connect(self.server_url) 
        except: self.chat_history.append("<i>⚠️ Could not connect to server.</i>")

    @Slot(dict)
    def handle_host_update(self, data):
        host_sid = data.get('host_sid')
        host_name = data.get('host_name', 'Unknown')
        self.is_host = (host_sid == self.my_sid)

        if self.is_host:
            self.host_status_label.setText(f"👑 Host: You ({host_name})")
            self.host_status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 14px; padding: 5px;")
            self.play_btn.setEnabled(True)
            self.slider.setEnabled(True)
            self.request_host_btn.hide()
            self.chat_history.append("<i>🎉 You are the Host! You have control.</i>")
        else:
            self.host_status_label.setText(f"👑 Host: {host_name}")
            self.host_status_label.setStyleSheet("color: black; font-weight: bold; font-size: 14px; padding: 5px;")
            self.play_btn.setEnabled(False)
            self.slider.setEnabled(False)
            self.request_host_btn.show()
            self.chat_history.append(f"<i>ℹ️ {host_name} is now the Host.</i>")

    def request_host_clicked(self):
        sio.emit('request_host')
        self.chat_history.append("<i>🙋 Requesting Host status... waiting.</i>")
        self.request_host_btn.setEnabled(False) 

    @Slot(dict)
    def handle_host_request_dialog(self, data):
        requester_name = data.get('requester_name')
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Host Request")
        msg_box.setText(f"{requester_name} wants to be the Host. Grant control?")
        msg_box.setIcon(QMessageBox.Question)
        grant_btn = msg_box.addButton("Grant Control", QMessageBox.AcceptRole)
        msg_box.addButton("Deny", QMessageBox.RejectRole)
        msg_box.exec()

        if msg_box.clickedButton() == grant_btn:
            sio.emit('grant_host', {'new_host_sid': data.get('requester_sid')})
            self.chat_history.append(f"<i>✅ You granted Host status to {requester_name}.</i>")
        else:
            self.chat_history.append(f"<i>🚫 You denied {requester_name}.</i>")

    @Slot(dict)
    def handle_network_sync(self, data):
        if self.friend_filename and self.my_filename != self.friend_filename: return 
        
        action = data.get('action')
        sync_time = data.get('time', 0) 
        
        if action == 'seek':
            self.media_player.setPosition(sync_time)
        elif action == 'pause':
            self.media_player.setPosition(sync_time)
            self.media_player.pause()
        elif action == 'play':
            self.media_player.setPosition(sync_time)
            self.media_player.play()

    @Slot(dict)
    def handle_network_file(self, data):
        filename = data.get('filename')
        sender = data.get('sender', 'Friend')
        
        self.friend_filename = filename 
        if self.my_filename and self.my_filename != self.friend_filename:
            self.chat_history.append(f"<b style='color: red;'>❌ ERROR: {sender} loaded '{filename}'. Mismatch!</b>")
        elif not self.my_filename:
            self.chat_history.append(f"<b style='color: #ff9900;'>⚠️ {sender} loaded local file: {filename}</b>")

    def send_chat_message(self):
        text = self.chat_input.text()
        if text.strip() != "":
            self.chat_history.append(f"<b>You:</b> {text}")
            sio.emit('chat_event', text)
            self.chat_input.clear()

    @Slot(dict)
    def handle_network_chat(self, data):
        sender = data.get('sender', 'System')
        text = data.get('text')
        self.chat_history.append(f"<b>{sender}:</b> {text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    username, ok = QInputDialog.getText(None, "Welcome to Watch Together", "Enter your username:")
    if not ok or not username.strip():
        username = "Guest" 
        
    player = VideoPlayer(username.strip())
    player.show()
    app.aboutToQuit.connect(sio.disconnect)
    sys.exit(app.exec())
