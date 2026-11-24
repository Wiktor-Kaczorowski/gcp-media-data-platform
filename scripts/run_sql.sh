
#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT="gcp-media-data-platform"
LOCATION="us-central1"

run_sql() {
    local file="$1"
    local max_bytes=100000000

    if [[ "$file" == "sql/03_quality.sql" ]]; then
        max_bytes=250000000
    fi

    echo "=== Executing $file ==="

    bq \
        --project_id="$PROJECT" \
        --location="$LOCATION" \
        query \
        --use_legacy_sql=false \
        --maximum_bytes_billed="$max_bytes" \
        < "$file"

    echo "=== Completed $file ==="
}

case "${1:-all}" in
    silver)
        run_sql sql/01_silver.sql
        ;;
    gold)
        run_sql sql/02_gold.sql
        ;;
    quality)
        run_sql sql/03_quality.sql
        ;;
    all)
        run_sql sql/01_silver.sql
        run_sql sql/02_gold.sql
        run_sql sql/03_quality.sql
        ;;
    *)
        echo "Usage: $0 [silver|gold|quality|all]"
        exit 1
        ;;
esac

echo "SQL execution completed successfully."
