import os
import signal
import logging

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
LOG_FILE = os.path.join(PROJECT_ROOT, "log.txt")

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def set_debug(signum, frame):
    """SIGUSR1 → Passer en DEBUG"""
    logging.getLogger().setLevel(logging.DEBUG)
    for handler in logging.getLogger().handlers:
        handler.setLevel(logging.DEBUG)
    logging.info(">>> LOG LEVEL: DEBUG <<<")


def set_info(signum, frame):
    """SIGUSR2 → Passer en INFO"""
    logging.getLogger().setLevel(logging.INFO)
    for handler in logging.getLogger().handlers:
        handler.setLevel(logging.INFO)
    logging.info(">>> LOG LEVEL: INFO <<<")


# Réduire le bruit des logs Kafka et WebSocket
logging.getLogger("kafka").setLevel(logging.WARNING)
logging.getLogger("kafka.consumer.fetcher").setLevel(logging.CRITICAL)  # Éviter "Fetch cancelled" pendant warmup
logging.getLogger("websocket").setLevel(logging.WARNING)

# Signaux pour changement à chaud (Unix)
try:
    signal.signal(signal.SIGUSR1, set_debug)  # kill -SIGUSR1 <pid> → DEBUG
    signal.signal(signal.SIGUSR2, set_info)  # kill -SIGUSR2 <pid> → INFO
except AttributeError:
    pass  # Windows
