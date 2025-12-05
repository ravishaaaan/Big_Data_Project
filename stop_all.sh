#!/bin/bash

# FinTech Fraud Detection Pipeline - Shutdown Script
# This script stops all components of the fraud detection system

set -e

echo "=========================================="
echo "FinTech Fraud Detection Pipeline"
echo "Stopping All Services..."
echo "=========================================="
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Step 1: Stop Kafka Producer
echo "📨 Step 1: Stopping Kafka producer..."
pkill -f "kafka_client/producer.py" 2>/dev/null && echo "✓ Kafka Producer stopped" || echo "  No Kafka Producer process found"
echo ""

# Step 2: Stop Spark Streaming
echo "⚡ Step 2: Stopping Spark Streaming..."
pkill -f "fraud_detection_streaming.py" 2>/dev/null && echo "✓ Spark Streaming stopped" || echo "  No Spark Streaming process found"
echo ""

# Step 3: Stop Docker services
echo "📦 Step 3: Stopping Docker services..."
docker compose down
echo "✓ Docker services stopped"
echo ""

# Step 4: Cleanup
echo "🧹 Step 4: Cleaning up..."
# Optional: Clear checkpoint directories
# rm -rf /tmp/spark-checkpoints/*
echo "✓ Cleanup complete"
echo ""

echo "=========================================="
echo "✅ All Services Stopped Successfully!"
echo "=========================================="
echo ""
echo "To start all services again, run: ./start_all.sh"
echo "=========================================="
