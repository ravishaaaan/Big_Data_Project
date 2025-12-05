#!/bin/bash

# FinTech Fraud Detection - Deliverables Generation Pipeline
# This script runs the system and captures all required outputs

set -e

DELIVERABLES_DIR="deliverables"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "=========================================="
echo "FinTech Fraud Detection Pipeline"
echo "Deliverables Generation Started"
echo "Timestamp: $TIMESTAMP"
echo "=========================================="
echo ""

# Create deliverables directory
mkdir -p "$DELIVERABLES_DIR"

# Step 1: Start Docker Services
echo "Step 1: Starting Docker services..."
docker compose up -d
echo "✓ Docker services started"
echo ""

# Step 2: Wait for services to be ready
echo "Step 2: Waiting for services to be ready..."
echo -n "Waiting for PostgreSQL..."
until docker exec fintech-fraud-detection-postgres-1 pg_isready -U fintech_user -d fintech_db > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " Ready!"

echo -n "Waiting for Kafka..."
sleep 10
until docker exec fintech-fraud-detection-kafka-1 kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " Ready!"
echo ""

# Step 3: Create Kafka topics
echo "Step 3: Creating Kafka topics..."
docker exec fintech-fraud-detection-kafka-1 kafka-topics --create --topic transactions --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists > /dev/null 2>&1
docker exec fintech-fraud-detection-kafka-1 kafka-topics --create --topic fraud-alerts --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists > /dev/null 2>&1
echo "✓ Kafka topics created"
echo ""

# Step 4: Start Kafka Producer and capture output
echo "=========================================="
echo "DELIVERABLE 1: Kafka Producer Console Output"
echo "=========================================="
PRODUCER_LOG="$DELIVERABLES_DIR/1_kafka_producer_output_${TIMESTAMP}.txt"
echo "Starting Kafka Producer (will run for 60 seconds)..."
echo "Output will be saved to: $PRODUCER_LOG"
echo ""

(
    echo "Kafka Producer Output - $(date)" > "$PRODUCER_LOG"
    echo "========================================" >> "$PRODUCER_LOG"
    echo "" >> "$PRODUCER_LOG"
    source .venv/bin/activate
    timeout 60 python kafka_client/producer.py 2>&1 | tee -a "$PRODUCER_LOG" || true
) &
PRODUCER_PID=$!

# Wait for producer to generate some data
sleep 15

# Step 5: Start Spark Streaming and capture output
echo ""
echo "=========================================="
echo "DELIVERABLE 2: Spark Streaming Console Output"
echo "=========================================="
SPARK_LOG="$DELIVERABLES_DIR/2_spark_streaming_output_${TIMESTAMP}.txt"
echo "Starting Spark Streaming (will run for 50 seconds)..."
echo "Output will be saved to: $SPARK_LOG"
echo ""

(
    echo "Spark Streaming Output - $(date)" > "$SPARK_LOG"
    echo "========================================" >> "$SPARK_LOG"
    echo "" >> "$SPARK_LOG"
    source .venv/bin/activate
    timeout 50 python spark/fraud_detection_streaming.py 2>&1 | tee -a "$SPARK_LOG" || true
) &
SPARK_PID=$!

# Wait for both producer and spark to finish
wait $PRODUCER_PID 2>/dev/null || true
wait $SPARK_PID 2>/dev/null || true

echo ""
echo "✓ Kafka Producer and Spark Streaming completed"
echo ""

# Give Spark a moment to flush final batches
sleep 5

# Step 6: Trigger Airflow DAG and capture output
echo "=========================================="
echo "DELIVERABLE 3: Airflow DAG Execution Output"
echo "=========================================="
AIRFLOW_LOG="$DELIVERABLES_DIR/3_airflow_dag_output_${TIMESTAMP}.txt"
echo "Triggering Airflow ETL DAG..."
echo "Output will be saved to: $AIRFLOW_LOG"
echo ""

