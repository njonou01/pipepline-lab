# Tech Pulse - Bluesky Collector (Streaming Jetstream) | Équipe: UCCNT

import json
import time
import logging
import websocket
import threading
import logger as _
from producer import create_producer, send_message
from config import TOPICS
from utils import remap_content, get_keywords_count, get_remap_count

logger = logging.getLogger("bluesky")
JETSTREAM_URL = "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"

producer = None
topic = None
seen_ids = set()
msg_count = 0


def on_message(ws, message):
    global seen_ids, msg_count
    try:
        data = json.loads(message)
        if data.get("kind") != "commit":
            return

        commit = data.get("commit", {})
        if commit.get("collection") != "app.bsky.feed.post":
            return

        record = commit.get("record", {})
        text = record.get("text", "")
        if not text:
            return

        post_id = f"{data.get('did')}:{commit.get('rkey')}"
        if post_id in seen_ids:
            logger.debug(f"Post déjà vu: {post_id[:20]}...")
            return

        new_content, old_content, original_kw, mapped_kw, categories, categorized, is_remapped = remap_content(text)
        if not mapped_kw:
            logger.debug(f"Aucun keyword trouvé, ignoré")
            return

        post_data = {
            "id": post_id,
            "did": data.get("did"),
            "content": new_content,
            "old_content": old_content,
            "original_keywords": original_kw,
            "mapped_keywords": mapped_kw,
            "categories": categories,
            "categorized_keywords": categorized,
            "is_remapped": is_remapped,
            "created_at": record.get("createdAt"),
            "langs": record.get("langs", []),
            "reply_to": record.get("reply", {}).get("parent", {}).get("uri"),
            "source": "bluesky"
        }

        send_message(producer, topic, post_data, key=post_id)
        seen_ids.add(post_id)
        msg_count += 1

        if len(seen_ids) > 10000:
            seen_ids = set(list(seen_ids)[-5000:])
            logger.debug("Cache nettoyé (5000 gardés)")

    except Exception as e:
        logger.error(f"Erreur traitement message: {e}")


def on_error(ws, error):
    logger.error(f"Erreur WebSocket: {error}")


def on_close(ws, close_status, close_msg):
    logger.warning(f"WebSocket fermé: {close_status}")


def on_open(ws):
    logger.info("Connecté au Jetstream Bluesky")


def connect_jetstream():
    while True:
        try:
            logger.debug(f"Tentative connexion à {JETSTREAM_URL}")
            ws = websocket.WebSocketApp(JETSTREAM_URL, on_open=on_open, on_message=on_message,
                                        on_error=on_error, on_close=on_close)
            ws.run_forever()
        except Exception as e:
            logger.error(f"Erreur connexion: {e}")
        logger.warning("Reconnexion dans 10s...")
        time.sleep(10)


def collect():
    global producer, topic, msg_count
    producer = create_producer()
    topic = TOPICS["bluesky"]

    logger.info("=== Démarrage collector Bluesky (Streaming) ===")
    logger.info(f"Keywords: {get_keywords_count()} | Remapping: {get_remap_count()} mots")

    stream_thread = threading.Thread(target=connect_jetstream, daemon=True)
    stream_thread.start()

    try:
        while True:
            time.sleep(60)
            logger.info(f"[Bluesky] +{msg_count} posts | Cache: {len(seen_ids)}")
            msg_count = 0
    except KeyboardInterrupt:
        logger.warning("Arrêt du collector...")

    producer.close()


if __name__ == "__main__":
    collect()
