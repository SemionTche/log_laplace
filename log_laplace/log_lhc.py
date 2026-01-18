import logging
from pathlib import Path
from datetime import date
import sys

_logger_instance = None  # singleton instance

def _log_func(msg, level="info"):
    """Internal log function used by log.info(), log.debug(), etc."""
    global _logger_instance
    if _logger_instance is None:
        raise RuntimeError("Logger not initialized! Call LoggerLHC(app_name, ...) first.")
    
    level = level.lower()
    if level == "debug":
        _logger_instance.debug(msg)
    elif level == "warning":
        _logger_instance.warning(msg)
    elif level == "error":
        _logger_instance.error(msg)
    else:
        _logger_instance.info(msg)


class _LogHelper:
    """Helper object to allow log.info(...), log.debug(...), etc."""
    def info(self, msg): _log_func(msg, level="info")
    def debug(self, msg): _log_func(msg, level="debug")
    def warning(self, msg): _log_func(msg, level="warning")
    def error(self, msg): _log_func(msg, level="error")


log = _LogHelper()


class LoggerLHC:
    """Logger class to handle logs for Laplace apps."""

    def __init__(
        self,
        app_name: str,
        log_root: Path | str | None = None,
        file_level: str = "debug",   # which level to save
        console_level: str = "info", # which level to print
    ):
        global _logger_instance
        if _logger_instance is not None:
            return  # already initialized

        self.app_name = app_name
        self.log_root = Path(log_root or Path.cwd()) / "logs"
        self.date_folder = self.log_root / date.today().isoformat()
        self.date_folder.mkdir(parents=True, exist_ok=True)

        self.log_file = self.date_folder / f"{app_name}.log"
        # self.logger = logging.getLogger()
        # self.logger.setLevel(logging.DEBUG)  # capture everything internally

        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)

        self.logger = logging.getLogger(f"{app_name}")

        # Set up handlers
        self._setup_handlers(file_level, console_level)

        # Redirect Python prints to console handler
        self._capture_prints()

        _logger_instance = self

    def _setup_handlers(self, file_level: str, console_level: str):
        """Setup file and console handlers with independent levels."""
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s", "%Y-%m-%d %H:%M:%S")

        # File handler
        fh = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        fh.setLevel(getattr(logging, file_level.upper(), logging.DEBUG))
        fh.setFormatter(fmt)
        # self.logger.addHandler(fh)
        self.root_logger.addHandler(fh)

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(getattr(logging, console_level.upper(), logging.INFO))
        ch.setFormatter(fmt)
        # self.logger.addHandler(ch)
        self.root_logger.addHandler(ch)

    def _capture_prints(self):
        """Redirect Python prints to console always, but avoid double logging."""
        class StreamToLogger:
            
            def __init__(self, logger, stream=None):
                self.logger = logger
                self.stream = stream or sys.__stdout__  # original stdout/stderr
            
            def write(self, message):
                message = message.rstrip()
                if not message:
                    return
                
                # Write to the original console always
                self.stream.write(message + "\n")
                self.stream.flush()
                
                self.logger.info(message)
                    # Only log to file (skip console handler)
                    # for h in logging.getLogger().handlers:
                    #     if isinstance(h, logging.FileHandler):
                    #         # h.emit(logging.LogRecord(
                    #         #     name=self.logger.name,
                    #         #     level=logging.INFO,
                    #         #     pathname="",
                    #         #     lineno=0,
                    #         #     msg=message,
                    #         #     args=None,
                    #         #     exc_info=None
                    #         # ))
                    #         self.logger.log(logging.INFO, message)
            
            def flush(self):
                if self.stream:
                    self.stream.flush()

        sys.stdout = StreamToLogger(self.root_logger)
        sys.stderr = StreamToLogger(self.root_logger)

    # Shortcut methods
    def info(self, msg): self.logger.info(msg)
    def debug(self, msg): self.logger.debug(msg)
    def warning(self, msg): self.logger.warning(msg)
    def error(self, msg): self.logger.error(msg)
