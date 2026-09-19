import datetime
import sys
import types
from types import SimpleNamespace

# Airflow is not supported natively on this Windows environment, so stub the minimal API
# surface used by the DAG module during import and test execution.

airflow_module = types.ModuleType("airflow")
models_module = types.ModuleType("airflow.models")
models_taskinstance_module = types.ModuleType("airflow.models.taskinstance")
operators_module = types.ModuleType("airflow.operators")
python_operators_module = types.ModuleType("airflow.operators.python")
utils_module = types.ModuleType("airflow.utils")
trigger_rule_module = types.ModuleType("airflow.utils.trigger_rule")


class TaskGroup:
    def __init__(self, *args, **kwargs):
        self.group_id = kwargs.get("group_id")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def __rshift__(self, other):
        return other

    def __rrshift__(self, other):
        return self


class PythonOperator:
    def __init__(self, *args, **kwargs):
        self.task_id = kwargs.get("task_id")

    def __rshift__(self, other):
        return other


class DAG:
    def __init__(self, *args, **kwargs):
        self.dag_id = kwargs.get("dag_id")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class TriggerRule:
    NONE_FAILED_MIN_ONE_SUCCESS = "none_failed_min_one_success"


models_module.TaskGroup = TaskGroup
models_taskinstance_module.TaskInstance = object
operators_module.python = python_operators_module
python_operators_module.PythonOperator = PythonOperator
utils_module.trigger_rule = trigger_rule_module
trigger_rule_module.TriggerRule = TriggerRule
airflow_module.DAG = DAG
airflow_module.models = models_module
airflow_module.operators = operators_module
airflow_module.utils = utils_module

sys.modules.setdefault("airflow", airflow_module)
sys.modules.setdefault("airflow.models", models_module)
sys.modules.setdefault("airflow.models.taskinstance", models_taskinstance_module)
sys.modules.setdefault("airflow.operators", operators_module)
sys.modules.setdefault("airflow.operators.python", python_operators_module)
sys.modules.setdefault("airflow.utils", utils_module)
sys.modules.setdefault("airflow.utils.trigger_rule", trigger_rule_module)

from dags import crypto_etl_dag as dag_module


class FakeCursor:
    def __init__(self):
        self._fetch_result = None
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if "SELECT run_id FROM pipeline_runs" in sql:
            self._fetch_result = None
        elif "INSERT INTO pipeline_runs" in sql:
            self._fetch_result = (1,)

    def fetchone(self):
        return self._fetch_result


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        pass

    def close(self):
        pass


def test_record_dag_start_inserts_pipeline_run_entry(monkeypatch):
    fake_conn = FakeConnection()
    monkeypatch.setattr(dag_module.psycopg2, "connect", lambda **kwargs: fake_conn)

    context = {
        "dag": SimpleNamespace(dag_id="crypto_etl"),
        "dag_run": SimpleNamespace(run_id="scheduled__2026-01-02"),
        "logical_date": datetime.datetime(2026, 1, 2, 0, 0, 0),
        "execution_date": datetime.datetime(2026, 1, 2, 0, 0, 0),
        "ti": SimpleNamespace(task_id="dag_start"),
    }

    dag_module.record_dag_start(**context)

    insert_sql, insert_params = next(
        (sql, params) for sql, params in fake_conn.cursor_obj.executed if "INSERT INTO pipeline_runs" in sql
    )
    assert "INSERT INTO pipeline_runs" in insert_sql
    assert insert_params[0] == "scheduled__2026-01-02"
    assert insert_params[3] == "running"
    assert isinstance(insert_params[4], str)
