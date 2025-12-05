from kafka.admin import KafkaAdminClient, NewTopic
import os

KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP', 'localhost:9092')
DEFAULT_PARTITIONS = int(os.getenv('KAFKA_PARTITIONS', 3))
DEFAULT_REPLICATION = int(os.getenv('KAFKA_REPLICATION', 1))


def create_topics(topic_names: list[str]):
    """Create topics if they don't exist. Adjust partitions/replication via env vars.

    Partition and replication settings: For local dev we use small replication factor (1)
    and multiple partitions to allow parallel consumers and simulate scale. In production,
    replication should be >= 2 for fault tolerance and partitions sized to expected throughput.
    """
    admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP, client_id='fintech-admin')
    existing = admin.list_topics()
    topics_to_create = []
    for t in topic_names:
        if t not in existing:
            topics_to_create.append(NewTopic(name=t, num_partitions=DEFAULT_PARTITIONS, replication_factor=DEFAULT_REPLICATION))
    if topics_to_create:
        admin.create_topics(new_topics=topics_to_create, validate_only=False)
    admin.close()


def producer_config() -> dict:
    return {
        'bootstrap_servers': KAFKA_BOOTSTRAP,
        'linger_ms': 5,
        'request_timeout_ms': 20000,
    }


def consumer_config(group_id: str) -> dict:
    return {
        'bootstrap_servers': KAFKA_BOOTSTRAP,
        'group_id': group_id,
        'auto_offset_reset': 'earliest',
        'enable_auto_commit': True,
    }
