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
    connected_signal = Signal() 

    def __init__(self):
        super().__init__()
        
        # 🔴 YOUR RENDER URL
        self.server_url = 'https://watch-together-6kuy.onrender.com' 
        
        self.setWindowTitle("Watch Together | CSE 2100 Project")
        self.resize(1100, 650) 
        self.setStyleSheet("background-color: #121212;") 

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
        self.app_stack.setCurrentIndex(0)

        # --- NEW: THE "THEATER CURTAIN" (For lag-free transitions) ---
        self.curtain = QWidget(self)
        self.curtain.setStyleSheet("background-color: #121212;") # Pure black/dark overlay
        self.curtain.resize(self.size())
        self.curtain.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.curtain_effect = QGraphicsOpacityEffect(self.curtain)
        self.curtain.setGraphicsEffect(self.curtain_effect)
        self.curtain_effect.setOpacity(0.0)
        self.curtain.hide()
        # -------------------------------------------------------------

        self.connected_signal.connect(self.transition_to_cinema)

    # Automatically keep the curtain the size of the window
    def resizeEvent(self, event):
        self.curtain.resize(self.size())
        super().resizeEvent(event)

    # --- NEW: LAG-FREE TRANSITION ENGINE ---
    def animate_stack_transition(self, new_index, callback=None):
        self.curtain.show()
        self.curtain.raise_() # Bring black screen to the very front
        
        self.anim_group = QSequentialAnimationGroup()

        # Fade to Black
        fade_in = QPropertyAnimation(self.curtain_effect, b"opacity")
        fade_in.setDuration(350) 
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.InOutQuad)

        # Fade from Black
        fade_out = QPropertyAnimation(self.curtain_effect, b"opacity")
        fade_out.setDuration(350)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InOutQuad)

        # The magic swap that happens while the screen is completely black
        def perform_swap():
            self.app_stack.setCurrentIndex(new_index)

        def finish_transition():
            self.curtain.hide()
            if callback: 
                callback() # Start the heavy internet tasks ONLY after the animation finishes!

        fade_in.finished.connect(perform_swap)
        fade_out.finished.connect(finish_transition)

        self.anim_group.addAnimation(fade_in)
        self.anim_group.addAnimation(fade_out)
        self.anim_group.start()
    # ---------------------------------------

    # ================= STAGE 1: THE LOGIN SCREEN =================
    def build_login_screen(self):
        self.login_widget = QWidget()
        self.login_widget.setStyleSheet("background-color: #121212; color: white;")
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
        self.app_stack.addWidget(self.login_widget) 

    # ================= STAGE 2: THE CINEMATIC SPLASH =================
    def build_splash_screen(self):
        self.splash_widget = QWidget()
        self.splash_widget.setStyleSheet("background-color: #121212; color: white;")
        layout = QVBoxLayout(self.splash_widget)
        layout.setAlignment(Qt.AlignCenter)

        self.welcome_label = QLabel("")
        self.welcome_label.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        self.welcome_label.setAlignment(Qt.AlignCenter)

        # --- THE PANDA POPCORN ANIMATION ---
        self.panda_label = QLabel("🐼🍿")
        self.panda_label.setStyleSheet("font-size: 65px; margin-top: 20px;")
        self.panda_label.setAlignment(Qt.AlignCenter)
        
        self.panda_frames = [
            "🐼      🍿", 
            "🐼    🍿", 
            "🐼  🍿", 
            "😮 🍿", 
            "😋🍿", 
            "🐼🍿"
        ]
        self.panda_frame_index = 0
        self.panda_timer = QTimer(self)
        self.panda_timer.timeout.connect(self.animate_panda)
        # -----------------------------------

        self.loading_label = QLabel("Connecting to Global Server...")
        self.loading_label.setStyleSheet("font-size: 18px; color: #aaaaaa; margin-top: 10px;")
        self.loading_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.welcome_label)
        layout.addWidget(self.panda_label)
        layout.addWidget(self.loading_label)

        self.app_stack.addWidget(self.splash_widget) 

    def animate_panda(self):
        self.panda_frame_index = (self.panda_frame_index + 1) % len(self.panda_frames)
        self.panda_label.setText(self.panda_frames[self.panda_frame_index])

    def start_login_process(self):
        typed_name = self.name_input.text().strip()
        if typed_name: self.username = typed_name
        
        self.setWindowTitle(f"Watch Together - {self.username}")
        self.welcome_label.setText(f"Welcome to the Cinema, {self.username}.")
        
        # Fade to Splash Screen, THEN connect to server so it doesn't lag!
        self.animate_stack_transition(1, callback=self.trigger_network_bootup)

    def trigger_network_bootup(self):
        self.panda_timer.start(250) # Start the popcorn eating!
        self.connect_to_server()

        self.server_wait_timer = QTimer(self)
        self.server_wait_timer.setSingleShot(True)
        self.server_wait_timer.timeout.connect(self.show_render_warning)
        self.server_wait_timer.start(4000) 

    def show_render_warning(self):
        self.loading_label.setText("Waking up Cloud Server...\n(Free tier takes ~50 seconds to boot up. Please wait!)")
        self.loading_label.setStyleSheet("font-size: 16px; color: #ffcc00; margin-top: 10px;")

    @Slot()
    def transition_to_cinema(self):
        self.server_wait_timer.stop() 
        self.panda_timer.stop() # Stop eating popcorn
        self.set_ambient_theme()
        
        # Fade to Cinema UI!
        self.animate_stack_transition(2, callback=self.start_ping_tracker)
        
    def start_ping_tracker(self):
        self.ping_timer = QTimer(self)
        self.ping_timer.timeout.connect(self.send_ping)
        self.ping_timer.start(2000)

    # ================= STAGE 3: THE MAIN CINEMA UI =================
    def build_main_cinema(self):
        self.cinema_widget = QWidget()
        cinema_layout = QHBoxLayout(self.cinema_widget)
        cinema_layout.setContentsMargins(10, 10, 10, 10)

        # --- LEFT PANEL (MEDIA) ---
        self.media_layout = QVBoxLayout()
        
        # Theme Toolbar Wrapper (Light/Ambient switches)
        self.theme_toolbar_widget = QWidget()
        self.theme_toolbar = QHBoxLayout(self.theme_toolbar_widget)
        self.theme_toolbar.setContentsMargins(0, 0, 0, 5)

        self.theme_toolbar.addStretch() 
        self.light_mode_btn = QPushButton("☀️ Light Mode")
        self.light_mode_btn.clicked.connect(self.set_light_theme)
        self.theme_toolbar.addWidget(self.light_mode_btn)

        self.ambient_mode_btn = QPushButton("🌑 Ambient Mode")
        self.ambient_mode_btn.clicked.connect(self.set_ambient_theme)
        self.theme_toolbar.addWidget(self.ambient_mode_btn)
        self.media_layout.addWidget(self.theme_toolbar_widget)

        # Top Bar (Host, Ping, Fullscreen)
        self.top_bar_widget = QWidget()
        self.top_bar = QHBoxLayout(self.top_bar_widget)
        self.top_bar.setContentsMargins(0, 0, 0, 0)

        self.host_status_label = QLabel("👑 Host: Connecting...")
        self.host_status_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        
        self.ping_label = QLabel("📶 Ping: -- ms")
        self.ping_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; color: gray;")

        self.request_host_btn = QPushButton("🙋 Request Host")
        self.request_host_btn.clicked.connect(self.request_host_clicked)
        self.request_host_btn.hide()

        self.fullscreen_btn = QPushButton("⛶ Fullscreen")
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
        self.open_btn.clicked.connect(self.open_file)
        self.controls_layout.addWidget(self.open_btn)

        self.play_btn = QPushButton("⏯️ Play / Pause")
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
        self.chat_layout.addWidget(self.chat_history)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type a message and hit Enter...")
        self.chat_input.returnPressed.connect(self.send_chat_message) 
        self.chat_layout.addWidget(self.chat_input)

        self.reaction_toolbar_widget = QWidget()
        self.reaction_toolbar = QHBoxLayout(self.reaction_toolbar_widget)
        self.reaction_toolbar.setContentsMargins(0, 5, 0, 0)
        emojis = ["❤️", "😂", "😲", "🔥", "🎉"]
        for e in emojis:
            btn = QPushButton(e)
            btn.setStyleSheet("font-size: 20px;")
            btn.clicked.connect(lambda checked, emoji=e: self.send_reaction(emoji))
            self.reaction_toolbar.addWidget(btn)
            
        self.chat_layout.addWidget(self.reaction_toolbar_widget)
        cinema_layout.addWidget(self.chat_widget, stretch=1)

        self.app_stack.addWidget(self.cinema_widget)

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

    # ================= TRUE FULLSCREEN & ESC KEY =================
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.chat_widget.show()
            self.top_bar_widget.show()
            self.controls_widget.show()
            self.theme_toolbar_widget.show() 
        else:
            self.chat_widget.hide()
            self.top_bar_widget.hide()
            self.controls_widget.hide()
            self.theme_toolbar_widget.hide() 
            self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
        super().keyPressEvent(event)

    # --- DYNAMIC THEME ENGINE ---
    def set_light_theme(self):
        self.setStyleSheet("background-color: #ffffff;") 

        light_qss = """
            QWidget { color: black; font-family: 'Segoe UI'; }
            QLabel { background: transparent; }
            QPushButton { 
                padding: 10px; font-weight: bold; background-color: #fff; 
                border: 1px solid #ccc; border-radius: 4px; 
            }
            QPushButton:hover { background-color: #f0f0f0; }
            QPushButton:disabled { color: #888; background-color: #e0e0e0; }
            QTextEdit { background-color: white; border: 1px solid #ccc; border-radius: 4px; color: black; }
            QLineEdit { background-color: white; border: 1px solid #ccc; border-radius: 4px; color: black; padding: 10px; }
            QSlider::groove:horizontal { background: #ddd; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: #E50914; border: 1px solid #c00; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
        """
        emoji_override = "QPushButton { font-size: 20px; padding: 5px; border-radius: 5px; background-color: #e0e0e0; border: none; }"

        self.light_mode_btn.setStyleSheet("background-color: #E50914; color: white; border: none; font-weight: bold; padding: 8px 15px;")
        self.ambient_mode_btn.setStyleSheet("background-color: #ddd; color: black; border: none; font-weight: normal; padding: 8px 15px;")

        self.cinema_widget.setStyleSheet(light_qss)
        self.reaction_toolbar_widget.setStyleSheet(emoji_override) 
        self.chat_history.setStyleSheet("background-color: white; border: 1px solid #ccc; border-radius: 4px; padding: 5px; color: black;")
        self.chat_history.append("<i>☀️ Switched to Light Mode.</i>")

    def set_ambient_theme(self):
        self.setStyleSheet("background-color: #121212;") 

        dark_qss = """
            QWidget { color: white; font-family: 'Segoe UI'; }
            QLabel { background: transparent; color: white;}
            QPushButton { 
                padding: 10px; font-weight: bold; background-color: #222; 
                border: 1px solid #E50914; border-radius: 4px; color: white;
            }
            QPushButton:hover { background-color: #333; }
            QPushButton:disabled { color: #888; background-color: #1a1a1a; border: 1px solid #444; }
            QTextEdit { background-color: #1a1a1a; border: 1px solid #444; border-radius: 4px; color: white; }
            QLineEdit { background-color: #1a1a1a; border: 1px solid #444; border-radius: 4px; color: white; padding: 10px; }
            QSlider::groove:horizontal { background: #333; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: #E50914; border: 1px solid #f00; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
        """
        self.light_mode_btn.setStyleSheet("background-color: #ddd; color: black; border: none; font-weight: normal; padding: 8px 15px;")
        self.ambient_mode_btn.setStyleSheet("background-color: #E50914; color: white; border: none; font-weight: bold; padding: 8px 15px;")

        self.cinema_widget.setStyleSheet(dark_qss)
        self.reaction_toolbar_widget.setStyleSheet("QPushButton { font-size: 20px; }")
        self.chat_history.setStyleSheet("background-color: #1a1a1a; border: 1px solid #444; border-radius: 4px; padding: 5px; color: white;")
        
        self.chat_history.append("<i>🌑 Switched to Ambient Mode.</i>")
    # ----------------------------------

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
            sio.emit('join', {'name': self.username})
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

        try: sio.connect(self.server_url) 
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
            if self.palette().window().color().name() == "#ffffff":
                self.host_status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 14px; padding: 5px;")
            else:
                self.host_status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 14px; padding: 5px; background-color: rgba(255,255,255,10);")
            
            self.play_btn.setEnabled(True)
            self.slider.setEnabled(True)
            self.request_host_btn.hide()
            self.chat_history.append("<i>🎉 You are the Host! You have control.</i>")
        else:
            self.host_status_label.setText(f"👑 Host: {host_name}")
            if self.palette().window().color().name() == "#ffffff":
                 self.host_status_label.setStyleSheet("color: black; font-weight: bold; font-size: 14px; padding: 5px;")
            else:
                 self.host_status_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px; padding: 5px;")
                 
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
        msg_box.setStyleSheet("color: black; background-color: #f0f0f0;")
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
