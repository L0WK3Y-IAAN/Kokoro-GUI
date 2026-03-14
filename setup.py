import os
import subprocess
import sys

def run_cmd(cmd):
    """Utility to run shell commands cleanly."""
    print(f"[*] Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main():
    print("[*] Setting up Kokoro TTS Server...")

    # 1. Ensure 'uv' is installed
    # We use 'python -m uv' instead of just 'uv' to completely avoid PATH issues on Windows
    try:
        subprocess.run([sys.executable, "-m", "uv", "--version"], 
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("[+] 'uv' is already installed.")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("[-] 'uv' is not installed. Installing via pip...")
        run_cmd([sys.executable, "-m", "pip", "install", "uv"])

    # 2. Create virtual environment if it doesn't exist
    if not os.path.exists(".venv"):
        print("[*] Creating virtual environment...")
        run_cmd([sys.executable, "-m", "uv", "venv"])
    else:
        print("[+] Virtual environment already exists.")

    # 3. Install/Sync dependencies into the venv (not system Python)
    venv_python = os.path.join(".venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join(".venv", "bin", "python")
    # uv venv does not include pip; some dependencies expect it at runtime
    print("[*] Ensuring pip in venv...")
    run_cmd([sys.executable, "-m", "uv", "pip", "install", "pip", "--python", venv_python])
    print("[*] Installing dependencies...")
    run_cmd([sys.executable, "-m", "uv", "pip", "install", "-r", "requirements.txt", "--python", venv_python])

    # 4. Start the server using the venv we installed into (uv run does not use project .venv by default)
    print("[+] Setup complete! Starting the Flask backend...")
    print("--------------------------------------------------")
    try:
        run_cmd([venv_python, "api_server.py"])
    except KeyboardInterrupt:
        print("\n[*] Server stopped by user.")

if __name__ == "__main__":
    main()
