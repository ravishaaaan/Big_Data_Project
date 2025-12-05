"""
Fraud Analysis Report Generator

This module generates comprehensive fraud analysis reports from the PostgreSQL database.
It produces statistics on fraud detection, transaction patterns, and system performance.
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from database.db_config import get_connection, query
from datetime import datetime, timezone
import json

OUTPUT_DIR = os.getenv('REPORT_OUTPUT_DIR', './reports/output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_transaction_statistics():
    """Get overall transaction statistics"""
    conn = get_connection()
    
    stats = {}
    
    # Total transactions
    result = query(conn, "SELECT COUNT(*) as count, SUM(amount) as total_amount FROM transactions")
    stats['total_transactions'] = result[0]['count'] if result else 0
    stats['total_transaction_amount'] = float(result[0]['total_amount']) if result and result[0]['total_amount'] else 0.0
    
    # Transactions by category
    result = query(conn, """
        SELECT merchant_category, COUNT(*) as count, SUM(amount) as total_amount 
        FROM transactions 
        GROUP BY merchant_category 
        ORDER BY count DESC
    """)
    stats['transactions_by_category'] = result if result else []
    
    conn.close()
    return stats


def get_fraud_statistics():
    """Get fraud detection statistics"""
    conn = get_connection()
    
    stats = {}
    
    # Total fraud alerts
    result = query(conn, "SELECT COUNT(*) as count FROM fraud_alerts")
    stats['total_fraud_alerts'] = result[0]['count'] if result else 0
    
    # Fraud by type
    result = query(conn, """
        SELECT fraud_type, COUNT(*) as count 
        FROM fraud_alerts 
        GROUP BY fraud_type 
        ORDER BY count DESC
    """)
    stats['fraud_by_type'] = result if result else []
    
    # Fraud with transaction details
    result = query(conn, """
        SELECT f.fraud_type, COUNT(*) as count, SUM(t.amount) as total_amount 
        FROM fraud_alerts f
        JOIN transactions t ON f.transaction_id = t.transaction_id
        GROUP BY f.fraud_type
    """)
    stats['fraud_impact'] = result if result else []
    
    # Fraud by merchant category
    result = query(conn, """
        SELECT t.merchant_category, COUNT(*) as fraud_count 
        FROM fraud_alerts f
        JOIN transactions t ON f.transaction_id = t.transaction_id
        GROUP BY t.merchant_category 
        ORDER BY fraud_count DESC
    """)
    stats['fraud_by_category'] = result if result else []
    
    conn.close()
    return stats


def get_validation_statistics():
    """Get validation and reconciliation statistics"""
    conn = get_connection()
    
    stats = {}
    
    # Validated transactions
    result = query(conn, "SELECT COUNT(*) as count, SUM(amount) as total_amount FROM validated_transactions")
    stats['validated_transactions'] = result[0]['count'] if result else 0
    stats['validated_amount'] = float(result[0]['total_amount']) if result and result[0]['total_amount'] else 0.0
    
    # Calculate fraud rate
    total_tx_result = query(conn, "SELECT COUNT(*) as count FROM transactions")
    total_tx = total_tx_result[0]['count'] if total_tx_result else 1
    
    fraud_tx_result = query(conn, "SELECT COUNT(*) as count FROM fraud_alerts")
    fraud_tx = fraud_tx_result[0]['count'] if fraud_tx_result else 0
    
    stats['fraud_rate_percent'] = (fraud_tx / total_tx * 100) if total_tx > 0 else 0.0
    
    conn.close()
    return stats


def get_system_performance():
    """Get system performance metrics"""
    conn = get_connection()
    
    stats = {}
    
    # Average processing time (event time vs processing time)
    result = query(conn, """
        SELECT AVG(EXTRACT(EPOCH FROM (processing_time - event_time))) as avg_latency_seconds
        FROM transactions
        WHERE processing_time IS NOT NULL AND event_time IS NOT NULL
    """)
    stats['avg_processing_latency_seconds'] = float(result[0]['avg_latency_seconds']) if result and result[0]['avg_latency_seconds'] else 0.0
    
    # Fraud detection latency
    result = query(conn, """
        SELECT AVG(EXTRACT(EPOCH FROM (f.detection_time - t.event_time))) as avg_detection_latency
        FROM fraud_alerts f
        JOIN transactions t ON f.transaction_id = t.transaction_id
        WHERE f.detection_time IS NOT NULL AND t.event_time IS NOT NULL
    """)
    stats['avg_fraud_detection_latency_seconds'] = float(result[0]['avg_detection_latency']) if result and result[0]['avg_detection_latency'] else 0.0
    
    conn.close()
    return stats


def fetch_data():
    """Legacy function for backward compatibility"""
    conn = get_connection()
    try:
        df = pd.read_sql('SELECT t.*, f.fraud_type FROM transactions t LEFT JOIN fraud_alerts f ON t.transaction_id = f.transaction_id', conn)
        return df
    finally:
        conn.close()


def generate_visualizations():
    """Generate fraud analysis visualizations"""
    df = fetch_data()
    if df.empty:
        print('No data available for visualizations')
        return
    
    df['is_fraud'] = df['fraud_type'].notnull()
    fraud_by_cat = df[df['is_fraud']].groupby('merchant_category').size().reset_index(name='count')
    
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    
    # Bar chart - Fraud count by merchant category
    plt.figure(figsize=(10, 6))
    sns.barplot(data=fraud_by_cat, x='merchant_category', y='count', palette='viridis')
    plt.xticks(rotation=45, ha='right')
    plt.title('Fraud Alerts by Merchant Category', fontsize=14, fontweight='bold')
    plt.ylabel('Number of Fraud Alerts')
    plt.xlabel('Merchant Category')
    plt.tight_layout()
    bar_path = os.path.join(OUTPUT_DIR, f'fraud_by_category_bar_{ts}.png')
    plt.savefig(bar_path, dpi=300)
    plt.close()
    print(f'✓ Saved bar chart to {bar_path}')
    
    # Pie chart - Fraud percentage distribution by type
    if 'fraud_type' in df.columns and df['fraud_type'].notnull().any():
        fraud_types = df[df['fraud_type'].notnull()]['fraud_type'].value_counts()
        plt.figure(figsize=(8, 8))
        colors = sns.color_palette('pastel')[0:len(fraud_types)]
        plt.pie(fraud_types.values, labels=fraud_types.index, autopct='%1.1f%%',
                startangle=90, colors=colors)
        plt.title('Fraud Type Distribution', fontsize=14, fontweight='bold')
        plt.axis('equal')
        plt.tight_layout()
        pie_path = os.path.join(OUTPUT_DIR, f'fraud_type_distribution_{ts}.png')
        plt.savefig(pie_path, dpi=300)
        plt.close()
        print(f'✓ Saved pie chart to {pie_path}')
    
    # Time series - Fraud attempts over time
    if 'event_time' in df.columns and pd.api.types.is_datetime64_any_dtype(df['event_time']):
        # Convert event_time to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df['event_time']):
            df['event_time'] = pd.to_datetime(df['event_time'])
        
        # Resample fraud events by hour
        fraud_df = df[df['is_fraud']].copy()
        if not fraud_df.empty:
            fraud_df.set_index('event_time', inplace=True)
            fraud_by_time = fraud_df.resample('H').size()
            
            plt.figure(figsize=(12, 6))
            plt.plot(fraud_by_time.index, fraud_by_time.values, marker='o', linestyle='-', color='red')
            plt.title('Fraud Attempts Over Time (Hourly)', fontsize=14, fontweight='bold')
            plt.ylabel('Number of Fraud Attempts')
            plt.xlabel('Time')
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            timeseries_path = os.path.join(OUTPUT_DIR, f'fraud_timeseries_{ts}.png')
            plt.savefig(timeseries_path, dpi=300)
            plt.close()
            print(f'✓ Saved time series chart to {timeseries_path}')

    # CSV
    csv_path = os.path.join(OUTPUT_DIR, f'fraud_summary_{ts}.csv')
    fraud_by_cat.to_csv(csv_path, index=False)
    print(f'✓ Saved CSV to {csv_path}')


def generate_console_report():
    """Generate a comprehensive console report"""
    print("=" * 80)
    print("FRAUD DETECTION SYSTEM - COMPREHENSIVE ANALYSIS REPORT")
    print(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)
    print()
    
    # Transaction Statistics
    print("📊 TRANSACTION STATISTICS")
    print("-" * 80)
    tx_stats = get_transaction_statistics()
    print(f"Total Transactions: {tx_stats['total_transactions']:,}")
    print(f"Total Transaction Amount: ${tx_stats['total_transaction_amount']:,.2f}")
    print()
    if tx_stats['transactions_by_category']:
        print("Transactions by Category:")
        for cat in tx_stats['transactions_by_category']:
            print(f"  • {cat['merchant_category']}: {cat['count']:,} transactions (${float(cat['total_amount']):,.2f})")
    print()
    
    # Fraud Statistics
    print("🚨 FRAUD DETECTION STATISTICS")
    print("-" * 80)
    fraud_stats = get_fraud_statistics()
    print(f"Total Fraud Alerts: {fraud_stats['total_fraud_alerts']:,}")
    print()
    if fraud_stats['fraud_by_type']:
        print("Fraud by Type:")
        for ft in fraud_stats['fraud_by_type']:
            print(f"  • {ft['fraud_type']}: {ft['count']:,} alerts")
    print()
    if fraud_stats['fraud_impact']:
        print("Fraud Impact:")
        for fi in fraud_stats['fraud_impact']:
            print(f"  • {fi['fraud_type']}: ${float(fi['total_amount']):,.2f} (from {fi['count']} transactions)")
    print()
    if fraud_stats['fraud_by_category']:
        print("Fraud by Merchant Category:")
        for fc in fraud_stats['fraud_by_category']:
            print(f"  • {fc['merchant_category']}: {fc['fraud_count']:,} fraud alerts")
    print()
    
    # Validation Statistics
    print("✅ VALIDATION & RECONCILIATION")
    print("-" * 80)
    val_stats = get_validation_statistics()
    print(f"Validated Transactions: {val_stats['validated_transactions']:,}")
    print(f"Validated Amount: ${val_stats['validated_amount']:,.2f}")
    print(f"Fraud Rate: {val_stats['fraud_rate_percent']:.2f}%")
    print()
    
    # System Performance
    print("⚡ SYSTEM PERFORMANCE")
    print("-" * 80)
    perf_stats = get_system_performance()
    print(f"Average Processing Latency: {perf_stats['avg_processing_latency_seconds']:.3f} seconds")
    print(f"Average Fraud Detection Latency: {perf_stats['avg_fraud_detection_latency_seconds']:.3f} seconds")
    print()
    
    print("=" * 80)
    print("END OF REPORT")
    print("=" * 80)
    
    # Return all stats for testing
    return {
        'transaction_stats': tx_stats,
        'fraud_stats': fraud_stats,
        'validation_stats': val_stats,
        'performance_stats': perf_stats
    }


def save_report_json(filename='fraud_analysis_report.json'):
    """Save report as JSON file"""
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'transaction_stats': get_transaction_statistics(),
        'fraud_stats': get_fraud_statistics(),
        'validation_stats': get_validation_statistics(),
        'performance_stats': get_system_performance()
    }
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"✓ Report saved to: {filepath}")
    return filepath


def generate_pdf_report():
    """Generate comprehensive PDF report with visualizations"""
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    pdf_path = os.path.join(OUTPUT_DIR, f'fraud_analysis_report_{ts}.pdf')
    
    # Get all statistics
    tx_stats = get_transaction_statistics()
    fraud_stats = get_fraud_statistics()
    val_stats = get_validation_statistics()
    perf_stats = get_system_performance()
    
    with PdfPages(pdf_path) as pdf:
        # Page 1: Summary Statistics
        fig = plt.figure(figsize=(11, 8.5))
        fig.suptitle('Fraud Detection System - Analysis Report', fontsize=16, fontweight='bold')
        
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        report_text = f"""
Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

