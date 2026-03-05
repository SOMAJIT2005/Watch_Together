import sys
import os
import socketio
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QTextEdit, QLineEdit, QStackedWidget, QLabel, QMessageBox
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Signal, Slot, Qt

# Create the Socket.IO client globally
sio = socketio.Client()

class VideoPlayer(QMainWindow):
    # Define signals for thread-safe UI updates
    sync_signal = Signal(dict)
    chat_signal = Signal(dict)
    file_signal = Signal(dict)
    host_update_signal = Signal(dict)
    host_request_signal = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Watch Together - Host Mode")
        self.resize(1100, 650)

        # --- State Variables ---
        self.my_filename = None
        self.friend_filename = None
        self.is_host = False
        self.current_host_name = "Unknown"
        self.my_sid = None
        # -----------------------

        # Main UI Setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # ================= LEFT PANEL: MEDIA PLAYER =================
        self.media_layout = QVBoxLayout()

        # --- Top Bar: Host Status & Request Button ---
        self.top_bar = QHBoxLayout()
        
        # Host Status Label
        self.host_status_label = QLabel("👑 Host: Finding...")
        self.host_status_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        
        # Request Host Button
        self.request_host_btn = QPushButton("🙋 Request Host")
        self.request_host_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.request_host_btn.clicked.connect(self.request_host_clicked)
        self.request_host_btn.hide() # Hidden by default, shown if not host

        self.top_bar.addWidget(self.host_status_label)
        self.top_bar.addStretch() # Push the button to the right
        self.top_bar.addWidget(self.request_host_btn)
        self.media_layout.addLayout(self.top_bar)
        # -----------------------------------------------------------

        # --- Hybrid Media Stack (Local/Web) ---
        self.media_stack = QStackedWidget()

        # Card 0: Local Video
        self.local_video_widget = QWidget()
        self.local_layout = QVBoxLayout(self.local_video_widget)
        self.local_layout.setContentsMargins(0,0,0,0)
        self.video_widget = QVideoWidget()
        self.local_layout.addWidget(self.video_widget)
        self.media_stack.addWidget(self.local_video_widget)

        # Card 1: Web Browser
        self.web_view = QWebEngineView()
        self.media_stack.addWidget(self.web_view)

        self.media_layout.addWidget(self.media_stack)

        # --- Bottom Controls ---
        self.controls_layout = QHBoxLayout()

        self.mode_btn = QPushButton("🌐 Switch to Web Mode")
        self.mode_btn.clicked.connect(self.toggle_mode)
        self.controls_layout.addWidget(self.mode_btn)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube link & hit Enter")
        self.url_input.hide()
        self.url_input.returnPressed.connect(self.load_web_url)
        self.controls_layout.addWidget(self.url_input)

        self.open_btn = QPushButton("📁 Open Video File")
        self.open_btn.clicked.connect(self.open_file)
        self.controls_layout.addWidget(self.open_btn)

        self.play_btn = QPushButton("⏯️ Play / Pause")
        self.play_btn.clicked.connect(self.play_pause_clicked)
        self.play_btn.setEnabled(False) # Disabled by default until we know who the host is
        self.controls_layout.addWidget(self.play_btn)

        self.media_layout.addLayout(self.controls_layout)
        self.main_layout.addLayout(self.media_layout, stretch=3)

        # ================= RIGHT PANEL: CHAT =================
        self.chat_layout = QVBoxLayout()
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_layout.addWidget(self.chat_history)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type a message and hit Enter...")
        self.chat_input.returnPressed.connect(self.send_chat_message)
        self.chat_layout.addWidget(self.chat_input)

        self.main_layout.addLayout(self.chat_layout, stretch=1)

        # --- Media Engine & Networking Setup ---
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.8)

        # Connect signals to slots
        self.sync_signal.connect(self.handle_network_sync)
        self.chat_signal.connect(self.handle_network_chat)
        self.file_signal.connect(self.handle_network_file)
        self.host_update_signal.connect(self.handle_host_update)
        self.host_request_signal.connect(self.handle_host_request_dialog)
        
        self.connect_to_server()

    # --- NETWORKING FUNCTIONS ---
    def connect_to_server(self):
        # Define network event handlers inside the method to access 'self'
        @sio.on('connect')
        def on_connect():
            self.my_sid = sio.get_sid()
            self.chat_history.append("<i>✅ Connected to Server!</i>")

        @sio.on('sync_event')
        def on_sync(data):
            self.sync_signal.emit(data)

        @sio.on('chat_event')
        def on_chat(data):
            self.chat_signal.emit(data)

        @sio.on('file_info')
        def on_file_info(data):
            self.file_signal.emit(data)

        @sio.on('host_update')
        def on_host_update(data):
            self.host_update_signal.emit(data)

        @sio.on('host_request_received')
        def on_host_request(data):
            self.host_request_signal.emit(data)
        
        try:
            # CHANGE THIS URL TO YOUR NGROK LINK WHEN TESTING WITH A FRIEND
            sio.connect('http://127.0.0.1:5000')
        except Exception as e:
            self.chat_history.append(f"<i>⚠️ Connection failed: {e}</i>")

    # --- HOSTING LOGIC ---

    @Slot(dict)
    def handle_host_update(self, data):
        host_sid = data.get('host_sid')
        host_name = data.get('host_name', 'Unknown')
        
        self.current_host_name = host_name
        # Check if *I* am the new host
        self.is_host = (host_sid == self.my_sid)

        if self.is_host:
            self.host_status_label.setText(f"👑 Host: You ({host_name})")
            self.host_status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 14px; padding: 5px;")
            self.play_btn.setEnabled(True)
            self.request_host_btn.hide()
            self.chat_history.append("<i>🎉 You are now the Host! You have control.</i>")
        else:
            self.host_status_label.setText(f"👑 Host: {host_name}")
            self.host_status_label.setStyleSheet("color: black; font-weight: bold; font-size: 14px; padding: 5px;")
            self.play_btn.setEnabled(False)
            self.request_host_btn.show()
            self.chat_history.append(f"<i>ℹ️ {host_name} is now the Host.</i>")

    def request_host_clicked(self):
        # Send a request to the server
        sio.emit('request_host')
        self.chat_history.append("<i>🙋 Requesting Host status... waiting for response.</i>")
        self.request_host_btn.setEnabled(False) # Disable button to prevent spamming

    @Slot(dict)
    def handle_host_request_dialog(self, data):
        # This slot is only called if you are the current host
        requester_name = data.get('requester_name')
        requester_sid = data.get('requester_sid')

        # Create a Yes/No dialog box
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Host Request")
        msg_box.setText(f"{requester_name} wants to be the Host.")
        msg_box.setInformativeText("Do you want to grant them control?")
        msg_box.setIcon(QMessageBox.Question)
        
        grant_btn = msg_box.addButton("Grant Control", QMessageBox.AcceptRole)
        deny_btn = msg_box.addButton("Deny", QMessageBox.RejectRole)
        
        msg_box.exec()

        if msg_box.clickedButton() == grant_btn:
            # Send the grant command back to the server
            sio.emit('grant_host', {'new_host_sid': requester_sid})
            self.chat_history.append(f"<i>✅ You granted Host status to {requester_name}.</i>")
        else:
            self.chat_history.append(f"<i>🚫 You denied the request from {requester_name}.</i>")

    # --- PLAYBACK LOGIC (Updated for Host) ---

    def play_pause_clicked(self):
        # 1. Host Check: Only the host can click this button.
        if not self.is_host:
            # This shouldn't be reachable since the button is disabled, but good as a fallback.
            self.chat_history.append("<i>⚠️ Only the Host can control playback.</i>")
            return

        # 2. Mismatch Check: Cannot play if files don't match.
        if self.media_stack.currentIndex() == 0 and self.friend_filename and self.my_filename != self.friend_filename:
            self.chat_history.append("<b style='color: red;'>⛔ Play Blocked: Video mismatch.</b>")
            return 

        # Send the appropriate command based on mode and state
        if self.media_stack.currentIndex() == 0: # Local Mode
            current_time = self.media_player.position()
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                sio.emit('sync_event', {'action': 'pause', 'time': current_time})
                self.media_player.pause()
            else:
                sio.emit('sync_event', {'action': 'play', 'time': current_time})
                self.media_player.play()
        else: # Web Mode
            sio.emit('sync_event', {'action': 'web_toggle', 'time': 0})
            self.inject_web_toggle()

    # --- (The rest of your existing functions remain unchanged) ---
    # ... toggle_mode, load_web_url, inject_web_toggle, open_file, 
    # handle_network_sync, handle_network_file, send_chat_message, handle_network_chat ...

    # --- HYBRID MODE LOGIC ---
    def toggle_mode(self):
        if self.media_stack.currentIndex() == 0:
            self.media_stack.setCurrentIndex(1)
            self.mode_btn.setText("🎬 Switch to Local Video")
            self.url_input.show()
            self.open_btn.hide()
            self.media_player.pause()
        else:
            self.media_stack.setCurrentIndex(0)
            self.mode_btn.setText("🌐 Switch to Web Mode")
            self.url_input.hide()
            self.open_btn.show()

    def load_web_url(self):
        url = self.url_input.text()
        if url.strip() != "":
            if not url.startswith("http"):
                url = "https://" + url 
            self.web_view.setUrl(QUrl(url))
            self.chat_history.append(f"<i>🌐 Loading Webpage: {url}</i>")
            sio.emit('chat_event', f"Load this URL: {url}")
            self.url_input.clear()

    def inject_web_toggle(self):
        js_code = "var v = document.getElementsByTagName('video')[0]; if(v) { if(v.paused) v.play(); else v.pause(); }"
        self.web_view.page().runJavaScript(js_code)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.avi *.mkv *.mov)")
        if file_path:
            filename = os.path.basename(file_path)
            self.my_filename = filename 
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.media_player.pause()
            
            if self.friend_filename and self.my_filename != self.friend_filename:
                 self.chat_history.append(f"<b style='color: red;'>❌ MISMATCH: You loaded '{filename}'. You must load '{self.friend_filename}' to unlock playback!</b>")
            else:
                 self.chat_history.append(f"<i>🎬 You loaded: {filename}. Ready.</i>")
            sio.emit('file_info', {'filename': filename})

    @Slot(dict)
    def handle_network_sync(self, data):
        action = data.get('action')
        if action == 'web_toggle':
            if self.media_stack.currentIndex() == 1:
                self.inject_web_toggle()
            return
        if self.friend_filename and self.my_filename != self.friend_filename:
            return 
        sync_time = data.get('time', 0) 
        self.media_player.setPosition(sync_time)
        if action == 'pause':
            self.media_player.pause()
        elif action == 'play':
            self.media_player.play()

    @Slot(dict)
    def handle_network_file(self, data):
        filename = data.get('filename')
        sender = data.get('sender', 'Friend')
        self.friend_filename = filename 
        if self.my_filename and self.my_filename != self.friend_filename:
            self.chat_history.append(f"<b style='color: red;'>❌ ERROR: {sender} loaded '{filename}'. Mismatch!</b>")
        elif not self.my_filename:
            self.chat_history.append(f"<b style='color: #ff9900;'>⚠️ {sender} wants to watch: {filename}</b>")

    def send_chat_message(self):
        text = self.chat_input.text()
        if text.strip() != "":
            self.chat_history.append(f"<b>You:</b> {text}")
            sio.emit('chat_event', text)
            self.chat_input.clear()

    @Slot(dict)
    def handle_network_chat(self, data):
        sender = data.get('sender', 'Friend')
        text = data.get('text')
        self.chat_history.append(f"<b>{sender}:</b> {text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    app.aboutToQuit.connect(sio.disconnect)
    sys.exit(app.exec())