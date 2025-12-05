import pytest
import subprocess
import time
import sys
import os
sys.path.append(os.getcwd())

from database.db_config import get_connection, query, execute
from kafka_client.config import create_topics, producer_config
from kafka_client.producer import generate_transaction


def test_docker_compose_file_exists():
    """Test 1.1: Docker compose file exists and is properly configured."""
    assert os.path.exists('docker-compose.yml'), "docker-compose.yml not found"
    
    with open('docker-compose.yml', 'r') as f:
        content = f.read()
    
    # Verify required services are defined
    required_services = ['postgres', 'kafka', 'zookeeper', 'airflow']
    for service in required_services:
        assert service in content, f"Service {service} not found in docker-compose.yml"
    
    print("✓ Test 1.1 PASSED: Docker compose file properly configured")


def test_database_schema_file():
    """Test 1.2: Database schema file exists and contains required tables."""
    init_sql_path = os.path.join('database', 'init.sql')
    assert os.path.exists(init_sql_path), "database/init.sql not found"
    
    with open(init_sql_path, 'r') as f:
        sql = f.read().lower()
    
    # Verify table creation statements
    assert 'create table' in sql and 'transactions' in sql, "transactions table definition not found"
    assert 'create table' in sql and 'fraud_alerts' in sql, "fraud_alerts table definition not found"
    assert 'create table' in sql and 'validated_transactions' in sql, "validated_transactions table definition not found"
    
    print("✓ Test 1.2 PASSED: Database schema contains all required tables")


def test_database_config_module():
    """Test 1.3: Database configuration module has required functions."""
    from database import db_config
    
    # Verify required functions exist
    assert hasattr(db_config, 'get_connection'), "get_connection function not found"
    assert hasattr(db_config, 'query'), "query function not found"
    assert hasattr(db_config, 'execute'), "execute function not found"
    
    print("✓ Test 1.3 PASSED: Database config module properly structured")


def test_kafka_config_module():
    """Test 1.4: Kafka configuration module has required functions."""
    from kafka_client import config
    
    # Verify required functions exist
    assert hasattr(config, 'create_topics'), "create_topics function not found"
    assert hasattr(config, 'producer_config'), "producer_config function not found"
    assert hasattr(config, 'consumer_config'), "consumer_config function not found"
    
    # Verify producer config returns proper structure (uses bootstrap_servers in Python)
    cfg = producer_config()
    assert 'bootstrap_servers' in cfg, "bootstrap_servers not in producer config"
    
    print("✓ Test 1.4 PASSED: Kafka config module properly structured")


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
