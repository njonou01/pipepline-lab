import os
import json
import logging
import boto3
from datetime import datetime
from kafka import KafkaConsumer

# Configuration
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
S3_BUCKET = os.getenv("S3_BUCKET", "uccnt-ef98cc0f-raw")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "2000"))
BATCH_TIMEOUT_SEC = int(os.getenv("BATCH_TIMEOUT_SEC", "300"))

TOPICS = [
    "bluesky",
    "nostr",
    "hackernews",
    "stackoverflow",
    "rss"
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("kafka-to-s3")


class KafkaToS3:
    def __init__(self):
        self.s3 = boto3.client("s3", region_name=AWS_REGION)
        self.consumer = KafkaConsumer(
            *TOPICS,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id="uccnt-s3-consumer",
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            consumer_timeout_ms=BATCH_TIMEOUT_SEC * 1000
        )
        self.buffers = {topic: [] for topic in TOPICS}
        logger.info(f"Connecté à Kafka {KAFKA_BOOTSTRAP}")
        logger.info(f"Topics: {TOPICS}")
        logger.info(f"Bucket S3: {S3_BUCKET}")

    def get_s3_key(self, topic):
        """Générer le chemin S3 partitionné par date"""
        now = datetime.utcnow()
        source = topic
        return f"{source}/year={now.year}/month={now.month:02d}/day={now.day:02d}/hour={now.hour:02d}/{now.strftime('%Y%m%d_%H%M%S')}_{source}.json"

    def flush_buffer(self, topic):
        """Envoyer le buffer vers S3"""
        if not self.buffers[topic]:
            return 0

        data = self.buffers[topic]
        key = self.get_s3_key(topic)

        # Convertir en NDJSON (newline-delimited JSON)
        content = "\n".join(json.dumps(record) for record in data)

        try:
            self.s3.put_object(
                Bucket=S3_BUCKET,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType="application/json"
            )
            count = len(data)
            self.buffers[topic] = []
            logger.info(f"[{topic}] -> S3: {count} records -> s3://{S3_BUCKET}/{key}")
            return count
        except Exception as e:
            logger.error(f"Erreur S3 upload: {e}")
            return 0

    def flush_all(self):
        """Flush tous les buffers"""
        total = 0
        for topic in TOPICS:
            total += self.flush_buffer(topic)
        return total

    def run(self):
        """Boucle principale"""
        logger.info("=== Démarrage Consumer Kafka -> S3 ===")
        total_processed = 0

        try:
            while True:
                try:
                    for message in self.consumer:
                        topic = message.topic
                        self.buffers[topic].append(message.value)

                        # Flush si buffer plein
                        if len(self.buffers[topic]) >= BATCH_SIZE:
                            self.flush_buffer(topic)

                except StopIteration:
                    # Timeout - flush tous les buffers
                    count = self.flush_all()
                    if count > 0:
                        total_processed += count
                        logger.info(f"Batch timeout - flushed {count} records (total: {total_processed})")

        except KeyboardInterrupt:
            logger.warning("Arrêt demandé...")
            self.flush_all()
            self.consumer.close()
            logger.info(f"Total traité: {total_processed} records")


def main():
    consumer = KafkaToS3()
    consumer.run()


if __name__ == "__main__":
    main()

