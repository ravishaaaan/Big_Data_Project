# FinTech Fraud Detection Pipeline

End-to-end real-time fraud detection system for digital wallet transactions using Lambda Architecture.

## Architecture

### Lambda Architecture

This system implements a **Lambda Architecture** with three layers:

1. **Speed Layer (Real-time)**: Apache Kafka + Spark Structured Streaming
   - Processes transactions as they arrive
   - Detects fraud patterns in real-time
   - Writes alerts and transactions to PostgreSQL
   - Handles event time vs processing time with watermarking

2. **Batch Layer**: Apache Airflow
   - Runs every 6 hours for reconciliation
   - Extracts non-fraud transactions
   - Performs aggregations and validation
   - Generates reconciliation reports

3. **Serving Layer**: PostgreSQL
   - ACID-compliant storage for all data
   - Tables: `transactions`, `fraud_alerts`, `validated_transactions`
   - Supports both real-time writes and batch queries

### Components

#### Kafka
- Message broker for transaction stream
- Topics: `transactions`, `fraud-alerts`
- Producer generates synthetic transactions with controlled fraud injection

#### Spark Structured Streaming
- Real-time fraud detection engine
- **High-Value Detection**: Flags transactions > $5,000
- **Impossible Travel Detection**: Detects same user in multiple locations within 10 minutes
- Event-time processing with 2-minute watermarking

#### PostgreSQL
- Stores all transactions and fraud alerts
- Validated transactions table for reconciled data
- Supports concurrent reads and writes

#### Airflow
- Orchestrates batch ETL workflows
- Reconciliation DAG runs every 6 hours
- Generates fraud analysis reports by category

## Installation

### Prerequisites
- Docker & Docker Compose
- Python 3.9+
- Git

### Setup

1. Clone the repository:
```bash
git clone https://github.com/ravishaaaan/Big_Data_Project.git
cd fintech-fraud-detection
```

2. Create Python virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Start all services (automated):
```bash
./start_all.sh
```

Or manually:

```bash
# Start Docker infrastructure
docker compose up -d

# Wait for services to initialize
sleep 15

# Create Kafka topics
docker exec fintech-fraud-detection-kafka-1 kafka-topics --create --if-not-exists --topic transactions --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# Start Spark Streaming
nohup ./run_spark.sh > /tmp/spark_output.log 2>&1 &

# Start Kafka Producer
source .venv/bin/activate
nohup python3 kafka_client/producer.py > /tmp/producer_output.log 2>&1 &
```

4. Verify all services are running:
```bash
docker compose ps
ps aux | grep -E "producer|fraud_detection"
```

## Tech Stack Justification

### Why Kafka?
- **High Throughput**: Handles millions of transactions per second
- **Durability**: Persists messages for replay and fault tolerance
- **Scalability**: Partitioned topics for parallel processing
- **Real-time**: Low-latency message delivery for fraud detection

### Why Spark Structured Streaming?
- **Unified Batch/Streaming**: Single API for both processing modes
- **Event Time Processing**: Handles out-of-order events with watermarking
- **Fault Tolerance**: Checkpointing and exactly-once semantics
- **Scalability**: Distributes processing across cluster
- **Rich APIs**: Window operations, joins, aggregations for complex fraud patterns

### Why Apache Airflow?
- **Workflow Orchestration**: Manages complex ETL DAGs with dependencies
- **Scheduling**: Cron-based scheduling for batch reconciliation
- **Monitoring**: UI for tracking task execution and failures
- **Extensibility**: Custom operators and hooks for PostgreSQL integration

### Why PostgreSQL?
- **ACID Compliance**: Guarantees data consistency for financial transactions
- **JSON Support**: JSONB for flexible fraud alert details
- **Performance**: Indexes and query optimization for large datasets
- **Reliability**: Mature, production-tested database
- **Integration**: Native support in Airflow and Spark

## Event Time vs Processing Time Handling

### Event Time
- **Definition**: The timestamp when the transaction actually occurred (embedded in message)
- **Usage**: Primary timestamp for fraud detection windowing
- **Advantage**: Correctly handles late-arriving events and out-of-order processing

### Processing Time
- **Definition**: The timestamp when Spark processes the message
- **Usage**: Tracked for performance monitoring and latency analysis
- **Storage**: Both event_time and processing_time stored in database

### Watermarking Strategy
- **Watermark**: 2 minutes
- **Purpose**: Defines how long to wait for late events before closing windows
- **Trade-off**: Balance between latency (smaller watermark) and completeness (larger watermark)

```python
# Example from fraud_detection_streaming.py
windowed = json_df.withWatermark('event_time', '2 minutes') \
    .groupBy(F.window('event_time', '10 minutes', '5 minutes'), 'user_id')
```

### Impossible Travel Detection
Uses 10-minute tumbling windows to detect same user in multiple locations:
- Window 1: 10:00-10:10 → User A in USA and Singapore → FRAUD
- Window 2: 10:10-10:20 → User B only in UK → Normal

## Usage

### Generate All Deliverables (Recommended)

**Run the complete pipeline to generate all required deliverables:**

```bash
./generate_deliverables.sh
```

