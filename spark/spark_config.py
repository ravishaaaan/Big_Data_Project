from pyspark.sql import SparkSession
import os

def get_spark_session(app_name: str = 'fraud-detection') -> SparkSession:
    builder = SparkSession.builder.appName(app_name)
    # Basic local settings, tuned for small dev environments
    builder = builder.master(os.getenv('SPARK_MASTER', 'local[*]'))
    builder = builder.config('spark.sql.shuffle.partitions', int(os.getenv('SPARK_SHUFFLE_PARTS', 4)))
    builder = builder.config('spark.driver.memory', os.getenv('SPARK_DRIVER_MEMORY', '2g'))
    builder = builder.config('spark.executor.memory', os.getenv('SPARK_EXECUTOR_MEMORY', '2g'))
    builder = builder.config('spark.sql.streaming.checkpointLocation', os.getenv('SPARK_CHECKPOINT_DIR', '/tmp/spark-checkpoints'))
    # Kafka offsets strategy: use earliest for dev; in production use committed offsets and proper checkpointing
    builder = builder.config('spark.sql.streaming.kafka.consumer.cache.enabled', 'false')
    spark = builder.getOrCreate()
    return spark
