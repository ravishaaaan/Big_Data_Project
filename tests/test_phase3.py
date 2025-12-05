import pytest
import sys
import os
sys.path.append(os.getcwd())

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StringType, DoubleType
from datetime import datetime, timedelta, timezone
from spark.spark_config import get_spark_session


def test_spark_session_creation():
    """Test 3.1: Spark session can be created with proper configuration"""
    spark = get_spark_session('test-fraud-detection')
    assert spark is not None
    assert spark.sparkContext.appName == 'test-fraud-detection'
    
    # Check configurations
    conf = spark.sparkContext.getConf()
    assert conf.get('spark.driver.memory') == '2g'
    
    spark.stop()
    print("✓ Test 3.1 PASSED: Spark session created successfully")


def test_high_value_fraud_detection_logic():
    """Test 3.2: High value fraud detection logic works correctly"""
    spark = get_spark_session('test-high-value')
    
    # Create test data
    data = [
        ('tx1', 'user1', '2024-01-01T10:00:00Z', 'Electronics', 100.0, 'USA'),
        ('tx2', 'user2', '2024-01-01T10:01:00Z', 'Travel', 6000.0, 'UK'),
        ('tx3', 'user3', '2024-01-01T10:02:00Z', 'Groceries', 50.0, 'India'),
        ('tx4', 'user4', '2024-01-01T10:03:00Z', 'Restaurant', 7500.0, 'Singapore'),
    ]
    
    schema = StructType() \
        .add('transaction_id', StringType()) \
        .add('user_id', StringType()) \
        .add('timestamp', StringType()) \
        .add('merchant_category', StringType()) \
        .add('amount', DoubleType()) \
        .add('location', StringType())
    
    df = spark.createDataFrame(data, schema)
    df = df.withColumn('event_time', F.to_timestamp('timestamp'))
    
    # Apply high value detection logic
    high_value = df.filter(F.col('amount') > 5000)
    
    result = high_value.collect()
    assert len(result) == 2, f"Expected 2 high value transactions, got {len(result)}"
    
    amounts = [row.amount for row in result]
    assert 6000.0 in amounts
    assert 7500.0 in amounts
    
    spark.stop()
    print(f"✓ Test 3.2 PASSED: Detected {len(result)} high value frauds correctly")


def test_impossible_travel_detection_logic():
    """Test 3.3: Impossible travel detection logic works correctly"""
    spark = get_spark_session('test-impossible-travel')
    
    # Create test data: user1 has transactions in USA and UK within same 10-minute window
    # Use a fixed base time to ensure both events fall in same window
    base_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    data = [
        ('tx1', 'user1', base_time.isoformat(), 'Electronics', 100.0, 'USA'),
        ('tx2', 'user1', (base_time + timedelta(minutes=5)).isoformat(), 'Travel', 200.0, 'UK'),
        ('tx3', 'user2', base_time.isoformat(), 'Groceries', 50.0, 'India'),
        ('tx4', 'user2', (base_time + timedelta(minutes=2)).isoformat(), 'Restaurant', 75.0, 'India'),  # Same location, not fraud
    ]
    
    schema = StructType() \
        .add('transaction_id', StringType()) \
        .add('user_id', StringType()) \
        .add('timestamp', StringType()) \
        .add('merchant_category', StringType()) \
        .add('amount', DoubleType()) \
        .add('location', StringType())
    
    df = spark.createDataFrame(data, schema)
    df = df.withColumn('event_time', F.to_timestamp('timestamp'))
    
    # Apply impossible travel detection (batch mode, no watermark for testing)
    windowed = df.groupBy(
        F.window('event_time', '10 minutes'),
        'user_id'
    ).agg(F.collect_set('location').alias('locations'))
    
    fraud = windowed.filter(F.size('locations') > 1)
    
    result = fraud.collect()
    assert len(result) >= 1, f"Expected at least 1 impossible travel fraud, got {len(result)}"
    
    # Verify user1 is flagged
    user_ids = [row.user_id for row in result]
    assert 'user1' in user_ids, "user1 should be flagged for impossible travel"
    
    spark.stop()
    print(f"✓ Test 3.3 PASSED: Detected {len(result)} impossible travel fraud(s) correctly")


def test_event_time_vs_processing_time():
    """Test 3.4: Event time and processing time are both captured"""
    spark = get_spark_session('test-event-time')
    
    data = [
        ('tx1', 'user1', '2024-01-01T10:00:00Z', 'Electronics', 100.0, 'USA'),
        ('tx2', 'user2', '2024-01-01T10:01:00Z', 'Travel', 200.0, 'UK'),
    ]
    
    schema = StructType() \
        .add('transaction_id', StringType()) \
        .add('user_id', StringType()) \
        .add('timestamp', StringType()) \
        .add('merchant_category', StringType()) \
        .add('amount', DoubleType()) \
        .add('location', StringType())
    
    df = spark.createDataFrame(data, schema)
    df = df.withColumn('event_time', F.to_timestamp('timestamp')) \
           .withColumn('processing_time', F.current_timestamp())
    
    result = df.select('event_time', 'processing_time').collect()
    
    for row in result:
        assert row.event_time is not None, "Event time should not be null"
        assert row.processing_time is not None, "Processing time should not be null"
        # Processing time should be later than event time for old data
        # (or approximately equal for real-time data)
    
    spark.stop()
    print("✓ Test 3.4 PASSED: Event time and processing time captured correctly")


def test_transaction_schema_parsing():
    """Test 3.5: Transaction JSON schema can be parsed correctly"""
    spark = get_spark_session('test-schema')
    
    # Simulate Kafka message format
    json_data = [
        ('{"transaction_id": "tx1", "user_id": "u1", "timestamp": "2024-01-01T10:00:00Z", "merchant_category": "Electronics", "amount": 100.0, "location": "USA"}',),
        ('{"transaction_id": "tx2", "user_id": "u2", "timestamp": "2024-01-01T10:01:00Z", "merchant_category": "Travel", "amount": 200.0, "location": "UK"}',),
    ]
    
    df = spark.createDataFrame(json_data, ['value'])
    
    # Define schema as in fraud_detection_streaming.py
    from pyspark.sql.types import StructType, StringType, DoubleType
    schema = StructType() \
        .add('transaction_id', StringType()) \
        .add('user_id', StringType()) \
        .add('timestamp', StringType()) \
        .add('merchant_category', StringType()) \
        .add('amount', DoubleType()) \
        .add('location', StringType())
    
    parsed = df.select(F.from_json('value', schema).alias('data')).select('data.*')
    
    result = parsed.collect()
    assert len(result) == 2
    assert result[0].transaction_id == 'tx1'
    assert result[0].amount == 100.0
    assert result[1].user_id == 'u2'
    
    spark.stop()
    print("✓ Test 3.5 PASSED: JSON schema parsing works correctly")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
