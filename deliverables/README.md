# Deliverables Output Directory

This directory contains all generated deliverables from the FinTech Fraud Detection Pipeline.

## Generated Files

### Console Outputs (Terminal Logs)
1. **`1_kafka_producer_output_<timestamp>.txt`** - Kafka Producer console output showing transaction generation
2. **`2_spark_streaming_output_<timestamp>.txt`** - Spark Streaming console output showing fraud detection
3. **`3_airflow_dag_output_<timestamp>.txt`** - Airflow DAG execution output showing ETL process

### Report Files
4. **`4_reconciliation_report_<timestamp>.txt`** - Financial reconciliation report (TXT format)
5. **`5_fraud_by_merchant_category_<timestamp>.csv`** - Fraud analysis by merchant category (CSV format)
6. **`6_comprehensive_fraud_analysis_<timestamp>.pdf`** - Comprehensive fraud analysis with visualizations (PDF format)

## How to Generate

Run the deliverables generation pipeline:

```bash
./generate_deliverables.sh
```

This will:
1. Start all Docker services
2. Create Kafka topics
3. Run Kafka Producer for 60 seconds (capture output)
4. Run Spark Streaming for 50 seconds (capture output)
5. Execute Airflow DAG tasks (capture output)
6. Generate reconciliation report
7. Generate fraud by merchant category CSV
8. Generate comprehensive fraud analysis PDF

All outputs will be saved in this directory with timestamps.

## File Naming Convention

All files are timestamped with format: `YYYYMMDD_HHMMSS`

Example: `1_kafka_producer_output_20251206_143052.txt`
