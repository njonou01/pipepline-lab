# Tech Pulse - Kafka Producer | Équipe: UCCNT

import json
import logging
from datetime import datetime
from kafka import KafkaProducer
from config import KAFKA_BOOTSTRAP_SERVERS
import logger as _

logger = logging.getLogger(__name__)


def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )


def send_message(producer, topic, data, key=None):
    data['_ingested_at'] = datetime.utcnow().isoformat()
    data['_source_topic'] = topic
    try:
        future = producer.send(topic, key=key, value=data)
        future.get(timeout=10)
        logger.debug(f"Envoyé vers {topic}: {key or 'sans-clé'}")  # DEBUG: chaque message
        return True
    except Exception as e:
        logger.error(f"Erreur envoi vers {topic}: {e}")
        return False
