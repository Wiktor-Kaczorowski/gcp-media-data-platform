
-- Gold layer: dimensional model and business metrics.

-- 1. Campaign dimension.
-- Grain: one row per campaign.

CREATE OR REPLACE TABLE
    `gcp-media-data-platform.media_gold.dim_campaign`
AS

SELECT
    campaign_id,
    brand,
    platform,
    country
FROM `gcp-media-data-platform.media_silver.media_events`

QUALIFY ROW_NUMBER() OVER (
    PARTITION BY campaign_id
    ORDER BY
        ingestion_timestamp DESC,
        event_id DESC
) = 1;


-- 2. Date dimension.
-- Grain: one row per calendar date.

CREATE OR REPLACE TABLE
    `gcp-media-data-platform.media_gold.dim_date`
AS

SELECT
    calendar_date AS date_id,
    EXTRACT(YEAR FROM calendar_date) AS year,
    EXTRACT(QUARTER FROM calendar_date) AS quarter,
    EXTRACT(MONTH FROM calendar_date) AS month,
    EXTRACT(DAY FROM calendar_date) AS day,
    EXTRACT(DAYOFWEEK FROM calendar_date) AS day_of_week,
    FORMAT_DATE('%A', calendar_date) AS day_name,
    FORMAT_DATE('%B', calendar_date) AS month_name,
    EXTRACT(DAYOFWEEK FROM calendar_date)
        IN (1, 7) AS is_weekend

FROM UNNEST(
    GENERATE_DATE_ARRAY(
        DATE '2026-01-01',
        DATE '2027-12-31'
    )
) AS calendar_date;


-- 3. Media performance fact table.
-- Grain: one row per unique media event.

CREATE OR REPLACE TABLE
    `gcp-media-data-platform.media_gold.fact_media_events`
PARTITION BY event_date
CLUSTER BY campaign_id, source
AS

SELECT
    event_id,
    event_date,
    event_timestamp,
    campaign_id,
    impressions,
    clicks,
    conversions,
    spend,
    revenue,
    revenue - spend AS profit,
    source,
    batch_id,
    ingestion_timestamp

FROM `gcp-media-data-platform.media_silver.media_events`;


-- 4. Daily campaign analytics mart.
-- Grain: one row per campaign and calendar date.

CREATE OR REPLACE TABLE
    `gcp-media-data-platform.media_gold.mart_campaign_daily`
PARTITION BY event_date
CLUSTER BY campaign_id, platform
AS

WITH aggregated AS (
    SELECT
        f.event_date,
        f.campaign_id,
        c.brand,
        c.platform,
        c.country,
        d.year,
        d.month,

        COUNT(*) AS total_events,
        SUM(f.impressions) AS impressions,
        SUM(f.clicks) AS clicks,
        SUM(f.conversions) AS conversions,
        SUM(f.spend) AS spend,
        SUM(f.revenue) AS revenue,
        SUM(f.profit) AS profit

    FROM `gcp-media-data-platform.media_gold.fact_media_events` AS f

    INNER JOIN
        `gcp-media-data-platform.media_gold.dim_campaign` AS c
        ON f.campaign_id = c.campaign_id

    INNER JOIN
        `gcp-media-data-platform.media_gold.dim_date` AS d
        ON f.event_date = d.date_id

    GROUP BY
        f.event_date,
        f.campaign_id,
        c.brand,
        c.platform,
        c.country,
        d.year,
        d.month
)

SELECT
    *,
    ROUND(SAFE_DIVIDE(clicks, impressions) * 100, 4)
        AS ctr_pct,

    ROUND(SAFE_DIVIDE(spend, clicks), 4)
        AS cpc,

    ROUND(SAFE_DIVIDE(spend, impressions) * 1000, 4)
        AS cpm,

    ROUND(SAFE_DIVIDE(spend, conversions), 4)
        AS cpa,

    ROUND(SAFE_DIVIDE(conversions, clicks) * 100, 4)
        AS conversion_rate_pct,

    ROUND(SAFE_DIVIDE(revenue, spend), 4)
        AS roas

FROM aggregated;
