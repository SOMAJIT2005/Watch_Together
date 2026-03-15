import sys
import os
import time
import random
import socketio
import threading 

from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                               QHBoxLayout, QWidget, QFileDialog, QTextEdit, 
                               QLineEdit, QLabel, QMessageBox, QStackedWidget,
                               QSlider, QGraphicsOpacityEffect, QProgressBar)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import QUrl, Signal, Slot, Qt, QTimer, QEvent, QPropertyAnimation, QPoint, QEasingCurve, QSequentialAnimationGroup, QRect

sio = socketio.Client()

class VideoPlayer(QMainWindow):
    sync_signal = Signal(dict)
    chat_signal = Signal(dict)  
    file_signal = Signal(dict)
    host_update_signal = Signal(dict)
    host_request_signal = Signal(dict)
    reaction_signal = Signal(dict)
    ping_signal = Signal(int) 
    connected_signal = Signal() 
    laser_signal = Signal(dict)
    hype_signal = Signal(int)
    confetti_signal = Signal()
    error_signal = Signal(str) 

    def __init__(self):
        super().__init__()
        
        self.server_url = 'https://watch-together-6kuy.onrender.com' 
        self.username = "Guest"
        self.my_avatar = "👤"
        self.my_color = random.choice(["#FF3366", "#33CCFF", "#00FF99", "#FF9900", "#CC33FF", "#FFFF33"])
        
        self.setWindowTitle("Watch Together | CSE 2100 Project")
        self.resize(1100, 650) 
        self.setStyleSheet("QMainWindow { background-color: #121212; } QWidget { color: white; }") 

        self.my_filename = None       
        self.friend_filename = None   
        self.is_host = False
        self.my_sid = None
        self.active_animations = [] 
        self.last_ping_time = 0

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: #121212;")
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.app_stack = QStackedWidget()
        self.main_layout.addWidget(self.app_stack)

        self.build_login_screen()
        self.build_splash_screen()
        self.build_main_cinema()
        self.app_stack.setCurrentIndex(0)

        self.curtain = QWidget(self)
        self.curtain.setStyleSheet("background-color: #121212;") 
        self.curtain.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.curtain_effect = QGraphicsOpacityEffect(self.curtain)
        self.curtain.setGraphicsEffect(self.curtain_effect)
        self.curtain_effect.setOpacity(0.0)
        self.curtain.hide()

        self.setup_network_events()
        self.connected_signal.connect(self.transition_to_cinema)
        self.error_signal.connect(self.handle_connection_error)

    def closeEvent(self, event):
        try: 
            sio.disconnect()
            time.sleep(0.5) 
        except: pass
        os._exit(0) 

    def resizeEvent(self, event):
        self.curtain.resize(self.size())
        super().resizeEvent(event)

    def animate_stack_transition(self, new_index, callback=None):
        self.curtain.show(); self.curtain.raise_() 
        self.anim_group = QSequentialAnimationGroup()
        f_in = QPropertyAnimation(self.curtain_effect, b"opacity")
        f_in.setDuration(350); f_in.setStartValue(0.0); f_in.setEndValue(1.0)
        f_out = QPropertyAnimation(self.curtain_effect, b"opacity")
        f_out.setDuration(350); f_out.setStartValue(1.0); f_out.setEndValue(0.0)
        f_in.finished.connect(lambda: self.app_stack.setCurrentIndex(new_index))
        f_out.finished.connect(lambda: (self.curtain.hide(), callback() if callback else None))
        self.anim_group.addAnimation(f_in); self.anim_group.addAnimation(f_out)
        self.anim_group.start()

    def build_login_screen(self):
        self.login_widget = QWidget()
        self.login_widget.setStyleSheet("background-color: #121212; color: white;") 
        layout = QVBoxLayout(self.login_widget); layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("🍿 WATCH TOGETHER")
        title.setStyleSheet("font-size: 40px; font-weight: bold; color: #E50914; margin-bottom: 20px;")
        
        avatar_layout = QHBoxLayout(); self.avatar_buttons = []
        for a in ["🥷", "🤖", "👽", "👻", "🤠"]:
            btn = QPushButton(a); btn.setStyleSheet("font-size: 30px; padding: 10px; background: transparent; border-radius: 8px;")
            btn.clicked.connect(lambda chk, choice=a, b=btn: self.select_avatar(choice, b))
            avatar_layout.addWidget(btn); self.avatar_buttons.append(btn)
        
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("Enter Name...")
        self.name_input.setStyleSheet("font-size: 18px; padding: 15px; background: #222; color: white; border: 1px solid #444; border-radius: 5px;")
        self.name_input.setFixedWidth(400); self.name_input.returnPressed.connect(self.start_login_process)
        
        go_btn = QPushButton("Enter Cinema"); go_btn.setFixedWidth(400)
        go_btn.setStyleSheet("font-size: 18px; font-weight: bold; padding: 15px; background: #E50914; color: white; border-radius: 5px;")
        go_btn.clicked.connect(self.start_login_process)

        layout.addWidget(title); layout.addLayout(avatar_layout); layout.addWidget(self.name_input); layout.addWidget(go_btn)
        self.app_stack.addWidget(self.login_widget)

    def select_avatar(self, choice, btn):
        self.my_avatar = choice
        for b in self.avatar_buttons: b.setStyleSheet("font-size: 30px; padding: 10px; background: transparent; border-radius: 8px;")
        btn.setStyleSheet("font-size: 30px; padding: 10px; background: #333; border: 2px solid #E50914; border-radius: 8px;")

    def build_splash_screen(self):
        self.splash_widget = QWidget()
        self.splash_widget.setStyleSheet("background-color: #121212;") 
        layout = QVBoxLayout(self.splash_widget); layout.setAlignment(Qt.AlignCenter)
        
        self.welcome_label = QLabel(""); self.welcome_label.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        self.panda_label = QLabel("🐼🍿"); self.panda_label.setStyleSheet("font-size: 65px; margin-top: 20px; color: white;")
        self.loading_label = QLabel("Connecting..."); self.loading_label.setStyleSheet("font-size: 18px; color: #aaa;")
        
        self.panda_frames = ["🐼      🍿", "🐼    🍿", "🐼  🍿", "😮 🍿", "😋🍿", "🐼🍿"]
        self.p_timer = QTimer(self); self.p_timer.timeout.connect(self.animate_panda)
        layout.addWidget(self.welcome_label); layout.addWidget(self.panda_label); layout.addWidget(self.loading_label)
        self.app_stack.addWidget(self.splash_widget)

    def animate_panda(self):
        idx = (self.panda_frames.index(self.panda_label.text()) + 1) % len(self.panda_frames) if self.panda_label.text() in self.panda_frames else 0
        self.panda_label.setText(self.panda_frames[idx])

    def start_login_process(self):
        self.username = self.name_input.text().strip() or "Guest"
        self.welcome_label.setText(f"Welcome to the Cinema, {self.username}.")
        self.animate_stack_transition(1, callback=self.initiate_network)

    def initiate_network(self):
        self.p_timer.start(250) 
        self.server_wait_timer = QTimer(self)
        self.server_wait_timer.setSingleShot(True)
        self.server_wait_timer.timeout.connect(self.show_render_warning)
        self.server_wait_timer.start(4000) 
        threading.Thread(target=self.connect_to_server, daemon=True).start()

    def show_render_warning(self):
        self.loading_label.setText("Waking up Cloud Server...\n(Free tier takes ~50 seconds to boot up. Please wait!)")
        self.loading_label.setStyleSheet("font-size: 16px; color: #ffcc00; margin-top: 10px;")

    @Slot(str)
    def handle_connection_error(self, msg):
        self.p_timer.stop() 
        if hasattr(self, 'server_wait_timer'): self.server_wait_timer.stop()
        self.loading_label.setText(msg)
        self.loading_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff3333; margin-top: 10px;")

    @Slot()
    def transition_to_cinema(self):
        self.p_timer.stop()
        if hasattr(self, 'server_wait_timer'): self.server_wait_timer.stop()
        self.set_ambient_theme()
        self.animate_stack_transition(2, callback=lambda: QTimer.singleShot(100, self.start_ping_tracker))

    def build_main_cinema(self):
        self.cinema_widget = QWidget()
        l = QHBoxLayout(self.cinema_widget)
        self.media_layout = QVBoxLayout()
        
        t_bar = QHBoxLayout()
        self.light_mode_btn = QPushButton("☀️ Light Mode"); self.light_mode_btn.clicked.connect(self.set_light_theme)
        self.ambient_mode_btn = QPushButton("🌑 Ambient Mode"); self.ambient_mode_btn.clicked.connect(self.set_ambient_theme)
        t_bar.addStretch(); t_bar.addWidget(self.light_mode_btn); t_bar.addWidget(self.ambient_mode_btn)
        self.media_layout.addLayout(t_bar)

        top = QHBoxLayout()
        self.host_status_label = QLabel("👑 Host: Connecting..."); self.ping_label = QLabel("📶 Ping: -- ms")
        self.request_host_btn = QPushButton("🙋 Request Host"); self.request_host_btn.clicked.connect(self.request_host_clicked); self.request_host_btn.hide()
        self.fullscreen_btn = QPushButton("⛶ Fullscreen"); self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        top.addWidget(self.host_status_label); top.addStretch(); top.addWidget(self.ping_label); top.addWidget(self.request_host_btn); top.addWidget(self.fullscreen_btn)
        self.media_layout.addLayout(top)

        # --- THE HARDWARE ACCELERATION ANIMATION FIX ---
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background: black;")
        self.media_layout.addWidget(self.video_widget, stretch=1)
        
        # We install the event filter DIRECTLY onto the video player to catch your mouse clicks!
        self.video_widget.installEventFilter(self)
        # -----------------------------------------------

        self.slider = QSlider(Qt.Horizontal); self.slider.sliderMoved.connect(self.set_position); self.slider.setEnabled(False)
        self.media_layout.addWidget(self.slider)

        ctrl = QHBoxLayout()
        self.open_btn = QPushButton("📁 Open Local Movie File (.mp4)"); self.open_btn.clicked.connect(self.open_file)
        self.play_btn = QPushButton("⏯️ Play / Pause"); self.play_btn.clicked.connect(self.play_pause_clicked); self.play_btn.setEnabled(False)
        ctrl.addWidget(self.open_btn); ctrl.addWidget(self.play_btn)
        self.media_layout.addLayout(ctrl)
        l.addLayout(self.media_layout, stretch=3)

        soc = QVBoxLayout()
        self.hype_bar = QProgressBar(); self.hype_bar.setFormat("🔥 GLOBAL HYPE: %p%")
        self.chat_history = QTextEdit(); self.chat_history.setReadOnly(True)
        self.chat_input = QLineEdit(); self.chat_input.setPlaceholderText("Chat..."); self.chat_input.returnPressed.connect(self.send_chat_message)
        reac = QHBoxLayout()
        for e in ["❤️", "😂", "😲", "🔥", "🎉"]:
            b = QPushButton(e); b.clicked.connect(lambda chk, emoji=e: self.send_reaction(emoji))
            reac.addWidget(b)
        soc.addWidget(self.hype_bar); soc.addWidget(self.chat_history); soc.addWidget(self.chat_input); soc.addLayout(reac)
        l.addLayout(soc, stretch=1); self.app_stack.addWidget(self.cinema_widget)

        self.media_player = QMediaPlayer(); self.audio_output = QAudioOutput()
        self.media_player.setVideoOutput(self.video_widget); self.media_player.setAudioOutput(self.audio_output)
        self.media_player.positionChanged.connect(lambda p: self.slider.setValue(p)); self.media_player.durationChanged.connect(lambda d: self.slider.setRange(0, d))

    def setup_network_events(self):
        @sio.on('connect')
        def on_con(): 
            self.my_sid = sio.sid
            sio.emit('join', {'name': self.username, 'avatar': self.my_avatar, 'color': self.my_color})
            self.connected_signal.emit()
            
        @sio.on('sync_event')
        def on_sync(d): self.sync_signal.emit(d)
        @sio.on('chat_event')
        def on_chat(d): self.chat_signal.emit(d)
        @sio.on('file_info')
        def on_file(d): self.file_signal.emit(d)
        @sio.on('host_update')
        def on_host(d): self.host_update_signal.emit(d)
        @sio.on('host_request_received')
        def on_host_req(d): self.host_request_signal.emit(d)
        @sio.on('reaction_event')
        def on_reac(d): self.reaction_signal.emit(d)
        @sio.on('laser_ping')
        def on_laser(d): self.laser_signal.emit(d)
        @sio.on('hype_update')
        def on_hype(d): self.hype_signal.emit(d)
        @sio.on('confetti_event')
        def on_conf(): self.confetti_signal.emit()
        @sio.on('pong_client')
        def on_pong(): self.ping_signal.emit(int((time.time() - self.last_ping_time) * 1000))

        self.sync_signal.connect(self.handle_sync); self.chat_signal.connect(self.handle_chat); self.file_signal.connect(self.handle_file)
        self.host_update_signal.connect(self.handle_host); self.host_request_signal.connect(self.handle_host_dialog)
        self.reaction_signal.connect(self.handle_reac); self.ping_signal.connect(self.update_ping) 
        self.laser_signal.connect(self.draw_laser); self.hype_signal.connect(lambda v: self.hype_bar.setValue(v)); self.confetti_signal.connect(self.trigger_confetti)

    def connect_to_server(self):
        try: 
            sio.connect(self.server_url, wait_timeout=15)
        except Exception as e:
            self.error_signal.emit(f"⚠️ Connection Failed:\n{str(e)}\n\nCheck Render Start Command!")

    def eventFilter(self, obj, ev):
        # Listen for clicks directly on the Video Widget
        if obj == self.video_widget and ev.type() == QEvent.Type.MouseButtonPress:
            x_pct = ev.position().x() / max(1, self.video_widget.width())
            y_pct = ev.position().y() / max(1, self.video_widget.height())
            self.draw_laser({'x': x_pct, 'y': y_pct, 'color': self.my_color})
            sio.emit('laser_ping', {'x': x_pct, 'y': y_pct})
            return True
        return super().eventFilter(obj, ev)

    @Slot(dict)
    def draw_laser(self, d):
        x, y, c = d['x'], d['y'], d['color']
        tx, ty = int(x * self.video_widget.width()), int(y * self.video_widget.height())
        
        # Parent the ping DIRECTLY to the video player, and use a QLabel to ensure CSS borders draw!
        p = QLabel(self.video_widget) 
        p.setStyleSheet(f"border: 4px solid {c}; border-radius: 25px; background: rgba(255,255,255,50);")
        p.setGeometry(tx-25, ty-25, 50, 50)
        p.show() 
        
        a = QPropertyAnimation(p, b"geometry")
        a.setDuration(800); a.setStartValue(QRect(tx-25, ty-25, 50, 50)); a.setEndValue(QRect(tx, ty, 0, 0))
        a.finished.connect(p.deleteLater); a.start(); self.active_animations.append(a)

    @Slot()
    def trigger_confetti(self):
        for _ in range(40):
            # Parent the confetti DIRECTLY to the video player
            l = QLabel(random.choice(["🎉", "✨", "🔥", "🎊"]), self.video_widget)
            l.setStyleSheet("font-size: 35px; background:transparent;")
            l.setAttribute(Qt.WA_TransparentForMouseEvents)
            l.show() 
            
            sx, sy = self.video_widget.width()//2, self.video_widget.height()//2
            l.move(sx, sy)
            ex, ey = sx + random.randint(-500, 500), sy + random.randint(-500, 500)
            
            a = QPropertyAnimation(l, b"pos"); a.setEndValue(QPoint(ex, ey)); a.setDuration(random.randint(1000, 2500)); a.setEasingCurve(QEasingCurve.OutExpo)
            a.finished.connect(l.deleteLater); a.start(); self.active_animations.append(a)

    def trigger_emoji(self, e):
        # Parent the emojis DIRECTLY to the video player
        l = QLabel(e, self.video_widget)
        l.setStyleSheet("font-size: 48px; background:transparent;")
        l.setAttribute(Qt.WA_TransparentForMouseEvents)
        l.show()
        
        sx, sy = random.randint(20, max(20, self.video_widget.width()-80)), self.video_widget.height()-60
        l.move(sx, sy)
        
        a = QPropertyAnimation(l, b"pos"); a.setEndValue(QPoint(sx, sy-250)); a.setDuration(2500); a.finished.connect(l.deleteLater); a.start()
        self.active_animations.append(a)

    def set_light_theme(self):
        self.setStyleSheet("background: #f9f9f9; color: #222;")
        self.cinema_widget.setStyleSheet("""
            QPushButton { background: #ffffff; color: #333; border: 1px solid #ccc; border-radius: 5px; font-weight: bold; padding: 8px;} 
            QPushButton:hover { background: #eee; }
            QLineEdit, QTextEdit { background: #ffffff; color: #111; border: 1px solid #ccc; border-radius: 5px; padding: 5px;}
        """)
        self.request_host_btn.setStyleSheet("background: #E50914; color: white; border: none; border-radius: 5px; font-weight: bold; padding: 8px;")
        self.hype_bar.setStyleSheet("QProgressBar { border: 1px solid #ccc; border-radius: 4px; text-align: center; color: #333; background: #fff; font-weight: bold;} QProgressBar::chunk { background: #E50914; border-radius: 3px; }")
        self.chat_history.append("<i>☀️ Switched to Light Mode</i>")

    def set_ambient_theme(self):
        self.setStyleSheet("background: #121212; color: white;")
        self.cinema_widget.setStyleSheet("""
            QPushButton { background: #2a2a2a; color: white; border: 1px solid #444; border-radius: 5px; font-weight: bold; padding: 8px;} 
            QPushButton:hover { background: #3a3a3a; border: 1px solid #666;}
            QLineEdit, QTextEdit { background: #1a1a1a; color: white; border: 1px solid #333; border-radius: 5px; padding: 5px;}
        """)
        self.request_host_btn.setStyleSheet("background: #E50914; color: white; border: none; border-radius: 5px; font-weight: bold; padding: 8px;")
        self.hype_bar.setStyleSheet("QProgressBar { border: 1px solid #444; border-radius: 4px; text-align: center; color: white; background: #222; font-weight: bold;} QProgressBar::chunk { background: #E50914; border-radius: 3px; }")
        self.chat_history.append("<i>🌑 Switched to Ambient Mode</i>")

    def toggle_fullscreen(self):
        if self.isFullScreen(): 
            self.showNormal(); self.social_panel_visible(True)
        else: 
            self.showFullScreen(); self.social_panel_visible(False)

    def social_panel_visible(self, v): [w.setVisible(v) for w in [self.chat_history, self.chat_input, self.open_btn, self.play_btn, self.light_mode_btn, self.ambient_mode_btn, self.hype_bar]]
    
    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Escape and self.isFullScreen(): self.toggle_fullscreen()
        super().keyPressEvent(ev)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open MP4", "", "Video (*.mp4)")
        if path:
            self.my_filename = os.path.basename(path); self.media_player.setSource(QUrl.fromLocalFile(path)); self.media_player.pause()
            sio.emit('file_info', {'filename': self.my_filename})

    def play_pause_clicked(self):
        if not self.is_host or (self.friend_filename and self.my_filename != self.friend_filename): return
        act = 'pause' if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState else 'play'
        sio.emit('sync_event', {'action': act, 'time': self.media_player.position()})
        self.media_player.pause() if act == 'pause' else self.media_player.play()

    def send_ping(self): self.last_ping_time = time.time(); sio.emit('ping_server')
    def start_ping_tracker(self): self.p_tracker = QTimer(self); self.p_tracker.timeout.connect(self.send_ping); self.p_tracker.start(2000)
    def update_ping(self, l): self.ping_label.setText(f"📶 Ping: {l}ms"); self.ping_label.setStyleSheet(f"color: {'#00ff00' if l<150 else '#ff3333'}; font-weight: bold;")
    
    def send_chat_message(self):
        t = self.chat_input.text()
        if t.strip():
            self.chat_history.append(f"<b style='color:{self.my_color};'>{self.my_avatar} You:</b> {t}")
            sio.emit('chat_event', t); self.chat_input.clear()
            
    def handle_chat(self, d): self.chat_history.append(f"<b style='color:{d['color']};'>{d['avatar']} {d['sender']}:</b> {d['text']}")
    def send_reaction(self, e): sio.emit('reaction_event', e); self.trigger_emoji(e)
    def handle_reac(self, d): self.trigger_emoji(d['emoji'])
    
    def handle_sync(self, d):
        self.media_player.setPosition(d['time'])
        if d['action'] == 'pause': self.media_player.pause()
        elif d['action'] == 'play': self.media_player.play()
    def handle_file(self, d): self.friend_filename = d['filename']; self.chat_history.append(f"⚠️ Friend loaded: {d['filename']}")
    
    def handle_host(self, d):
        self.is_host = (d['host_sid'] == self.my_sid) or (d['host_name'] == self.username)
        self.host_status_label.setText(f"👑 Host: {'You (' + d['host_name'] + ')' if self.is_host else d['host_name']}")
        self.play_btn.setEnabled(self.is_host); self.slider.setEnabled(self.is_host); self.request_host_btn.setVisible(not self.is_host)
        
    def request_host_clicked(self): 
        sio.emit('request_host')
        self.chat_history.append("<i>🙋 Request sent to the current host...</i>")
        
    def handle_host_dialog(self, d):
        box = QMessageBox(self)
        box.setWindowTitle("Host Request")
        box.setText(f"{d['requester_name']} wants to be the Host. Grant control?")
        yes = box.addButton("Grant Control", QMessageBox.AcceptRole)
        box.addButton("Deny", QMessageBox.RejectRole)
        if self.palette().window().color().name() == "#ffffff":
            box.setStyleSheet("background: white; color: black;")
        else:
            box.setStyleSheet("background: #1a1a1a; color: white;")
        box.exec()
        if box.clickedButton() == yes: sio.emit('grant_host', {'new_host_sid': d['requester_sid']})
        
    def set_position(self, p):
        if self.is_host: self.media_player.setPosition(p); sio.emit('sync_event', {'action': 'seek', 'time': p})

if __name__ == "__main__":
    app = QApplication(sys.argv); p = VideoPlayer(); p.show(); sys.exit(app.exec())
