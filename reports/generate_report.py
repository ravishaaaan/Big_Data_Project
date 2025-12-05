import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from database.db_config import get_connection
from datetime import datetime

OUTPUT_DIR = os.getenv('REPORT_OUTPUT_DIR', './reports/output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_data():
    conn = get_connection()
    try:
        df = pd.read_sql('SELECT t.*, f.fraud_type FROM transactions t LEFT JOIN fraud_alerts f ON t.transaction_id = f.transaction_id', conn)
        return df
    finally:
        conn.close()


def generate():
    df = fetch_data()
    if df.empty:
        print('No data to generate report')
        return
    df['is_fraud'] = df['fraud_type'].notnull()
    fraud_by_cat = df[df['is_fraud']].groupby('merchant_category').size().reset_index(name='count')
    # Bar chart
    plt.figure(figsize=(8,6))
    sns.barplot(data=fraud_by_cat, x='merchant_category', y='count')
    plt.xticks(rotation=45)
    plt.tight_layout()
    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    bar_path = os.path.join(OUTPUT_DIR, f'fraud_by_category_{ts}.png')
    plt.savefig(bar_path)
    print('Saved bar chart to', bar_path)

    # CSV
    csv_path = os.path.join(OUTPUT_DIR, f'fraud_summary_{ts}.csv')
    fraud_by_cat.to_csv(csv_path, index=False)
    print('Saved CSV to', csv_path)

    # Simple console summary
    print('Fraud counts by category:')
    print(fraud_by_cat)


if __name__ == '__main__':
    generate()