(
    echo "Airflow DAG Execution Output - $(date)" > "$AIRFLOW_LOG"
    echo "========================================" >> "$AIRFLOW_LOG"
    echo "" >> "$AIRFLOW_LOG"
    
    source .venv/bin/activate
    
    # Initialize Airflow DB if needed
    echo "Initializing Airflow..." | tee -a "$AIRFLOW_LOG"
    export AIRFLOW_HOME=$(pwd)/airflow
    airflow db init >> "$AIRFLOW_LOG" 2>&1 || true
    
    # Test the DAG
    echo "" | tee -a "$AIRFLOW_LOG"
    echo "Testing DAG tasks..." | tee -a "$AIRFLOW_LOG"
    airflow tasks test etl_reconciliation_dag extract_non_fraud_transactions 2024-12-06 2>&1 | tee -a "$AIRFLOW_LOG" || true
    echo "" | tee -a "$AIRFLOW_LOG"
    airflow tasks test etl_reconciliation_dag transform_data 2024-12-06 2>&1 | tee -a "$AIRFLOW_LOG" || true
    echo "" | tee -a "$AIRFLOW_LOG"
    airflow tasks test etl_reconciliation_dag load_to_validated_transactions 2024-12-06 2>&1 | tee -a "$AIRFLOW_LOG" || true
    echo "" | tee -a "$AIRFLOW_LOG"
    airflow tasks test etl_reconciliation_dag generate_reconciliation_report 2024-12-06 2>&1 | tee -a "$AIRFLOW_LOG" || true
    echo "" | tee -a "$AIRFLOW_LOG"
    airflow tasks test etl_reconciliation_dag calculate_fraud_by_merchant 2024-12-06 2>&1 | tee -a "$AIRFLOW_LOG" || true
)

echo ""
echo "✓ Airflow DAG execution completed"
echo ""

# Step 7: Generate Reconciliation Report
echo "=========================================="
echo "DELIVERABLE 4: Reconciliation Report (TXT)"
echo "=========================================="
RECONCILIATION_REPORT="$DELIVERABLES_DIR/4_reconciliation_report_${TIMESTAMP}.txt"
echo "Generating reconciliation report..."
echo "Output will be saved to: $RECONCILIATION_REPORT"
echo ""

source .venv/bin/activate
python << EOF > "$RECONCILIATION_REPORT" 2>&1
import psycopg2
from datetime import datetime

print("=" * 60)
print("FINANCIAL RECONCILIATION REPORT")
print("=" * 60)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)
print()

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="fintech_db",
        user="fintech_user",
        password="fintech_pass"
    )
    cur = conn.cursor()
    
    # Total transactions
    cur.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM transactions")
    total_count, total_amount = cur.fetchone()
    
    # Fraud transactions
    cur.execute("""
        SELECT COUNT(DISTINCT fa.transaction_id), COALESCE(SUM(t.amount), 0)
        FROM fraud_alerts fa
        JOIN transactions t ON fa.transaction_id = t.transaction_id
    """)
    fraud_count, fraud_amount = cur.fetchone()
    
    # Validated transactions
    cur.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM validated_transactions")
    validated_count, validated_amount = cur.fetchone()
    
    print("TRANSACTION SUMMARY")
    print("-" * 60)
    print(f"Total Transactions Ingested:     {total_count:>10}")
    print(f"Total Amount Ingested:           ${total_amount:>10,.2f}")
    print()
    print(f"Fraud Transactions Detected:     {fraud_count:>10}")
    print(f"Fraud Amount Detected:           ${fraud_amount:>10,.2f}")
    print(f"Fraud Percentage:                {(fraud_count/total_count*100 if total_count > 0 else 0):>9.2f}%")
    print()
    print(f"Validated Transactions:          {validated_count:>10}")
    print(f"Validated Amount:                ${validated_amount:>10,.2f}")
    print()
    print("=" * 60)
    print("RECONCILIATION CHECK")
    print("-" * 60)
    
    expected_validated = total_count - fraud_count
    amount_check = abs(total_amount - (fraud_amount + validated_amount))
    
    print(f"Expected Validated Count:        {expected_validated:>10}")
    print(f"Actual Validated Count:          {validated_count:>10}")
    print(f"Count Difference:                {abs(expected_validated - validated_count):>10}")
    print()
    print(f"Amount Reconciliation:           ${amount_check:>10,.2f}")
    print()
    
    if amount_check < 0.01:
        print("✓ RECONCILIATION SUCCESSFUL - All amounts match!")
    else:
        print("⚠ RECONCILIATION WARNING - Amount mismatch detected")
    
    print("=" * 60)
    
    # Fraud by type
    print()
    print("FRAUD BREAKDOWN BY TYPE")
    print("-" * 60)
    cur.execute("""
        SELECT fraud_type, COUNT(*), COALESCE(SUM(t.amount), 0)
        FROM fraud_alerts fa
        JOIN transactions t ON fa.transaction_id = t.transaction_id
        GROUP BY fraud_type
        ORDER BY COUNT(*) DESC
    """)
    
    for fraud_type, count, amount in cur.fetchall():
        print(f"{fraud_type:<25} {count:>6} transactions  ${amount:>10,.2f}")
    
    print("=" * 60)
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error generating report: {e}")
EOF