This automated pipeline will:
1. ✓ Start all Docker services (Kafka, PostgreSQL, Spark, Airflow)
2. ✓ Run Kafka Producer for 60 seconds and capture console output
3. ✓ Run Spark Streaming for 50 seconds and capture console output
4. ✓ Execute Airflow DAG and capture execution output
5. ✓ Generate reconciliation report (TXT)
6. ✓ Generate fraud by merchant category report (CSV)
7. ✓ Generate comprehensive fraud analysis report (PDF)

**All outputs saved to `deliverables/` directory:**
- `1_kafka_producer_output_<timestamp>.txt`
- `2_spark_streaming_output_<timestamp>.txt`
- `3_airflow_dag_output_<timestamp>.txt`
- `4_reconciliation_report_<timestamp>.txt`
- `5_fraud_by_merchant_category_<timestamp>.csv`
- `6_comprehensive_fraud_analysis_<timestamp>.pdf`

### Quick Start (Automated)

Start everything with one command:
```bash
./start_all.sh
```

Stop everything:
```bash
./stop_all.sh
```

### Manual Execution

#### Start the Kafka Producer

Generate synthetic transactions with fraud patterns:

```bash
source .venv/bin/activate
python kafka_client/producer.py
```

This generates:
- 85% normal transactions ($10-$1,000)
- 10% impossible travel fraud (multiple locations in 5-8 minutes)
- 5% high-value fraud ($5,000-$10,000)

#### Start Spark Streaming Job

Run real-time fraud detection:

```bash
source .venv/bin/activate
python spark/fraud_detection_streaming.py
```

Monitors Kafka stream and writes fraud alerts to PostgreSQL.

#### Trigger Airflow DAG

Access Airflow UI at http://localhost:8081 (username: `admin`, password: `admin`) and trigger `etl_reconciliation` DAG manually, or wait for the 6-hour schedule.

#### Generate Reports

Create comprehensive fraud analysis reports:

```bash
python reports/generate_report.py

# With visualizations (bar chart, pie chart, time series):
python reports/generate_report.py --visualizations

# Save as JSON:
python reports/generate_report.py --json

# Generate PDF report:
python reports/generate_report.py --pdf

# Generate all formats:
python reports/generate_report.py --all
```

### Monitoring

#### View Docker Services
```bash
docker compose ps
```

#### Check Database
```bash
docker exec -it fintech-postgres psql -U fintech_user -d fintech

# Query transactions
SELECT COUNT(*) FROM transactions;

# Query fraud alerts
SELECT fraud_type, COUNT(*) FROM fraud_alerts GROUP BY fraud_type;

# Check validated transactions
SELECT COUNT(*) FROM validated_transactions;
```

#### Monitor Kafka Topics
```bash
# List topics
docker exec fintech-fraud-detection-kafka-1 kafka-topics --list --bootstrap-server localhost:9092

# Consume messages
docker exec fintech-fraud-detection-kafka-1 kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic transactions \
  --from-beginning \
  --max-messages 10
```

#### Check Logs
```bash
# Spark Streaming
tail -f /tmp/spark_output.log

# Kafka Producer
tail -f /tmp/producer_output.log

# Docker services
docker compose logs -f
```

## Ethics & Privacy Implications

### Data Privacy Considerations

1. **Synthetic Data Only**: This project uses faker library to generate synthetic transaction data. No real customer data is processed.

2. **PII Protection**: In production systems:
   - Implement data masking/encryption for sensitive fields (user_id, location)
   - Use tokenization for user identifiers
   - Apply GDPR/CCPA compliance measures
   - Implement data retention policies and right-to-be-forgotten

3. **Fraud Detection Ethics**:
   - **False Positives**: Balance fraud detection sensitivity to minimize blocking legitimate transactions
   - **Bias**: Ensure fraud models don't discriminate based on location, demographics, or spending patterns
   - **Transparency**: Provide explanations for fraud alerts to users
   - **Appeal Process**: Allow customers to dispute false fraud flags

4. **Security**:
   - Encrypt data in transit (TLS for Kafka, Spark, PostgreSQL)
   - Encrypt data at rest in PostgreSQL
   - Implement role-based access control (RBAC)
   - Audit all access to fraud detection systems

5. **Regulatory Compliance**:
   - PCI-DSS for payment card data
   - SOC 2 for financial services
   - Regional data residency requirements

### Responsible AI/ML

- **Model Explainability**: Document fraud detection logic clearly
- **Human Oversight**: Critical decisions should involve human review
- **Fairness Testing**: Regularly audit for biased outcomes across user segments

## Testing

The project follows a phase-by-phase testing approach:

```bash
# Run all tests
pytest tests/ -v

# Run specific phase tests
pytest tests/test_phase1.py -v  # Database & Kafka infrastructure
pytest tests/test_phase2.py -v  # Fraud generation logic
pytest tests/test_phase3.py -v  # Spark streaming detection
pytest tests/test_phase4.py -v  # Airflow ETL workflows
pytest tests/test_phase5.py -v  # Final integration
```

### Test Results Summary

