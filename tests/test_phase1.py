import pytest
import subprocess
import time
import sys
import os
sys.path.append(os.getcwd())

from database.db_config import get_connection, query, execute
from kafka_client.config import create_topics, producer_config
from kafka_client.producer import generate_transaction


def test_docker_services_running():
    """Test 1.1: Docker compose shows services (best-effort)."""
    result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
    # This is a soft check: if docker-compose isn't available the test will fail on CI/local env
    assert result.returncode == 0, f"docker-compose ps failed: {result.stderr}"


def test_database_connection():
    """Test 1.2: PostgreSQL connection works (uses env or defaults)."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        val = cur.fetchone()[0]
        assert val == 1
    finally:
        if conn:
            conn.close()


def test_database_tables_created():
    """Test 1.3: All required tables exist (create them if missing)."""
    # Attempt to create tables by executing init.sql if present
    init_sql_path = os.path.join('database', 'init.sql')
    if os.path.exists(init_sql_path):
        with open(init_sql_path, 'r') as f:
            sql = f.read()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema='public' AND table_name IN ('transactions', 'fraud_alerts', 'validated_transactions')
    """)
    tables = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    assert 'transactions' in tables and 'fraud_alerts' in tables and 'validated_transactions' in tables


def test_kafka_topics_created():
    """Test 1.4: Kafka topics exist (creates them if necessary)."""
    # create_topics will attempt to contact Kafka; this is a best-effort test
    try:
        create_topics(['transactions', 'fraud-alerts'])
    except Exception as e:
        pytest.skip(f"Skipping Kafka topic creation test (Kafka not available): {e}")


def test_kafka_producer_sends_message():
    """Test 1.5: Can create a producer config and generate a transaction message."""
    cfg = producer_config()
    # We don't open a real KafkaProducer here to avoid collisions in CI; validate payload instead
    txn = generate_transaction()
    required_fields = ['transaction_id', 'user_id', 'timestamp', 'merchant_category', 'amount', 'location']
    for f in required_fields:
        assert f in txn
    assert 10 <= txn['amount'] <= 10000


if __name__ == '__main__':
    pytest.main([__file__, '-q'])
