#!/usr/bin/env python3
import psycopg2
import csv
import sys

try:
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'fraud_by_merchant.csv'
    
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
    
    with open(output_file, 'w', newline='') as f:
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
    sys.exit(1)
