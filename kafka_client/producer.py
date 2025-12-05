import json
import time
import uuid
import random
from typing import Dict
from faker import Faker
from kafka import KafkaProducer
from kafka.errors import KafkaError
from datetime import datetime, timedelta, timezone
import os
from kafka_client.config import create_topics, producer_config

TOPIC = os.getenv('KAFKA_TOPIC', 'transactions')
RATE = float(os.getenv('TX_RATE', 10))  # transactions per second
FRAUD_RATE = float(os.getenv('FRAUD_RATE', 0.12))  # 10-15% default

CATEGORIES = ["Electronics", "Groceries", "Travel", "Restaurant", "Gas", "Online"]
LOCATIONS = ["USA", "UK", "India", "Singapore", "Australia", "Germany"]
faker = Faker()


def generate_transaction(user_id: str | None = None) -> Dict:
    """Generate a normal transaction with amount between $10-$1000."""
    if user_id is None:
        user_id = str(uuid.uuid4())
    amount = round(random.uniform(10.0, 1000.0), 2)
    txn = {
        'transaction_id': str(uuid.uuid4()),
        'user_id': user_id,
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'merchant_category': random.choice(CATEGORIES),
        'amount': amount,
        'location': random.choice(LOCATIONS),
    }
    return txn


def generate_high_value_fraud(user_id: str | None = None) -> Dict:
    """Generate a high-value fraud transaction (>$5000)."""
    if user_id is None:
        user_id = str(uuid.uuid4())
    amount = round(random.uniform(5000.01, 10000.0), 2)
    txn = {
        'transaction_id': str(uuid.uuid4()),
        'user_id': user_id,
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'merchant_category': random.choice(CATEGORIES),
        'amount': amount,
        'location': random.choice(LOCATIONS),
    }
    return txn


def generate_impossible_travel_fraud(previous_transaction: Dict) -> Dict:
    """Generate an impossible travel fraud transaction based on previous transaction.
    
    Creates a transaction 5-8 minutes later in a different country.
    """
    user_id = previous_transaction['user_id']
    prev_location = previous_transaction['location']
    prev_time = datetime.fromisoformat(previous_transaction['timestamp'])
    
    # Choose different location
    available_locations = [loc for loc in LOCATIONS if loc != prev_location]
    new_location = random.choice(available_locations)
    
    # Time difference: 5-8 minutes
    time_diff = random.uniform(5, 8)
    new_time = prev_time + timedelta(minutes=time_diff)
    
    amount = round(random.uniform(10.0, 1000.0), 2)
    txn = {
        'transaction_id': str(uuid.uuid4()),
        'user_id': user_id,
        'timestamp': new_time.isoformat(),
        'merchant_category': random.choice(CATEGORIES),
        'amount': amount,
        'location': new_location,
    }
    return txn


def send_transaction(producer: KafkaProducer, transaction: Dict, log_prefix: str = "[NORMAL]") -> bool:
    """Send a transaction to Kafka and log it cleanly."""
    try:
        producer.send(TOPIC, value=json.dumps(transaction).encode('utf-8'))
        
        # Clean console output
        if transaction['amount'] > 5000:
            print(f"[FRAUD-VALUE] Transaction {transaction['transaction_id'][:8]}: User {transaction['user_id'][:8]} | ${transaction['amount']:.2f} | {transaction['merchant_category']} | {transaction['location']}")
        else:
            print(f"{log_prefix} Transaction {transaction['transaction_id'][:8]}: User {transaction['user_id'][:8]} | ${transaction['amount']:.2f} | {transaction['merchant_category']} | {transaction['location']}")
        return True
    except KafkaError as e:
        print(f"Failed to send message: {e}")
        return False


def run_producer(duration_seconds: int = 60):
    """Run producer for specified duration with fraud injection.
    
    Args:
        duration_seconds: How long to run the producer (default 60 seconds)
    
    Statistics:
        - 85% normal transactions
        - 10% impossible travel fraud
        - 5% high value fraud
    """
    cfg = producer_config()
    create_topics([TOPIC, 'fraud-alerts'])
    producer = KafkaProducer(**cfg)
    
    # Track user transaction history for impossible travel
    user_history: Dict[str, Dict] = {}
    users = [str(uuid.uuid4()) for _ in range(50)]
    
    stats = {'total': 0, 'normal': 0, 'fraud_travel': 0, 'fraud_value': 0}
    interval = 1.0 / RATE
    start_time = time.time()
    
    try:
        while (time.time() - start_time) < duration_seconds:
            rand = random.random()
            user_id = random.choice(users)
            
            if rand < 0.10 and user_id in user_history:
                # 10% impossible travel fraud (if user has history)
                prev_tx = user_history[user_id]
                fraud_tx = generate_impossible_travel_fraud(prev_tx)
                
                # Send previous transaction first if not sent
                if 'sent' not in prev_tx:
                    send_transaction(producer, prev_tx, "[NORMAL]")
                    stats['normal'] += 1
                    stats['total'] += 1
                    prev_tx['sent'] = True
                
                # Send fraud transaction
                send_transaction(producer, fraud_tx, f"[FRAUD-TRAVEL]")
                print(f"  └─ {prev_tx['location']} -> {fraud_tx['location']} | {(datetime.fromisoformat(fraud_tx['timestamp']) - datetime.fromisoformat(prev_tx['timestamp'])).seconds / 60:.1f} minutes")
                user_history[user_id] = fraud_tx
                stats['fraud_travel'] += 1
                stats['total'] += 1
                
            elif rand < 0.15:
                # 5% high value fraud
                fraud_tx = generate_high_value_fraud(user_id)
                send_transaction(producer, fraud_tx, "[FRAUD-VALUE]")
                user_history[user_id] = fraud_tx
                stats['fraud_value'] += 1
                stats['total'] += 1
                
            else:
                # 85% normal transactions
                normal_tx = generate_transaction(user_id)
                send_transaction(producer, normal_tx, "[NORMAL]")
                user_history[user_id] = normal_tx
                stats['normal'] += 1
                stats['total'] += 1
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print('\nProducer stopped by user')
    finally:
        producer.flush()
        producer.close()
    
    # Print summary after cleanup
    print(f"\n{'='*60}")
    print(f"PRODUCER SUMMARY ({duration_seconds}s)")
    print(f"{'='*60}")
    print(f"Total Transactions: {stats['total']}")
    print(f"Normal: {stats['normal']} ({stats['normal']/stats['total']*100:.1f}%)")
    print(f"Fraud (Impossible Travel): {stats['fraud_travel']} ({stats['fraud_travel']/stats['total']*100:.1f}%)")
    print(f"Fraud (High Value): {stats['fraud_value']} ({stats['fraud_value']/stats['total']*100:.1f}%)")
    print(f"{'='*60}\n")
    
    return stats


if __name__ == '__main__':
    # Run producer indefinitely (can stop with Ctrl+C)
    # For testing, use run_producer(duration_seconds=60)
    import sys
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 3600  # Default 1 hour
    run_producer(duration)
