from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
from datetime import timedelta

DEFAULT_ARGS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='etl_reconciliation',
    default_args=DEFAULT_ARGS,
    schedule_interval='0 */6 * * *',  # every 6 hours
    start_date=days_ago(1),
    catchup=False,
) as dag:

    @task()
    def extract_non_fraud():
        pg = PostgresHook(postgres_conn_id='postgres_default')
        sql = """
        SELECT t.* FROM transactions t
        LEFT JOIN fraud_alerts f ON t.transaction_id = f.transaction_id
        WHERE f.transaction_id IS NULL
        """
        return pg.get_records(sql)

    @task()
    def transform(rows):
        import pandas as pd
        df = pd.DataFrame(rows, columns=['transaction_id','user_id','event_time','merchant_category','amount','location','processing_time'])
        # simple aggregations
        totals = df.groupby('merchant_category').amount.sum().reset_index()
        summary = {
            'total_ingest': float(df['amount'].sum()),
            'validated_amount': float(df['amount'].sum()),
            'by_category': totals.to_dict(orient='records')
        }
        return df.to_dict(orient='records'), summary

    @task()
    def load_validated(transformed_rows):
        pg = PostgresHook(postgres_conn_id='postgres_default')
        insert_sql = "INSERT INTO validated_transactions (transaction_id,user_id,event_time,merchant_category,amount,location,processing_time) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (transaction_id) DO NOTHING"
        for r in transformed_rows:
            pg.run(insert_sql, parameters=(r['transaction_id'], r['user_id'], r['event_time'], r['merchant_category'], r['amount'], r['location'], r['processing_time']))
        return True

    @task()
    def generate_reconciliation_report(summary):
        pg = PostgresHook(postgres_conn_id='postgres_default')
        # Totals
        total_ingest = pg.get_first('SELECT SUM(amount) FROM transactions')[0] or 0.0
        fraud_total = pg.get_first('SELECT SUM(t.amount) FROM transactions t JOIN fraud_alerts f ON t.transaction_id = f.transaction_id')[0] or 0.0
        validated_total = pg.get_first('SELECT SUM(amount) FROM validated_transactions')[0] or 0.0
        report = {
            'total_ingest': float(total_ingest),
            'fraud_total': float(fraud_total),
            'validated_total': float(validated_total)
        }
        # Fraud attempts by merchant_category
        cat_counts = pg.get_records('SELECT merchant_category, COUNT(*) FROM transactions t JOIN fraud_alerts f ON t.transaction_id = f.transaction_id GROUP BY merchant_category')
        report['fraud_by_category'] = [{ 'merchant_category': c[0], 'count': c[1]} for c in cat_counts]
        print('Reconciliation report:', report)
        return report

    rows = extract_non_fraud()
    transformed_rows, summary = transform(rows)
    loaded = load_validated(transformed_rows)
    report = generate_reconciliation_report(summary)

    rows >> transform >> load_validated >> generate_reconciliation_report
