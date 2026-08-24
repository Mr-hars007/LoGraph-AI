#!/usr/bin/env python
import os
import sys
import subprocess
import time
import webbrowser
# Add Docker Desktop to system PATH if running on Windows (fallback path matching user environment)
docker_bin = r"C:\Users\hars1\AppData\Local\Programs\DockerDesktop\resources\bin"
if os.path.exists(docker_bin) and docker_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = docker_bin + os.pathsep + os.environ.get("PATH", "")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def check_docker():
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False

def run_cmd(cmd, wait=True):
    print(f"\n> Running: {' '.join(cmd)}")
    try:
        if wait:
            res = subprocess.run(cmd)
            return res.returncode == 0
        else:
            subprocess.Popen(cmd)
            return True
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def select_logs_submenu():
    while True:
        clear_screen()
        print("=== Logoph AI Container Logs Menu ===")
        print("1. All Containers (Follow)")
        print("2. Central Backend (logoph-backend)")
        print("3. AI Service (logoph-ai-service)")
        print("4. Frontend Nginx (logoph-frontend)")
        print("5. Frontend Microservice (ms-fe)")
        print("6. Backend Microservice (ms-be)")
        print("7. Database Microservice (ms-db)")
        print("8. Go Back")
        print("=====================================")
        choice = input("Select a service (1-8): ").strip()
        
        if choice == "8":
            break
            
        service_map = {
            "1": [],
            "2": ["logoph-backend"],
            "3": ["logoph-ai-service"],
            "4": ["logoph-frontend"],
            "5": ["mock-backend-1"],
            "6": ["mock-backend-2"],
            "7": ["mock-backend-3"]
        }
        
        if choice in service_map:
            args = ["docker", "compose", "logs", "-f", "--tail=50"] + service_map[choice]
            try:
                subprocess.run(args)
            except KeyboardInterrupt:
                print("\nLogs stream stopped.")
                time.sleep(1)
        else:
            print("Invalid selection.")
            time.sleep(1)

def select_portals_submenu():
    while True:
        clear_screen()
        print("=== Logoph AI Microservice Portals ===")
        print("1. Open GNN Operations Dashboard (http://localhost:8080)")
        print("2. Open MS FE Portal (http://localhost:8001)")
        print("3. Open MS BE Portal (http://localhost:8002)")
        print("4. Open MS DB Portal (http://localhost:8003)")
        print("5. Go Back")
        print("======================================")
        choice = input("Select an endpoint (1-5): ").strip()
        
        url_map = {
            "1": "http://localhost:8080",
            "2": "http://localhost:8001",
            "3": "http://localhost:8002",
            "4": "http://localhost:8003"
        }
        
        if choice == "5":
            break
        elif choice in url_map:
            print(f"Opening {url_map[choice]} in browser...")
            webbrowser.open(url_map[choice])
            time.sleep(1)
        else:
            print("Invalid selection.")
            time.sleep(1)

def main():
    if not check_docker():
        print("[ERROR] Docker daemon is not running or 'docker' command is unavailable.")
        print("Please launch Docker Desktop and add Docker bin files to your system PATH.")
        sys.exit(1)
        
    while True:
        clear_screen()
        print("=== Logoph AI CLI Automation Manager ===")
        print("1. Start Stack (docker compose up -d)")
        print("2. Stop Stack & Wipe Volumes (docker compose down -v)")
        print("3. Stop Stack (docker compose down)")
        print("4. Rebuild & Start Stack (docker compose up --build -d)")
        print("5. Show Service Status (docker compose ps)")
        print("6. View Service Logs (Submenu)")
        print("7. Access Web Portals & Dashboards (Submenu)")
        print("8. Connect to PostgreSQL CLI Shell")
        print("9. Run E2E Verification Integration Test")
        print("0. Exit")
        print("========================================")
        choice = input("Enter choice (0-9): ").strip()
        
        if choice == "0":
            print("Exiting manager. Goodbye!")
            break
        elif choice == "1":
            run_cmd(["docker", "compose", "up", "-d"])
            input("\nPress Enter to continue...")
        elif choice == "2":
            run_cmd(["docker", "compose", "down", "-v"])
            input("\nPress Enter to continue...")
        elif choice == "3":
            run_cmd(["docker", "compose", "down"])
            input("\nPress Enter to continue...")
        elif choice == "4":
            run_cmd(["docker", "compose", "up", "--build", "-d"])
            input("\nPress Enter to continue...")
        elif choice == "5":
            run_cmd(["docker", "compose", "ps"])
            input("\nPress Enter to continue...")
        elif choice == "6":
            select_logs_submenu()
        elif choice == "7":
            select_portals_submenu()
        elif choice == "8":
            print("\nConnecting to PostgreSQL CLI shell. Type '\\q' to exit.")
            cmd = ["docker", "compose", "exec", "-it", "logoph-database", "psql", "-U", "postgres", "-d", "logoph"]
            try:
                # Need shell=True on windows to execute interactive exec cleanly in cmd/powershell
                subprocess.run(cmd)
            except Exception as e:
                print(f"Error launching PostgreSQL console: {e}")
            input("\nPress Enter to continue...")
        elif choice == "9":
            run_cmd([sys.executable, "test_e2e.py"])
            input("\nPress Enter to continue...")
        else:
            print("Invalid choice. Try again.")
            time.sleep(1)

if __name__ == "__main__":
    main()
