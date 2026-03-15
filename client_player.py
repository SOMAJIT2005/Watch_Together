import sys
import os
import time
import random
import socketio

from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                               QHBoxLayout, QWidget, QFileDialog, QTextEdit, 
                               QLineEdit, QLabel, QMessageBox, QStackedWidget,
                               QSlider, QGraphicsOpacityEffect)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import QUrl, Signal, Slot, Qt, QTimer, QEvent, QPropertyAnimation, QPoint, QEasingCurve, QSequentialAnimationGroup

sio = socketio.Client()

class VideoPlayer(QMainWindow):
    # --- SIGNALS ---
    sync_signal = Signal(dict)
    chat_signal = Signal(dict)  
    file_signal = Signal(dict)
    host_update_signal = Signal(dict)
    host_request_signal = Signal(dict)
    reaction_signal = Signal(dict)
    ping_signal = Signal(int) 
    connected_signal = Signal() # Safely tells the UI to drop the splash screen

    def __init__(self):
        super().__init__()
        
        # 🔴 YOUR RENDER URL
        self.server_url = 'https://watch-together-6kuy.onrender.com' 
        
        self.setWindowTitle("Watch Together | CSE 2100 Project")
        self.resize(1100, 650) 
        self.setStyleSheet("background-color: #121212; color: white;") # Dark mode theme!

        self.username = "Guest"
        self.my_filename = None       
        self.friend_filename = None   
        self.is_host = False
        self.my_sid = None
        self.active_animations = [] 
        self.last_ping_time = 0

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # THE 3-STAGE MASTER STACK
        self.app_stack = QStackedWidget()
        self.main_layout.addWidget(self.app_stack)

        self.build_login_screen()
        self.build_splash_screen()
        self.build_main_cinema()

        # Start at the Login Screen
        self.app_stack.setCurrentIndex(0)

        # Safely transition to cinema when server connects
        self.connected_signal.connect(self.transition_to_cinema)

    # ================= STAGE 1: THE LOGIN SCREEN =================
    def build_login_screen(self):
        self.login_widget = QWidget()
        layout = QVBoxLayout(self.login_widget)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("🍿 WATCH TOGETHER")
        title.setStyleSheet("font-size: 40px; font-weight: bold; color: #E50914; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your Name/Ticket...")
        self.name_input.setStyleSheet("font-size: 18px; padding: 15px; border-radius: 8px; background-color: #222; color: white; border: 1px solid #444;")
        self.name_input.setFixedWidth(400)
        self.name_input.returnPressed.connect(self.start_login_process)

        enter_btn = QPushButton("Enter Cinema")
        enter_btn.setStyleSheet("font-size: 18px; font-weight: bold; padding: 15px; border-radius: 8px; background-color: #E50914; color: white;")
        enter_btn.setFixedWidth(400)
        enter_btn.clicked.connect(self.start_login_process)

        layout.addWidget(title)
        layout.addWidget(self.name_input)
        layout.addWidget(enter_btn)
        
        self.app_stack.addWidget(self.login_widget) # Index 0

    # ================= STAGE 2: THE CINEMATIC SPLASH =================
    def build_splash_screen(self):
        self.splash_widget = QWidget()
        layout = QVBoxLayout(self.splash_widget)
        layout.setAlignment(Qt.AlignCenter)

        self.welcome_label = QLabel("")
        self.welcome_label.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        self.welcome_label.setAlignment(Qt.AlignCenter)

        self.loading_label = QLabel("Connecting to Global Server...")
        self.loading_label.setStyleSheet("font-size: 18px; color: #aaaaaa; margin-top: 20px;")
        self.loading_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.welcome_label)
        layout.addWidget(self.loading_label)

        self.app_stack.addWidget(self.splash_widget) # Index 1

    def start_login_process(self):
        typed_name = self.name_input.text().strip()
        if typed_name: self.username = typed_name
        
        self.setWindowTitle(f"Watch Together - {self.username}")
        self.welcome_label.setText(f"Welcome to the Cinema, {self.username}.")
        
        # Switch to splash screen
        self.app_stack.setCurrentIndex(1)
        
        # Start connection process
        self.connect_to_server()

        # Smart Server Status Timer (Tells professors if Render is asleep)
        self.server_wait_timer = QTimer(self)
        self.server_wait_timer.setSingleShot(True)
        self.server_wait_timer.timeout.connect(self.show_render_warning)
        self.server_wait_timer.start(4000) # If not connected in 4s, show warning

    def show_render_warning(self):
        self.loading_label.setText("Waking up Cloud Server...\n(Free tier takes ~50 seconds to boot up. Please wait!)")
        self.loading_label.setStyleSheet("font-size: 16px; color: #ffcc00; margin-top: 20px;")

    @Slot()
    def transition_to_cinema(self):
        self.server_wait_timer.stop() # Cancel the warning timer
        
        # Fade out splash and show cinema!
        self.app_stack.setCurrentIndex(2)
        
        # Start the background pings now that we are connected
        self.ping_timer = QTimer(self)
        self.ping_timer.timeout.connect(self.send_ping)
        self.ping_timer.start(2000)

    # ================= STAGE 3: THE MAIN CINEMA UI =================
    def build_main_cinema(self):
        self.cinema_widget = QWidget()
        self.cinema_widget.setStyleSheet("background-color: #f0f0f0; color: black;") # Revert to normal colors for main UI
        cinema_layout = QHBoxLayout(self.cinema_widget)
        cinema_layout.setContentsMargins(10, 10, 10, 10)

        # --- LEFT PANEL (MEDIA) ---
        self.media_layout = QVBoxLayout()
        
        self.top_bar_widget = QWidget()
        self.top_bar = QHBoxLayout(self.top_bar_widget)
        self.top_bar.setContentsMargins(0, 0, 0, 0)

        self.host_status_label = QLabel("👑 Host: Connecting...")
        self.host_status_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        
        self.ping_label = QLabel("📶 Ping: -- ms")
        self.ping_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; color: gray;")

        self.request_host_btn = QPushButton("🙋 Request Host")
        self.request_host_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px 15px; border-radius: 4px;")
        self.request_host_btn.clicked.connect(self.request_host_clicked)
        self.request_host_btn.hide()

        self.fullscreen_btn = QPushButton("⛶ Fullscreen")
        self.fullscreen_btn.setStyleSheet("padding: 5px 15px; border-radius: 4px; background-color: #ddd;")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)

        self.top_bar.addWidget(self.host_status_label)
        self.top_bar.addStretch()
        self.top_bar.addWidget(self.ping_label)
        self.top_bar.addWidget(self.request_host_btn)
        self.top_bar.addWidget(self.fullscreen_btn)
        self.media_layout.addWidget(self.top_bar_widget)

        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.media_layout.addWidget(self.video_widget, stretch=1)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)
        self.slider.setEnabled(False) 
        self.media_layout.addWidget(self.slider)

        self.controls_widget = QWidget()
        self.controls_layout = QHBoxLayout(self.controls_widget)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)

        self.open_btn = QPushButton("📁 Open Local Movie File (.mp4)")
        self.open_btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #fff; border: 1px solid #ccc; border-radius: 4px;")
        self.open_btn.clicked.connect(self.open_file)
        self.controls_layout.addWidget(self.open_btn)

        self.play_btn = QPushButton("⏯️ Play / Pause")
        self.play_btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #fff; border: 1px solid #ccc; border-radius: 4px;")
        self.play_btn.clicked.connect(self.play_pause_clicked)
        self.play_btn.setEnabled(False) 
        self.controls_layout.addWidget(self.play_btn)

        self.media_layout.addWidget(self.controls_widget)
        cinema_layout.addLayout(self.media_layout, stretch=3)

        # --- RIGHT PANEL (SOCIAL) ---
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True) 
        self.chat_history.setStyleSheet("background-color: white; border: 1px solid #ccc; border-radius: 4px; padding: 5px;")
        self.chat_layout.addWidget(self.chat_history)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type a message and hit Enter...")
        self.chat_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 4px;")
        self.chat_input.returnPressed.connect(self.send_chat_message) 
        self.chat_layout.addWidget(self.chat_input)

        self.reaction_toolbar = QHBoxLayout()
        emojis = ["❤️", "😂", "😲", "🔥", "🎉"]
        for e in emojis:
            btn = QPushButton(e)
            btn.setStyleSheet("font-size: 20px; padding: 5px; border-radius: 5px; background-color: #e0e0e0; border: none;")
            btn.clicked.connect(lambda checked, emoji=e: self.send_reaction(emoji))
            self.reaction_toolbar.addWidget(btn)
            
        self.chat_layout.addLayout(self.reaction_toolbar)
        cinema_layout.addWidget(self.chat_widget, stretch=1)

        self.app_stack.addWidget(self.cinema_widget) # Index 2

        # Media Engine Setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.8)

        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

        # Signal connections
        self.sync_signal.connect(self.handle_network_sync)
        self.chat_signal.connect(self.handle_network_chat) 
        self.file_signal.connect(self.handle_network_file)
        self.host_update_signal.connect(self.handle_host_update)
        self.host_request_signal.connect(self.handle_host_request_dialog)
        self.reaction_signal.connect(self.handle_incoming_reaction)
        self.ping_signal.connect(self.update_ping_display) 

    # ================= OS DISTRACTION MONITOR =================
    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange:
            if not self.isActiveWindow() and self.app_stack.currentIndex() == 2: 
                if self.is_host and self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self.play_pause_clicked()
                    sio.emit('chat_event', "⚠️ <b>System Alert:</b> Host tabbed out! Video auto-paused to keep sync.")
                elif not self.is_host:
                    sio.emit('chat_event', "👀 <b>System Alert:</b> Guest tabbed out of the watch party!")
        super().changeEvent(event)
    # ==========================================================

    # ================= TRUE FULLSCREEN & ESC KEY =================
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.chat_widget.show()
            self.top_bar_widget.show()
            self.controls_widget.show()
        else:
            self.chat_widget.hide()
            self.top_bar_widget.hide()
            self.controls_widget.hide()
            self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
        super().keyPressEvent(event)
    # ==========================================================

    # --- UI & MEDIA LOGIC ---
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

    @Slot(int)
    def update_ping_display(self, latency):
        self.ping_label.setText(f"📶 Ping: {latency}ms")
        if latency < 100: self.ping_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; color: green;")
        elif latency < 250: self.ping_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; color: orange;")
        else: self.ping_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; color: red;")

    def send_reaction(self, emoji):
        sio.emit('reaction_event', emoji)
        self.trigger_floating_emoji(emoji)

    @Slot(dict)
    def handle_incoming_reaction(self, data):
        emoji = data.get('emoji')
        sender = data.get('sender')
        self.chat_history.append(f"<span style='color: gray; font-size: 10px;'><i>{sender} reacted {emoji}</i></span>")
        self.trigger_floating_emoji(emoji)

    def trigger_floating_emoji(self, emoji):
        label = QLabel(emoji, self.video_widget)
        label.setStyleSheet("font-size: 48px; background: transparent;")
        label.setAttribute(Qt.WA_TransparentForMouseEvents) 
        label.show()
        
        start_x = random.randint(20, max(20, self.video_widget.width() - 80))
        start_y = self.video_widget.height() - 60
        label.move(start_x, start_y)
        
        anim = QPropertyAnimation(label, b"pos")
        anim.setEndValue(QPoint(start_x, start_y - 250))
        anim.setDuration(2500)
        anim.setEasingCurve(QEasingCurve.OutExpo)
        anim.finished.connect(label.deleteLater)
        anim.start()
        
        self.active_animations.append(anim)
        self.active_animations = [a for a in self.active_animations if a.state() == QPropertyAnimation.State.Running]

    # --- NETWORKING & HOSTING LOGIC ---
    def connect_to_server(self):
        @sio.on('connect')
        def on_connect():
            self.my_sid = sio.get_sid()
            self.chat_history.append("<i>✅ Connected to Global Server!</i>")
            sio.emit('join', {'name': self.username})
            # Trigger the safe UI transition!
            self.connected_signal.emit()

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
            self.ping_signal.emit(latency)

        try: 
            # We run this in a background thread implicitly so it doesn't freeze the loading animation
            sio.connect(self.server_url) 
        except: 
            self.loading_label.setText("⚠️ Server Offline. Please try again later.")
            self.loading_label.setStyleSheet("color: red;")

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
    player = VideoPlayer()
    player.show()
    app.aboutToQuit.connect(sio.disconnect)
    sys.exit(app.exec())
