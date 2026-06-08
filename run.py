# run.py
import os
from src.env_utils import load_env

# Load environment variables from .env or .env.example
load_env()

import sys
import logging
from logging.handlers import RotatingFileHandler

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure root logger to write to a rotating logfile
log_path = os.path.join("logs", "app.log")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class StreamToLogger:
    """File-like object that redirects writes to a logger instance."""
    def __init__(self, logger, level=logging.INFO):
        self.logger = logger
        self.level = level

    def write(self, buf):
        if not buf:
            return
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line)

    def flush(self):
        pass

# Redirect stdout / stderr to the logger
sys.stdout = StreamToLogger(logger, logging.INFO)
sys.stderr = StreamToLogger(logger, logging.ERROR)

from src.app_ui import VideoTrimmer
import tkinter as tk


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoTrimmer(root)

    def on_closing():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()