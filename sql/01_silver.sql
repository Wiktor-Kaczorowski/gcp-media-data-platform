
-- Silver layer: consolidate, validate and deduplicate events.
-- Grain: one row per unique event_id.

CREATE OR REPLACE TABLE
    `gcp-media-data-platform.media_silver.media_events`
PARTITION BY DATE(event_timestamp)
CLUSTER BY campaign_id, platform
AS

WITH combined AS (
    SELECT *
    FROM `gcp-media-data-platform.media_bronze.raw_batch_events`

    UNION ALL BY NAME

    SELECT *
    FROM `gcp-media-data-platform.media_bronze.raw_streaming_events`
),

validated AS (
    SELECT
        event_id,
        event_timestamp,
        DATE(event_timestamp) AS event_date,
        campaign_id,
        brand,
        platform,
        country,
        impressions,
        clicks,
        conversions,
        SAFE_CAST(ROUND(spend, 2) AS NUMERIC) AS spend,
        SAFE_CAST(ROUND(revenue, 2) AS NUMERIC) AS revenue,
        batch_id,
        ingestion_timestamp,
        source
    FROM combined
    WHERE
        NULLIF(TRIM(event_id), '') IS NOT NULL
        AND NULLIF(TRIM(campaign_id), '') IS NOT NULL
        AND NULLIF(TRIM(brand), '') IS NOT NULL
        AND NULLIF(TRIM(platform), '') IS NOT NULL
        AND NULLIF(TRIM(country), '') IS NOT NULL
        AND event_timestamp IS NOT NULL
        AND ingestion_timestamp IS NOT NULL
        AND impressions >= 0
        AND clicks >= 0
        AND conversions >= 0
        AND spend >= 0
        AND revenue >= 0
        AND clicks <= impressions
        AND conversions <= clicks
        AND source IN ('batch', 'streaming')
)

SELECT *
FROM validated AS v
WHERE spend IS NOT NULL
    AND revenue IS NOT NULL

QUALIFY ROW_NUMBER() OVER (
    PARTITION BY event_id
    ORDER BY
        ingestion_timestamp DESC,
        event_timestamp DESC,
        TO_JSON_STRING(v) DESC
) = 1;
