import time
import requests
import logging
import logger as _
from producer import create_producer, send_message
from config import (
    TOPICS,
    POLL_INTERVAL_SO,
    STACKOVERFLOW_TAGS_HIGH,
    STACKOVERFLOW_TAGS_MEDIUM,
    STACKOVERFLOW_TAGS_LOW,
    SO_BATCH_SIZE,
    STACKOVERFLOW_KEY,
    KAFKA_BOOTSTRAP_SERVERS,
    CACHE_WARMUP_HOURS,
)
from utils import clean_html
from redis_cache import RedisCache

logger = logging.getLogger("stackoverflow")
SO_API = "https://api.stackexchange.com/2.3"

rotation_state = {"cycle": 0, "medium_index": 0, "low_index": 0}


def get_current_tags():
    """
    Sélectionne les tags à scanner pour ce cycle avec rotation intelligente.

    Stratégie optimisée pour 100 tags/cycle:
    - HIGH: Toujours inclus (26 tags)
    - MEDIUM: Rotation par batch de 40 tags
    - LOW: Rotation par batch de 34 tags

    Total: ~100 tags/cycle au lieu de 300+
    """
    tags = list(STACKOVERFLOW_TAGS_HIGH)

    medium_batch_size = 40
    if rotation_state["cycle"] % 2 == 0:
        start_idx = rotation_state["medium_index"]
        medium_tags = STACKOVERFLOW_TAGS_MEDIUM[start_idx:start_idx + medium_batch_size]
        tags.extend(medium_tags)
        rotation_state["medium_index"] = (start_idx + medium_batch_size) % len(STACKOVERFLOW_TAGS_MEDIUM)

    low_batch_size = 34
    if rotation_state["cycle"] % 5 == 0:
        start_idx = rotation_state["low_index"]
        low_tags = STACKOVERFLOW_TAGS_LOW[start_idx:start_idx + low_batch_size]
        tags.extend(low_tags)
        rotation_state["low_index"] = (start_idx + low_batch_size) % len(STACKOVERFLOW_TAGS_LOW)

    rotation_state["cycle"] += 1

    return tags[:SO_BATCH_SIZE]


def get_questions(tag, page=1, page_size=100):
    try:
        params = {
            "order": "desc",
            "sort": "creation",
            "tagged": tag,
            "site": "stackoverflow",
            "pagesize": page_size,
            "page": page,
            "filter": "withbody",
            "key": STACKOVERFLOW_KEY,
        }
        resp = requests.get(f"{SO_API}/questions", params=params, timeout=10)

        if resp.status_code == 400:
            logger.warning(f"Rate limit ou erreur API pour tag: {tag}")
            return [], 0, False

        if resp.status_code == 429:
            logger.error(f"QUOTA ÉPUISÉ - Backoff requis")
            return [], 0, False

        if not resp.text:
            return [], 0, False

        data = resp.json()
        quota = data.get("quota_remaining", 0)

        if quota < 100:
            logger.warning(f"Quota critique: {quota} requêtes restantes")
        elif quota < 500:
            logger.info(f"Quota: {quota} requêtes restantes")

        return data.get("items", []), quota, data.get("has_more", False)
    except requests.exceptions.Timeout:
        logger.error(f"Timeout pour tag {tag}")
        return [], 0, False
    except Exception as e:
        logger.error(f"Erreur récupération tag {tag}: {e}")
        return [], 0, False


def collect():
    producer = create_producer()
    topic = TOPICS["stackoverflow"]
    cache = RedisCache("stackoverflow")

    logger.info("=== Démarrage collector Stack Overflow (Rotation Intelligente) ===")
    logger.info(f"Tags HIGH: {len(STACKOVERFLOW_TAGS_HIGH)} | MEDIUM: {len(STACKOVERFLOW_TAGS_MEDIUM)} | LOW: {len(STACKOVERFLOW_TAGS_LOW)}")
    logger.info(f"Batch size: {SO_BATCH_SIZE} tags/cycle | Intervalle: {POLL_INTERVAL_SO}s")

    hours = CACHE_WARMUP_HOURS.get("stackoverflow", 24)
    cache.warmup_from_kafka(topic, KAFKA_BOOTSTRAP_SERVERS, hours)

    logger.info(f"Début de la collecte Stack Overflow")

    while True:
        try:
            cycle_start = time.time()
            current_tags = get_current_tags()
            total_new = 0
            quota_remaining = 10000

            logger.info(f"Cycle #{rotation_state['cycle']} - Scanning {len(current_tags)} tags...")

            for idx, tag in enumerate(current_tags, 1):
                if quota_remaining < 10:
                    logger.warning("Quota trop bas, fin du cycle anticipée")
                    break

                questions, quota_remaining, _ = get_questions(tag)
                new_count = 0

                for q in questions:
                    q_id = q.get("question_id")
                    if cache.is_seen(q_id):
                        continue

                    data = {
                        "id": q_id,
                        "title": clean_html(q.get("title", "")),
                        "url": q.get("link"),
                        "author": q.get("owner", {}).get("display_name"),
                        "body": clean_html(q.get("body", ""))[:1000],
                        "tags": q.get("tags", []),
                        "score": q.get("score"),
                        "views": q.get("view_count"),
                        "answers": q.get("answer_count"),
                        "is_answered": q.get("is_answered"),
                        "timestamp": q.get("creation_date"),
                        "source": "stackoverflow",
                    }
                    send_message(producer, topic, data, key=str(q_id))
                    cache.add(q_id)
                    new_count += 1

                if new_count > 0:
                    logger.debug(f"  [{idx}/{len(current_tags)}] {tag}: +{new_count} questions")

                total_new += new_count
                time.sleep(2)

            cycle_duration = time.time() - cycle_start
            logger.info(
                f"[StackOverflow] +{total_new} nouvelles questions | "
                f"Quota: {quota_remaining} | Cache: {cache.count()} | "
                f"Durée: {cycle_duration:.1f}s"
            )

            if quota_remaining <= 2:
                logger.error(
                    f"QUOTA CRITIQUE ({quota_remaining}), pause de 1 heure pour éviter le ban"
                )
                time.sleep(3600)
            else:
                logger.debug(f"Prochain cycle dans {POLL_INTERVAL_SO}s")
                time.sleep(POLL_INTERVAL_SO)

        except KeyboardInterrupt:
            logger.warning("Arrêt du collector...")
            break
        except Exception as e:
            logger.error(f"Erreur dans la boucle principale: {e}", exc_info=True)
            time.sleep(60)

    producer.close()


if __name__ == "__main__":
    collect()
