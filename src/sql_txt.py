trend_top_qry = """
WITH monthly_series_prices AS (
    SELECT
        DATE_TRUNC('month', observation_date)::date AS observation_date,
        category_id,
        category_name,
        commodity_id,
        commodity_name,
        market_id,
        market_name,
        unit,
        price_type,
        currency,
        AVG(price) AS avg_price
    FROM v_price_observations
"""

trend_next_qry = """
GROUP BY
        DATE_TRUNC('month', observation_date)::date,
        category_id,
        category_name,
        commodity_id,
        commodity_name,
        market_id,
        market_name,
        unit,
        price_type,
        currency
),

first_month_per_series AS (
    SELECT DISTINCT ON (
        category_id, commodity_id, market_id, unit, price_type, currency
    )
        category_id,
        commodity_id,
        market_id,
        unit,
        price_type,
        currency,
        avg_price AS base_price
    FROM monthly_series_prices
    ORDER BY
        category_id, commodity_id, market_id, unit, price_type, currency,
        observation_date
),

category_base_price AS (
    SELECT
        m.category_id,
        m.category_name,
        m.unit,
        m.price_type,
        m.currency,
        AVG(b.base_price) AS base_avg_price
    FROM first_month_per_series AS b
    JOIN monthly_series_prices AS m
    ON m.category_id = b.category_id
    AND m.commodity_id = b.commodity_id
    AND m.market_id = b.market_id
    AND m.unit = b.unit
    AND m.price_type = b.price_type
    AND m.currency = b.currency
    GROUP BY
        m.category_id,
        m.category_name,
        m.unit,
        m.price_type,
        m.currency
),

monthly_category_prices AS (
    SELECT
        observation_date,
        category_id,
        category_name,
        unit,
        price_type,
        currency,
        AVG(avg_price) AS avg_price
    FROM monthly_series_prices
    GROUP BY
        observation_date,
        category_id,
        category_name,
        unit,
        price_type,
        currency
),

monthly_category_trend AS (
    SELECT
        DENSE_RANK() OVER (ORDER BY m.observation_date DESC) as date_rank,
        m.observation_date,
        TO_CHAR(m.observation_date, 'YYYY-MM') AS observation_month,
        m.category_id,
        m.category_name,
        m.unit,
        m.price_type,
        m.currency,
        m.avg_price,
        b.base_avg_price,
        100.0 * (m.avg_price / NULLIF(b.base_avg_price, 0) - 1) AS trend_pct
    FROM monthly_category_prices AS m
    JOIN category_base_price AS b
    ON m.category_id = b.category_id
    AND m.category_name = b.category_name
    AND m.unit = b.unit
    AND m.price_type = b.price_type
    AND m.currency = b.currency
)
"""

price_increase_top_qry = """
WITH price_obs_data AS (
    SELECT
        DENSE_RANK() OVER (ORDER BY observation_date DESC) as date_rank,
        observation_date,
        category_id,
        category_name,
        commodity_id,
        commodity_name,
        unit,
        price_type,
        currency,
        market_id,
        market_name,
        price
    FROM v_price_observations
"""

price_increase_addtl_cond = """observation_date in (:obs_date_1,:obs_date_2,:prev_obs_date_1,:prev_obs_date_2)"""

price_increase_bottom_qry = """
),
	joined_data AS (
	SELECT
		a.category_id,
		a.category_name,
		a.commodity_id,
		a.commodity_name,
		a.unit,
		a.price_type,
		a.currency,
		a.market_id,
		a.market_name,
		a.price AS lat_price1,
		b.price AS lat_price2,
		c.price AS prev_price1,
		d.price AS prev_price2,
		CASE 
			WHEN b.price IS NULL THEN 0
			ELSE ROUND(((a.price - b.price) / b.price) * 100, 2)
		END AS lat_pct_increase,
		CASE 
			WHEN c.price IS NULL OR d.price IS NULL THEN 0
			ELSE ROUND(((c.price - d.price) / d.price) * 100, 2)
		END AS prev_pct_increase,
        CASE 
            WHEN b.price IS NULL THEN 'Y'
            WHEN c.price IS NULL THEN 'Y'
            WHEN d.price IS NULL THEN 'Y'
            ELSE 'N'
        END AS exclude
	FROM price_obs_data AS a
	LEFT JOIN (SELECT * FROM price_obs_data WHERE date_rank = 2) AS b
	ON a.category_id = b.category_id AND
		a.commodity_id = b.commodity_id AND
		a.unit = b.unit AND
		a.price_type = b.price_type AND
		a.currency = b.currency AND
		a.market_id = b.market_id
	LEFT JOIN (SELECT * FROM price_obs_data WHERE date_rank = 3) AS c
	ON a.category_id = c.category_id AND
		a.commodity_id = c.commodity_id AND
		a.unit = c.unit AND
		a.price_type = c.price_type AND
		a.currency = c.currency AND
		a.market_id = c.market_id
	LEFT JOIN (SELECT * FROM price_obs_data WHERE date_rank = 4) AS d
	ON a.category_id = d.category_id AND
		a.commodity_id = d.commodity_id AND
		a.unit = d.unit AND
		a.price_type = d.price_type AND
		a.currency = d.currency AND
		a.market_id = d.market_id
	WHERE a.date_rank = 1
)
SELECT 
	commodity_name, 
	AVG(lat_pct_increase) AS avg_lat_pct_increase,
	AVG(prev_pct_increase) AS avg_prev_pct_increase
FROM joined_data 
WHERE exclude = 'N'
GROUP BY commodity_name 
ORDER BY 2 DESC LIMIT 10
"""