TRANSACTION STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Transactions: {tx_stats['total_transactions']:,}
Total Transaction Amount: ${tx_stats['total_transaction_amount']:,.2f}

FRAUD DETECTION STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Fraud Alerts: {fraud_stats['total_fraud_alerts']:,}
Fraud Rate: {val_stats['fraud_rate_percent']:.2f}%

VALIDATION & RECONCILIATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validated Transactions: {val_stats['validated_transactions']:,}
Validated Amount: ${val_stats['validated_amount']:,.2f}

SYSTEM PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Average Processing Latency: {perf_stats['avg_processing_latency_seconds']:.3f} seconds
Average Fraud Detection Latency: {perf_stats['avg_fraud_detection_latency_seconds']:.3f} seconds
"""
        
        ax.text(0.1, 0.9, report_text, fontsize=11, family='monospace',
                verticalalignment='top', transform=ax.transAxes)
        
        pdf.savefig(fig)
        plt.close()
        
        # Page 2: Visualizations
        df = fetch_data()
        if not df.empty:
            df['is_fraud'] = df['fraud_type'].notnull()
            
            # Bar chart
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8.5))
            
            fraud_by_cat = df[df['is_fraud']].groupby('merchant_category').size().reset_index(name='count')
            sns.barplot(data=fraud_by_cat, x='merchant_category', y='count', palette='viridis', ax=ax1)
            ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha='right')
            ax1.set_title('Fraud Alerts by Merchant Category', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Number of Fraud Alerts')
            
            # Pie chart
            if 'fraud_type' in df.columns and df['fraud_type'].notnull().any():
                fraud_types = df[df['fraud_type'].notnull()]['fraud_type'].value_counts()
                colors = sns.color_palette('pastel')[0:len(fraud_types)]
                ax2.pie(fraud_types.values, labels=fraud_types.index, autopct='%1.1f%%',
                       startangle=90, colors=colors)
                ax2.set_title('Fraud Type Distribution', fontsize=12, fontweight='bold')
            
            plt.tight_layout()
            pdf.savefig(fig)
            plt.close()
    
    print(f"✓ PDF report saved to: {pdf_path}")
    return pdf_path


def generate():
    """Main function to generate all reports"""
    generate_console_report()
    
    if '--visualizations' in sys.argv or '-v' in sys.argv:
        generate_visualizations()
    
    if '--json' in sys.argv or '-j' in sys.argv:
        save_report_json()
    
    if '--pdf' in sys.argv or '-p' in sys.argv:
        generate_pdf_report()
    
    # Generate all formats if --all flag provided
    if '--all' in sys.argv or '-a' in sys.argv:
        generate_visualizations()
        save_report_json()
        generate_pdf_report()


if __name__ == '__main__':
    generate()

