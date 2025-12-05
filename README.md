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

3. Start infrastructure services:
```bash
docker compose up -d
```

4. Initialize PostgreSQL schema:
```bash
docker exec -i fintech-postgres psql -U fintech_user -d fintech < database/init.sql
```

## Usage

### Start the Kafka Producer

Generate synthetic transactions with fraud patterns:

```bash
python kafka_client/producer.py
```

This generates:
- 85% normal transactions ($10-$1,000)
- 10% impossible travel fraud (multiple locations in 5-8 minutes)
- 5% high-value fraud ($5,000-$10,000)

### Start Spark Streaming Job

Run real-time fraud detection:

```bash
python spark/fraud_detection_streaming.py
```

Monitors Kafka stream and writes fraud alerts to PostgreSQL.

### Trigger Airflow DAG

Access Airflow UI at http://localhost:8081 and trigger `etl_reconciliation` DAG manually, or wait for the 6-hour schedule.

### Generate Reports

Create comprehensive fraud analysis reports:

```bash
python reports/generate_report.py

# With visualizations:
python reports/generate_report.py --visualizations

# Save as JSON:
python reports/generate_report.py --json
```

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

- **Phase 1**: Database & Kafka infrastructure (best-effort, Docker-dependent)
- **Phase 2**: Fraud generation logic (4 tests passed)
- **Phase 3**: Spark streaming fraud detection (5 tests passed)
- **Phase 4**: Airflow ETL & reconciliation (7 tests passed)
- **Phase 5**: Final integration & documentation (8 tests passed)

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
