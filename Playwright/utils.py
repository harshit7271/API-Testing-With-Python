import logging
import colorama


def setup_logger():
    """Initializes and configures the custom colored logger."""
    colorama.init(autoreset=True, strip=False)

    class ColoredFormatter(logging.Formatter):
        COLORS = {
            logging.DEBUG: "\033[36m",
            logging.INFO: "\033[32m",
            logging.WARNING: "\033[33;1m",
            logging.ERROR: "\033[31;1m",
            logging.CRITICAL: "\033[41;37;1m",
        }
        RESET = "\033[0m"

        def format(self, record):
            log_color = self.COLORS.get(record.levelno, "")
            prefix = ""
            if record.levelno == logging.ERROR:
                prefix = "❌ "
            elif record.levelno == logging.WARNING:
                prefix = "⚠ "
            elif record.levelno == logging.INFO:
                prefix = "✅ "
            elif record.levelno == logging.CRITICAL:
                prefix = "🚨 "
            message = super().format(record)
            return f"{log_color}{prefix}{message}{self.RESET}"

    log_format = '%(asctime)s [%(levelname)s] [%(lineno)d] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    file_handler = logging.FileHandler(
        "automation_results.log", mode='w', encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        log_format, datefmt=date_format))

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        ColoredFormatter(log_format, datefmt=date_format))

    logging.basicConfig(level=logging.INFO, handlers=[
                        file_handler, console_handler])
