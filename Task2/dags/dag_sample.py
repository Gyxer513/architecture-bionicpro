from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import csv
from decimal import Decimal
import clickhouse_connect

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 12, 1),
}

def get_ch_client(database=None):
    host = os.environ.get('CLICKHOUSE_HOST', 'clickhouse')
    port = int(os.environ.get('CLICKHOUSE_PORT', '8123'))
    user = os.environ.get('CLICKHOUSE_USER', 'airflow')
    password = os.environ.get('CLICKHOUSE_PASSWORD', 'airflow')

    db = database or os.environ.get('CLICKHOUSE_DB', 'airflow_results')
    return clickhouse_connect.get_client(
        host=host,
        port=port,
        username=user,
        password=password,
        database=db,
    )

def create_clickhouse_db_and_table():
    # сначала подключаемся к default
    client = get_ch_client(database='default')

    # создаем БД
    client.command('CREATE DATABASE IF NOT EXISTS airflow_results')

    # теперь подключаемся к нужной базе
    client = get_ch_client(database='airflow_results')

    ddl = """
    CREATE TABLE IF NOT EXISTS sample_table
    (
        id UInt64,
        order_number UInt64,
        total Decimal(18,2),
        discount Decimal(18,2),
        buyer_id String
    )
    ENGINE = MergeTree
    ORDER BY id
    """
    client.command(ddl)

def load_csv_to_clickhouse():
    csv_path = '/opt/airflow/sample_files/sample.csv'
    client = get_ch_client()

    batch = []
    batch_size = 5000  # можно менять
    columns = ['id', 'order_number', 'total', 'discount', 'buyer_id']

    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader, None)  # пропустить заголовок, если он есть
        for row in reader:
            # преобразование типов под DDL
            rec = [
                int(row[0]),
                int(row[1]),
                Decimal(row[2]) if row[2] else Decimal('0'),
                Decimal(row[3]) if row[3] else Decimal('0'),
                row[4]
            ]
            batch.append(rec)
            if len(batch) >= batch_size:
                client.insert('sample_table', batch, column_names=columns)
                batch.clear()

    if batch:
        client.insert('sample_table', batch, column_names=columns)

with DAG(
    'csv_to_clickhouse_dag',
    default_args=default_args,
    schedule_interval='@once',
    catchup=False
) as dag:

    create_table = PythonOperator(
        task_id='create_clickhouse_table',
        python_callable=create_clickhouse_db_and_table
    )

    load_csv = PythonOperator(
        task_id='load_csv_to_clickhouse',
        python_callable=load_csv_to_clickhouse
    )

    create_table >> load_csv