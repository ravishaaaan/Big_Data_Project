import pytest
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql import Row
from spark.spark_config import get_spark_session
from pyspark.sql import functions as F


def test_high_value_filter():
    spark = get_spark_session('test')
    data = [Row(transaction_id='1', user_id='u1', timestamp='2020-01-01T00:00:00', merchant_category='Electronics', amount=6000.0, location='USA')]
    df = spark.createDataFrame(data)
    result = df.filter(F.col('amount') > 5000).collect()
    assert len(result) == 1


def test_impossible_travel_detection():
    spark = get_spark_session('test')
    now = datetime.utcnow()
    rows = [
        Row(transaction_id='t1', user_id='u1', timestamp=(now - timedelta(minutes=6)).isoformat(), merchant_category='Travel', amount=50.0, location='USA'),
        Row(transaction_id='t2', user_id='u1', timestamp=now.isoformat(), merchant_category='Travel', amount=30.0, location='UK'),
    ]
    df = spark.createDataFrame(rows).withColumn('event_time', F.to_timestamp('timestamp'))
    windowed = df.withWatermark('event_time', '2 minutes').groupBy(F.window('event_time', '10 minutes'), 'user_id').agg(F.collect_set('location').alias('locations')).filter(F.size('locations') > 1)
    res = windowed.collect()
    assert len(res) == 1
