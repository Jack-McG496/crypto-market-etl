import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import psycopg2
from airflow import DAG
from airflow.models.taskinstance import TaskInstance
from airflow.operators.python import PythonOperator
from airflow.models import TaskGroup
from airflow.utils.trigger_rule import TriggerRule

from src.config.settings import settings


def _resolve_run_id(context):
    dag_run = context.get("dag_run")
    if dag_run and getattr(dag_run, "run_id", None):
        return dag_run.run_id
    return getattr(settings, "RUN_ID", None) or "manual_run"


def _db_config():
    return {
        "host": os.getenv("POSTGRES_HOST", "postgres"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "crypto_db"),
        "user": os.getenv("POSTGRES_USER", "crypto"),
        "password": os.getenv("POSTGRES_PASSWORD", "crypto"),
    }


def _write_run_metadata(context, status: str, **extra):
    dag_run_id = _resolve_run_id(context)
    dag_id = context.get("dag").dag_id if context.get("dag") else "crypto_etl"
    ti = context.get("ti")
    logical_date = context.get("logical_date")
    execution_date = context.get("execution_date")

    metadata = {
        "dag_id": dag_id,
        "dag_run_id": dag_run_id,
        "logical_date": logical_date.isoformat() if logical_date else None,
        "execution_date": execution_date.isoformat() if execution_date else None,
        "task_id": getattr(ti, "task_id", None) if ti else None,
        "event": extra.pop("event", None),
        **extra,
    }

    conn = psycopg2.connect(**_db_config())
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT run_id FROM pipeline_runs WHERE dag_run = %s ORDER BY start_ts DESC LIMIT 1",
                (dag_run_id,),
            )
            row = cur.fetchone()
            now = datetime.utcnow()
            if row is None:
                cur.execute(
                    "INSERT INTO pipeline_runs (dag_run, start_ts, end_ts, status, metadata) VALUES (%s, %s, %s, %s, %s)",
                    (dag_run_id, now, now if status != "running" else None, status, json.dumps(metadata)),
                )
            else:
                cur.execute(
                    "UPDATE pipeline_runs SET status = %s, end_ts = %s, metadata = metadata || %s::jsonb WHERE run_id = %s",
                    (status, now, json.dumps(metadata), row[0]),
                )
        conn.commit()
    finally:
        conn.close()


def record_dag_start(**context):
    _write_run_metadata(context, "running", event="start")


def record_dag_finish(**context):
    ti = context["task_instance"]
    status = "success" if ti.state == "success" else "failed"
    _write_run_metadata(context, status, event="finish", dag_state=ti.state)


def _mark_failure(context):
    exception = context.get("exception")
    task_instance = context.get("task_instance")
    _write_run_metadata(
        context,
        "failed",
        event="failure",
        task_id=getattr(task_instance, "task_id", None),
        failure_message=str(exception) if exception else "unknown",
        dag_state=getattr(task_instance, "state", None),
    )


def run_extract(**context):
    from src.pipelines.extraction_pipeline import run_extraction_pipeline

    run_extraction_pipeline(run_id=_resolve_run_id(context))


def run_market_pipeline(**context):
    from src.pipelines.market_pipeline import run_market_pipeline

    return run_market_pipeline(metrics=None, run_id=_resolve_run_id(context))


def run_analytics(**context):
    from src.pipelines.analytics_pipeline import run_analytics_pipeline

    transform_result = context["task_instance"].xcom_pull(task_ids="transform_load.transform_load_task")
    if not transform_result:
        raise ValueError("transform_load_task did not produce market and sentiment data")
    _, sentiment_df = transform_result
    sentiment_score = sentiment_df["sentiment_score"].iloc[-1]
    sentiment_label = sentiment_df["sentiment_label"].iloc[-1]

    return run_analytics_pipeline(sentiment_score, sentiment_label, metrics=None, run_id=_resolve_run_id(context))


def run_alerts(**context):
    from src.pipelines.alert_pipeline import run_alert_pipeline

    analytics_df = context["task_instance"].xcom_pull(task_ids="analytics.analytics_task")
    return run_alert_pipeline(analytics_df, metrics=None, run_id=_resolve_run_id(context))


def run_notifications(**context):
    from src.pipelines.notification_pipeline import run_notification_pipeline

    context["task_instance"].xcom_pull(task_ids="alerts.alerts_task")
    run_notification_pipeline(metrics=None, run_id=_resolve_run_id(context))


