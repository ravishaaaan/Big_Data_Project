import json
import time
import uuid
import random
from typing import Dict
from faker import Faker
from kafka import KafkaProducer
from kafka.errors import KafkaError
from datetime import datetime, timedelta
import os
from kafka_client.config import create_topics, producer_config

TOPIC = os.getenv('KAFKA_TOPIC', 'transactions')
RATE = float(os.getenv('TX_RATE', 10))  # transactions per second
FRAUD_RATE = float(os.getenv('FRAUD_RATE', 0.12))  # 10-15% default

CATEGORIES = ["Electronics", "Groceries", "Travel", "Restaurant", "Gas", "Online"]
LOCATIONS = ["USA", "UK", "India", "Singapore", "Australia", "Germany"]
faker = Faker()


def generate_transaction(user_id: str | None = None) -> Dict:
    if user_id is None:
        user_id = str(uuid.uuid4())
    # Normal amount
    is_high_value = random.random() < 0.05  # 5% high value
    if is_high_value:
        amount = round(random.uniform(5000.01, 10000.0), 2)
    else:
        amount = round(random.uniform(10.0, 1000.0), 2)
    txn = {
        'transaction_id': str(uuid.uuid4()),
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat(),
        'merchant_category': random.choice(CATEGORIES),
        'amount': amount,
        'location': random.choice(LOCATIONS),
    }
    return txn


def inject_impossible_travel_sequence(producer: KafkaProducer, base_user: str):
    """Generate two transactions for same user in different countries within ~5 minutes."""
    country_a, country_b = random.sample(LOCATIONS, 2)
    now = datetime.utcnow()
    txn1 = {
        'transaction_id': str(uuid.uuid4()),
        'user_id': base_user,
        'timestamp': (now - timedelta(minutes=6)).isoformat(),
        'merchant_category': random.choice(CATEGORIES),
        'amount': round(random.uniform(10.0, 500.0), 2),
        'location': country_a,
    }
    txn2 = {
        'transaction_id': str(uuid.uuid4()),
        'user_id': base_user,
        'timestamp': (now).isoformat(),
        'merchant_category': random.choice(CATEGORIES),
        'amount': round(random.uniform(10.0, 200.0), 2),
        'location': country_b,
    }
    for t in (txn1, txn2):
        producer.send(TOPIC, value=json.dumps(t).encode('utf-8'))
        print(f"[PRODUCER] Sent: {t}")


def run():
    cfg = producer_config()
    create_topics([TOPIC, 'fraud-alerts'])
    producer = KafkaProducer(**cfg)
    try:
        users = [str(uuid.uuid4()) for _ in range(50)]
        interval = 1.0 / RATE
        while True:
            # Decide if we inject an impossible travel sequence
            if random.random() < FRAUD_RATE:
                base_user = random.choice(users)
                inject_impossible_travel_sequence(producer, base_user)
                time.sleep(0.1)
            else:
                txn = generate_transaction(random.choice(users))
                # Explicitly inject a high value with some probability
                if random.random() < 0.05:
                    txn['amount'] = round(random.uniform(5000.01, 10000.0), 2)
                try:
                    producer.send(TOPIC, value=json.dumps(txn).encode('utf-8'))
                    print(f"[PRODUCER] Sent: {txn}")
                except KafkaError as e:
                    print(f"Failed to send message: {e}")
                time.sleep(interval)
    except KeyboardInterrupt:
        print('Producer stopped by user')
    finally:
        producer.flush()
        producer.close()


if __name__ == '__main__':
    run()
