import logging
import sys
import inspect
class LogColors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    INFO = "\033[92m"      # Bright Green
    DEBUG = "\033[96m"     # Bright Cyan
    WARNING = "\033[93m"   # Bright Yellow
    ERROR = "\033[91m"     # Bright Red
    CRITICAL = "\033[95m"  # Magenta

class ColoredSeparatorFormatter(logging.Formatter):
    def format(self, record):
        color = LogColors.RESET
        if record.levelno == logging.INFO:
            color = LogColors.INFO
        elif record.levelno == logging.DEBUG:
            color = LogColors.DEBUG
        elif record.levelno == logging.WARNING:
            color = LogColors.WARNING
        elif record.levelno >= logging.ERROR:
            color = LogColors.ERROR

        log_time = self.formatTime(record, self.datefmt)
        level_name = record.levelname
        location = f"{record.filename}:{record.lineno} - {record.funcName}()"
        message = record.getMessage()

        # Automatically extract local variables from the caller's frame if not explicitly provided
        args_str = "{}"
        try:
            # Walk up frames to find the function scope that called logger
            frame = inspect.currentframe()
            while frame:
                if frame.f_code.co_name == record.funcName:
                    # Filter out large objects like SQLAlchemy sessions or modules if desired
                    filtered_locals = {
                        k: v for k, v in frame.f_locals.items() 
                        if not k.startswith('_') and not callable(v) and type(v).__name__ not in ['Session', 'module', 'SQLiteType']
                    }
                    args_str = str(filtered_locals)
                    break
                frame = frame.f_back
        except Exception:
            pass

        separator = "=" * 50
        formatted_message = (
            f"\n{separator}\n"
            f"{color}{log_time} | [{level_name}] | {location}{LogColors.RESET}\n"
            f"{color}{message}{LogColors.RESET}\n"
            f"{color}args: {args_str}{LogColors.RESET}\n"
            f"{separator}"
        )
        return formatted_message

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        
        formatter = ColoredSeparatorFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger