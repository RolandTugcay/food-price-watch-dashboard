import os
import json

from flask import Flask, Response, request, jsonify, render_template
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, bindparam
from scripts.connection import database_url, db


# Initialize the Flask application
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.get("/health/db")
def check_database():
    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return jsonify(status="connected"), 200

    except Exception:
        app.logger.exception("Supabase database connection failed")
        return jsonify(status="error", message="Database connection failed"), 503

@app.get("/")
def index():

    ########## GET THE IDs AS RAW STRING ##########
    raw_category_ids = request.args.get("category_ids", "")
    raw_commodity_ids = request.args.get("commodity_ids", "")
    raw_region_values = request.args.get("region_values", "")


    ##### PASS THE IDs INTO AN ARRAY #####
    try:
        selected_category_ids = [
            int(value.strip())
            for value in raw_category_ids.split(",")
            if value.strip()
        ]

        selected_commodity_ids = [
            int(value.strip())
            for value in raw_commodity_ids.split(",")
            if value.strip()
        ]

        selected_region_values = [
            str(value.strip())
            for value in raw_region_values.split(",")
            if value.strip()
        ]
    except ValueError:
        selected_category_ids = []
        selected_commodity_ids = []
        selected_region_values = []
    

    ########## OPEN SUPABASE CONNECTION ##########
    with db.engine.connect() as connection:
        
        ########## BUILD  THE SELECTED CATEGORIES ##########
        category_names = []
        if selected_category_ids:
            category_result = connection.execute(
                text("""
                    SELECT category_name
                    FROM categories
                    WHERE category_id IN :category_ids
                    ORDER BY category_name
                """).bindparams(bindparam("category_ids", expanding=True)),
                {"category_ids": selected_category_ids},
            )
            category_names = [
                row["category_name"] for row in category_result.mappings()
            ]


        ######## BUILD  THE SELECTED COMMODITIES ########
        commodity_names = []
        if selected_commodity_ids:
            commodity_result = connection.execute(
                text("""
                    SELECT commodity_name
                    FROM commodities
                    WHERE commodity_id IN :commodity_ids
                    ORDER BY commodity_name
                """).bindparams(bindparam("commodity_ids", expanding=True)),
                {"commodity_ids": selected_commodity_ids},
            )
            commodity_names = [
                row["commodity_name"] for row in commodity_result.mappings()
            ]

        ######## BUILD  THE SELECTED REGIONS ########
        region_texts = []
        if selected_region_values:
            region_result = connection.execute(
                text("""
                    SELECT DISTINCT admin1 AS region_value,
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
                    FROM markets
                    WHERE admin1 in :region_values
                    ORDER BY admin1;
                    """).bindparams(bindparam("region_values", expanding=True)),
                {"region_values": selected_region_values},
            )
            region_texts = [
                row["region_text"] for row in region_result.mappings()
            ]

        ######## CATEGORIES DROPDOWN DATA ########
        categories_result = connection.execute(
            text("SELECT * FROM categories"))
        categories_columns = list(categories_result.keys())
        categories_rows = [
            dict(row) for row in categories_result.mappings()
        ]

        ######## COMMODITIES DROPDOWN DATA ########
        commodities_query= text("""""")
        if selected_category_ids:
            commodities_query = text("""
                SELECT *
                FROM commodities
                WHERE category_id IN :category_ids
                ORDER BY commodity_name
            """).bindparams(bindparam("category_ids", expanding=True))

            commodities_result = connection.execute(
                commodities_query,
                {"category_ids": selected_category_ids},
            )
        else:
            commodities_result = connection.execute(text("""
                SELECT *
                FROM commodities
                ORDER BY commodity_name
            """))
        
        commodities_rows = [dict(row) for row in commodities_result.mappings()]
        commodities_columns = list(commodities_result.keys())

        ######## REGION DROPDOWN DATA ########
        regions_result = connection.execute(text("""SELECT DISTINCT admin1 AS region_value,
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
                    FROM markets 
                    ORDER BY admin1;"""))
        regions_columns = list(regions_result.keys())
        regions_rows = [
                    dict(row) for row in regions_result.mappings()
                ]

        markets_result = connection.execute(text("SELECT * FROM markets"))
        markets_columns = list(markets_result.keys())
        markets_rows = [
            dict(row) for row in markets_result.mappings()
        ]

        ########## KPI CARDS #########
        commodities_count = connection.execute(
            text("SELECT COUNT(*) FROM commodities")
            ).scalar_one()

        category_count = connection.execute(
            text("SELECT COUNT(*) FROM categories")
            ).scalar_one()

        market_count = connection.execute(
            text("SELECT COUNT(*) FROM markets")
            ).scalar_one()

        region_count = connection.execute(
            text("SELECT COUNT(DISTINCT admin1) FROM markets")
            ).scalar_one()

        price_obs_count = connection.execute(
            text("SELECT COUNT(*) FROM price_observations")
            ).scalar_one()

        price_obs_count_new = connection.execute(
            text("SELECT count(*) FROM price_observations WHERE observation_date = ( SELECT max(observation_date) FROM price_observations )")
        ).scalar_one()


        price_obs_result = connection.execute(text("""
            SELECT
                po.observation_date,
                c.commodity_name,
                m.market_name,
                cat.category_name,
                po.price,
                po.unit,
                po.price_type
            FROM
            price_observations AS po
            INNER JOIN markets AS m ON po.market_id = m.market_id
            INNER JOIN commodities AS c ON po.commodity_id = c.commodity_id
            INNER JOIN categories AS cat ON c.category_id = cat.category_id
            ORDER BY
            observation_date DESC
            LIMIT 10
        """))
        price_obs_columns = list(price_obs_result.keys())
        price_obs_rows = [
            dict(row) for row in price_obs_result.mappings()
        ]


    return render_template(
        "index.html",
        commodities_count=commodities_count,
        category_count=category_count,
        market_count=market_count,
        region_count=region_count,
        price_obs_count=price_obs_count,
        price_obs_count_new=price_obs_count_new,
        price_obs_columns=price_obs_columns,
        categories_columns=categories_columns,
        categories_rows=categories_rows,
        markets_columns=markets_columns,
        markets_rows=markets_rows,
        regions_columns=regions_columns,
        regions_rows=regions_rows,
        commodities_columns=commodities_columns,
        commodities_rows=commodities_rows,
        observations=price_obs_rows,
        category_ids=selected_category_ids,
        category_names=category_names,
        commodity_ids=selected_commodity_ids,
        commodity_names=commodity_names,
        region_values=selected_region_values,
        region_texts=region_texts
    )

@app.route('/price-observations')
def price_observations():
    return render_template('price-observations.html')

@app.route('/commodities')
def commodities():
    return render_template('commodities.html')

@app.route('/markets')
def markets():
    return render_template('markets.html')

@app.route('/test')
def test():
    return render_template('test.html')

if __name__ == "__main__":
    app.run(debug=True)