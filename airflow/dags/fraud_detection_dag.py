"""
Fraud Detection DAG
Real-time fraud detection and alerting pipeline
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import json


default_args = {
    'owner': 'efinance',
    'depends_on_past': False,
    'email': ['fraud-team@efinance.com'],
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}


def get_suspicious_transactions(**context):
    """Get transactions flagged as suspicious"""
    hook = PostgresHook(postgres_conn_id='efinance_postgres')
    
    sql = """
        SELECT 
            id, account_id, reference_number, amount, 
            risk_score, fraud_flags, created_at
        FROM transactions
        WHERE is_suspicious = true
        AND reviewed_at IS NULL
        AND created_at >= NOW() - INTERVAL '1 hour'
        ORDER BY risk_score DESC
        LIMIT 100
    """
    
    records = hook.get_records(sql)
    
    context['ti'].xcom_push(key='suspicious_count', value=len(records))
    context['ti'].xcom_push(key='suspicious_transactions', value=records)
    
    return records


def analyze_patterns(**context):
    """Analyze fraud patterns"""
    ti = context['ti']
    transactions = ti.xcom_pull(task_ids='get_suspicious_transactions', key='suspicious_transactions')
    
    if not transactions:
        return {'patterns': [], 'high_risk_accounts': []}
    
    # In production, would run ML models here
    # For demo, simple pattern detection
    
    high_risk_accounts = []
    patterns = []
    
    # Group by account
    account_transactions = {}
    for tx in transactions:
        account_id = tx[1]
        if account_id not in account_transactions:
            account_transactions[account_id] = []
        account_transactions[account_id].append(tx)
    
    for account_id, txs in account_transactions.items():
        if len(txs) >= 3:
            high_risk_accounts.append({
                'account_id': str(account_id),
                'suspicious_count': len(txs),
                'total_amount': sum(tx[3] for tx in txs)
            })
            patterns.append({
                'pattern': 'velocity_breach',
                'account_id': str(account_id),
                'description': f'Multiple suspicious transactions ({len(txs)}) in short period'
            })
    
    return {
        'patterns': patterns,
        'high_risk_accounts': high_risk_accounts
    }


def generate_alerts(**context):
    """Generate fraud alerts"""
    ti = context['ti']
    analysis = ti.xcom_pull(task_ids='analyze_patterns')
    suspicious_count = ti.xcom_pull(task_ids='get_suspicious_transactions', key='suspicious_count')
    
    if suspicious_count == 0:
        print("No suspicious transactions found")
        return
    
    hook = PostgresHook(postgres_conn_id='efinance_postgres')
    
    # Create alerts for high-risk accounts
    for account in analysis.get('high_risk_accounts', []):
        alert_sql = """
            INSERT INTO fraud_alerts 
            (account_id, alert_type, severity, description, status, created_at)
            VALUES (%s, 'VELOCITY_BREACH', 'HIGH', %s, 'OPEN', NOW())
        """
        
        description = f"Account has {account['suspicious_count']} suspicious transactions"
        hook.run(alert_sql, parameters=(account['account_id'], description))
    
    print(f"Generated {len(analysis.get('high_risk_accounts', []))} fraud alerts")


def notify_fraud_team(**context):
    """Send notifications to fraud team"""
    ti = context['ti']
    suspicious_count = ti.xcom_pull(task_ids='get_suspicious_transactions', key='suspicious_count')
    analysis = ti.xcom_pull(task_ids='analyze_patterns')
    
    if suspicious_count == 0:
        return
    
    notification = {
        'timestamp': datetime.now().isoformat(),
        'suspicious_transactions': suspicious_count,
        'high_risk_accounts': len(analysis.get('high_risk_accounts', [])),
        'patterns_detected': len(analysis.get('patterns', [])),
        'action_required': suspicious_count > 10
    }
    
    print(f"Fraud Alert Notification: {json.dumps(notification, indent=2)}")
    
    # In production, would send to Slack, PagerDuty, etc.


def update_ml_model(**context):
    """Trigger ML model retraining if needed"""
    ti = context['ti']
    suspicious_count = ti.xcom_pull(task_ids='get_suspicious_transactions', key='suspicious_count')
    
    # Check if we have enough new data for retraining
    if suspicious_count >= 100:
        print("Triggering ML model retraining...")
        # Would call fraud detection service to retrain
    else:
        print("Not enough new data for retraining")


with DAG(
    'fraud_detection_pipeline',
    default_args=default_args,
    description='Real-time fraud detection and alerting',
    schedule_interval='*/15 * * * *',  # Run every 15 minutes
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['fraud', 'ml', 'alerting'],
) as dag:
    
    start = DummyOperator(task_id='start')
    
    get_suspicious = PythonOperator(
        task_id='get_suspicious_transactions',
        python_callable=get_suspicious_transactions,
        provide_context=True,
    )
    
    analyze = PythonOperator(
        task_id='analyze_patterns',
        python_callable=analyze_patterns,
        provide_context=True,
    )
    
    alerts = PythonOperator(
        task_id='generate_alerts',
        python_callable=generate_alerts,
        provide_context=True,
    )
    
    notify = PythonOperator(
        task_id='notify_fraud_team',
        python_callable=notify_fraud_team,
        provide_context=True,
    )
    
    update_model = PythonOperator(
        task_id='update_ml_model',
        python_callable=update_ml_model,
        provide_context=True,
    )
    
    end = DummyOperator(task_id='end')
    
    start >> get_suspicious >> analyze >> [alerts, notify] >> update_model >> end

