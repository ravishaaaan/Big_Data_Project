# FinTech Fraud Detection Pipeline

End-to-end Lambda architecture for real-time fraud detection in a digital wallet system. Ingests transaction events via Kafka, processes them in real-time with Spark Structured Streaming, and runs batch reconciliation with Airflow. PostgreSQL stores transactions and alerts. Docker Compose is used for local infrastructure.

Architecture overview (high-level):
- Producers: Kafka producer generates synthetic transactions
- Real-time: Spark Structured Streaming reads Kafka topic, detects fraud (Impossible Travel, High-Value), writes alerts & transactions to PostgreSQL
- Batch: Airflow DAG extracts non-fraud transactions, transforms and loads into `validated_transactions`, and produces reconciliation reports

Setup (placeholder):
1. Install Docker & Docker Compose
2. Configure environment variables (see `.env.example`)
3. Start services: `docker compose up -d`
4. Start producer: `python kafka/producer.py`
5. Start Spark job: `python spark/fraud_detection_streaming.py`
6. Trigger Airflow DAG via UI or CLI

See the `fintech_copilot_prompt.md` for full requirements and design decisions.
