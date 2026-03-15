# 🎬 Watch Together

<div align="center">

![Watch Together Banner](https://img.shields.io/badge/Watch-Together-E50914?style=for-the-badge&logo=youtube&logoColor=white)

**A synchronized video watching platform for real-time collaboration**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-4.0+-010101?style=flat&logo=socket.io&logoColor=white)](https://socket.io/)
[![PySide6](https://img.shields.io/badge/PySide6-Qt6-41CD52?style=flat&logo=qt&logoColor=white)](https://www.qt.io/)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=flat)](LICENSE)

[Features](#-features) • [Technologies](#-technologies) • [Installation](#-installation) • [User Manual](#-user-manual) • [Architecture](#-architecture) • [Contact](#-contact)

</div>

---

## 📖 Overview

**Watch Together** is a private, cloud-secured application that enables synchronized video playback across multiple users in real-time. Built as a CSE 2100 project, it combines robust backend infrastructure with an intuitive desktop client to create a seamless collaborative viewing experience.

### 🎯 Key Highlights

- 🔐 **Cloud PIN Authentication**: Secure access control with Discord webhook notifications
- 🎭 **Real-time Synchronization**: Perfect playback sync across all connected users
- 💬 **Interactive Chat**: Live messaging with custom avatars and colors
- 👑 **Host Management**: Dynamic host control with transfer capabilities
- 🎨 **Customizable Themes**: Light and Ambient modes for different viewing preferences
- 🎉 **Visual Effects**: Reactions, laser pointers, and confetti animations
- 📊 **Hype Meter**: Track collective excitement levels in real-time

---

## ✨ Features

### 🔒 Security & Authentication

#### **Cloud PIN System**
- **PIN Request Flow**: Users request access by entering their name
- **Discord Notification**: Admin receives instant notification via Discord webhook
- **Email Alert**: Simultaneous notification sent to `somajitdeb2005@gmail.com`
- **Verification**: 6-digit PIN verification with secure session management
- **Local License**: Cached authentication for returning users

**PIN Request Format:**
```
🚨 New Access Request!
👤 User: [Username]
🔑 PIN: [6-digit code]
*Awaiting your approval.*
```

### 🎮 Host Control System

#### **Host Privileges**
- Play/Pause control
- Video seeking (timeline control)
- File selection and loading
- Sync command broadcasting

#### **Host Transfer**
- **Request Host**: Non-host users can request control
- **Grant/Deny Dialog**: Current host receives popup notification
- **Automatic Reassignment**: Host transfers to next user if current host disconnects
- **First-Join Priority**: First user to join becomes initial host

### 🎥 Video Playback Features

#### **Supported Formats**
- MP4, MKV, AVI, MOV, WMV, FLV
- Local file playback only
- Cross-platform codec support via Qt Multimedia

#### **Playback Controls**
- **Keyboard Shortcuts:**
  - `Space`: Play/Pause
  - `→` / `.` / `>`: Skip forward (5-20s based on video length)
  - `←` / `,` / `<`: Skip backward (5-20s based on video length)
  - `Esc`: Exit fullscreen
  - Click anywhere on video: Laser pointer ping

#### **Synchronization**
- Real-time position sync (<50ms latency)
- Play/pause state broadcasting
- File name verification across users
- Automatic conflict detection

### 💬 Social & Interaction Features

#### **Live Chat**
- Custom user avatars (emoji-based)
- Personal color assignment from palette:
  - `#FF3366` (Red), `#33CCFF` (Blue), `#00FF99` (Green)
  - `#FF9900` (Orange), `#CC33FF` (Purple), `#FFFF33` (Yellow)
- System notifications for join/leave events
- Rich HTML formatting support

#### **Reactions & Animations**
- **Reaction Emojis**: 😂, 😍, 🔥, 👏, 😱, 🤔
- **Floating Animations**: Emojis float up with fade-out effect
- **Hype Meter**: Fills by +5% per reaction (max 100%)
- **Confetti Burst**: Triggered at high hype levels
  - 40 animated emojis: 🎉, ✨, 🔥, 🎊, 💯, 🍿

#### **Laser Pointer**
- Click anywhere on video to create expanding circle
- Color-coded per user (matches chat color)
- 1-second fade animation
- Broadcasts to all connected users

### 🎨 Visual Customization

#### **Theme Modes**
1. **Ambient Mode (Default)**
   - Dark background (#121212)
   - Low-eye-strain design
   - Ideal for nighttime viewing

2. **Light Mode**
   - Bright background (#f9f9f9)
   - High-contrast text
   - Daytime-friendly

#### **Fullscreen Mode**
- Hides all UI panels for immersive viewing
- Press `Esc` to exit
- Maintains chat/control history

### 📊 Connection & Monitoring

#### **Network Status**
- **Ping Display**: Real-time latency monitoring
  - Green (<150ms): Excellent connection
  - Red (≥150ms): High latency warning
- **Auto-reconnect**: Handles server sleep/wake cycles
- **Connection Status**: Visual indicators for server state

---

## 🛠 Technologies

### Backend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Flask** | 2.0+ | Web application framework |
| **Flask-SocketIO** | 5.0+ | WebSocket server for real-time communication |
| **Socket.IO** | 4.0+ | Bidirectional event-based communication |
| **Python** | 3.8+ | Core language |
| **Discord Webhooks** | API v10 | Push notifications for admin |

### Frontend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **PySide6** | 6.4+ | Qt6 Python bindings for GUI |
| **Qt Multimedia** | 6.4+ | Video playback engine |
| **Qt Widgets** | 6.4+ | UI components |
| **Socket.IO Client** | 5.0+ | Real-time client communication |

### Infrastructure

| Service | Purpose |
|---------|---------|
| **Render.com** | Cloud hosting for Flask backend |
| **Discord** | Webhook-based notification system |
| **Local Storage** | License caching (AppData/Home directory) |

### Architecture Pattern
- **Client-Server Model**: Centralized sync server with desktop clients
- **Event-Driven**: Socket.IO event emissions for all actions
- **Stateful Sessions**: Per-user session management with SID tracking
- **Broadcasting**: Real-time state synchronization across clients

---

## 📥 Installation

### Prerequisites

**System Requirements:**
- Windows 10/11, macOS 10.14+, or Linux (Ubuntu 20.04+)
- Python 3.8 or higher
- 4GB RAM minimum
- Active internet connection

**Required Python Packages:**
```bash
# Backend dependencies
flask>=2.0.0
flask-socketio>=5.0.0
python-socketio>=5.0.0

# Client dependencies
PySide6>=6.4.0
python-socketio[client]>=5.0.0
```

### Step 1: Clone Repository

```bash
git clone https://github.com/SOMAJIT2005/Watch_Together.git
cd Watch_Together
```

### Step 2: Install Dependencies

#### Backend Setup
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install server dependencies
pip install flask flask-socketio python-socketio
```

#### Client Setup
```bash
# Install client dependencies
pip install PySide6 python-socketio[client]
```

### Step 3: Configure Server (Admin Only)

**Edit `server.py`** (lines 10-11):
```python
DISCORD_WEBHOOK_URL = "your_discord_webhook_url_here"
```

**Get Discord Webhook:**
1. Open Discord → Server Settings → Integrations
2. Create Webhook → Copy URL
3. Paste into `server.py`

### Step 4: Deploy Server

#### Option A: Local Development
```bash
python server.py
# Server runs at http://localhost:10000
```

#### Option B: Render.com (Recommended for Production)
1. Create Render account at [render.com](https://render.com)
2. New Web Service → Connect GitHub repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
   - **Environment**: Python 3
4. Deploy → Note the URL (e.g., `https://watch-together-xxxx.onrender.com`)

### Step 5: Update Client URL

**Edit `client_player.py`** (line 25):
```python
self.server_url = 'https://your-deployed-server-url.onrender.com'
```

### Step 6: Launch Client

```bash
python client_player.py
```

---

## 📚 User Manual

### First-Time Setup

#### 1️⃣ **Application Launch**
When you first open Watch Together, you'll see the Cloud Security screen.

#### 2️⃣ **Request Access PIN**
1. **Enter Your Name**: Type your real name (sent to developer)
2. **Click "Request PIN via Cloud Server"**
3. **Wait for Notification**: Admin receives:
   - Discord notification
   - Email to `somajitdeb2005@gmail.com`

**Example Request:**
```
🚨 New Access Request!
👤 User: John Doe
🔑 PIN: 482915
*Awaiting your approval.*
```

#### 3️⃣ **Enter PIN**
1. Admin sends you the 6-digit PIN (via email/message)
2. Enter PIN in the verification field
3. Click "Verify PIN"
4. Upon success, you'll see the cinema lobby

#### 4️⃣ **Welcome Screen**
- Application displays "Welcome!" splash
- Auto-connects to server (2-3 seconds)
- Transitions to main cinema interface

---

### Main Interface Guide

#### 🎬 **Cinema Screen Layout**

```
┌─────────────────────────────────────────────────────────────┐
│ Watch Together | CSE 2100 Project                          │
├─────────────────────────────────────────────────────────────┤
│ 👑 Host: [Username]           📶 Ping: XXms                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                   VIDEO PLAYBACK AREA                       │
│                  (Click to Laser Pointer)                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ ═══════════════════════════════════ [00:00 / 00:00]        │ ← Timeline
├─────────────────────────────────────────────────────────────┤
│ [Open] [▶️/⏸️] [Light] [Ambient] [Request Host] [Hype Bar]  │
├─────────────────────────────────────────────────────────────┤
│ CHAT HISTORY                    │ REACTION EMOJIS          │
│ System: User joined             │ [😂][😍][🔥]              │
│ User: Hello everyone!           │ [👏][😱][🤔]              │
│ ─────────────────────────────── │                          │
│ [Type message here...]          │                          │
└─────────────────────────────────────────────────────────────┘
```

---

### 🎮 Control Guide

#### **Host User Controls**

**File Management:**
- **Open File**: Click "Open" → Select video file
- **Supported Formats**: MP4, MKV, AVI, MOV, WMV, FLV

**Playback Controls:**
- **Play/Pause Button**: Toggle video playback
- **Timeline Slider**: Drag to seek video position
- **Keyboard Shortcuts**:
  - `Space`: Play/Pause
  - `→`: Skip forward
  - `←`: Skip backward

**Visual Controls:**
- **Light Mode**: Switch to bright theme
- **Ambient Mode**: Switch to dark theme
- **Fullscreen**: Double-click video or use system shortcut

#### **Non-Host User Controls**

**Limited Access:**
- ❌ Cannot play/pause
- ❌ Cannot seek timeline
- ❌ Cannot open files
- ✅ Can request host control
- ✅ Full chat & reaction access
- ✅ Laser pointer enabled

**Request Host:**
1. Click "Request Host" button
2. Wait for current host response
3. If granted, all controls unlock
4. If denied, retry after discussion

---

### 💬 Chat & Social Features

#### **Sending Messages**
1. Type message in chat input field
2. Press `Enter` to send
3. Message broadcasts to all users

**Your messages appear as:**
```
🟢 You: Your message here
```

**Other users appear as:**
```
🔵 Username: Their message here
```

#### **Reaction Emojis**
Click any emoji button to:
- Send reaction to all users
- Trigger floating animation on your screen
- Increase hype meter by +5%
- Broadcast to all connected users

**Available Reactions:**
- 😂 **Laughing** - Comedy moments
- 😍 **Love** - Romantic scenes
- 🔥 **Fire** - Epic sequences
- 👏 **Applause** - Impressive moments
- 😱 **Shocked** - Plot twists
- 🤔 **Thinking** - Confusing parts

#### **Hype Meter**
- **Purpose**: Track collective excitement
- **Increment**: +5% per reaction
- **Maximum**: 100%
- **Visual**: Red progress bar at top
- **Effect**: Confetti burst at high levels

---

### 🎯 Laser Pointer Usage

**Activation:**
- Click anywhere on the video
- Expanding red circle appears (if you're the one clicking)
- Color matches your chat color

**Use Cases:**
- Point out specific details in scene
- Draw attention to easter eggs
- Coordinate viewing with friends
- Non-verbal communication

**Technical Details:**
- 1-second animation duration
- Broadcasts to all users
- No limit on frequency
- Works in fullscreen mode

---

### 🔄 Advanced Features

#### **Multi-User Synchronization**

**Automatic Sync:**
- Host actions broadcast immediately
- Other users receive updates in <50ms
- Position adjustments auto-correct

**Sync Events:**
- Play/Pause state changes
- Timeline seek operations
- File loading notifications

**Conflict Resolution:**
- File name verification before playback
- Warning if users have different files
- Auto-pause on mismatch detection

#### **Connection Management**

**Ping Monitoring:**
- Updates every 2 seconds
- Green: <150ms (excellent)
- Red: ≥150ms (high latency)

**Auto-Reconnect:**
- Handles server restarts
- Survives temporary disconnects
- Retries silently in background

**Server Sleep Mode:**
- Render free tier sleeps after 15min inactivity
- Client detects and shows warning
- Auto-connects when server wakes

---

### 🎨 Customization

#### **Theme Switching**

**Ambient Mode (Default):**
- Dark background (#121212)
- Reduces eye strain
- Best for dark rooms

**Light Mode:**
- Bright background (#f9f9f9)
- High contrast
- Best for daylight viewing

**Toggle Shortcut:**
- Click theme buttons anytime
- Instant UI update
- Preference not saved (resets on restart)

#### **Fullscreen Mode**

**Enter Fullscreen:**
- F11 (Windows/Linux)
- Ctrl+Cmd+F (macOS)
- Double-click video

**Exit Fullscreen:**
- Press `Esc`
- F11 again
- Click restore button

**UI Behavior:**
- Hides chat, controls, and status bar
- Video expands to full screen
- Keyboard shortcuts remain active
- Laser pointer still functional

---

### ⚠️ Troubleshooting

#### **Connection Issues**

**Problem**: "Cloud server is currently waking up"
- **Cause**: Render free tier server sleep
- **Solution**: Wait 15 seconds, click "Request PIN" again
- **Prevention**: Have admin keep server alive during sessions

**Problem**: High ping (red indicator)
- **Cause**: Network congestion or server load
- **Solution**: Check internet connection, close bandwidth-heavy apps
- **Note**: Sync still works but may have slight delays

#### **Playback Issues**

**Problem**: "Friend loaded different file" warning
- **Cause**: Users have different video files
- **Solution**: Host shares file with other users, reload same file
- **Workaround**: Sync will still work but content won't match

**Problem**: Video stuttering or buffering
- **Cause**: Local codec issues or file corruption
- **Solution**: Convert file to MP4 H.264 format, ensure file isn't on slow drive
- **Note**: Not a network issue - affects only your playback

#### **Permission Issues**

**Problem**: Cannot control playback
- **Cause**: You're not the host
- **Solution**: Click "Request Host" and wait for approval
- **Alternative**: Ask current host in chat

**Problem**: "Request Host" button missing
- **Cause**: You ARE the host
- **Verification**: Check if status shows "👑 Host: You ([Name])"

---

## 🏗 Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PySide6 GUI │  │ Qt Multimedia│  │ SocketIO     │      │
│  │  (UI Layer)  │  │ (Video)      │  │ Client       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ WebSocket (Socket.IO)
                            │
┌─────────────────────────────────────────────────────────────┐
│                       SERVER LAYER                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Flask-SocketIO Server                    │   │
│  │  ┌─────────────┐  ┌────────────┐  ┌──────────────┐  │   │
│  │  │ Session Mgmt│  │ Event Router│  │ Broadcast Mgr│  │   │
│  │  └─────────────┘  └────────────┘  └──────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS Webhook
                            │
┌─────────────────────────────────────────────────────────────┐
│                   NOTIFICATION LAYER                         │
│  ┌──────────────┐                 ┌──────────────┐          │
│  │   Discord    │                 │    Email     │          │
│  │   Webhook    │                 │  (Implicit)  │          │
│  └──────────────┘                 └──────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Event Flow Diagram

```
CLIENT A (Host)                 SERVER                  CLIENT B (Guest)
    │                              │                          │
    │──── join ─────────────────→ │                          │
    │                              │ ← session created        │
    │                              │ ← host assignment        │
    │← host_update ───────────────│──── host_update ────────→│
    │                              │                          │
    │──── sync_event (play) ─────→│                          │
    │                              │──── sync_event ─────────→│
    │                              │                          │ ← video plays
    │                              │                          │
    │                              │←──── request_host ───────│
    │← host_request_received ─────│                          │
    │                              │                          │
    │──── grant_host ────────────→│                          │
    │                              │──── host_update ─────────→│
    │                              │                          │ ← becomes host
```

### Security Flow

```
1. Client Launch
   ↓
2. Check Local License (wt_cloud.lic)
   ├─ Exists → Login Screen
   └─ Not Found → Auth Screen
      ↓
3. Silent Connection to Server
   ↓
4. User Requests PIN
   ├─ Name Input → Server
   └─ Server Generates Random 6-digit PIN
      ↓
5. Notification Dispatch
   ├─ Discord Webhook → Admin's Discord
   └─ Server Logs → Email Alert
      ↓
6. Admin Shares PIN with User
   ↓
7. User Enters PIN
   ↓
8. Server Verification
   ├─ Match → Create Local License
   │         → auth_success
   └─ Fail → auth_failed
      ↓
9. Access Granted → Cinema Interface
```

---

## 📡 API Documentation

### Socket.IO Events

#### **Client → Server Events**

| Event | Payload | Description |
|-------|---------|-------------|
| `request_cloud_pin` | `{name: str}` | Request access PIN |
| `verify_cloud_pin` | `{pin: str}` | Verify entered PIN |
| `join` | `{name: str, avatar: str, color: str}` | Join cinema room |
| `sync_event` | `{action: str, time: int}` | Broadcast playback sync |
| `chat_event` | `str` | Send chat message |
| `file_info` | `{filename: str}` | Notify file loaded |
| `reaction_event` | `str` (emoji) | Send reaction |
| `laser_ping` | `{x: float, y: float}` | Send laser pointer |
| `request_host` | None | Request host privileges |
| `grant_host` | `{new_host_sid: str}` | Grant host to user |
| `ping_server` | None | Latency check |

#### **Server → Client Events**

| Event | Payload | Description |
|-------|---------|-------------|
| `pin_request_sent` | None | Confirm PIN requested |
| `auth_success` | None | PIN verified successfully |
| `auth_failed` | None | PIN verification failed |
| `host_update` | `{host_sid: str, host_name: str}` | New host assigned |
| `chat_event` | `{sender: str, avatar: str, color: str, text: str}` | Chat message broadcast |
| `sync_event` | `{action: str, time: int}` | Playback sync command |
| `file_info` | `{filename: str}` | File loaded notification |
| `reaction_event` | `{emoji: str}` | Reaction broadcast |
| `laser_ping` | `{x: float, y: float, color: str}` | Laser pointer broadcast |
| `hype_update` | `int` (0-100) | Hype meter level |
| `host_request_received` | `{requester_sid: str, requester_name: str}` | Host request notification |
| `pong_client` | None | Latency response |

---

## 🔐 Security & Privacy

### Authentication
- **PIN-based Access**: 6-digit random PIN per request
- **Local License Caching**: Stored in OS-specific AppData/Home directory
- **Session Management**: Unique SID per connection
- **No Password Storage**: Stateless authentication

### Data Handling
- **No User Data Storage**: All session data in-memory only
- **No Video Upload**: Local files only, never transmitted
- **Metadata Only**: Only filename and sync data sent to server
- **Discord Webhook**: Admin-only, no user data in logs

### Privacy Considerations
- **Real Name Required**: For PIN request identification
- **IP Address**: Logged by hosting provider (Render.com)
- **Session Tracking**: SID used for connection management
- **Chat History**: Not persisted, session-only

---

## 📞 Contact & Support

### 🔑 PIN Request Contact

**For Access PIN:**
- **Email**: somajitdeb2005@gmail.com
- **Subject**: "Watch Together PIN Request - [Your Name]"
- **Include**: Your real name (as entered in the application)

**Response Time:**
- Active hours: 9 AM - 11 PM IST (UTC+5:30)
- Typical response: Within 15-30 minutes
- Off-hours: Check Discord for faster response

### 🐛 Bug Reports & Feature Requests

**GitHub Issues:**
- Repository: [SOMAJIT2005/Watch_Together](https://github.com/SOMAJIT2005/Watch_Together)
- Use issue templates for bugs
- Tag feature requests appropriately

**Direct Contact:**
- **Developer**: Somajit Deb
- **Email**: somajitdeb2005@gmail.com
- **Project**: CSE 2100 - Computer Engineering

---

## 📄 License

**Proprietary Software** - Private Access Only

This application is a private academic project. Access is granted on a per-user basis via PIN authentication. Unauthorized distribution, modification, or commercial use is prohibited.

For licensing inquiries, contact: somajitdeb2005@gmail.com

---

## 🎓 Academic Context

**Course**: CSE 2100 - Computer Engineering  
**Institution**: [Your University/College Name]  
**Project Type**: Real-time Collaborative Application  
**Semester**: [Semester/Year]  

**Learning Objectives:**
- Real-time communication protocols (WebSocket/Socket.IO)
- Client-server architecture design
- GUI development with Qt framework
- Cloud deployment and DevOps
- User authentication and session management
- Multimedia synchronization algorithms

---

## 🙏 Acknowledgments

**Technologies:**
- Flask & Flask-SocketIO teams
- Qt Company (PySide6)
- Socket.IO community
- Render.com platform

**Inspiration:**
- Discord watch parties
- Netflix Party / Teleparty
- Twitch co-streaming features

---

## 📊 Project Statistics

```
Language Breakdown:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Python         ████████████████████  100%

Files:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
server.py      130 lines
client_player.py   406 lines
icon.ico       Binary asset
Total          536 lines of code
```

---

## 🚀 Future Roadmap

**Planned Features:**
- [ ] Screen sharing integration
- [ ] Voice chat support
- [ ] YouTube/streaming platform sync
- [ ] Playlist management
- [ ] Recording sessions
- [ ] Mobile app (Android/iOS)
- [ ] User statistics dashboard
- [ ] Custom emoji reactions
- [ ] Text-to-speech chat reading
- [ ] Subtitle synchronization

**Known Limitations:**
- Local files only (no streaming URLs)
- Single room per server instance
- No persistent chat history
- Render free tier cold starts

---

<div align="center">

**Built with ❤️ by Somajit Deb**

[⬆ Back to Top](#-watch-together)

</div>
