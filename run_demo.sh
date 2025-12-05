#!/bin/bash

# FinTech Fraud Detection System - Run Script

echo "🚀 Starting FinTech Fraud Detection System..."
echo ""

# Check Docker services
echo "📋 Checking Docker services..."
docker compose ps

echo ""
echo "=" * 80
echo "✅ System Status:"
echo "   ✓ PostgreSQL: Running on port 5432"
echo "   ✓ Kafka: Running on port 9092"
echo "   ✓ Zookeeper: Running on port 2181"
echo ""
echo "🎯 Running Fraud Detection Demo..."
echo "=" * 80
echo ""

# Activate virtual environment and run demo
source .venv/bin/activate
python demo.py 30
