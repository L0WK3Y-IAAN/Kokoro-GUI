import os
import platform
import shutil
import subprocess
import sys
import time
import webbrowser

# ── helpers ──────────────────────────────────────────────────────────────────

def run_cmd(cmd):
    """Run a command, printing it first. Raises on non-zero exit."""
    print(f"[*] Running: {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True)


def is_windows():
    return os.name == "nt"


def _wait_for_server(port=8000, timeout=120):
    """Poll until the Flask server responds or timeout."""
    try:
        from urllib.request import urlopen
        from urllib.error import URLError
    except ImportError:
        time.sleep(5)
        return
    url = f"http://127.0.0.1:{port}/voices"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urlopen(url, timeout=2)
            return
        except (URLError, OSError):
            time.sleep(0.5)
    raise SystemExit("[!] Server did not become ready in time.")


def venv_python_path():
    """Return the path to the Python binary inside .venv (cross-platform)."""
    if is_windows():
        return os.path.join(".venv", "Scripts", "python.exe")
    return os.path.join(".venv", "bin", "python")


# ── uv installation ───────────────────────────────────────────────────────────

INSTALL_HINTS = {
    "arch":   "sudo pacman -S uv",
    "debian": "pipx install uv  # or: pip install uv",
    "fedora": "pip install uv   # or: pipx install uv",
    "darwin": "brew install uv  # or: pip install uv",
    "win32":  "winget install --id=astral-sh.uv  # or: pip install uv",
}

def get_install_hint():
    p = sys.platform
    if p == "darwin":
        return INSTALL_HINTS["darwin"]
    if p == "win32":
        return INSTALL_HINTS["win32"]
    name = ""
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    name = line.strip().split("=", 1)[1].strip('"').lower()
                    break
    except OSError:
        pass
    if "arch" in name or "manjaro" in name or "endeavour" in name:
        return INSTALL_HINTS["arch"]
    if any(x in name for x in ("debian", "ubuntu", "mint", "pop", "kali")):
        return INSTALL_HINTS["debian"]
    if any(x in name for x in ("fedora", "rhel", "centos", "rocky", "alma")):
        return INSTALL_HINTS["fedora"]
    return "pip install uv   # or visit https://docs.astral.sh/uv/getting-started/installation/"


def ensure_uv():
    """
    Find or install uv, returning the command prefix to invoke it.
    Preference order:
      1. 'uv' already on PATH  (system package, pipx, etc.)
      2. Install via the official installer script (macOS/Linux/Windows)
      3. pip fallback
    Returns a list, e.g. ['uv'] or [sys.executable, '-m', 'uv'].
    """
    if shutil.which("uv"):
        print("[+] 'uv' found on PATH.")
        return ["uv"]

    print("[-] 'uv' not found on PATH. Attempting automatic install...")

    installed = False
    if sys.platform in ("linux", "darwin"):
        curl = shutil.which("curl")
        sh   = shutil.which("sh")
        if curl and sh:
            print("[*] Installing uv via official installer (curl | sh)...")
            try:
                installer = subprocess.run(
                    [curl, "-LsSf", "https://astral.sh/uv/install.sh"],
                    capture_output=True, check=True
                )
                subprocess.run([sh], input=installer.stdout, check=True)
                installed = True
            except subprocess.CalledProcessError as e:
                print(f"[!] Installer failed: {e}")

    elif sys.platform == "win32":
        pwsh = shutil.which("pwsh") or shutil.which("powershell")
        if pwsh:
            print("[*] Installing uv via official installer (PowerShell)...")
            try:
                run_cmd([pwsh, "-Command",
                         "irm https://astral.sh/uv/install.ps1 | iex"])
                installed = True
            except subprocess.CalledProcessError as e:
                print(f"[!] Installer failed: {e}")

    if not installed:
        print("[*] Falling back to: pip install uv")
        base_python = _base_python()
        try:
            run_cmd([base_python, "-m", "pip", "install", "uv"])
            installed = True
        except subprocess.CalledProcessError:
            pass

    # Re-check PATH — installer puts uv in ~/.local/bin or ~/.cargo/bin
    extra_paths = [
        os.path.expanduser("~/.local/bin"),
        os.path.expanduser("~/.cargo/bin"),
    ]
    for ep in extra_paths:
        candidate = os.path.join(ep, "uv.exe" if is_windows() else "uv")
        if os.path.isfile(candidate):
            print(f"[+] Found uv at {candidate}")
            return [candidate]

    if shutil.which("uv"):
        print("[+] 'uv' now available on PATH.")
        return ["uv"]

    try:
        subprocess.run([sys.executable, "-m", "uv", "--version"],
                       check=True, capture_output=True)
        print("[+] 'uv' available as python module.")
        return [sys.executable, "-m", "uv"]
    except subprocess.CalledProcessError:
        pass

    hint = get_install_hint()
    print(f"\n[!] Could not install uv automatically.")
    print(f"    Please install it manually and re-run this script:")
    print(f"    {hint}")
    print(f"    Full docs: https://docs.astral.sh/uv/getting-started/installation/")
    sys.exit(1)


def _base_python():
    """
    Return a system-level Python executable, escaping any active venv.
    Useful as a pip fallback when sys.executable is a stripped venv Python.
    """
    base = getattr(sys, "real_prefix", None) or getattr(sys, "base_prefix", sys.prefix)
    if base == sys.prefix:
        return sys.executable
    for name in ("python3", "python"):
        found = shutil.which(name)
        if found and sys.prefix not in found:
            return found
    return sys.executable


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("[*] Setting up Kokoro TTS Server...")
    print(f"[*] Platform: {platform.system()} {platform.release()} / Python {sys.version.split()[0]}")

    uv = ensure_uv()

    # Create venv with Python 3.12 (spacy/kokoro stack needs it; 3.13+ breaks Pydantic v1)
    if not os.path.exists(".venv"):
        print("[*] Creating virtual environment (Python 3.12)...")
        run_cmd(uv + ["venv", ".venv", "--python", "3.12", "--seed"])
    else:
        py = venv_python_path()
        # Require Python 3.12 (spacy/kokoro break on 3.13+ due to Pydantic v1)
        try:
            result = subprocess.run(
                [py, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                capture_output=True, text=True, check=True
            )
            venv_ver = result.stdout.strip()
            if venv_ver not in ("3.12",):
                print(f"[!] .venv is Python {venv_ver}; kokoro/spacy need 3.12.")
                print("    Remove .venv and re-run this script to create a 3.12 venv.")
                sys.exit(1)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        print("[+] Virtual environment already exists.")
        try:
            subprocess.run([py, "-m", "pip", "--version"],
                           check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("[*] pip missing from existing venv — reseeding...")
            run_cmd(uv + ["pip", "install", "pip", "--seed", "--python", py])

    py = venv_python_path()
    print("[*] Installing dependencies from requirements.txt...")
    run_cmd(uv + ["pip", "install", "-r", "requirements.txt", "--python", py])

    print("[+] Setup complete! Starting the Flask backend...")
    print("--------------------------------------------------")
    server = subprocess.Popen([py, "api_server.py"], cwd=os.path.dirname(os.path.abspath(__file__)) or ".")
    try:
        _wait_for_server(port=8000, timeout=120)
        gui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)) or ".", "web_gui.html")
        if os.path.isfile(gui_path):
            path = os.path.abspath(gui_path).replace("\\", "/")
            webbrowser.open(("file:///" + path) if not path.startswith("/") else ("file://" + path))
            print("[+] Opened web_gui.html in your browser.")
        else:
            print(f"[!] web_gui.html not found at {gui_path}")
        server.wait()
    except KeyboardInterrupt:
        print("\n[*] Server stopped by user.")
        server.terminate()
        server.wait()


if __name__ == "__main__":
    main()
