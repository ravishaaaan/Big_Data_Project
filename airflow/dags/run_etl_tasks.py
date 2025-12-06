#!/usr/bin/env python3
"""
Standalone ETL Task Runner
Runs ETL tasks without Airflow dependencies (Python 3.14 compatible)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.db_config import get_connection, query
import pandas as pd
from datetime import datetime

def extract_non_fraud():
    """Extract transactions that are not flagged as fraud"""
    print("Task 1: Extracting non-fraud transactions...")
    conn = get_connection()
    sql = """
    SELECT t.* FROM transactions t
    LEFT JOIN fraud_alerts f ON t.transaction_id = f.transaction_id
    WHERE f.transaction_id IS NULL
    """
    rows = query(conn, sql, None)
    conn.close()
    print(f"✓ Extracted {len(rows)} non-fraud transactions")
    return rows

def transform(rows):
    """Transform extracted data"""
    print("\nTask 2: Transforming data...")
    if not rows:
        print("✓ No data to transform")
        return [], {'total_ingest': 0.0, 'validated_amount': 0.0, 'by_category': []}
    
    df = pd.DataFrame(rows)
    
    # Aggregations by merchant category
    totals = df.groupby('merchant_category')['amount'].sum().reset_index()
    
    summary = {
        'total_ingest': float(df['amount'].sum()),
        'validated_amount': float(df['amount'].sum()),
        'by_category': totals.to_dict(orient='records')
    }
    
    print(f"✓ Transformed data - Total amount: ${summary['total_ingest']:,.2f}")
    return df.to_dict(orient='records'), summary

def load_validated(transformed_rows):
    """Load validated transactions into database"""
    print("\nTask 3: Loading validated transactions...")
    if not transformed_rows:
        print("✓ No data to load")
        return True
    
    conn = get_connection()
    cursor = conn.cursor()
    
    insert_sql = """
    INSERT INTO validated_transactions 
    (transaction_id, user_id, event_time, merchant_category, amount, location, processing_time)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (transaction_id) DO NOTHING
    """
    
    inserted = 0
    for r in transformed_rows:
        cursor.execute(insert_sql, (
            r['transaction_id'],
            r['user_id'],
            r['event_time'],
            r['merchant_category'],
            r['amount'],
            r['location'],
            r['processing_time']
        ))
        inserted += cursor.rowcount
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✓ Loaded {inserted} records into validated_transactions")
    return True

def generate_reconciliation_report(summary):
    """Generate reconciliation report"""
    print("\nTask 4: Generating reconciliation report...")
    conn = get_connection()
    
    # Get total ingested amount
    total_ingest_result = query(conn, 'SELECT SUM(amount) FROM transactions', None)
    total_ingest = float(total_ingest_result[0]['sum']) if total_ingest_result and total_ingest_result[0]['sum'] else 0.0
    
    # Get fraud total
    fraud_sql = """
    SELECT SUM(t.amount) FROM transactions t 
    JOIN fraud_alerts f ON t.transaction_id = f.transaction_id
    """
    fraud_result = query(conn, fraud_sql, None)
    fraud_total = float(fraud_result[0]['sum']) if fraud_result and fraud_result[0]['sum'] else 0.0
    
    # Get validated total
    validated_result = query(conn, 'SELECT SUM(amount) FROM validated_transactions', None)
    validated_total = float(validated_result[0]['sum']) if validated_result and validated_result[0]['sum'] else 0.0
    
    # Get fraud by category
    cat_sql = """
    SELECT t.merchant_category, COUNT(*) as count
    FROM transactions t 
    JOIN fraud_alerts f ON t.transaction_id = f.transaction_id
    GROUP BY t.merchant_category
    """
    cat_counts = query(conn, cat_sql, None)
    
    conn.close()
    
    report = {
        'total_ingest': total_ingest,
        'fraud_total': fraud_total,
        'validated_total': validated_total,
        'fraud_by_category': [{'merchant_category': c['merchant_category'], 'count': c['count']} for c in cat_counts]
    }
    
    print(f"\n{'='*60}")
    print("RECONCILIATION REPORT")
    print(f"{'='*60}")
    print(f"Total Ingested:      ${report['total_ingest']:>15,.2f}")
    print(f"Fraud Amount:        ${report['fraud_total']:>15,.2f}")
    print(f"Validated Amount:    ${report['validated_total']:>15,.2f}")
    print(f"{'='*60}")
    
    if abs((report['total_ingest'] - report['fraud_total']) - report['validated_total']) < 0.01:
        print("✓ Reconciliation PASSED: Ingested = Fraud + Validated")
    else:
        print("✗ Reconciliation FAILED: Amounts do not match")
    
    print(f"\nFraud by Category:")
    for item in report['fraud_by_category']:
        print(f"  - {item['merchant_category']}: {item['count']} fraud transactions")
    print(f"{'='*60}\n")
    
    return report

def calculate_fraud_by_merchant():
    """Calculate fraud statistics by merchant category"""
    print("\nTask 5: Calculating fraud statistics by merchant...")
    conn = get_connection()
    
    sql = """
    SELECT 
        t.merchant_category,
        COUNT(DISTINCT f.transaction_id) as fraud_count,
        COALESCE(SUM(t.amount), 0) as total_fraud_amount
    FROM fraud_alerts f
    JOIN transactions t ON f.transaction_id = t.transaction_id
    GROUP BY t.merchant_category
    ORDER BY fraud_count DESC
    """
    
    results = query(conn, sql, None)
    conn.close()
    
    print(f"\nMerchant Category Fraud Analysis:")
    print(f"{'Category':<20} {'Fraud Count':>12} {'Total Amount':>15}")
    print(f"{'-'*50}")
    
    for row in results:
        print(f"{row['merchant_category']:<20} {row['fraud_count']:>12} ${row['total_fraud_amount']:>14,.2f}")
    
    print(f"✓ Analyzed {len(results)} merchant categories\n")
    return results

def main():
    """Run all ETL tasks"""
    print(f"\n{'='*60}")
    print("ETL Reconciliation DAG - Direct Execution")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        # Execute tasks in sequence
        rows = extract_non_fraud()
        transformed_rows, summary = transform(rows)
        load_validated(transformed_rows)
        report = generate_reconciliation_report(summary)
        fraud_stats = calculate_fraud_by_merchant()
        
        print(f"{'='*60}")
        print("✓ All ETL tasks completed successfully")
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        return 0
    except Exception as e:
        print(f"\n✗ Error during ETL execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
