"""Artifact references, hashing, MIME sniffing, and GRAYFISH sealing."""

from __future__ import annotations

import hashlib
import mimetypes
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Tuple, Union
import magic

from quantum.core.db import execute, execute_one, execute_write, transaction
from quantum.core.ids import new_loot_id, content_hash, file_hash
from quantum.core.env import LOOT_DIR, QCLI_DIR
from quantum.core.grayfish import GRAYFISH

# Initialize MIME types
mimetypes.init()

# Artifact kind categories
ARTIFACT_KINDS = {
    "credential", "cookie", "token", "key", "wallet", "hash",
    "file", "screenshot", "recording", "log", "dump", "export",
    "certificate", "profile", "config", "database", "archive",
    "binary", "script", "payload", "exploit", "loot", "other",
}


@dataclass
class ArtifactRef:
    """Reference to an artifact (file or data blob)."""
    id: str
    device_id: str
    task_id: Optional[str]
    kind: str
    path: str
    size: int
    sha256: str
    mime: str
    sealed: bool = False
    ts: float = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "device_id": self.device_id,
            "task_id": self.task_id,
            "kind": self.kind,
            "path": self.path,
            "size": self.size,
            "sha256": self.sha256,
            "mime": self.mime,
            "sealed": self.sealed,
            "ts": self.ts,
        }

    @property
    def full_path(self) -> Path:
        return LOOT_DIR / self.path

    def exists(self) -> bool:
        return self.full_path.exists()

    def read_bytes(self) -> bytes:
        with open(self.full_path, "rb") as f:
            return f.read()

    def read_text(self, encoding: str = "utf-8") -> str:
        with open(self.full_path, "r", encoding=encoding) as f:
            return f.read()


def detect_mime(path: Union[str, Path], data: Optional[bytes] = None) -> str:
    """Detect MIME type using python-magic with fallback to mimetypes."""
    path = Path(path)

    # Try python-magic first (most accurate)
    try:
        if data is not None:
            mime = magic.from_buffer(data, mime=True)
        else:
            mime = magic.from_file(str(path), mime=True)
        if mime:
            return mime
    except Exception:
        pass

    # Fallback to mimetypes
    mime, _ = mimetypes.guess_type(str(path))
    if mime:
        return mime

    # Fallback by extension
    ext = path.suffix.lower()
    ext_map = {
        ".json": "application/json",
        ".xml": "application/xml",
        ".txt": "text/plain",
        ".log": "text/plain",
        ".pcap": "application/vnd.tcpdump.pcap",
        ".db": "application/x-sqlite3",
        ".sqlite": "application/x-sqlite3",
        ".sqlite3": "application/x-sqlite3",
        ".gz": "application/gzip",
        ".zip": "application/zip",
        ".tar": "application/x-tar",
        ".gfy": "application/octet-stream",  # GRAYFISH sealed
        ".bin": "application/octet-stream",
        ".exe": "application/x-msdownload",
        ".dll": "application/x-msdownload",
        ".so": "application/x-sharedlib",
        ".apk": "application/vnd.android.package-archive",
        ".ipa": "application/octet-stream",
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".csv": "text/csv",
        ".html": "text/html",
        ".js": "application/javascript",
        ".py": "text/x-python",
        ".sh": "application/x-sh",
        ".ps1": "application/x-powershell",
    }
    return ext_map.get(ext, "application/octet-stream")


