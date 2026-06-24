import socket
import sys
import os
from pathlib import Path

SOCKET_PATH = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "ocrpeeker.sock"


def send(cmd: str):
    if not SOCKET_PATH.exists():
        print(f"OCRPeeker daemon is not running (no socket at {SOCKET_PATH})", file=sys.stderr)
        sys.exit(1)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(str(SOCKET_PATH))
        s.sendall(cmd.encode())


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "capture"
    if cmd not in ("capture", "quit", "toggle"):
        print(f"Unknown command: {cmd}. Use 'capture', 'toggle' or 'quit'.", file=sys.stderr)
        sys.exit(1)
    send(cmd)


if __name__ == "__main__":
    main()
