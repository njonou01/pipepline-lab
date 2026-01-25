import time
import hashlib
import logging
import feedparser
import logger as _
from producer import create_producer, send_message
from config import (
    TOPICS,
    POLL_INTERVAL_RSS,
    RSS_FEEDS,
    KAFKA_BOOTSTRAP_SERVERS,
    CACHE_WARMUP_HOURS,
)
from utils import clean_html
from redis_cache import RedisCache

logger = logging.getLogger("rss")
feedparser.USER_AGENT = "UCCNT-Bot/1.0 (Data Engineering Project; UCCNT Team)"


def get_entry_id(entry):
    unique = entry.get("id") or entry.get("link") or entry.get("title", "")
    return hashlib.md5(unique.encode()).hexdigest()


def parse_feed(url):
    try:
        feed = feedparser.parse(url)
        return feed.entries, feed.feed.get("title", url)
    except Exception as e:
        logger.error(f"Erreur parsing {url}: {e}")
        return [], url


def collect():
    producer = create_producer()
    topic = TOPICS["rss"]
    cache = RedisCache("rss")

    logger.info("=== Démarrage collector RSS (Batch) ===")
    logger.info(f"Feeds: {len(RSS_FEEDS)} | Intervalle: {POLL_INTERVAL_RSS}s")

    hours = CACHE_WARMUP_HOURS.get("rss", 24)
    cache.warmup_from_kafka(topic, KAFKA_BOOTSTRAP_SERVERS, hours)

    while True:
        try:
            new_count = 0
            for feed_url in RSS_FEEDS:
                entries, feed_name = parse_feed(feed_url)
                feed_count = 0

                for entry in entries:
                    entry_id = get_entry_id(entry)
                    if cache.is_seen(entry_id):
                        continue

                    data = {
                        "id": entry_id,
                        "title": clean_html(entry.get("title", "")),
                        "url": entry.get("link"),
                        "author": entry.get("author"),
                        "summary": clean_html(entry.get("summary", ""))[:500],
                        "feed_name": feed_name,
                        "feed_url": feed_url,
                        "published": entry.get("published"),
                        "tags": [t.get("term") for t in entry.get("tags", [])],
                        "source": "rss",
                    }
                    send_message(producer, topic, data, key=entry_id)
                    cache.add(entry_id)
                    feed_count += 1
                    new_count += 1

                logger.debug(f"[{feed_name[:20]}] +{feed_count} articles")
                time.sleep(2)

            logger.info(f"[RSS] +{new_count} nouveaux | Cache: {cache.count()}")

            logger.debug(f"Prochain cycle dans {POLL_INTERVAL_RSS}s")
            time.sleep(POLL_INTERVAL_RSS)

        except KeyboardInterrupt:
            logger.warning("Arrêt du collector...")
            break
        except Exception as e:
            logger.error(f"Erreur dans la boucle: {e}")
            time.sleep(60)

    producer.close()


if __name__ == "__main__":
    collect()
