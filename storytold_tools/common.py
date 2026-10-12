"""Bounded JSON and conservative local file operations.

These checks reduce mistakes; they do not replace OS isolation. Ancestor checks
are intentionally strict, including existing symlinks and Windows reparse points.
A concurrently hostile process running as the same user remains outside our
security guarantee. Work only in private, trusted parent directories.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any

MAX_JSON = 8 * 1024 * 1024
MAX_FILE = 512 * 1024 * 1024
ROOT = Path(__file__).resolve().parent.parent
IS_WINDOWS = os.name == 'nt'

class StorytoldError(ValueError):
    """Expected validation/operation failure, safe for a local CLI diagnostic."""

def require(condition: object, message: str) -> None:
    if not condition:
        raise StorytoldError(message)

def encoded(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for k, v in pairs:
        require(k not in result, f'duplicate JSON key: {k}')
        result[k] = v
    return result

def _finite_float(value: str) -> float:
    result = float(value)
    require(math.isfinite(result), 'JSON floating-point range exceeded')
    return result


def parse_json(data: bytes, limit: int = MAX_JSON) -> Any:
    require(len(data) <= limit, 'JSON byte limit exceeded')
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=_pairs, parse_float=_finite_float,
                          parse_constant=lambda s: (_ for _ in ()).throw(StorytoldError(f'invalid JSON number: {s}')))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise StorytoldError('invalid or excessively nested UTF-8 JSON') from exc

def keys(value: Any, required: set[str], optional: set[str] | None = None, label: str = 'object') -> dict:
    require(isinstance(value, dict), f'{label} must be an object')
    require(required <= set(value) <= required | (optional or set()), f'{label} has missing or unknown fields')
    return value

def text(value: Any, label: str, limit: int = 512) -> str:
    require(isinstance(value, str) and 0 < len(value) <= limit, f'{label} must be non-empty text, <= {limit} characters')
    require(not any(ord(c) < 32 or ord(c) == 127 for c in value), f'{label} contains control characters')
    return value

def sha(value: Any) -> str:
    require(isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value), 'expected a lowercase SHA-256 digest')
    return value

def absolute(path: str | Path) -> Path:
    value = text(str(path), 'path', 4096)
    require(not value.startswith(('//', '\\\\')), 'network/UNC paths are not supported')
    result = Path(value)
    require(result.is_absolute(), 'an absolute path is required')
    require('..' not in result.parts, 'path traversal is not allowed')
    # Do not resolve before checking: resolution would hide symlink components.
    for node in [*reversed(result.parents), result]:
        try:
            st = node.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(st.st_mode), f'symlink path is not allowed: {node}')
        require(not getattr(st, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400),
                f'reparse/junction path is not allowed: {node}')
    return result

def local(path: str | Path) -> Path:
    """Resolve CLI-relative names without concealing existing symlinks."""
    p = Path(path)
    return absolute(p if p.is_absolute() else Path.cwd() / p)

def directory(path: str | Path) -> Path:
    p = absolute(path)
    require(p.is_dir(), f'missing directory: {p}')
    return p

def regular(path: str | Path, *, multiple_links: bool = True) -> Path:
    p = absolute(path)
    st = p.stat()
    require(stat.S_ISREG(st.st_mode), f'not a regular file: {p}')
    require(multiple_links or st.st_nlink == 1, f'hard-linked file is not allowed: {p}')
    return p

def snapshot(path: str | Path, *, limit: int = MAX_FILE, body: bool = False) -> tuple[str, int, bytes | None]:
    p = regular(path)
    # Windows os.open defaults to CRT text mode (CRLF/Ctrl-Z translation); hashes need raw bytes.
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    with os.fdopen(os.open(p, flags), 'rb') as f:
        before = os.fstat(f.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'file type or byte limit rejected')
        h = hashlib.sha256(); total = 0; chunks = []
        while chunk := f.read(1024 * 1024):
            total += len(chunk)
            require(total <= limit, 'file byte limit exceeded during read')
            h.update(chunk)
            if body: chunks.append(chunk)
        after = os.fstat(f.fileno())
        current = p.stat()
        require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns) ==
                (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns), 'file changed during read')
        require((current.st_dev,current.st_ino) == (after.st_dev,after.st_ino), 'file replaced during read')
        require(total == before.st_size, 'incomplete file read')
        return h.hexdigest(), total, b''.join(chunks) if body else None

def load_json(path: str | Path) -> Any:
    return parse_json(snapshot(absolute(path),limit=MAX_JSON,body=True)[2] or b'')

def child(root: Path, relative: str) -> Path:
    text(relative, 'relative path', 4096)
    require('\\' not in relative and ':' not in relative, 'portable relative paths must use forward slashes, without drives')
    parts = relative.split('/')
    require(all(p not in {'','.', '..'} for p in parts), 'invalid relative path')
    candidate = absolute(root.joinpath(*parts))
    require(candidate.is_relative_to(root), 'path escapes root')
    return candidate

def create_new(path: Path, data: bytes, mode: int = 0o600) -> Path:
    """Publish a new file without replacement using a same-directory hard link.

    No rename/replace fallback: if atomic no-clobber publication is unsupported,
    fail rather than silently weaken protection. POSIX local filesystems and
    NTFS normally support this operation; target filesystem testing is required.
    """
    p = absolute(path); directory(p.parent)
    require(not p.exists(), f'refusing to overwrite existing file: {p}')
    fd, name = tempfile.mkstemp(prefix='.storytold-write-', dir=p.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        # A Windows read-only attribute affects every hard link. Set it only
        # after removing the temporary name, otherwise unlink can fail.
        if not IS_WINDOWS:
            tmp.chmod(mode)
        os.link(tmp, p, follow_symlinks=False)
    finally:
        tmp.unlink(missing_ok=True)
    if IS_WINDOWS:
        p.chmod(mode)
    return p
