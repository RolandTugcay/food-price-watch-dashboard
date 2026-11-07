import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Flask, request, jsonify, render_template
from sqlalchemy import text
from src.connection import database_url, db
import src.helpers as helpers
import src.sql_txt as sql_txt


#==================== Initialize the Flask application =====================
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

#==================== GET THE IDs, VALUES AS RAW STRING =====================
    raw_category_ids = request.args.get("category_ids", "")
    raw_commodity_ids = request.args.get("commodity_ids", "")
    raw_region_values = request.args.get("region_values", "")
    raw_province_values = request.args.get("province_names", "").strip()
    raw_market_ids = request.args.get("market_ids", "").strip()

    filtered_cat_com = any(value and value.strip() for value in (
                raw_category_ids,
                raw_commodity_ids
            ))

    filtered_reg_prov_mkt = any(value and value.strip() for value in (
                raw_region_values,
                raw_province_values,
                raw_market_ids
            ))

    filter_date_from = request.args.get("filter_date_from", "").strip()
    if not filter_date_from:
        filter_date_from = helpers.fetch_single_static_qry("SELECT MIN(observation_date) FROM price_observations")  # Default value if not provided

    filter_date_to = request.args.get("filter_date_to", "").strip()
    if not filter_date_to:
        filter_date_to = helpers.fetch_single_static_qry("SELECT MAX(observation_date) FROM price_observations")  # Default value if not provided


#==================== PASS THE IDs INTO AN ARRAY =====================
    selected_category_ids = helpers.raw_string_to_array(raw_category_ids, "int")
    selected_commodity_ids = helpers.raw_string_to_array(raw_commodity_ids, "int")
    selected_region_values = helpers.raw_string_to_array(raw_region_values, "str")
    selected_province_values = helpers.raw_string_to_array(raw_province_values, "str")
    selected_market_ids = helpers.raw_string_to_array(raw_market_ids, "int")
    
    selected_unit_values = helpers.raw_string_to_array(request.args.get("unit_values", ""), "str")
    if not selected_unit_values:
        selected_unit_values = ["KG"]   
    
    selected_price_type_values = helpers.raw_string_to_array(request.args.get("price_type_values", ""), "str")
    if not selected_price_type_values:
        selected_price_type_values = ['Retail']

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


    region_case_statements = """CASE
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
                            END AS region_text"""
    
    region_texts = helpers.records_to_array_from_ids(selected_region_values, text("""
                        SELECT DISTINCT admin1 AS region_value, 
                        """ + region_case_statements + """ 
                        FROM markets
                        WHERE admin1 in :region_values
                        ORDER BY admin1;
                        """), "region_values", "region_text")



