import sys
import os
import time
import random
import socketio

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QTextEdit,
    QLineEdit,
    QLabel,
    QMessageBox,
    QStackedWidget,
    QSlider,
    QGraphicsOpacityEffect,
    QProgressBar,
    QStackedLayout,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import (
    QUrl,
    Signal,
    Slot,
    Qt,
    QTimer,
    QEvent,
    QPropertyAnimation,
    QPoint,
    QEasingCurve,
    QSequentialAnimationGroup,
    QRect,
)

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

    def __init__(self):
        super().__init__()

        self.server_url = "https://watch-together-6kuy.onrender.com"
        self.username = "Guest"
        self.my_avatar = "👤"
        self.my_color = random.choice(
            ["#FF3366", "#33CCFF", "#00FF99", "#FF9900", "#CC33FF", "#FFFF33"]
        )

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

        self.app_stack = QStackedWidget()
        self.main_layout.addWidget(self.app_stack)

        self.build_login_screen()
        self.build_splash_screen()
        self.build_main_cinema()
        self.app_stack.setCurrentIndex(0)

        # Transition Curtain
        self.curtain = QWidget(self)
        self.curtain.setStyleSheet("background-color: #121212;")
        self.curtain.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.curtain_effect = QGraphicsOpacityEffect(self.curtain)
        self.curtain.setGraphicsEffect(self.curtain_effect)
        self.curtain_effect.setOpacity(0.0)
        self.curtain.hide()

        self.connected_signal.connect(self.transition_to_cinema)

    def resizeEvent(self, event):
        self.curtain.resize(self.size())
        super().resizeEvent(event)

    def animate_stack_transition(self, new_index, callback=None):
        self.curtain.show()
        self.curtain.raise_()
        self.anim_group = QSequentialAnimationGroup()
        fade_in = QPropertyAnimation(self.curtain_effect, b"opacity")
        fade_in.setDuration(350)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_out = QPropertyAnimation(self.curtain_effect, b"opacity")
        fade_out.setDuration(350)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_in.finished.connect(lambda: self.app_stack.setCurrentIndex(new_index))
        fade_out.finished.connect(
            lambda: (self.curtain.hide(), callback() if callback else None)
        )
        self.anim_group.addAnimation(fade_in)
        self.anim_group.addAnimation(fade_out)
        self.anim_group.start()

    # ================= LOGIN & SPLASH =================
    def build_login_screen(self):
        self.login_widget = QWidget()
        layout = QVBoxLayout(self.login_widget)
        layout.setAlignment(Qt.AlignCenter)
        title = QLabel("🍿 WATCH TOGETHER")
        title.setStyleSheet(
            "font-size: 40px; font-weight: bold; color: #E50914; margin-bottom: 10px;"
        )

        avatar_label = QLabel("Choose your Avatar:")
        avatar_layout = QHBoxLayout()
        self.avatar_buttons = []
        for a in ["🥷", "🤖", "👽", "👻", "🤠"]:
            btn = QPushButton(a)
            btn.setStyleSheet(
                "font-size: 30px; padding: 10px; background: transparent; border-radius: 8px;"
            )
            btn.clicked.connect(
                lambda checked, choice=a, b=btn: self.select_avatar(choice, b)
            )
            avatar_layout.addWidget(btn)
            self.avatar_buttons.append(btn)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your Name...")
        self.name_input.setStyleSheet(
            "font-size: 18px; padding: 15px; border-radius: 8px; background-color: #222; color: white;"
        )
        self.name_input.setFixedWidth(400)
        self.name_input.returnPressed.connect(self.start_login_process)

        enter_btn = QPushButton("Enter Cinema")
        enter_btn.setFixedWidth(400)
        enter_btn.setStyleSheet(
            "font-size: 18px; font-weight: bold; padding: 15px; background-color: #E50914; color: white;"
        )
        enter_btn.clicked.connect(self.start_login_process)

        layout.addWidget(title)
        layout.addWidget(avatar_label)
        layout.addLayout(avatar_layout)
        layout.addWidget(self.name_input)
        layout.addWidget(enter_btn)
        self.app_stack.addWidget(self.login_widget)

    def select_avatar(self, choice, button):
        self.my_avatar = choice
        for b in self.avatar_buttons:
            b.setStyleSheet("font-size: 30px; padding: 10px; background: transparent;")
        button.setStyleSheet(
            "font-size: 30px; padding: 10px; background-color: #333; border: 2px solid #E50914; border-radius: 8px;"
        )

    def build_splash_screen(self):
        self.splash_widget = QWidget()
        layout = QVBoxLayout(self.splash_widget)
        layout.setAlignment(Qt.AlignCenter)
        self.welcome_label = QLabel("")
        self.welcome_label.setStyleSheet(
            "font-size: 32px; font-weight: bold; color: white;"
        )
        self.panda_label = QLabel("🐼🍿")
        self.panda_label.setStyleSheet("font-size: 65px; margin-top: 20px;")
        self.loading_label = QLabel("Connecting...")
        self.loading_label.setStyleSheet("font-size: 18px; color: #aaa;")

        self.panda_frames = [
            "🐼      🍿",
            "🐼    🍿",
            "🐼  🍿",
            "😮 🍿",
            "😋🍿",
            "🐼🍿",
        ]
        self.panda_frame_index = 0
        self.panda_timer = QTimer(self)
        self.panda_timer.timeout.connect(self.animate_panda)

        layout.addWidget(self.welcome_label)
        layout.addWidget(self.panda_label)
        layout.addWidget(self.loading_label)
        self.app_stack.addWidget(self.splash_widget)

    def animate_panda(self):
        self.panda_frame_index = (self.panda_frame_index + 1) % len(self.panda_frames)
        self.panda_label.setText(self.panda_frames[self.panda_frame_index])

    def start_login_process(self):
        self.username = self.name_input.text().strip() or "Guest"
        self.welcome_label.setText(f"Welcome to the Cinema, {self.username}.")
        self.animate_stack_transition(
            1, callback=lambda: (self.panda_timer.start(250), self.connect_to_server())
        )

    @Slot()
    def transition_to_cinema(self):
        self.panda_timer.stop()
        self.set_ambient_theme()
        self.animate_stack_transition(
            2, callback=lambda: QTimer.singleShot(100, self.start_ping_tracker)
        )

    # ================= MAIN CINEMA UI =================
    def build_main_cinema(self):
        self.cinema_widget = QWidget()
        cinema_layout = QHBoxLayout(self.cinema_widget)

        self.media_layout = QVBoxLayout()
        # Theme/Top Bar
        self.theme_bar = QHBoxLayout()
        self.light_mode_btn = QPushButton("☀️ Light Mode")
        self.light_mode_btn.clicked.connect(self.set_light_theme)
        self.ambient_mode_btn = QPushButton("🌑 Ambient Mode")
        self.ambient_mode_btn.clicked.connect(self.set_ambient_theme)
        self.theme_bar.addStretch()
        self.theme_bar.addWidget(self.light_mode_btn)
        self.theme_bar.addWidget(self.ambient_mode_btn)
        self.media_layout.addLayout(self.theme_bar)

        self.top_bar = QHBoxLayout()
        self.host_status_label = QLabel("👑 Host: Connecting...")
        self.ping_label = QLabel("📶 Ping: -- ms")
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
        self.media_layout.addLayout(self.top_bar)

        # --- THE FIX: QStackedLayout forces the overlay ON TOP of the video ---
        self.video_container = QWidget()
        self.video_container_layout = QStackedLayout(self.video_container)
        self.video_container_layout.setStackingMode(QStackedLayout.StackAll)

        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")

        self.video_overlay = QWidget()
        self.video_overlay.setStyleSheet("background: transparent;")
        self.video_overlay.setAttribute(
            Qt.WA_TransparentForMouseEvents, False
        )  # Catch clicks here!
        self.video_overlay.installEventFilter(self)

        # Add video first, then overlay, so overlay sits on top
        self.video_container_layout.addWidget(self.video_widget)
        self.video_container_layout.addWidget(self.video_overlay)

        self.media_layout.addWidget(self.video_container, stretch=1)
        # ----------------------------------------------------------------------

        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.set_position)
        self.slider.setEnabled(False)
        self.media_layout.addWidget(self.slider)

        self.controls = QHBoxLayout()
        self.open_btn = QPushButton("📁 Open Local Movie File (.mp4)")
        self.open_btn.clicked.connect(self.open_file)
        self.play_btn = QPushButton("⏯️ Play / Pause")
        self.play_btn.clicked.connect(self.play_pause_clicked)
        self.play_btn.setEnabled(False)
        self.controls.addWidget(self.open_btn)
        self.controls.addWidget(self.play_btn)
        self.media_layout.addLayout(self.controls)
        cinema_layout.addLayout(self.media_layout, stretch=3)

        # Social Panel
        self.social_layout = QVBoxLayout()
        self.hype_bar = QProgressBar()
        self.hype_bar.setFormat("🔥 GLOBAL HYPE: %p%")
        self.hype_bar.setStyleSheet(
            "QProgressBar { border: 2px solid #333; border-radius: 5px; text-align: center; color: white; background: #222; font-weight: bold;} QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffaa00, stop:1 #ff0000); }"
        )
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Chat...")
        self.chat_input.returnPressed.connect(self.send_chat_message)
        self.reaction_bar = QHBoxLayout()
        for e in ["❤️", "😂", "😲", "🔥", "🎉"]:
            btn = QPushButton(e)
            btn.clicked.connect(lambda checked, emoji=e: self.send_reaction(emoji))
            self.reaction_bar.addWidget(btn)

        self.social_layout.addWidget(self.hype_bar)
        self.social_layout.addWidget(self.chat_history)
        self.social_layout.addWidget(self.chat_input)
        self.social_layout.addLayout(self.reaction_bar)
        cinema_layout.addLayout(self.social_layout, stretch=1)

        self.app_stack.addWidget(self.cinema_widget)

        # Media Player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

        # Signals
        self.sync_signal.connect(self.handle_network_sync)
        self.chat_signal.connect(self.handle_network_chat)
        self.file_signal.connect(self.handle_network_file)
        self.host_update_signal.connect(self.handle_host_update)
        self.host_request_signal.connect(self.handle_host_request_dialog)
        self.reaction_signal.connect(self.handle_incoming_reaction)
        self.ping_signal.connect(self.update_ping_display)
        self.laser_signal.connect(self.draw_laser_ping)
        self.hype_signal.connect(lambda v: self.hype_bar.setValue(v))
        self.confetti_signal.connect(self.trigger_confetti_explosion)

    # ================= INTERACTIVE LOGIC =================
    def eventFilter(self, obj, event):
        if obj == self.video_overlay and event.type() == QEvent.MouseButtonPress:
            x_pct = event.position().x() / self.video_overlay.width()
            y_pct = event.position().y() / self.video_overlay.height()
            self.draw_laser_ping({"x": x_pct, "y": y_pct, "color": self.my_color})
            sio.emit("laser_ping", {"x": x_pct, "y": y_pct})
            return True
        return super().eventFilter(obj, event)

    @Slot(dict)
    def draw_laser_ping(self, data):
        # Ensure we draw on the video_overlay
        x_pct, y_pct, color = data["x"], data["y"], data["color"]
        tx = int(x_pct * self.video_overlay.width())
        ty = int(y_pct * self.video_overlay.height())
        ping = QWidget(self.video_overlay)
        ping.show()
        ping.setStyleSheet(
            f"border: 4px solid {color}; border-radius: 25px; background: rgba(255,255,255,50);"
        )
        ping.setGeometry(tx - 25, ty - 25, 50, 50)
        anim = QPropertyAnimation(ping, b"geometry")
        anim.setDuration(800)
        anim.setStartValue(QRect(tx - 25, ty - 25, 50, 50))
        anim.setEndValue(QRect(tx, ty, 0, 0))
        anim.finished.connect(ping.deleteLater)
        anim.start()
        self.active_animations.append(anim)

    @Slot()
    def trigger_confetti_explosion(self):
        # Draw confetti on the overlay
        for _ in range(40):
            e = random.choice(["🎉", "✨", "🔥", "🎊"])
            label = QLabel(e, self.video_overlay)
            label.setStyleSheet("font-size: 35px; background: transparent;")
            label.show()
            sx = self.video_overlay.width() // 2
            sy = self.video_overlay.height() // 2
            label.move(sx, sy)
            ex = sx + random.randint(-500, 500)
            ey = sy + random.randint(-500, 500)
            anim = QPropertyAnimation(label, b"pos")
            anim.setEndValue(QPoint(ex, ey))
            anim.setDuration(random.randint(1000, 2500))
            anim.setEasingCurve(QEasingCurve.OutExpo)
            anim.finished.connect(label.deleteLater)
            anim.start()
            self.active_animations.append(anim)

    # --- THEMES & UI ---
    def set_light_theme(self):
        self.setStyleSheet("background-color: white; color: black;")
        self.cinema_widget.setStyleSheet(
            "QPushButton { background: white; color: black; border: 1px solid #ccc; font-weight: bold; padding: 10px;} QLineEdit, QTextEdit { background: white; color: black; }"
        )
        self.chat_history.append("<i>☀️ Light Mode On</i>")

    def set_ambient_theme(self):
        self.setStyleSheet("background-color: #121212; color: white;")
        self.cinema_widget.setStyleSheet(
            "QPushButton { background: #222; color: white; border: 1px solid #E50914; font-weight: bold; padding: 10px;} QLineEdit, QTextEdit { background: #1a1a1a; color: white; }"
        )
        self.chat_history.append("<i>🌑 Ambient Mode On</i>")

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            [
                w.show()
                for w in [
                    self.chat_widget,
                    self.top_bar_widget,
                    self.controls_widget,
                    self.theme_toolbar_widget,
                ]
            ]
        else:
            self.showFullScreen()
            [
                w.hide()
                for w in [
                    self.chat_widget,
                    self.top_bar_widget,
                    self.controls_widget,
                    self.theme_toolbar_widget,
                ]
            ]

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
        super().keyPressEvent(event)

    # --- MEDIA & NETWORKING ---
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open MP4", "", "Video (*.mp4)")
        if path:
            self.my_filename = os.path.basename(path)
            self.media_player.setSource(QUrl.fromLocalFile(path))
            self.media_player.pause()
            self.chat_history.append(
                f"🎬 Loaded Local File: {self.my_filename}. Ready."
            )
            sio.emit("file_info", {"filename": self.my_filename})

    def play_pause_clicked(self):
        if not self.is_host:
            return
        if self.friend_filename and self.my_filename != self.friend_filename:
            self.chat_history.append(
                "<b style='color: red;'>⛔ Play Blocked: Video mismatch. Both users must load the same file.</b>"
            )
            return
        state = self.media_player.playbackState()
        action = "pause" if state == QMediaPlayer.PlaybackState.PlayingState else "play"
        sio.emit("sync_event", {"action": action, "time": self.media_player.position()})
        self.media_player.pause() if action == "pause" else self.media_player.play()

    def connect_to_server(self):
        @sio.on("connect")
        def on_connect():
            sio.emit(
                "join",
                {
                    "name": self.username,
                    "avatar": self.my_avatar,
                    "color": self.my_color,
                },
            )
            self.connected_signal.emit()

        @sio.on("sync_event")
        def on_sync(data):
            self.sync_signal.emit(data)

        @sio.on("chat_event")
        def on_chat(data):
            self.chat_signal.emit(data)

        @sio.on("file_info")
        def on_file(data):
            self.file_signal.emit(data)

        @sio.on("host_update")
        def on_host(data):
            self.host_update_signal.emit(data)

        @sio.on("reaction_event")
        def on_reac(data):
            self.reaction_signal.emit(data)

        @sio.on("laser_ping")
        def on_laser(data):
            self.laser_signal.emit(data)

        @sio.on("hype_update")
        def on_hype(data):
            self.hype_signal.emit(data)

        @sio.on("confetti_event")
        def on_conf():
            self.confetti_signal.emit()

        @sio.on("pong_client")
        def on_pong():
            self.ping_signal.emit(int((time.time() - self.last_ping_time) * 1000))

        try:
            sio.connect(self.server_url)
        except:
            self.loading_label.setText("⚠️ Offline")

    def send_ping(self):
        self.last_ping_time = time.time()
        sio.emit("ping_server")

    def start_ping_tracker(self):
        self.ping_timer = QTimer(self)
        self.ping_timer.timeout.connect(self.send_ping)
        self.ping_timer.start(2000)

    def update_ping_display(self, l):
        self.ping_label.setText(f"📶 Ping: {l}ms")
        self.ping_label.setStyleSheet(
            f"color: {'green' if l<150 else 'red'}; font-weight: bold;"
        )

    def send_chat_message(self):
        t = self.chat_input.text()
        if t.strip():
            self.chat_history.append(
                f"<b style='color:{self.my_color};'>{self.my_avatar} You:</b> {t}"
            )
            sio.emit("chat_event", t)
            self.chat_input.clear()

    def handle_network_chat(self, d):
        self.chat_history.append(
            f"<b style='color:{d['color']};'>{d['avatar']} {d['sender']}:</b> {d['text']}"
        )

    def send_reaction(self, e):
        sio.emit("reaction_event", e)
        self.trigger_floating_emoji(e)

    def handle_incoming_reaction(self, d):
        self.trigger_floating_emoji(d["emoji"])

    def trigger_floating_emoji(self, e):
        # Draw floating emojis on the overlay
        l = QLabel(e, self.video_overlay)
        l.setStyleSheet("font-size: 48px; background:transparent;")
        l.show()
        sx = random.randint(20, max(20, self.video_overlay.width() - 80))
        sy = self.video_overlay.height() - 60
        l.move(sx, sy)
        a = QPropertyAnimation(l, b"pos")
        a.setEndValue(QPoint(sx, sy - 250))
        a.setDuration(2500)
        a.finished.connect(l.deleteLater)
        a.start()
        self.active_animations.append(a)

    def handle_network_sync(self, d):
        if d["action"] == "seek":
            self.media_player.setPosition(d["time"])
        elif d["action"] == "pause":
            self.media_player.setPosition(d["time"])
            self.media_player.pause()
        elif d["action"] == "play":
            self.media_player.setPosition(d["time"])
            self.media_player.play()

    def handle_network_file(self, d):
        self.friend_filename = d["filename"]
        self.chat_history.append(f"⚠️ Friend loaded: {d['filename']}")

    def handle_host_update(self, d):
        self.is_host = d["host_sid"] == sio.sid
        self.host_status_label.setText(
            f"👑 Host: {'You' if self.is_host else d['host_name']}"
        )
        self.play_btn.setEnabled(self.is_host)
        self.slider.setEnabled(self.is_host)
        self.request_host_btn.setVisible(not self.is_host)

    def request_host_clicked(self):
        sio.emit("request_host")
        self.chat_history.append("<i>🙋 Requested Host...</i>")

    def handle_host_request_dialog(self, d):
        box = QMessageBox(self)
        box.setText(f"{d['requester_name']} wants Host. Grant?")
        yes = box.addButton("Grant", QMessageBox.AcceptRole)
        box.addButton("Deny", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() == yes:
            sio.emit("grant_host", {"new_host_sid": d["requester_sid"]})

    def position_changed(self, p):
        self.slider.setValue(p)

    def duration_changed(self, d):
        self.slider.setRange(0, d)

    def set_position(self, p):
        if self.is_host:
            self.media_player.setPosition(p)
            sio.emit("sync_event", {"action": "seek", "time": p})


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())
