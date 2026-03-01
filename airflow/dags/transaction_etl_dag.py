"""
Transaction ETL DAG
Daily ETL pipeline for transaction data processing
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator


default_args = {
    'owner': 'efinance',
    'depends_on_past': False,
    'email': ['data-team@efinance.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}


def extract_transactions(**context):
    """Extract transactions from source database"""
    execution_date = context['ds']
    
    hook = PostgresHook(postgres_conn_id='efinance_postgres')
    
    sql = f"""
        SELECT 
            id, account_id, reference_number, transaction_type,
            amount, currency, fee, status, created_at
        FROM transactions
        WHERE DATE(created_at) = '{execution_date}'
        AND status = 'COMPLETED'
    """
    
    records = hook.get_records(sql)
    
    # Push to XCom for next task
    context['ti'].xcom_push(key='transaction_count', value=len(records))
    
    return records


def transform_transactions(**context):
    """Transform and aggregate transaction data"""
    execution_date = context['ds']
    
    # In production, would perform complex transformations
    # Calculate daily aggregates, risk metrics, etc.
    
    print(f"Transforming transactions for {execution_date}")
    
    # Mock transformation results
    return {
        'total_volume': 1000000,
        'transaction_count': 500,
        'avg_amount': 2000,
        'date': execution_date
    }


def load_to_warehouse(**context):
    """Load transformed data to data warehouse"""
    ti = context['ti']
    transformed_data = ti.xcom_pull(task_ids='transform_transactions')
    
    hook = PostgresHook(postgres_conn_id='efinance_warehouse')
    
    sql = """
        INSERT INTO daily_transaction_summary 
        (date, total_volume, transaction_count, avg_amount, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        ON CONFLICT (date) DO UPDATE SET
            total_volume = EXCLUDED.total_volume,
            transaction_count = EXCLUDED.transaction_count,
            avg_amount = EXCLUDED.avg_amount,
            updated_at = NOW()
    """
    
    hook.run(sql, parameters=(
        transformed_data['date'],
        transformed_data['total_volume'],
        transformed_data['transaction_count'],
        transformed_data['avg_amount']
    ))


def calculate_risk_metrics(**context):
    """Calculate risk metrics for fraud detection"""
    execution_date = context['ds']
    
    hook = PostgresHook(postgres_conn_id='efinance_postgres')
    
    # Calculate velocity metrics
    velocity_sql = """
        INSERT INTO user_velocity_metrics (user_id, date, daily_count, daily_volume)
        SELECT 
            u.id as user_id,
            DATE(t.created_at) as date,
            COUNT(t.id) as daily_count,
            SUM(t.amount) as daily_volume
        FROM users u
        JOIN accounts a ON a.user_id = u.id
        JOIN transactions t ON t.account_id = a.id
        WHERE DATE(t.created_at) = %s
        GROUP BY u.id, DATE(t.created_at)
        ON CONFLICT (user_id, date) DO UPDATE SET
            daily_count = EXCLUDED.daily_count,
            daily_volume = EXCLUDED.daily_volume
    """
    
    hook.run(velocity_sql, parameters=(execution_date,))


def send_daily_report(**context):
    """Generate and send daily transaction report"""
    execution_date = context['ds']
    ti = context['ti']
    
    transaction_count = ti.xcom_pull(task_ids='extract_transactions', key='transaction_count')
    
    report = f"""
    E-Finance Daily Transaction Report
    Date: {execution_date}
    
    Total Transactions Processed: {transaction_count}
    
    Report generated at: {datetime.now().isoformat()}
    """
    
    print(report)
    # In production, would send via email or Slack


with DAG(
    'transaction_etl_daily',
    default_args=default_args,
    description='Daily ETL pipeline for transaction data',
    schedule_interval='0 2 * * *',  # Run at 2 AM daily
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['etl', 'transactions', 'daily'],
) as dag:
    
    start = DummyOperator(task_id='start')
    
    extract = PythonOperator(
        task_id='extract_transactions',
        python_callable=extract_transactions,
        provide_context=True,
    )
    
    transform = PythonOperator(
        task_id='transform_transactions',
        python_callable=transform_transactions,
        provide_context=True,
    )
    
    load = PythonOperator(
        task_id='load_to_warehouse',
        python_callable=load_to_warehouse,
        provide_context=True,
    )
    
    risk_metrics = PythonOperator(
        task_id='calculate_risk_metrics',
        python_callable=calculate_risk_metrics,
        provide_context=True,
    )
    
    report = PythonOperator(
        task_id='send_daily_report',
        python_callable=send_daily_report,
        provide_context=True,
    )
    
    end = DummyOperator(task_id='end')
    
    # Define task dependencies
    start >> extract >> transform >> [load, risk_metrics] >> report >> end

