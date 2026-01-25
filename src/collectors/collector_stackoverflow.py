# Tech Pulse - Stack Overflow Collector | Équipe: UCCNT

import time
import requests
import logging
import logger as _
from producer import create_producer, send_message
from config import TOPICS, POLL_INTERVAL_SO, STACKOVERFLOW_TAGS
from utils import clean_html

logger = logging.getLogger("stackoverflow")
SO_API = "https://api.stackexchange.com/2.3"


def get_questions(tag, page=1, page_size=100):
    try:
        params = {"order": "desc", "sort": "activity", "tagged": tag, "site": "stackoverflow",
                  "pagesize": page_size, "page": page, "filter": "withbody"}
        resp = requests.get(f"{SO_API}/questions", params=params, timeout=10)

        if resp.status_code == 400:
            logger.warning(f"Rate limit atteint pour tag: {tag}")
            return [], 0, False

        if not resp.text:
            return [], 0, False

        data = resp.json()
        quota = data.get("quota_remaining", 0)
        if quota < 20:
            logger.warning(f"Quota critique: {quota} requêtes restantes")

        return data.get("items", []), quota, data.get("has_more", False)
    except Exception as e:
        logger.error(f"Erreur récupération tag {tag}: {e}")
        return [], 0, False


def collect():
    producer = create_producer()
    topic = TOPICS["stackoverflow"]
    seen_ids = set()

    logger.info("=== Démarrage collector Stack Overflow (Batch) ===")
    logger.info(f"Tags: {len(STACKOVERFLOW_TAGS)} | Intervalle: {POLL_INTERVAL_SO}s")

    while True:
        try:
            total_new = 0
            quota_remaining = 300

            for tag in STACKOVERFLOW_TAGS:
                if quota_remaining < 10:
                    logger.warning("Quota trop bas, pause jusqu'au prochain cycle")
                    break

                questions, quota_remaining, _ = get_questions(tag)
                new_count = 0

                for q in questions:
                    q_id = q.get("question_id")
                    if q_id in seen_ids:
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
                        "source": "stackoverflow"
                    }
                    send_message(producer, topic, data, key=str(q_id))
                    seen_ids.add(q_id)
                    new_count += 1

                logger.debug(f"[{tag}] +{new_count} questions")
                total_new += new_count
                time.sleep(2)

            logger.info(f"[StackOverflow] +{total_new} nouvelles | Quota: {quota_remaining} | Cache: {len(seen_ids)}")

            if len(seen_ids) > 5000:
                seen_ids = set(list(seen_ids)[-2500:])
                logger.debug("Cache nettoyé")

            logger.debug(f"Prochain cycle dans {POLL_INTERVAL_SO}s")
            time.sleep(POLL_INTERVAL_SO)

        except KeyboardInterrupt:
            logger.warning("Arrêt du collector...")
            break
        except Exception as e:
            logger.error(f"Erreur dans la boucle: {e}")
            time.sleep(60)

    producer.close()


if __name__ == "__main__":
    collect()