cat "$RECONCILIATION_REPORT"
echo ""
echo "✓ Reconciliation report generated"
echo ""

# Step 8: Generate Fraud by Merchant Category Report (CSV)
echo "=========================================="
echo "DELIVERABLE 5: Fraud by Merchant Category (CSV)"
echo "=========================================="
MERCHANT_CSV="$DELIVERABLES_DIR/5_fraud_by_merchant_category_${TIMESTAMP}.csv"
echo "Generating fraud by merchant category report..."
echo "Output will be saved to: $MERCHANT_CSV"
echo ""

source .venv/bin/activate
python << EOF
import psycopg2
import csv

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="fintech_db",
        user="fintech_user",
        password="fintech_pass"
    )
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            t.merchant_category,
            COUNT(*) as fraud_count,
            ROUND(AVG(t.amount)::numeric, 2) as avg_fraud_amount,
            ROUND(SUM(t.amount)::numeric, 2) as total_fraud_amount,
            COUNT(DISTINCT fa.fraud_type) as fraud_types_count
        FROM fraud_alerts fa
        JOIN transactions t ON fa.transaction_id = t.transaction_id
        GROUP BY t.merchant_category
        ORDER BY fraud_count DESC
    """)
    
    rows = cur.fetchall()
    
    with open('$MERCHANT_CSV', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Merchant Category', 'Fraud Count', 'Avg Fraud Amount', 'Total Fraud Amount', 'Fraud Types Count'])
        writer.writerows(rows)
    
    print(f"✓ Generated CSV with {len(rows)} merchant categories")
    
    # Display preview
    print("\nPreview:")
    print("-" * 80)
    print(f"{'Merchant Category':<20} {'Fraud Count':>12} {'Avg Amount':>15} {'Total Amount':>15}")
    print("-" * 80)
    for row in rows:
        print(f"{row[0]:<20} {row[1]:>12} ${float(row[2]):>14,.2f} ${float(row[3]):>14,.2f}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
EOF

echo ""
echo "✓ Fraud by merchant category report generated"
echo ""

# Step 9: Generate Comprehensive Fraud Analysis Report (PDF)
echo "=========================================="
echo "DELIVERABLE 6: Comprehensive Fraud Analysis (PDF)"
echo "=========================================="
PDF_REPORT="$DELIVERABLES_DIR/6_comprehensive_fraud_analysis_${TIMESTAMP}.pdf"
echo "Generating comprehensive fraud analysis report..."
echo "Output will be saved to: $PDF_REPORT"
echo ""

source .venv/bin/activate
python reports/generate_report.py --pdf --output "$PDF_REPORT"

echo ""
echo "✓ Comprehensive fraud analysis PDF generated"
echo ""

# Step 10: Summary
echo "=========================================="
echo "DELIVERABLES GENERATION COMPLETED"
echo "=========================================="
echo ""
echo "All deliverables have been generated in the '$DELIVERABLES_DIR' directory:"
echo ""
echo "1. Kafka Producer Output:          $PRODUCER_LOG"
echo "2. Spark Streaming Output:         $SPARK_LOG"
echo "3. Airflow DAG Output:             $AIRFLOW_LOG"
echo "4. Reconciliation Report (TXT):    $RECONCILIATION_REPORT"
echo "5. Fraud by Merchant (CSV):        $MERCHANT_CSV"
echo "6. Comprehensive Analysis (PDF):   $PDF_REPORT"
echo ""
echo "=========================================="
echo "Pipeline execution completed at $(date)"
echo "=========================================="
