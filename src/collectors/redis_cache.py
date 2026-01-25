import redis
import logging
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB, CACHE_TTL

logger = logging.getLogger("redis_cache")


class RedisCache:
    """Gestionnaire de cache Redis pour éviter les doublons"""

    def __init__(self, source_name):
        """
        Initialiser le cache Redis pour une source donnée

        Args:
            source_name: Nom de la source (bluesky, nostr, hackernews, etc.)
        """
        self.source_name = source_name
        self.key = f"uccnt:seen_ids:{source_name}"

        try:
            self.redis = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                db=REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Test de connexion
            self.redis.ping()
            logger.info(f"[{source_name}] Connecté à Redis {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            logger.error(f"[{source_name}] Erreur connexion Redis: {e}")
            logger.warning(f"[{source_name}] Fallback sur cache en mémoire")
            self.redis = None
            self.memory_cache = set()

    def is_seen(self, item_id):
        """
        Vérifier si un ID a déjà été vu

        Args:
            item_id: ID unique de l'élément

        Returns:
            bool: True si déjà vu, False sinon
        """
        if self.redis:
            try:
                return self.redis.sismember(self.key, str(item_id))
            except Exception as e:
                logger.error(f"Erreur Redis is_seen: {e}")
                return str(item_id) in self.memory_cache
        else:
            return str(item_id) in self.memory_cache

    def add(self, item_id):
        """
        Ajouter un ID au cache

        Args:
            item_id: ID unique de l'élément
        """
        if self.redis:
            try:
                self.redis.sadd(self.key, str(item_id))
                # Définir TTL sur la clé (auto-nettoyage après 24h)
                self.redis.expire(self.key, CACHE_TTL)
            except Exception as e:
                logger.error(f"Erreur Redis add: {e}")
                self.memory_cache.add(str(item_id))
        else:
            self.memory_cache.add(str(item_id))

    def count(self):
        """
        Obtenir le nombre d'IDs dans le cache

        Returns:
            int: Nombre d'IDs
        """
        if self.redis:
            try:
                return self.redis.scard(self.key)
            except Exception as e:
                logger.error(f"Erreur Redis count: {e}")
                return len(self.memory_cache)
        else:
            return len(self.memory_cache)

    def warmup_from_kafka(self, topic_name, bootstrap_servers, hours_back=24):
        """
        Pré-remplir le cache avec les IDs des messages depuis un timestamp

        Args:
            topic_name: Nom du topic Kafka
            bootstrap_servers: Serveurs Kafka
            hours_back: Nombre d'heures en arrière (défaut: 24h)
        """
        try:
            from kafka import KafkaConsumer, TopicPartition
            from datetime import datetime, timedelta
            import json

            logger.info(
                f"[{self.source_name}] Warmup: lecture des messages des dernières {hours_back}h de '{topic_name}'..."
            )

            # Créer consumer sans subscribe (on va utiliser assign)
            consumer = KafkaConsumer(
                bootstrap_servers=bootstrap_servers,
                auto_offset_reset="latest",
                enable_auto_commit=False,
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
                consumer_timeout_ms=5000,
            )

            # Obtenir les partitions
            partitions = consumer.partitions_for_topic(topic_name)
            if not partitions:
                logger.warning(
                    f"[{self.source_name}] Aucune partition trouvée pour '{topic_name}'"
                )
                consumer.close()
                return

            # Assigner les partitions manuellement
            topic_partitions = [TopicPartition(topic_name, p) for p in partitions]
            consumer.assign(topic_partitions)

            # Calculer le timestamp (en millisecondes)
            target_time = datetime.now() - timedelta(hours=hours_back)
            timestamp_ms = int(target_time.timestamp() * 1000)

            logger.info(
                f"[{self.source_name}] Recherche des messages depuis {target_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Positionner le consumer au timestamp pour chaque partition
            timestamps = {tp: timestamp_ms for tp in topic_partitions}
            offsets = consumer.offsets_for_times(timestamps)

            for tp, offset_and_timestamp in offsets.items():
                if offset_and_timestamp is not None:
                    consumer.seek(tp, offset_and_timestamp.offset)
                else:
                    # Si pas de message à ce timestamp, partir du début
                    consumer.seek_to_beginning(tp)

            # Lire les messages
            count = 0
            for message in consumer:
                try:
                    data = message.value
                    item_id = data.get("id")
                    if item_id:
                        self.add(item_id)
                        count += 1
                        # Log progression tous les 10k messages
                        if count % 10000 == 0:
                            logger.info(
                                f"[{self.source_name}] Warmup: {count} IDs chargés..."
                            )
                except Exception as e:
                    logger.error(f"Erreur parsing message: {e}")
                    continue

            consumer.close()
            logger.info(
                f"[{self.source_name}] Warmup terminé: {count} IDs ajoutés au cache (dernières {hours_back}h)"
            )

        except Exception as e:
            logger.error(f"[{self.source_name}] Erreur warmup Kafka: {e}")
            logger.warning(
                f"[{self.source_name}] Démarrage sans warmup (risque de doublons)"
            )

    def clear(self):
        """Vider le cache (utile pour debug)"""
        if self.redis:
            try:
                self.redis.delete(self.key)
                logger.info(f"[{self.source_name}] Cache Redis vidé")
            except Exception as e:
                logger.error(f"Erreur Redis clear: {e}")
                self.memory_cache.clear()
        else:
            self.memory_cache.clear()
            logger.info(f"[{self.source_name}] Cache mémoire vidé")
