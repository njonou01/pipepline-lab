import json
import time
import logging
import hashlib
import websocket
import threading
import logger as _
from producer import create_producer, send_message
from config import TOPICS, NOSTR_RELAYS, KAFKA_BOOTSTRAP_SERVERS, CACHE_WARMUP_HOURS
from utils import remap_content, get_keywords_count, get_remap_count
from redis_cache import RedisCache

logger = logging.getLogger("nostr")

producer = None
topic = None
cache = None
first_run = True
msg_count = 0


def on_message(ws, message):
    global cache, msg_count
    try:
        data = json.loads(message)
        if data[0] == "EVENT":
            event = data[2]
            event_id = event.get("id")

            if cache.is_seen(event_id):
                logger.debug(f"Event déjà vu: {event_id[:16]}...")
                return

            content = event.get("content", "")
            (
                new_content,
                old_content,
                original_kw,
                mapped_kw,
                categories,
                categorized,
                is_remapped,
            ) = remap_content(content)

            if not mapped_kw:
                logger.debug("Aucun keyword trouvé, ignoré")
                return

            post_data = {
                "id": event_id,
                "pubkey": event.get("pubkey"),
                "content": new_content,
                "old_content": old_content,
                "original_keywords": original_kw,
                "mapped_keywords": mapped_kw,
                "categories": categories,
                "categorized_keywords": categorized,
                "is_remapped": is_remapped,
                "created_at": event.get("created_at"),
                "kind": event.get("kind"),
                "tags": event.get("tags", []),
                "source": "nostr",
            }

            send_message(producer, topic, post_data, key=event_id)
            cache.add(event_id)
            msg_count += 1

    except Exception as e:
        logger.error(f"Erreur traitement message: {e}")


def on_error(ws, error):
    logger.error(f"Erreur WebSocket: {error}")


def on_close(ws, close_status, close_msg):
    logger.warning(f"WebSocket fermé: {close_status}")


def on_open(ws):
    global first_run
    logger.debug("Connecté au relay")
    limit = 500 if first_run else 100
    subscription = json.dumps(
        [
            "REQ",
            hashlib.md5(str(time.time()).encode()).hexdigest()[:16],
            {"kinds": [1], "limit": limit},
        ]
    )
    ws.send(subscription)
    first_run = False


def connect_relay(relay_url):
    while True:
        try:
            logger.debug(f"Connexion à {relay_url}")
            ws = websocket.WebSocketApp(
                relay_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            ws.run_forever()
        except Exception as e:
            logger.error(f"Erreur connexion {relay_url}: {e}")
        logger.warning(f"Reconnexion {relay_url} dans 30s...")
        time.sleep(30)


def collect():
    global producer, topic, cache, msg_count
    producer = create_producer()
    topic = TOPICS["nostr"]
    cache = RedisCache("nostr")

    logger.info("=== Démarrage collector Nostr (Streaming) ===")
    logger.info(
        f"Keywords: {get_keywords_count()} | Remapping: {get_remap_count()} mots"
    )
    logger.info(f"Relays: {len(NOSTR_RELAYS)}")

    hours = CACHE_WARMUP_HOURS.get("nostr", 24)
    cache.warmup_from_kafka(topic, KAFKA_BOOTSTRAP_SERVERS, hours)

    for relay in NOSTR_RELAYS:
        t = threading.Thread(target=connect_relay, args=(relay,), daemon=True)
        t.start()
        time.sleep(1)

    try:
        while True:
            time.sleep(60)
            logger.info(f"[Nostr] +{msg_count} events | Cache: {cache.count()}")
            msg_count = 0
    except KeyboardInterrupt:
        logger.warning("Arrêt du collector...")

    producer.close()


if __name__ == "__main__":
    collect()
