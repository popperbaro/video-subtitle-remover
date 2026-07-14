"""Lightweight file-based diagnostic logger.

Used to diagnose silent failures (e.g. empty/black output videos) when the
app is launched with pythonw.exe where stdout prints are discarded.

The log file is written to ``<BASE_DIR>/../logs/vsr.log`` by default; call
``set_log_path`` to override. The module is safe to import even if the path
cannot be created (it degrades to a no-op).
"""
import os
import threading
import traceback
from datetime import datetime

from backend.config import BASE_DIR

_LOCK = threading.Lock()
_LOG_PATH = None
_ENABLED = True


def _default_log_path():
    logs_dir = os.path.join(os.path.dirname(BASE_DIR), "logs")
    try:
        os.makedirs(logs_dir, exist_ok=True)
    except Exception:
        return None
    return os.path.join(logs_dir, "vsr.log")


def set_log_path(path):
    global _LOG_PATH
    _LOG_PATH = path


def get_log_path():
    global _LOG_PATH
    if _LOG_PATH is None:
        _LOG_PATH = _default_log_path()
    return _LOG_PATH


def log(*args, **kwargs):
    if not _ENABLED:
        return
    path = get_log_path()
    if not path:
        return
    msg = " ".join(str(a) for a in args)
    if kwargs:
        msg += " " + " ".join(f"{k}={v}" for k, v in kwargs.items())
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    line = f"[{stamp}] [pid={os.getpid()}] {msg}\n"
    try:
        with _LOCK:
            with open(path, "a", encoding="utf-8", errors="replace") as f:
                f.write(line)
    except Exception:
        pass


def log_exception(prefix=""):
    log(prefix + "\n" + traceback.format_exc())
