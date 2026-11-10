region_case_statements = """
CASE
    WHEN admin1 = 'Autonomous region in Muslim Mindanao' THEN 'Autonomous region in Muslim Mindanao (ARMM)'
    WHEN admin1 = 'Cordillera Administrative region' THEN 'Cordillera Administrative region (CAR)'
    WHEN admin1 = 'National Capital region' THEN 'National Capital region (NCR)'
    WHEN admin1 = 'Region I' THEN 'Region I (ILOCOS REGION)'
    WHEN admin1 = 'Region II' THEN 'Region II (CAGAYAN VALLEY)'
    WHEN admin1 = 'Region III' THEN 'Region III (CENTRAL LUZON)'
    WHEN admin1 = 'Region IV-A' THEN 'Region IV-A (CALABARZON)'
    WHEN admin1 = 'Region IV-B' THEN 'Region IV-B (MIMAROPA)'
    WHEN admin1 = 'Region V' THEN 'Region V (BICOL)'
    WHEN admin1 = 'Region VI' THEN 'Region VI (WESTERN VISAYAS)'
    WHEN admin1 = 'Region VII' THEN 'Region VII (CENTRAL VISAYAS)'
    WHEN admin1 = 'Region VIII' THEN 'Region VIII (EASTERN VISAYAS)'
    WHEN admin1 = 'Region IX' THEN 'Region IX (ZAMBOANGA PENINSULA)'
    WHEN admin1 = 'Region X' THEN 'Region X (NORTHERN MINDANAO)'
    WHEN admin1 = 'Region XI' THEN 'Region XI (DAVAO REGION)'
    WHEN admin1 = 'Region XII' THEN 'Region XII (SOCCSKSARGEN)'
    WHEN admin1 = 'Region XIII' THEN 'Region XIII (CARAGA)'
    ELSE admin1
END AS region_text
"""

trend_top_qry = """
WITH monthly_series_prices AS MATERIALIZED (
    SELECT
        DATE_TRUNC('month', observation_date)::date AS observation_date,
        category_id,
        commodity_id,
        market_id,
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
    commodity_id,
    market_id,
    unit,
    price_type,
    currency
),

first_month_per_series AS MATERIALIZED (
    SELECT DISTINCT ON (
        category_id, commodity_id, market_id, unit, price_type, currency
    )
        category_id,
        commodity_id,
        market_id,
        unit,
        price_type,
        currency,
        avg_price AS base_price,
        COUNT(*) OVER (
            PARTITION BY category_id, commodity_id, market_id, unit, price_type, currency
        ) AS month_count
    FROM monthly_series_prices
    ORDER BY
        category_id, commodity_id, market_id, unit, price_type, currency,
        observation_date
),

category_base_price AS MATERIALIZED (
    SELECT
        category_id,
        unit,
        price_type,
        currency,
        SUM(base_price * month_count) / SUM(month_count) AS base_avg_price
    FROM first_month_per_series
    GROUP BY
        category_id,
        unit,
        price_type,
        currency
),

monthly_category_prices AS MATERIALIZED (
    SELECT
        observation_date,
        category_id,
        unit,
        price_type,
        currency,
        AVG(avg_price) AS avg_price
    FROM monthly_series_prices
    GROUP BY
        observation_date,
        category_id,
        unit,
        price_type,
        currency
),

monthly_category_trend AS MATERIALIZED (
    SELECT
        DENSE_RANK() OVER (ORDER BY m.observation_date DESC) as date_rank,
        m.observation_date,
        TO_CHAR(m.observation_date, 'YYYY-MM') AS observation_month,
        m.category_id,
        c.category_name,
        m.unit,
        m.price_type,
        m.currency,
        m.avg_price,
        b.base_avg_price,
        100.0 * (m.avg_price / NULLIF(b.base_avg_price, 0) - 1) AS trend_pct
    FROM monthly_category_prices AS m
    JOIN category_base_price AS b
    ON m.category_id = b.category_id
    AND m.unit = b.unit
    AND m.price_type = b.price_type
    AND m.currency = b.currency
    JOIN categories AS c
    ON m.category_id = c.category_id
)
"""

