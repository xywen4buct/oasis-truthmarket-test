# example/log_capture.py
import sys
import logging
from pathlib import Path


class _Tee:
    """把写入同时发到多个流，便于保留控制台输出。"""
    def __init__(self, *streams):
        self._streams = streams

    def write(self, data):
        for s in self._streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass

    def flush(self):
        for s in self._streams:
            try:
                s.flush()
            except Exception:
                pass

    def isatty(self):
        return False


def setup_file_logging(log_path, keep_console: bool = False):
    """
    将 print 与 logging 的全部输出重定向到文件。

    Args:
        log_path: 日志文件路径（str 或 Path）
        keep_console: True 时同时保留控制台输出；False 时控制台静默

    Returns:
        打开的 log_file 对象
    """
    log_path = Path(log_path).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_file = open(log_path, "w", encoding="utf-8", buffering=1)

    # 1) 重定向 print
    if keep_console:
        sys.stdout = _Tee(sys.__stdout__, log_file)
        sys.stderr = _Tee(sys.__stderr__, log_file)
    else:
        sys.stdout = log_file
        sys.stderr = log_file

    # 2) 重定向 logging
    fmt = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    root.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # 已知的库 logger 可能自己挂了 handler，或者 propagate=False，单独处理
    for name in ("social.agent", "social", "oasis.env", "oasis"):
        lg = logging.getLogger(name)
        for h in list(lg.handlers):
            lg.removeHandler(h)
        lg.addHandler(file_handler)
        lg.propagate = False
        lg.setLevel(logging.INFO)

    return log_file