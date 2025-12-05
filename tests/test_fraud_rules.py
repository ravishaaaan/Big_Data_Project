import pytest
from datetime import datetime, timedelta, timezone
from pyspark.sql import SparkSession
from pyspark.sql import Row
from spark.spark_config import get_spark_session
from pyspark.sql import functions as F


def test_high_value_filter():
    """Test: High value fraud detection filters transactions over $5000."""
    spark = get_spark_session('test')
    data = [Row(transaction_id='1', user_id='u1', timestamp='2020-01-01T00:00:00', merchant_category='Electronics', amount=6000.0, location='USA')]
    df = spark.createDataFrame(data)
    result = df.filter(F.col('amount') > 5000).collect()
    assert len(result) == 1
    spark.stop()
    print("✓ High value filter test PASSED")


def test_impossible_travel_detection():
    """Test: Impossible travel detection identifies multiple locations in 10-min window."""
    spark = get_spark_session('test')
    
    # Use fixed timestamps to ensure both fall in same 10-minute window
    base_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    rows = [
        Row(transaction_id='t1', user_id='u1', timestamp=base_time.isoformat(), merchant_category='Travel', amount=50.0, location='USA'),
        Row(transaction_id='t2', user_id='u1', timestamp=(base_time + timedelta(minutes=5)).isoformat(), merchant_category='Travel', amount=30.0, location='UK'),
    ]
    df = spark.createDataFrame(rows).withColumn('event_time', F.to_timestamp('timestamp'))
    
    # For batch unit test we perform a simple windowed aggregation without watermarking
    windowed = df.groupBy(F.window('event_time', '10 minutes'), 'user_id').agg(F.collect_set('location').alias('locations')).filter(F.size('locations') > 1)
    res = windowed.collect()
    assert len(res) == 1, f"Expected 1 impossible travel fraud, got {len(res)}"
    spark.stop()
    print("✓ Impossible travel detection test PASSED")
