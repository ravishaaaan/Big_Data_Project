#!/bin/bash

# FinTech Fraud Detection Pipeline - Startup Script
# This script starts all components of the fraud detection system

set -e

echo "=========================================="
echo "FinTech Fraud Detection Pipeline"
echo "Starting All Services..."
echo "=========================================="
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Step 1: Start Docker services
echo "📦 Step 1: Starting Docker services (PostgreSQL, Kafka, Zookeeper, Spark, Airflow)..."
docker compose up -d
sleep 5

echo "✓ Docker services started"
echo ""

# Step 2: Wait for services to be ready
echo "⏳ Step 2: Waiting for services to initialize..."
sleep 15

# Check PostgreSQL
until docker exec fintech-postgres pg_isready -U fintech_user > /dev/null 2>&1; do
  echo "  Waiting for PostgreSQL..."
  sleep 2
done
echo "✓ PostgreSQL is ready"

# Check Kafka
until docker exec fintech-fraud-detection-kafka-1 kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; do
  echo "  Waiting for Kafka..."
  sleep 2
done
echo "✓ Kafka is ready"
echo ""

# Step 3: Create Kafka topics
echo "📋 Step 3: Creating Kafka topics..."
docker exec fintech-fraud-detection-kafka-1 kafka-topics --create --if-not-exists --topic transactions --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 2>/dev/null || echo "  Topic 'transactions' already exists"
docker exec fintech-fraud-detection-kafka-1 kafka-topics --create --if-not-exists --topic fraud-alerts --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 2>/dev/null || echo "  Topic 'fraud-alerts' already exists"
echo "✓ Kafka topics created"
echo ""

# Step 4: Start Spark Streaming
echo "⚡ Step 4: Starting Spark Streaming fraud detection..."
nohup ./run_spark.sh > /tmp/spark_output.log 2>&1 &
SPARK_PID=$!
echo "✓ Spark Streaming started (PID: $SPARK_PID)"
echo ""

# Step 5: Start Kafka Producer
echo "📨 Step 5: Starting Kafka producer..."
source .venv/bin/activate
nohup python3 kafka_client/producer.py > /tmp/producer_output.log 2>&1 &
PRODUCER_PID=$!
echo "✓ Kafka Producer started (PID: $PRODUCER_PID)"
echo ""

# Step 6: Display status
echo "=========================================="
echo "✅ All Services Started Successfully!"
echo "=========================================="
echo ""
echo "Service Status:"
echo "  • PostgreSQL: localhost:5432"
echo "  • Kafka: localhost:9092"
echo "  • Spark Master UI: http://localhost:8080"
echo "  • Airflow UI: http://localhost:8081 (user: admin, pass: admin)"
echo ""
echo "Background Processes:"
echo "  • Spark Streaming PID: $SPARK_PID"
echo "  • Kafka Producer PID: $PRODUCER_PID"
echo ""
echo "Logs:"
echo "  • Spark: tail -f /tmp/spark_output.log"
echo "  • Producer: tail -f /tmp/producer_output.log"
echo ""
echo "To stop all services, run: ./stop_all.sh"
echo "=========================================="