price_increase_top_qry = """
WITH price_obs_data AS MATERIALIZED (
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
	joined_data AS MATERIALIZED (
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

price_observations_qry = """
WITH lag_price_cte AS (
    SELECT
        po.price_id,
	    com.commodity_id,
	    com.commodity_name,
	    cat.category_name,
	    mkt.admin1 AS region,
	    mkt.market_name,
	    po.observation_date,
		po.unit,
	    po.price_type,
		po.price,
        LAG(po.price) OVER (
            PARTITION BY mkt.market_name, com.commodity_name, po.unit, po.price_type
            ORDER BY po.observation_date
        ) AS prev_price
    FROM price_observations AS po
    INNER JOIN markets AS mkt ON po.market_id = mkt.market_id
    INNER JOIN commodities AS com ON po.commodity_id = com.commodity_id
    INNER JOIN categories AS cat ON com.category_id = cat.category_id
)
SELECT
    price_id,
    commodity_id,
    commodity_id || '-' || REPLACE(REGEXP_REPLACE(LOWER(commodity_name),'[^\w ]+', '', 'g'),' ','-') AS icon_name,
    commodity_name,
    category_name,
    region,
    market_name,
    observation_date,
    price_type,
    ROUND(price, 2) || ' / ' || unit AS price,
    ROUND(prev_price, 2) || ' / ' || unit AS prev_price,
    ROUND(((price - prev_price) / NULLIF(prev_price, 0)) * 100, 2) AS change_pct
FROM lag_price_cte
WHERE
    commodity_name ILIKE '%' || :search || '%'
    OR region ILIKE '%' || :search || '%'
    OR market_name ILIKE '%' || :search || '%'
    OR price_type ILIKE '%' || :search || '%'
    OR CAST(observation_date AS TEXT) ILIKE '%' || :search || '%'
ORDER BY CAST(observation_date AS TEXT) DESC, price_id DESC
LIMIT :limit OFFSET :offset
"""


price_observations_count_qry = """
SELECT COUNT(*)
FROM price_observations AS po
INNER JOIN markets AS mkt ON po.market_id = mkt.market_id
INNER JOIN commodities AS com ON po.commodity_id = com.commodity_id
INNER JOIN categories AS cat ON com.category_id = cat.category_id     
WHERE
    com.commodity_name ILIKE '%' || :search || '%'
    OR mkt.admin1 ILIKE '%' || :search || '%'
    OR mkt.market_name ILIKE '%' || :search || '%'
    OR po.price_type ILIKE '%' || :search || '%'
    OR CAST(po.observation_date AS TEXT) ILIKE '%' || :search || '%'
"""

com_price_trend_qry = """
WITH cur_year_data_cte AS (
	SELECT
	    po.observation_date,
		TO_CHAR(po.observation_date, 'MM-Month') as month,
	    po.price
	FROM price_observations AS po
	INNER JOIN markets AS mkt ON po.market_id = mkt.market_id
	WHERE 
	    EXTRACT(YEAR FROM po.observation_date) = :cur_year AND
	    po.commodity_id = :commodity_id AND
	    mkt.market_name = :market_name
	ORDER BY po.observation_date
),
prev_year_data_cte AS (
	SELECT
	    po.observation_date,
		TO_CHAR(po.observation_date, 'MM-Month') as month,
	    po.price
	FROM price_observations AS po
	INNER JOIN markets AS mkt ON po.market_id = mkt.market_id
	WHERE 
	    EXTRACT(YEAR FROM po.observation_date) = :prev_year AND
	    po.commodity_id = :commodity_id AND
	    mkt.market_name = :market_name
	ORDER BY po.observation_date
)
SELECT 
	COALESCE(cur.month, prev.month) AS month,
    COALESCE(cur.price, NULL) AS cur_year,
    prev.price AS prev_year
FROM cur_year_data_cte AS cur
RIGHT JOIN prev_year_data_cte AS prev 
	ON cur.month = prev.month
"""