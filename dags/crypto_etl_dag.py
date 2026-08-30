from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.config.settings import settings


def _resolve_run_id(context):
    dag_run = context.get("dag_run")
    if dag_run and getattr(dag_run, "run_id", None):
        return dag_run.run_id
    return getattr(settings, "RUN_ID", None)


def run_extract(**context):
    from src.pipelines.extraction_pipeline import run_extraction_pipeline

    run_extraction_pipeline(run_id=_resolve_run_id(context))


def run_market_pipeline(**context):
    from src.pipelines.market_pipeline import run_market_pipeline

    return run_market_pipeline(metrics=None, run_id=_resolve_run_id(context))


def run_analytics(**context):
    from src.pipelines.analytics_pipeline import run_analytics_pipeline

    _, sentiment_df = context["task_instance"].xcom_pull(task_ids="transform_load")
    sentiment_score = sentiment_df["sentiment_score"].iloc[-1]
    sentiment_label = sentiment_df["sentiment_label"].iloc[-1]

    return run_analytics_pipeline(sentiment_score, sentiment_label, metrics=None, run_id=_resolve_run_id(context))


def run_alerts(**context):
    from src.pipelines.alert_pipeline import run_alert_pipeline

    analytics_df = context["task_instance"].xcom_pull(task_ids="analytics")
    return run_alert_pipeline(analytics_df, metrics=None, run_id=_resolve_run_id(context))


def run_notifications(**context):
    from src.pipelines.notification_pipeline import run_notification_pipeline

    context["task_instance"].xcom_pull(task_ids="alerts")
    run_notification_pipeline(metrics=None, run_id=_resolve_run_id(context))

default_args = {
    "owner": "crypto-etl",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 1, 1),
    "execution_timeout": timedelta(minutes=30)
}

with DAG(
    dag_id="crypto_etl",
    default_args=default_args,
    schedule_interval="@hourly",
    catchup=False,
    tags=["crypto", "etl"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=run_extract,
    )

    transform_load_task = PythonOperator(
        task_id="transform_load",
        python_callable=run_market_pipeline,
    )

    analytics_task = PythonOperator(
        task_id="analytics",
        python_callable=run_analytics,
    )

    alerts_task = PythonOperator(
        task_id="alerts",
        python_callable=run_alerts,
    )

    notifications_task = PythonOperator(
        task_id="notifications",
        python_callable=run_notifications,
    )

    extract_task >> transform_load_task >> analytics_task >> alerts_task >> notifications_task