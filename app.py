import os
import json
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Flask, request, jsonify, render_template, session
from sqlalchemy import text
from src.connection import database_url, db
from pathlib import Path
from dotenv import load_dotenv
import src.helpers as helpers
import src.sql_txt as sql_txt


#==================== Initialize the Flask application =====================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
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


    
    
    region_texts = helpers.records_to_array_from_ids(selected_region_values, text("""
                        SELECT DISTINCT admin1 AS region_value, 
                        """ + sql_txt.region_case_statements + """ 
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
                    """ + sql_txt.region_case_statements + """ 
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

    kpi_col, kpi_rows = helpers.fetch_filtered_records_dynamic_qry(
        base_qry=sql_txt.kpi_base_qry,
        filters=filters,
        addtl_cond_qry=None,
        addtl_qry=sql_txt.kpi_bottom_qry
    )

    kpi_row = kpi_rows[0] if kpi_rows else {}
    commodities_count = kpi_row.get("com_cnt", 0)
    category_count = kpi_row.get("cat_cnt", 0)
    market_count = kpi_row.get("mkt_cnt", 0)
    region_count = kpi_row.get("reg_cnt", 0)
    price_obs_count = kpi_row.get("po_cnt", 0)
    price_obs_count_new = kpi_row.get("new_po_cnt", 0)
    this_mo_avg_prc = kpi_row.get("avg_price", 0)
    avg_prc_pct_change = kpi_row.get("change_pct", 0)

    #========================================== CHART DATA ==========================================
    #========================= MONTHLY TREND CHART DATA ==========================
    monthly_trend_col, monthly_trend_rows = helpers.fetch_chart_data_dynamic_qry(
        sql_txt.trend_top_qry, 
        filters, "", 
        sql_txt.trend_next_qry +
        """SELECT *
            FROM monthly_category_trend 
            WHERE date_rank <= 25
            ORDER BY observation_date DESC
        """
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
        filters=filters,
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

    #========================= REGIONAL PRICE COMPARISON CHART DATA ==========================
    reg_prc_comp_chart_col, reg_prc_comp_chart_rows = helpers.fetch_chart_data_dynamic_qry(
        base_qry="""
        SELECT
            mkt.admin1 AS region,
            AVG(po.price) AS "Average Price"
        FROM price_observations AS po
            INNER JOIN markets AS mkt ON po.market_id = mkt.market_id
            INNER JOIN commodities AS com ON po.commodity_id = com.commodity_id
            INNER JOIN categories AS cat ON com.category_id = cat.category_id
        """,
        filters=filters,
        addtl_cond_qry=None,
        addtl_qry="""GROUP BY mkt.admin1 ORDER BY 2 DESC""",
        addtl_params=None
    )

    reg_prc_comp_chart = helpers.to_chart_data(
        reg_prc_comp_chart_rows,
        x_column="region",
        series_column=None,
        value_column="Average Price"
    )

    #========================= PROVINCIAL PRICE COMPARISON CHART DATA ==========================

    map_chart_col, map_chart_rows = helpers.fetch_chart_data_dynamic_qry(
        base_qry="""
        SELECT 
            mkt.admin2 AS province, 
            AVG(po.price) AS avg_price 
        FROM price_observations AS po
                INNER JOIN markets AS mkt ON po.market_id = mkt.market_id
                INNER JOIN commodities AS com ON po.commodity_id = com.commodity_id
                INNER JOIN categories AS cat ON com.category_id = cat.category_id
        """,
        filters=filters,
        addtl_cond_qry=None,
        addtl_qry="""GROUP BY mkt.admin2""",
        addtl_params=None
    )

    # Retrive the geometry json files inside ..\static\json\regions
    region_dir = Path(app.static_folder) / "json" / "regions"
    region_geojson_files = sorted(path.name for path in region_dir.glob("*.json"))

    #========================================== PIPELINE STATUS ==========================================
    latest_sync, latest_obs_date = helpers.fetch_latest_sync_obs_date()

    #========================================== RENDER TEMPLATE ==========================================
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
        avg_prc_pct_change=avg_prc_pct_change,
        monthly_trend_chart=monthly_trend_chart,
        price_increase_chart=price_increase_chart,
        reg_prc_comp_chart=reg_prc_comp_chart,
        map_chart_rows=map_chart_rows,
        region_geojson_files=region_geojson_files,
        latest_sync=latest_sync,
        latetst_obs_date=latest_obs_date
    )

@app.route('/price-observations')
def price_observations():

    #========================= POPULATE PRICE OBSEVATIONS TABLE =========================
    sort_columns = {
        "commodity": "commodity_name",
        "region": "region",
        "market": "market_name",
        "date": "observation_date",
        "price_type": "price_type",
        "price": "lag_price_cte.price",
        "change": "change_pct",
    }

    search = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    price_observations_col, price_observations_rows, price_observations_pagination = helpers.fetch_paginated_records(
        count_qry=sql_txt.price_observations_count_qry,
        data_qry=sql_txt.price_observations_qry,
        page=page,
        per_page=10,
        params={"search": search},
        sort=request.args.get("sort", "date"),
        direction=request.args.get("direction", "desc"),
        sort_columns=sort_columns,
        default_sort="date",
        tie_breaker="price_id DESC"
    )

    #========================= PRICE TREND CHART DATA =========================
    if "selected_observation" in request.args:
        selected_observation = request.args.get("selected_observation", "")

        if selected_observation:
            session["selected_observation"] = selected_observation
        else:
            # Your search JavaScript submits an empty value when search changes.
            session.pop("selected_observation", None)
    else:
        selected_observation = session.get("selected_observation", "")

    try:
        selection = json.loads(selected_observation) if selected_observation else {}
    except json.JSONDecodeError:
        selection = {}
        session.pop("selected_observation", None)
    
    price_id = selection.get("price_id")
    
    commodity_id = selection.get("commodity_id")
    if commodity_id is None:
        commodity_id = 80

    commodity_name = selection.get("commodity_name")
    if commodity_name is None:
        commodity_name = 'Rice (regular, milled)'

    market_name = selection.get("market_name")
    if market_name is None:
        market_name = 'Metro Manila'

    icon_name = selection.get("icon_name")
    if icon_name is None:
        icon_name = '80-rice-regular-milled'

    observation_date = selection.get("date")

    if observation_date:
        observation_date = date.fromisoformat(observation_date)
        cur_year = observation_date.strftime("%Y")
        prev_year = (observation_date - relativedelta(years=1)).strftime("%Y")
    else:
        observation_date = None
        cur_year = int(helpers.fetch_single_static_qry("SELECT TO_CHAR(MAX(observation_date), 'YYYY') FROM price_observations"))
        prev_year = cur_year - 1

    com_price_trend_cols, com_price_trend_rows = helpers.fetch_chart_data_dynamic_qry(
        base_qry=sql_txt.com_price_trend_qry,
        filters=None,
        addtl_cond_qry=None,
        addtl_qry=None,
        addtl_params={
            "cur_year": cur_year,
            "prev_year": prev_year,
            "commodity_id": commodity_id,
            "market_name": market_name,
        },
    )

    com_price_trend_chart_data = helpers.to_chart_data(
        com_price_trend_rows,
        x_column="month",
        series_column=None,  
        value_columns=["cur_year", "prev_year"],
        value_labels={
            "cur_year": cur_year,
            "prev_year": prev_year,
        },
        
    )

    #========================= PRICE TREND CHART DATA - ALL MARKET =========================
    com_price_trend_all_mkt_cols, com_price_trend_all_mkt__rows = helpers.fetch_chart_data_dynamic_qry(
        base_qry=sql_txt.com_price_trend_all_mkt_qry,
        filters=None,
        addtl_cond_qry=None,
        addtl_qry=None,
        addtl_params={
            "cur_year": cur_year,
            "prev_year": prev_year,
            "commodity_id": commodity_id,
        },
    )

    com_price_trend_all_mkt_rows_chart_data = helpers.to_chart_data(
        com_price_trend_all_mkt__rows,
        x_column="month",
        series_column=None,  
        value_columns=["cur_year", "prev_year"],
        value_labels={
            "cur_year": cur_year,
            "prev_year": prev_year,
        },
    )

    #========================================== PIPELINE STATUS ==========================================
    latest_sync, latest_obs_date = helpers.fetch_latest_sync_obs_date()

    return render_template(
        "price-observations.html",
        price_observations_col=price_observations_col,
        price_observations_rows=price_observations_rows,
        search=search,
        **price_observations_pagination,
        latest_sync=latest_sync,
        latest_obs_date=latest_obs_date,
        com_price_trend_chart_data=com_price_trend_chart_data,
        com_price_trend_all_mkt_rows_chart_data=com_price_trend_all_mkt_rows_chart_data,
        price_id=price_id,
        commodity_id=commodity_id,
        commodity_name=commodity_name,
        market_name=market_name,
        icon_name=icon_name
    )

@app.route('/commodities')
def commodities():

    #========================= POPULATE PRICE COMMODITIES TABLE =========================
    sort_columns = {
        "commodity_id": "commodity_id",
        "commodity": "commodity_name",
        "category": "category_name"
    }

    search = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    commodities_col, commodities_rows, commodities_pagination = helpers.fetch_paginated_records(
        count_qry=sql_txt.commodities_count_qry,
        data_qry=sql_txt.commodities_qry,
        page=page,
        per_page=10,
        params={"search": search},
        sort=request.args.get("sort", "commodity_id"),
        direction=request.args.get("direction", "asc"),
        sort_columns=sort_columns,
        default_sort="commodity_id",
        tie_breaker=None,
    )

    #========================= UNIQUE COMMODITIES PER CATEGORY CHART =========================
    uniq_com_per_cat_cols, uniq_com_per_cat_rows = helpers.fetch_chart_data_dynamic_qry(
            base_qry=sql_txt.uniq_com_per_cat_qry,
            filters=None,
            addtl_cond_qry=None,
            addtl_qry=None,
            addtl_params=None
        )

    uniq_com_per_cat_data = helpers.to_chart_data(
        uniq_com_per_cat_rows,
        x_column="category_name",
        series_column=None,
        value_column="Count"
    )

    #========================= DATA RECORDS BREAKDOWN BY CATEGORY AND PRICE TYPE CHART =========================
    data_records_breakdown_cols, data_records_breakdown_rows = helpers.fetch_chart_data_dynamic_qry(
        base_qry=sql_txt.data_records_breakdown_qry,
        filters=None,
        addtl_cond_qry=None,
        addtl_qry=None,
        addtl_params=None
    )

    data_records_breakdown_data = helpers.to_chart_data(
        data_records_breakdown_rows,
        x_column="category_name",
        series_column="price_type",  
        value_columns=['record_count'],
        value_labels=['record_count']
    )

    #========================================== PIPELINE STATUS ==========================================
    latest_sync, latest_obs_date = helpers.fetch_latest_sync_obs_date()

    return render_template(
        'commodities.html',
        latest_sync=latest_sync,
        latest_obs_date=latest_obs_date,
        commodities_rows=commodities_rows,
        **commodities_pagination,
        uniq_com_per_cat_data=uniq_com_per_cat_data,
        data_records_breakdown_data=data_records_breakdown_data
    )

@app.route('/markets')
def markets():
    #========================= POPULATE PRICE MARKETS TABLE =========================
    sort_columns = {
        "market_id": "market_id",
        "region": "region",
        "province": "province",
        "market": "market_name",
        "record_count": "record_count",
        "com_count": "com_count"
    }

    search = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    markets_col, markets_rows, markets_pagination = helpers.fetch_paginated_records(
        count_qry=sql_txt.markets_count_qry,
        data_qry=sql_txt.markets_qry,
        page=page,
        per_page=20,
        params={"search": search},
        sort=request.args.get("sort", "market_id"),
        direction=request.args.get("direction", "asc"),
        sort_columns=sort_columns,
        default_sort="market_id",
        tie_breaker=None,
    )


    #========================= RECORD DISTRIBUTION BY PROVINCE =========================
    rec_dist_by_prov_col, rec_dist_by_prov_rows = helpers.fetch_chart_data_dynamic_qry(
            base_qry=sql_txt.markets_geo_chart_qry,
            filters=None,
            addtl_cond_qry=None,
            addtl_qry=None,
            addtl_params=None
        )
    
    # Retrive the geometry json files inside ..\static\json\regions
    region_dir = Path(app.static_folder) / "json" / "regions"
    region_geojson_files = sorted(path.name for path in region_dir.glob("*.json"))

    #========================================== PIPELINE STATUS ==========================================
    latest_sync, latest_obs_date = helpers.fetch_latest_sync_obs_date()

    return render_template(
        'markets.html',
        markets_rows=markets_rows,
        **markets_pagination,
        latest_sync=latest_sync,
        latest_obs_date=latest_obs_date,
        rec_dist_by_prov_rows=rec_dist_by_prov_rows,
        region_geojson_files=region_geojson_files
    )

@app.route('/about')
def about():

    #========================================== PIPELINE STATUS ==========================================
    latest_sync, latest_obs_date = helpers.fetch_latest_sync_obs_date()
    
    return render_template(
        'about.html',
        latest_sync=latest_sync,
        latest_obs_date=latest_obs_date
    )

if __name__ == "__main__":
    app.run(debug=True)