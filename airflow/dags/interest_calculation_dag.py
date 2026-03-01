"""
Interest Calculation DAG
Daily interest calculation and credit for savings accounts
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from decimal import Decimal


default_args = {
    'owner': 'efinance',
    'depends_on_past': True,  # Important for interest calculation
    'email': ['finance-team@efinance.com'],
    'email_on_failure': True,
    'retries': 3,
    'retry_delay': timedelta(minutes=10),
}


def calculate_daily_interest(**context):
    """Calculate daily interest for all savings accounts"""
    execution_date = context['ds']
    
    hook = PostgresHook(postgres_conn_id='efinance_postgres')
    
    # Get accounts eligible for interest
    accounts_sql = """
        SELECT id, balance, interest_rate
        FROM accounts
        WHERE account_type IN ('savings', 'fixed_deposit')
        AND status = 'active'
        AND interest_rate IS NOT NULL
        AND interest_rate > 0
    """
    
    accounts = hook.get_records(accounts_sql)
    
    total_interest = 0
    accounts_processed = 0
    
    for account in accounts:
        account_id, balance, rate = account
        
        # Daily interest = Balance * (Annual Rate / 365)
        daily_interest = int(balance * (rate / 365))
        
        if daily_interest > 0:
            # Update accrued interest
            update_sql = """
                UPDATE accounts
                SET interest_accrued = COALESCE(interest_accrued, 0) + %s,
                    last_interest_calculated = %s
                WHERE id = %s
            """
            
            hook.run(update_sql, parameters=(daily_interest, execution_date, account_id))
            
            total_interest += daily_interest
            accounts_processed += 1
    
    context['ti'].xcom_push(key='total_interest', value=total_interest)
    context['ti'].xcom_push(key='accounts_processed', value=accounts_processed)
    
    print(f"Calculated interest for {accounts_processed} accounts. Total: ${total_interest/100:.2f}")


def check_monthly_credit(**context):
    """Check if it's time for monthly interest credit"""
    execution_date = datetime.strptime(context['ds'], '%Y-%m-%d')
    
    # Credit interest on the 1st of each month
    is_credit_day = execution_date.day == 1
    
    context['ti'].xcom_push(key='is_credit_day', value=is_credit_day)
    
    return is_credit_day


def credit_monthly_interest(**context):
    """Credit accrued interest to accounts"""
    ti = context['ti']
    is_credit_day = ti.xcom_pull(task_ids='check_monthly_credit', key='is_credit_day')
    
    if not is_credit_day:
        print("Not a credit day, skipping")
        return
    
    hook = PostgresHook(postgres_conn_id='efinance_postgres')
    
    # Get accounts with accrued interest
    accounts_sql = """
        SELECT id, account_number, balance, interest_accrued, currency
        FROM accounts
        WHERE interest_accrued > 0
    """
    
    accounts = hook.get_records(accounts_sql)
    
    total_credited = 0
    
    for account in accounts:
        account_id, account_number, balance, accrued, currency = account
        
        # Create interest credit transaction
        tx_sql = """
            INSERT INTO transactions 
            (account_id, reference_number, transaction_type, amount, currency,
             fee, balance_before, balance_after, status, description, channel, completed_at)
            VALUES 
            (%s, %s, 'interest', %s, %s, 0, %s, %s, 'completed', 
             'Monthly interest credit', 'automated', NOW())
        """
        
        ref_number = f"INT{datetime.now().strftime('%Y%m%d%H%M%S')}{account_id.hex[:6]}"
        new_balance = balance + accrued
        
        hook.run(tx_sql, parameters=(
            account_id, ref_number, accrued, currency, balance, new_balance
        ))
        
        # Update account balance and reset accrued
        update_sql = """
            UPDATE accounts
            SET balance = balance + interest_accrued,
                available_balance = available_balance + interest_accrued,
                interest_accrued = 0
            WHERE id = %s
        """
        
        hook.run(update_sql, parameters=(account_id,))
        
        total_credited += accrued
    
    print(f"Credited ${total_credited/100:.2f} interest to {len(accounts)} accounts")
    
    context['ti'].xcom_push(key='total_credited', value=total_credited)


def generate_interest_report(**context):
    """Generate interest calculation report"""
    ti = context['ti']
    
    total_interest = ti.xcom_pull(task_ids='calculate_daily_interest', key='total_interest') or 0
    accounts_processed = ti.xcom_pull(task_ids='calculate_daily_interest', key='accounts_processed') or 0
    total_credited = ti.xcom_pull(task_ids='credit_monthly_interest', key='total_credited') or 0
    
    report = f"""
    E-Finance Interest Calculation Report
    Date: {context['ds']}
    
    Daily Interest Calculated: ${total_interest/100:.2f}
    Accounts Processed: {accounts_processed}
    Monthly Interest Credited: ${total_credited/100:.2f}
    
    Report generated at: {datetime.now().isoformat()}
    """
    
    print(report)


with DAG(
    'interest_calculation_daily',
    default_args=default_args,
    description='Daily interest calculation and monthly credit',
    schedule_interval='0 0 * * *',  # Run at midnight daily
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['finance', 'interest', 'daily'],
) as dag:
    
    start = DummyOperator(task_id='start')
    
    calculate = PythonOperator(
        task_id='calculate_daily_interest',
        python_callable=calculate_daily_interest,
        provide_context=True,
    )
    
    check = PythonOperator(
        task_id='check_monthly_credit',
        python_callable=check_monthly_credit,
        provide_context=True,
    )
    
    credit = PythonOperator(
        task_id='credit_monthly_interest',
        python_callable=credit_monthly_interest,
        provide_context=True,
    )
    
    report = PythonOperator(
        task_id='generate_interest_report',
        python_callable=generate_interest_report,
        provide_context=True,
    )
    
    end = DummyOperator(task_id='end')
    
    start >> calculate >> check >> credit >> report >> end

