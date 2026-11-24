
#!/usr/bin/env bash

export AIRFLOW_HOME="$HOME/airflow-media-platform"

export AIRFLOW__CORE__DAGS_FOLDER="$(cd "$(dirname "${BASH_SOURCE[0]}")/../dags" && pwd)"

export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__CORE__EXECUTOR=SequentialExecutor
export AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=True

export AIRFLOW__WEBSERVER__WEB_SERVER_HOST=127.0.0.1
export AIRFLOW__WEBSERVER__WEB_SERVER_PORT=8085
export AIRFLOW__WEBSERVER__BASE_URL="http://localhost:8085"

export ALLOW_PAID_CLOUD_JOBS=false
export ALLOW_COMPOSER_DEPLOYMENT=false

source "$HOME/.venvs/media-airflow/bin/activate"