def register_artifact(
    device_id: str,
    kind: str,
    source_path: Union[str, Path],
    task_id: Optional[str] = None,
    seal: bool = False,
    move: bool = False,
) -> ArtifactRef:
    """Register a file as an artifact, optionally sealing and moving it."""
    source_path = Path(source_path)

    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    # Compute hash and size
    sha256 = file_hash(str(source_path))
    size = source_path.stat().st_size
    mime = detect_mime(source_path)

    # Determine destination path
    artifact_id = new_loot_id(device_id)
    safe_kind = kind.replace("/", "_").replace("\\", "_")
    dest_dir = LOOT_DIR / device_id / safe_kind
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_name = f"{artifact_id}{source_path.suffix}"
    dest_path = dest_dir / dest_name
    relative_path = dest_path.relative_to(LOOT_DIR)

    # Copy or move file
    if move:
        shutil.move(str(source_path), str(dest_path))
    else:
        shutil.copy2(str(source_path), str(dest_path))

    # Seal if requested
    sealed = False
    if seal:
        sealed_path = GRAYFISH.seal_file(dest_path)
        if sealed_path:
            dest_path.unlink()
            dest_path = sealed_path
            relative_path = dest_path.relative_to(LOOT_DIR)
            sealed = True

    # Create artifact record
    artifact = ArtifactRef(
        id=artifact_id,
        device_id=device_id,
        task_id=task_id,
        kind=kind,
        path=str(relative_path),
        size=size,
        sha256=sha256,
        mime=mime,
        sealed=sealed,
        ts=time.time(),
    )

    # Store in database
    with transaction() as conn:
        conn.execute(
            """INSERT INTO artifacts (id, device_id, task_id, kind, path, size, sha256, mime, sealed, ts)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (artifact.id, artifact.device_id, artifact.task_id, artifact.kind,
             artifact.path, artifact.size, artifact.sha256, artifact.mime,
             int(artifact.sealed), artifact.ts)
        )

        # Index in FTS if it's text content
        if mime.startswith("text/") or mime in ("application/json", "application/xml"):
            try:
                if sealed:
                    content = GRAYFISH.unseal_file(dest_path).decode("utf-8", errors="ignore")
                else:
                    content = artifact.read_text()
                conn.execute(
                    "INSERT INTO loot_fts (content, path, device_id, kind) VALUES (?, ?, ?, ?)",
                    (content, artifact.path, device_id, kind)
                )
            except Exception:
                pass

    return artifact


def register_artifact_bytes(
    device_id: str,
    kind: str,
    data: bytes,
    filename: str,
    task_id: Optional[str] = None,
    seal: bool = False,
) -> ArtifactRef:
    """Register raw bytes as an artifact."""
    # Write to temp file first
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        return register_artifact(device_id, kind, tmp_path, task_id, seal, move=True)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def get_artifact(artifact_id: str) -> Optional[ArtifactRef]:
    """Get artifact by ID."""
    row = execute_one(
        "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
    )
    if not row:
        return None
    return ArtifactRef(
        id=row["id"],
        device_id=row["device_id"],
        task_id=row["task_id"],
        kind=row["kind"],
        path=row["path"],
        size=row["size"],
        sha256=row["sha256"],
        mime=row["mime"],
        sealed=bool(row["sealed"]),
        ts=row["ts"],
    )


def get_artifacts_for_device(device_id: str, kind: Optional[str] = None) -> List[ArtifactRef]:
    """Get all artifacts for a device, optionally filtered by kind."""
    if kind:
        rows = execute(
            "SELECT * FROM artifacts WHERE device_id = ? AND kind = ? ORDER BY ts DESC",
            (device_id, kind)
        )
    else:
        rows = execute(
            "SELECT * FROM artifacts WHERE device_id = ? ORDER BY ts DESC",
            (device_id,)
        )
    return [
        ArtifactRef(
            id=r["id"],
            device_id=r["device_id"],
            task_id=r["task_id"],
            kind=r["kind"],
            path=r["path"],
            size=r["size"],
            sha256=r["sha256"],
            mime=r["mime"],
            sealed=bool(r["sealed"]),
            ts=r["ts"],
        )
        for r in rows
    ]


def get_artifacts_for_task(task_id: str) -> List[ArtifactRef]:
    """Get all artifacts produced by a task."""
    rows = execute(
        "SELECT * FROM artifacts WHERE task_id = ? ORDER BY ts DESC",
        (task_id,)
    )
    return [
        ArtifactRef(
            id=r["id"],
            device_id=r["device_id"],
            task_id=r["task_id"],
            kind=r["kind"],
            path=r["path"],
            size=r["size"],
            sha256=r["sha256"],
            mime=r["mime"],
            sealed=bool(r["sealed"]),
            ts=r["ts"],
        )
        for r in rows
    ]


def search_loot_fts(query: str, device_id: Optional[str] = None, kind: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Full-text search over loot using FTS5."""
    sql = "SELECT path, device_id, kind, rank FROM loot_fts WHERE content MATCH ?"
    params: List[Any] = [query]

    if device_id:
        sql += " AND device_id = ?"
        params.append(device_id)
    if kind:
        sql += " AND kind = ?"
        params.append(kind)

    sql += " ORDER BY rank LIMIT ?"
    params.append(limit)

    rows = execute(sql, tuple(params))
    return [dict(r) for r in rows]


def delete_artifact(artifact_id: str, wipe: bool = False) -> bool:
    """Delete an artifact record and optionally wipe the file."""
    artifact = get_artifact(artifact_id)
    if not artifact:
        return False

    # Delete file
    if artifact.exists():
        if wipe:
            # Secure wipe - overwrite with random data
            try:
                size = artifact.full_path.stat().st_size
                with open(artifact.full_path, "wb") as f:
                    f.write(os.urandom(size))
                artifact.full_path.unlink()
            except Exception:
                artifact.full_path.unlink(missing_ok=True)
        else:
            artifact.full_path.unlink(missing_ok=True)

    # Remove from database
    execute_write("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
    execute_write("DELETE FROM loot_fts WHERE path = ?", (artifact.path,))

    return True


def seal_artifact(artifact_id: str) -> bool:
    """Seal an existing artifact with GRAYFISH."""
    artifact = get_artifact(artifact_id)
    if not artifact or artifact.sealed:
        return False

    if not artifact.exists():
        return False

    sealed_path = GRAYFISH.seal_file(artifact.full_path)
    if not sealed_path:
        return False

    artifact.full_path.unlink()
    new_relative = sealed_path.relative_to(LOOT_DIR)

    with transaction() as conn:
        conn.execute(
            "UPDATE artifacts SET path = ?, sealed = 1 WHERE id = ?",
            (str(new_relative), artifact_id)
        )

    return True


def unseal_artifact(artifact_id: str) -> Optional[bytes]:
    """Unseal an artifact and return its contents."""
    artifact = get_artifact(artifact_id)
    if not artifact or not artifact.sealed:
        return None

    if not artifact.exists():
        return None

    return GRAYFISH.unseal_file(artifact.full_path)


def compute_artifact_hashes(path: Union[str, Path]) -> Dict[str, str]:
    """Compute multiple hashes for a file."""
    path = Path(path)
    hashes = {}
    for algo in ("md5", "sha1", "sha256", "sha512"):
        h = hashlib.new(algo)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        hashes[algo] = h.hexdigest()
    return hashes


def verify_artifact_integrity(artifact_id: str) -> bool:
    """Verify artifact file matches recorded hash."""
    artifact = get_artifact(artifact_id)
    if not artifact or not artifact.exists():
        return False

    current_hash = file_hash(str(artifact.full_path))
    return current_hash == artifact.sha256


def get_loot_stats(device_id: Optional[str] = None) -> Dict[str, Any]:
    """Get loot statistics."""
    if device_id:
        rows = execute(
            """SELECT kind, COUNT(*) as count, SUM(size) as total_size
               FROM artifacts WHERE device_id = ? GROUP BY kind""",
            (device_id,)
        )
    else:
        rows = execute(
            """SELECT kind, COUNT(*) as count, SUM(size) as total_size
               FROM artifacts GROUP BY kind"""
        )

    stats = {"total_files": 0, "total_size": 0, "by_kind": {}}
    for r in rows:
        stats["by_kind"][r["kind"]] = {"count": r["count"], "size": r["total_size"]}
        stats["total_files"] += r["count"]
        stats["total_size"] += r["total_size"] or 0

    return stats


import time
from typing import Any, Dict, List, Optional, Union