def check_extraction_quality(**context):
    raw_dir = Path("/opt/airflow/data/raw")
    if not raw_dir.exists():
        raw_dir = Path("data/raw")
    files = list(raw_dir.glob("*"))
    if not files:
        raise ValueError("No raw files were produced by the extraction stage")


def check_transform_quality(**context):
    transform_result = context["task_instance"].xcom_pull(task_ids="transform_load.transform_load_task")
    if not transform_result:
        raise ValueError("No transform output available for quality check")
    market_df, sentiment_df = transform_result
    if len(market_df) <= 0:
        raise ValueError("Transform stage produced zero market rows")
    if len(sentiment_df) <= 0:
        raise ValueError("Transform stage produced zero sentiment rows")


def check_analytics_quality(**context):
    analytics_df = context["task_instance"].xcom_pull(task_ids="analytics.analytics_task")
    if analytics_df is None or len(analytics_df) <= 0:
        raise ValueError("Analytics stage produced zero rows")


def check_alerts_quality(**context):
    alerts_df = context["task_instance"].xcom_pull(task_ids="alerts.alerts_task")
    if alerts_df is None:
        raise ValueError("Alerts stage produced no output")


default_args = {
    "owner": "crypto-etl",
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 1, 1),
    "execution_timeout": timedelta(minutes=30),
}

with DAG(
    dag_id="crypto_etl",
    default_args=default_args,
    schedule_interval="@hourly",
    catchup=False,
    tags=["crypto", "etl"],
    on_failure_callback=_mark_failure,
) as dag:
    dag_start = PythonOperator(
        task_id="dag_start",
        python_callable=record_dag_start,
        retries=1,
        retry_delay=timedelta(minutes=1),
        execution_timeout=timedelta(minutes=10),
    )

    with TaskGroup(group_id="extract") as extract_group:
        extract_task = PythonOperator(
            task_id="extract_task",
            python_callable=run_extract,
            retries=2,
            retry_delay=timedelta(minutes=3),
            execution_timeout=timedelta(minutes=30),
        )
        extraction_quality = PythonOperator(
            task_id="check_extraction_quality",
            python_callable=check_extraction_quality,
            retries=1,
            retry_delay=timedelta(minutes=2),
            execution_timeout=timedelta(minutes=10),
        )
        extract_task >> extraction_quality

    with TaskGroup(group_id="transform_load") as transform_group:
        transform_load_task = PythonOperator(
            task_id="transform_load_task",
            python_callable=run_market_pipeline,
            retries=2,
            retry_delay=timedelta(minutes=5),
            execution_timeout=timedelta(minutes=25),
        )
        transform_quality = PythonOperator(
            task_id="check_transform_quality",
            python_callable=check_transform_quality,
            retries=1,
            retry_delay=timedelta(minutes=2),
            execution_timeout=timedelta(minutes=10),
        )
        transform_load_task >> transform_quality

    with TaskGroup(group_id="analytics") as analytics_group:
        analytics_task = PythonOperator(
            task_id="analytics_task",
            python_callable=run_analytics,
            retries=2,
            retry_delay=timedelta(minutes=5),
            execution_timeout=timedelta(minutes=20),
        )
        analytics_quality = PythonOperator(
            task_id="check_analytics_quality",
            python_callable=check_analytics_quality,
            retries=1,
            retry_delay=timedelta(minutes=2),
            execution_timeout=timedelta(minutes=10),
        )
        analytics_task >> analytics_quality

    with TaskGroup(group_id="alerts") as alerts_group:
        alerts_task = PythonOperator(
            task_id="alerts_task",
            python_callable=run_alerts,
            retries=1,
            retry_delay=timedelta(minutes=3),
            execution_timeout=timedelta(minutes=15),
        )
        alerts_quality = PythonOperator(
            task_id="check_alerts_quality",
            python_callable=check_alerts_quality,
            retries=1,
            retry_delay=timedelta(minutes=2),
            execution_timeout=timedelta(minutes=10),
        )
        alerts_task >> alerts_quality

    with TaskGroup(group_id="notifications") as notifications_group:
        notifications_task = PythonOperator(
            task_id="notifications_task",
            python_callable=run_notifications,
            retries=2,
            retry_delay=timedelta(minutes=5),
            execution_timeout=timedelta(minutes=15),
        )

    dag_finish = PythonOperator(
        task_id="dag_finish",
        python_callable=record_dag_finish,
        retries=1,
        retry_delay=timedelta(minutes=1),
        execution_timeout=timedelta(minutes=10),
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    dag_start >> extract_group >> transform_group >> analytics_group >> alerts_group >> notifications_group >> dag_finish