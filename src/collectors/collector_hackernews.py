import time
import requests
import logging
import logger as _
from producer import create_producer, send_message
from config import TOPICS, POLL_INTERVAL_HN, KAFKA_BOOTSTRAP_SERVERS, CACHE_WARMUP_HOURS
from utils import clean_html
from redis_cache import RedisCache

logger = logging.getLogger("hackernews")
HN_API = "https://hacker-news.firebaseio.com/v0"
HN_ENDPOINTS = {
    "topstories": "top",
    "newstories": "new",
    "beststories": "best",
    "askstories": "ask",
    "showstories": "show",
}


def get_stories(endpoint):
    try:
        resp = requests.get(f"{HN_API}/{endpoint}.json", timeout=10)
        return resp.json()
    except Exception as e:
        logger.error(f"Erreur récupération {endpoint}: {e}")
        return []


def get_story(story_id):
    try:
        resp = requests.get(f"{HN_API}/item/{story_id}.json", timeout=10)
        return resp.json()
    except Exception as e:
        logger.debug(f"Erreur récupération story {story_id}: {e}")
        return None


def collect():
    producer = create_producer()
    topic = TOPICS["hackernews"]
    cache = RedisCache("hackernews")

    logger.info("=== Démarrage collector Hacker News (Batch) ===")
    logger.info(f"Endpoints: {len(HN_ENDPOINTS)} | Intervalle: {POLL_INTERVAL_HN}s")

    hours = CACHE_WARMUP_HOURS.get("hackernews", 24)
    cache.warmup_from_kafka(topic, KAFKA_BOOTSTRAP_SERVERS, hours)

    while True:
        try:
            total_new = 0
            for endpoint, story_type in HN_ENDPOINTS.items():
                story_ids = get_stories(endpoint)
                new_count = 0

                for story_id in story_ids:
                    if cache.is_seen(story_id):
                        continue

                    story = get_story(story_id)
                    if story and story.get("type") == "story":
                        data = {
                            "id": story.get("id"),
                            "title": story.get("title"),
                            "url": story.get("url"),
                            "text": clean_html(story.get("text", "")),
                            "author": story.get("by"),
                            "score": story.get("score"),
                            "comments": story.get("descendants", 0),
                            "timestamp": story.get("time"),
                            "story_type": story_type,
                            "source": "hackernews",
                        }
                        send_message(producer, topic, data, key=str(story_id))
                        cache.add(story_id)
                        new_count += 1

                    time.sleep(0.2)

                logger.debug(f"[{story_type}] +{new_count} stories")
                total_new += new_count

            logger.info(f"[HackerNews] +{total_new} nouvelles | Cache: {cache.count()}")

            logger.debug(f"Prochain cycle dans {POLL_INTERVAL_HN}s")
            time.sleep(POLL_INTERVAL_HN)

        except KeyboardInterrupt:
            logger.warning("Arrêt du collector...")
            break
        except Exception as e:
            logger.error(f"Erreur dans la boucle: {e}")
            time.sleep(60)

    producer.close()


if __name__ == "__main__":
    collect()
