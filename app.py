import os
import json

from flask import Flask, Response, request, jsonify, render_template
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, bindparam
from src.connection import database_url, db
import src.helpers as helpers


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

    #==================== GET THE IDs AS RAW STRING =====================
    raw_category_ids = request.args.get("category_ids", "")
    raw_commodity_ids = request.args.get("commodity_ids", "")
    raw_region_values = request.args.get("region_values", "")
    raw_province_values = request.args.get("province_names")
    raw_market_ids = request.args.get("market_ids")


    #==================== PASS THE IDs INTO AN ARRAY =====================
    selected_category_ids = helpers.raw_string_to_array(raw_category_ids, "int")
    selected_commodity_ids = helpers.raw_string_to_array(raw_commodity_ids, "int")
    selected_region_values = helpers.raw_string_to_array(raw_region_values, "str")
    selected_province_values = helpers.raw_string_to_array(raw_province_values, "str")
    selected_market_ids = helpers.raw_string_to_array(raw_market_ids, "int")
    

    #==================== RE-BUILD THE SELECTED ITEMS IN MULTI-SELECT DROPDOWNS ====================
    category_names = helpers.records_to_array_from_ids(selected_category_ids, text("""
                    SELECT category_name
                    FROM categories
                    WHERE category_id IN :category_ids
                    ORDER BY category_name
                """), "category_ids", "category_name")

    commodity_names = helpers.records_to_array_from_ids(selected_commodity_ids, text("""
                        SELECT commodity_name
                        FROM commodities
                        WHERE commodity_id IN :commodity_ids
                        ORDER BY commodity_name
                    """), "commodity_ids", "commodity_name")

    region_texts = helpers.records_to_array_from_ids(selected_region_values, text("""
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
                        """), "region_values", "region_text")

 
    #========================================== MULTI-SELECT DROPDOWN DATA ==========================================
    categories_columns, categories_rows = helpers.fetch_records_static_qry("SELECT * FROM categories")

    commodities_columns, commodities_rows = helpers.fetch_records_dynamic_qry("SELECT * FROM commodities", 
                                                                      "WHERE category_id IN :category_ids",
                                                                      "ORDER BY commodity_name",
                                                                      selected_category_ids,
                                                                      "category_ids"
                                                                      )
    
    regions_columns, regions_rows = helpers.fetch_records_static_qry("""SELECT DISTINCT admin1 AS region_value,
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
                    ORDER BY admin1;""")

    province_columns, province_rows = helpers.fetch_records_dynamic_qry("SELECT DISTINCT admin2 as province_name FROM MARKETS",
                                                                "WHERE admin1 IN :region_values",
                                                                "ORDER BY admin2",
                                                                selected_region_values,
                                                                "region_values")
    markets_columns, markets_rows = helpers.fetch_records_dynamic_qry("SELECT DISTINCT market_id, market_name FROM markets",
                                                              "WHERE admin1 IN :region_values",
                                                              "ORDER BY market_name",
                                                              selected_region_values,
                                                              "region_values")


    #========================================== KPI CARDS DATA ==========================================
    all_data_qry = """WITH all_data_cte AS (
                        SELECT 
                            po.price_id,
                            po.observation_date,
                            po.market_id,
                            po.commodity_id,
                            po.unit,
                            po.price_flag,
                            po.price_type,
                            po.currency,
                            po.price,
                            po.usd_price,
                            com.commodity_name,
                            cat.category_id,
                            cat.category_name,
                            mkt.market_name,
                            mkt.admin1,
                            mkt.admin2,
                            mkt.latitude,
                            mkt.longitude
                        FROM price_observations AS po
                        INNER JOIN markets AS mkt ON po.market_id = mkt.market_id
                        INNER JOIN commodities AS com ON po.commodity_id = com.commodity_id
                        INNER JOIN categories AS cat ON com.category_id = cat.category_id
                    )"""


    price_obs_count_qry = all_data_qry + " SELECT COUNT(*) FROM all_data_cte"
    price_obs_count_filters = {
        "category_ids": ("category_id IN :category_ids", selected_category_ids),
        "commodity_ids": ("commodity_id IN :commodity_ids", selected_commodity_ids),
        "region_values": ("admin1 IN :region_values", selected_region_values),
        "province_names": ("admin2 IN :province_names", selected_province_values),
        "market_ids": ("market_id IN :market_ids", selected_market_ids),
    }
    price_obs_count = helpers.fetch_single_dynamic_qry(price_obs_count_qry, 
                                                       price_obs_count_filters, 
                                                       "")
    price_obs_count_new = helpers.fetch_single_dynamic_qry(price_obs_count_qry, 
                                                           price_obs_count_filters, 
                                                           " observation_date = ( SELECT max(observation_date) FROM price_observations )")


    ########## OPEN SUPABASE CONNECTION ##########
    with db.engine.connect() as connection:
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

        # price_obs_count = connection.execute(
        #     text("SELECT COUNT(*) FROM price_observations")
        #     ).scalar_one()

        # price_obs_count_new = connection.execute(
        #     text("SELECT count(*) FROM price_observations WHERE observation_date = ( SELECT max(observation_date) FROM price_observations )")
        # ).scalar_one()


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
        province_columns=province_columns,
        province_rows=province_rows,
        commodities_columns=commodities_columns,
        commodities_rows=commodities_rows,
        observations=price_obs_rows,
        category_ids=selected_category_ids,
        category_names=category_names,
        commodity_ids=selected_commodity_ids,
        commodity_names=commodity_names,
        region_values=selected_region_values,
        region_texts=region_texts,
        province_names=selected_province_values
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