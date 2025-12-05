#!/usr/bin/env python3
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