#========================================== MULTI-SELECT DROPDOWN DATA ==========================================
    categories_columns, categories_rows = helpers.fetch_records_dynamic_qry("""SELECT DISTINCT cat.category_id, cat.category_name FROM commodities as com 
                                                                            INNER JOIN categories as cat on com.category_id = cat.category_id""", 
                                                                            """WHERE com.commodity_id IN :commodity_ids""",
                                                                            """ORDER BY cat.category_name""",
                                                                            selected_commodity_ids,
                                                                            "commodity_ids"
                                                                            )

    commodities_columns, commodities_rows = helpers.fetch_records_dynamic_qry("SELECT * FROM commodities", 
                                                                      "WHERE category_id IN :category_ids",
                                                                      "ORDER BY commodity_name",
                                                                      selected_category_ids,
                                                                      "category_ids"
                                                                      )
    
    regions_columns, regions_rows = helpers.fetch_records_static_qry("""SELECT DISTINCT admin1 AS region_value, 
                    """ + region_case_statements + """ 
                    FROM markets 
                    ORDER BY admin1;""")

    province_columns, province_rows = helpers.fetch_records_dynamic_qry("SELECT DISTINCT admin2 as province_name FROM MARKETS",
                                                                "WHERE admin1 IN :region_values",
                                                                "ORDER BY admin2",
                                                                selected_region_values,
                                                                "region_values")
    markets_columns, markets_rows = helpers.fetch_records_dynamic_qry("SELECT DISTINCT market_id, market_name FROM markets",
                                                              "WHERE admin2 IN :province_names",
                                                              "ORDER BY market_name",
                                                              selected_province_values,
                                                              "province_names")

    units_columns, units_rows = helpers.fetch_records_static_qry("SELECT DISTINCT unit FROM price_observations ORDER BY unit")
    price_types_columns, price_types_rows = helpers.fetch_records_static_qry("SELECT DISTINCT price_type FROM price_observations ORDER BY price_type")


    #========================================== KPI CARDS DATA ==========================================
    join_qry = """FROM price_observations AS po
                    INNER JOIN markets AS mkt ON po.market_id = mkt.market_id
                    INNER JOIN commodities AS com ON po.commodity_id = com.commodity_id
                    INNER JOIN categories AS cat ON com.category_id = cat.category_id
                """
    filters = {
        "category_ids": ("cat.category_id IN :category_ids", selected_category_ids),
        "commodity_ids": ("com.commodity_id IN :commodity_ids", selected_commodity_ids),
        "region_values": ("mkt.admin1 IN :region_values", selected_region_values),
        "province_names": ("mkt.admin2 IN :province_names", selected_province_values),
        "market_ids": ("mkt.market_id IN :market_ids", selected_market_ids),
        "unit_values": ("po.unit IN :unit_values", selected_unit_values),
        "price_type_values": ("po.price_type IN :price_type_values", selected_price_type_values),
        "filter_date_from": ("po.observation_date >= :filter_date_from", filter_date_from),
        "filter_date_to": ("po.observation_date <= :filter_date_to", filter_date_to)
    }

    commodities_count_select_qry = """SELECT count(DISTINCT com.commodity_id) as cnt"""
    commodities_count = helpers.fetch_single_dynamic_qry(f"{commodities_count_select_qry} {join_qry}", filters, "")

    category_count_select_qry = """SELECT count(DISTINCT cat.category_id) as cnt"""
    category_count = helpers.fetch_single_dynamic_qry(f"{category_count_select_qry} {join_qry}", filters, "")

    market_count_select_qry = """SELECT count(DISTINCT mkt.market_id) as cnt"""
    market_count = helpers.fetch_single_dynamic_qry(f"{market_count_select_qry} {join_qry}", filters, "")

    region_count_select_qry = """SELECT count(DISTINCT mkt.admin1) as cnt"""
    region_count = helpers.fetch_single_dynamic_qry(f"{region_count_select_qry} {join_qry}", filters, "")

    price_obs_count_select_qry = """SELECT count(*) as cnt"""
    price_obs_count = helpers.fetch_single_dynamic_qry(f"{price_obs_count_select_qry} {join_qry}", 
                                                       filters, 
                                                       "")

    price_obs_count_new = helpers.fetch_single_dynamic_qry(f"{price_obs_count_select_qry} {join_qry}", filters, 
                                                           " po.observation_date = ( SELECT max(observation_date) FROM price_observations )")

    # Average price
    this_mo_avg_prc_slct_qry = """SELECT avg(po.price) as avg_price"""
    this_mo_avg_prc = helpers.fetch_single_dynamic_qry(f"{this_mo_avg_prc_slct_qry} {join_qry}", filters, 
                                                            " po.observation_date = ( SELECT max(observation_date) FROM price_observations )")
    
    prev_mo_avg_prc_slct_qry = """SELECT avg(po.price) as avg_price"""
    prev_mo_avg_prc = helpers.fetch_single_dynamic_qry(f"{prev_mo_avg_prc_slct_qry} {join_qry}", filters,
                                                            " po.observation_date = (SELECT observation_date FROM v_observation_date_row_num WHERE row_num = 2)")

    this_mo_avg_prc = this_mo_avg_prc if this_mo_avg_prc is not None else 0
    avg_prc_pct_change = ((this_mo_avg_prc - prev_mo_avg_prc) / prev_mo_avg_prc * 100) if prev_mo_avg_prc else 0


    #========================================== CHART DATA ==========================================
    #========================= FILTERS FOR CHART DATA ==========================
    filters_chart = {
        "category_ids": ("category_id IN :category_ids", selected_category_ids),
        "commodity_ids": ("commodity_id IN :commodity_ids", selected_commodity_ids),
        "region_values": ("admin1 IN :region_values", selected_region_values),
        "province_names": ("admin2 IN :province_names", selected_province_values),
        "market_ids": ("market_id IN :market_ids", selected_market_ids),
        "unit_values": ("unit IN :unit_values", selected_unit_values),
        "price_type_values": ("price_type IN :price_type_values", selected_price_type_values),
        "filter_date_from": ("observation_date >= :filter_date_from", filter_date_from),
        "filter_date_to": ("observation_date <= :filter_date_to", filter_date_to)
    }

    #========================= MONTHLY TREND CHART DATA ==========================
    monthly_trend_col, monthly_trend_rows = helpers.fetch_chart_data_dynamic_qry(
        sql_txt.trend_top_qry, 
        filters_chart, "", 
        sql_txt.trend_next_qry +
        """SELECT *
        FROM monthly_category_trend 
        WHERE date_rank <= 25
        ORDER BY observation_date DESC"""
    )

    monthly_trend_chart = helpers.to_chart_data(
        monthly_trend_rows,
        x_column="observation_month",
        series_column="category_name",  
        value_column="trend_pct"    
    )

    #========================= PRICE INCREASE CHART DATA ==========================
    obs_date_1_obj = datetime.strptime(str(filter_date_to), "%Y-%m-%d")
    obs_date_1_str = obs_date_1_obj.strftime("%Y-%m-%d")
    obs_date_2_obj = obs_date_1_obj - relativedelta(months=1)
    obs_date_2_str = obs_date_2_obj.strftime("%Y-%m-%d")

    prev_obs_date_1_obj = obs_date_1_obj - relativedelta(years=1)
    prev_obs_date_1_str = prev_obs_date_1_obj.strftime("%Y-%m-%d")
    prev_obs_date_2_obj = obs_date_2_obj - relativedelta(years=1)
    prev_obs_date_2_str = prev_obs_date_2_obj.strftime("%Y-%m-%d")

    price_increase_chart_col, price_increase_chart_rows = helpers.fetch_chart_data_dynamic_qry(
        base_qry=sql_txt.price_increase_top_qry,
        filters=filters_chart,
        addtl_cond_qry=sql_txt.price_increase_addtl_cond,
        addtl_qry=sql_txt.price_increase_bottom_qry,
        addtl_params={
            "obs_date_1": obs_date_1_str,
            "obs_date_2": obs_date_2_str,
            "prev_obs_date_1": prev_obs_date_1_str,
            "prev_obs_date_2": prev_obs_date_2_str,
        },
    )

    price_increase_chart = helpers.to_chart_data(
        price_increase_chart_rows,
        x_column="commodity_name",
        series_column=None,  
        value_columns=["avg_lat_pct_increase", "avg_prev_pct_increase"],
        value_labels={
            "avg_lat_pct_increase": "Selected Month",
            "avg_prev_pct_increase": "Previous Year",
        },
    )

    #========================= RENDER TEMPLATE ==========================
    return render_template(
        "index.html",
        categories_columns=categories_columns,
        categories_rows=categories_rows,
        category_count=category_count,
        category_ids=selected_category_ids,
        category_names=category_names,
        commodities_columns=commodities_columns,
        commodities_count=commodities_count,
        commodities_rows=commodities_rows,
        commodity_ids=selected_commodity_ids,
        commodity_names=commodity_names,
        market_count=market_count,
        market_ids=selected_market_ids,
        markets_columns=markets_columns,
        markets_rows=markets_rows,
        price_obs_count_new=price_obs_count_new,
        price_obs_count=price_obs_count,
        price_type_values=selected_price_type_values,
        price_types_columns=price_types_columns,
        price_types_rows=price_types_rows,
        province_columns=province_columns,
        province_names=selected_province_values,
        province_rows=province_rows,
        region_count=region_count,
        region_texts=region_texts,
        region_values=selected_region_values,
        regions_columns=regions_columns,
        regions_rows=regions_rows,
        units_columns=units_columns,
        units_rows=units_rows,
        unit_values=selected_unit_values,
        filter_date_from=filter_date_from,
        filter_date_to=filter_date_to,
        filtered_cat_com=filtered_cat_com,
        filtered_reg_prov_mkt=filtered_reg_prov_mkt,
        this_mo_avg_prc=this_mo_avg_prc,
        prev_mo_avg_prc=prev_mo_avg_prc,
        avg_prc_pct_change=avg_prc_pct_change,
        monthly_trend_chart=monthly_trend_chart,
        price_increase_chart=price_increase_chart
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