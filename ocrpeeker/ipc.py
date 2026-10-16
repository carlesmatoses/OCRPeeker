import socket
import struct
import sys
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SOCKET_PATH = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "ocrpeeker.sock"

_HEADER = struct.Struct("!I")
MAX_MESSAGE_BYTES = 64 * 1024 * 1024


class ProtocolError(Exception):
    """Raised when a message on the socket is malformed or truncated."""


def _recv_exactly(conn: socket.socket, n: int) -> bytes | None:
    """Read exactly n bytes.

    Returns None if the peer disconnects before sending anything, which is a
    normal connect-and-close (the daemon liveness probe does this). Raises if
    the peer disconnects part way through, which means a truncated message.
    """
    chunks = []
    remaining = n
    while remaining:
        chunk = conn.recv(min(remaining, 65536))
        if not chunk:
            if remaining == n:
                return None
            raise ProtocolError(f"truncated message: wanted {n} bytes, got {n - remaining}")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def send_message(cmd: str, payload: bytes = b"") -> None:
    body = cmd.encode("utf-8") + b"\n" + payload
    if len(body) > MAX_MESSAGE_BYTES:
        raise ProtocolError(f"message too large: {len(body)} bytes")

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(str(SOCKET_PATH))
            s.sendall(_HEADER.pack(len(body)) + body)
    except (FileNotFoundError, ConnectionRefusedError):
        # No socket, or a stale one left behind by a daemon that died.
        logger.error(f"OCRPeeker daemon is not running (no socket at {SOCKET_PATH})")
        sys.exit(1)


def recv_message(conn: socket.socket) -> tuple[str, bytes] | None:
    """Read one message. Returns None if the peer connected and closed without sending."""
    header = _recv_exactly(conn, _HEADER.size)
    if header is None:
        return None

    (length,) = _HEADER.unpack(header)
    if length > MAX_MESSAGE_BYTES:
        raise ProtocolError(f"declared message size {length} exceeds limit")

    body = _recv_exactly(conn, length)
    if body is None:
        raise ProtocolError("header received but no body followed")

    cmd, _, payload = body.partition(b"\n")
    return cmd.decode("utf-8"), payload