All 32 tests passing with 0 skipped:
- **Phase 1**: Database & Kafka infrastructure (5 tests)
- **Phase 2**: Fraud generation logic (5 tests)
- **Phase 3**: Spark streaming fraud detection (5 tests)
- **Phase 4**: Airflow ETL & reconciliation (7 tests)
- **Phase 5**: Final integration & documentation (8 tests)
- **Fraud Rules**: Additional fraud rule validation (2 tests)

## Sample Outputs

### Kafka Producer Console
```
[NORMAL] Transaction a1b2c3d4: User user123 | $456.78 | Electronics | USA
[FRAUD-VALUE] Transaction e5f6g7h8: User user456 | $7,850.00 | Travel | UK
[FRAUD-TRAVEL] Transaction i9j0k1l2: User user789 | $125.50 | Gas | Singapore
  └─ USA -> Singapore | 6.2 minutes
```

### Fraud Alerts in PostgreSQL
```sql
fintech=# SELECT * FROM fraud_alerts LIMIT 5;
 alert_id |  user_id  | transaction_id |   fraud_type    |      detection_time      
----------+-----------+----------------+-----------------+--------------------------
        1 | user456   | e5f6g7h8       | HIGH_VALUE      | 2025-12-06 02:30:15
        2 | user789   | i9j0k1l2       | IMPOSSIBLE_TRAVEL| 2025-12-06 02:30:22
```

### Fraud Analysis Report
```
================================================================================
FRAUD DETECTION SYSTEM - COMPREHENSIVE ANALYSIS REPORT
Generated: 2025-12-06 02:35:00 UTC
================================================================================

📊 TRANSACTION STATISTICS
--------------------------------------------------------------------------------
Total Transactions: 10,482
Total Transaction Amount: $5,234,567.89

Transactions by Category:
  • Electronics: 1,847 transactions ($923,456.78)
  • Travel: 1,652 transactions ($826,789.01)
  • Groceries: 1,589 transactions ($398,234.56)

🚨 FRAUD DETECTION STATISTICS
--------------------------------------------------------------------------------
Total Fraud Alerts: 1,248
Fraud by Type:
  • HIGH_VALUE: 524 alerts
  • IMPOSSIBLE_TRAVEL: 724 alerts

✅ VALIDATION & RECONCILIATION
--------------------------------------------------------------------------------
Validated Transactions: 9,234
Validated Amount: $4,612,890.12
Fraud Rate: 11.91%
```

## Troubleshooting

### Kafka Connection Issues
```bash
# Check Kafka is running
docker compose ps kafka

# Verify Kafka broker
docker exec fintech-fraud-detection-kafka-1 kafka-broker-api-versions --bootstrap-server localhost:9092

# Check topic exists
docker exec fintech-fraud-detection-kafka-1 kafka-topics --list --bootstrap-server localhost:9092
```

### Spark Streaming Errors
```bash
# Check Spark logs
tail -f /tmp/spark_output.log

# Verify Kafka connector JARs exist
ls -lh spark/jars/

# Clear Spark checkpoints if corrupted
rm -rf /tmp/spark-checkpoints/*
```

### PostgreSQL Connection Issues
```bash
# Check PostgreSQL is running
docker exec fintech-postgres pg_isready -U fintech_user

# Connect to database
docker exec -it fintech-postgres psql -U fintech_user -d fintech

# Verify schema
\dt
```

### Airflow DAG Not Running
```bash
# Check Airflow scheduler logs
docker compose logs airflow-scheduler

# Access Airflow UI
open http://localhost:8081

# Manually trigger DAG from UI or CLI
docker exec airflow-webserver airflow dags trigger etl_reconciliation
```

### Python Module Import Errors
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Docker Commands Cheatsheet

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs for all services
docker compose logs -f

# View logs for specific service
docker compose logs -f postgres
docker compose logs -f kafka

# Restart a service
docker compose restart postgres

# Check service status
docker compose ps

# Remove all containers and volumes (WARNING: deletes data)
docker compose down -v

# Access PostgreSQL shell
docker exec -it fintech-postgres psql -U fintech_user -d fintech

# Access Kafka container
docker exec -it fintech-fraud-detection-kafka-1 bash

# View container resource usage
docker stats
```

## Project Structure

```
fintech-fraud-detection/
├── database/
│   ├── init.sql              # PostgreSQL schema
│   └── db_config.py          # Database connection helpers
├── kafka_client/
│   ├── config.py             # Kafka configuration
│   └── producer.py           # Transaction generator with fraud injection
├── spark/
│   ├── fraud_detection_streaming.py  # Real-time fraud detection
│   └── spark_config.py       # Spark session configuration
├── airflow/
│   └── dags/
│       └── etl_reconciliation_dag.py  # Batch ETL workflow
├── reports/
│   └── generate_report.py    # Fraud analysis report generator
├── tests/
│   ├── test_phase1.py
│   ├── test_phase2.py
│   ├── test_phase3.py
│   ├── test_phase4.py
│   └── test_phase5.py
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Contributing

See `TODO.md` for phase-by-phase implementation tracking.

## License

MIT

---

For detailed requirements and design decisions, see `fintech_copilot_prompt.md`.
