
-- Automated data quality assertions.
-- Failed assertions cause the BigQuery job to fail.

-- 1. Silver must contain data.

ASSERT (
    SELECT COUNT(*) > 0
    FROM `gcp-media-data-platform.media_silver.media_events`
) AS 'Silver table must not be empty';


-- 2. Event IDs must be unique.

ASSERT (
    SELECT COUNT(*) = COUNT(DISTINCT event_id)
    FROM `gcp-media-data-platform.media_silver.media_events`
) AS 'Duplicate event IDs found in Silver';


-- 3. Business metrics must be valid.

ASSERT (
    SELECT COUNTIF(
        impressions IS NULL
        OR clicks IS NULL
        OR conversions IS NULL
        OR spend IS NULL
        OR revenue IS NULL
        OR impressions < 0
        OR clicks < 0
        OR conversions < 0
        OR spend < 0
        OR revenue < 0
        OR clicks > impressions
        OR conversions > clicks
    ) = 0
    FROM `gcp-media-data-platform.media_silver.media_events`
) AS 'Invalid business metrics found';


-- 4. Campaign dimension must have unique keys.

ASSERT (
    SELECT COUNT(*) = COUNT(DISTINCT campaign_id)
    FROM `gcp-media-data-platform.media_gold.dim_campaign`
) AS 'Duplicate campaign dimension keys';


-- 5. Every fact must reference a campaign.

ASSERT (
    SELECT COUNTIF(c.campaign_id IS NULL) = 0

    FROM
        `gcp-media-data-platform.media_gold.fact_media_events` f

    LEFT JOIN
        `gcp-media-data-platform.media_gold.dim_campaign` c
        ON f.campaign_id = c.campaign_id
) AS 'Orphaned campaign foreign keys';


-- 6. Every fact must reference a calendar date.

ASSERT (
    SELECT COUNTIF(d.date_id IS NULL) = 0

    FROM
        `gcp-media-data-platform.media_gold.fact_media_events` f

    LEFT JOIN
        `gcp-media-data-platform.media_gold.dim_date` d
        ON f.event_date = d.date_id
) AS 'Orphaned date foreign keys';


-- 7. Fact and Silver row counts must match.

ASSERT (
    (
        SELECT COUNT(*)
        FROM `gcp-media-data-platform.media_gold.fact_media_events`
    ) = (
        SELECT COUNT(*)
        FROM `gcp-media-data-platform.media_silver.media_events`
    )
) AS 'Fact and Silver row counts differ';


-- 8. Aggregation must preserve event counts.

ASSERT (
    (
        SELECT SUM(total_events)
        FROM `gcp-media-data-platform.media_gold.mart_campaign_daily`
    ) = (
        SELECT COUNT(*)
        FROM `gcp-media-data-platform.media_gold.fact_media_events`
    )
) AS 'Event count reconciliation failed';


-- 9. Aggregation must preserve financial totals.

ASSERT (
    (
        SELECT SUM(spend)
        FROM `gcp-media-data-platform.media_gold.mart_campaign_daily`
    ) = (
        SELECT SUM(spend)
        FROM `gcp-media-data-platform.media_gold.fact_media_events`
    )
) AS 'Spend reconciliation failed';


-- 10. Mart business grain must be unique.

ASSERT (
    NOT EXISTS (
        SELECT event_date, campaign_id
        FROM `gcp-media-data-platform.media_gold.mart_campaign_daily`
        GROUP BY event_date, campaign_id
        HAVING COUNT(*) > 1
    )
) AS 'Duplicate daily campaign records';


SELECT
    'PASS' AS quality_status,
    10 AS assertions_passed,
    CURRENT_TIMESTAMP() AS checked_at;
