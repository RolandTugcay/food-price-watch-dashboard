from sqlalchemy import text, bindparam
from src.connection import db
from collections import defaultdict

def raw_string_to_array(raw_string, data_type="str"):
    # Handle empty or None input gracefully
    try:
        if not raw_string:
            return []
        
        # Split by comma and filter out empty strings
        parts = [v.strip() for v in raw_string.split(",") if v.strip()]
        
        if data_type == "int":
            return [int(v) for v in parts]
        elif data_type == "str":
            return parts
        else:
            raise ValueError(f"Unsupported data_type: '{data_type}'. Use 'int' or 'str'.")
    except ValueError:
        parts = []

def records_to_array_from_ids(data_ids, qry_text, ids_var_name, fetch_col_name):
    if not data_ids:
        return []
        
    with db.engine.connect() as connection:
        # qry_text is already a TextClause, so apply bindparams directly
        stmt = qry_text.bindparams(bindparam(ids_var_name, expanding=True))
        result = connection.execute(stmt, {ids_var_name: data_ids})
        
        return [row[fetch_col_name] for row in result.mappings()]

def fetch_records_static_qry(qry_string):
    with db.engine.connect() as connection:
        result = connection.execute(text(qry_string))
        columns = list(result.keys())
        rows = [dict(row) for row in result.mappings()]

        return columns, rows

def fetch_records_dynamic_qry(base_qry, clause_qry, sort_qry, data_ids, var_ids):
    with db.engine.connect() as connection:
        if data_ids:
            # Use an f-string with spaces to prevent words from sticking together
            full_query = f"{base_qry} {clause_qry} {sort_qry}"
            query = text(full_query).bindparams(bindparam(var_ids, expanding=True))
            result = connection.execute(query, {var_ids: data_ids})
        else:
            # If no data_ids, omit the clause query (e.g. the WHERE clause)
            full_query = f"{base_qry} {sort_qry}"
            result = connection.execute(text(full_query))
            
        columns = list(result.keys())
        rows = [dict(row) for row in result.mappings()]
        
        return columns, rows

def fetch_single_static_qry(str_qry):
    with db.engine.connect() as connection:
        # Returns the value if found, or None if the result set is empty
        return connection.execute(text(str_qry)).scalar_one_or_none()

def fetch_single_dynamic_qry(base_qry, filters, addtl_cond_qry=None):
    conditions = []
    params = {}

    for param_name, (condition, values) in filters.items():
        if values:
            conditions.append(condition)
            params[param_name] = values

    if addtl_cond_qry and addtl_cond_qry.strip():
        conditions.append(addtl_cond_qry.strip())

    query_text = base_qry
    if conditions:
        query_text += " WHERE " + " AND ".join(conditions)

    query = text(query_text)

    for param_name, value in params.items():
        is_list = isinstance(value, (list, tuple, set))
        query = query.bindparams(
            bindparam(param_name, expanding=is_list)
        )

    with db.engine.connect() as connection:
        result = connection.execute(query, params)
        return result.scalar_one_or_none()

def fetch_chart_data_dynamic_qry(
    base_qry,
    filters,
    addtl_cond_qry=None,
    addtl_qry=None,
    addtl_params=None,
):
    conditions = []
    params = dict(addtl_params or {})

    for param_name, (condition, values) in filters.items():
        if values:
            conditions.append(condition)
            params[param_name] = values

    if addtl_cond_qry and addtl_cond_qry.strip():
        conditions.append(addtl_cond_qry.strip())

    query_text = base_qry
    if conditions:
        query_text += " WHERE " + " AND ".join(conditions)

    query = text(f"{query_text} {addtl_qry}" if addtl_qry else query_text)

    for param_name, value in params.items():
        is_list = isinstance(value, (list, tuple, set))
        query = query.bindparams(
            bindparam(param_name, expanding=is_list)
        )

    with db.engine.connect() as connection:
        result = connection.execute(query, params)
        columns = list(result.keys())
        rows = [dict(row) for row in result.mappings()]
        
        return columns, rows


def to_chart_data(
    rows,
    *,
    x_column,
    series_column,
    value_column=None,
    dataset_options=None,
    value_columns=None,
    value_labels=None,
):
    """Pivot query rows into Chart.js labels and datasets.

    Use value_column for a single metric or value_columns for multiple metrics.
    """

    dataset_options = dataset_options or {}
    value_labels = value_labels or {}
    if value_columns is None:
        if value_column is None:
            raise ValueError("Provide either value_column or value_columns.")
        value_columns = [value_column]
    elif value_column is not None:
        raise ValueError("Provide value_column or value_columns, not both.")

    def normalize_x(value):
        # Chart.js labels need JSON-serializable values.
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    def make_dataset(label, data):
        options = dict(dataset_options)
        if len(value_columns) > 1:
            options.pop("label", None)
        return {
            "label": label,
            "data": data,
            "spanGaps": False,
            **options,
        }

    x_values = sorted({
        normalize_x(row[x_column])
        for row in rows
        if row.get(x_column) is not None
    })

    if series_column is None:
        datasets = []
        for column in value_columns:
            values_by_x = {
                normalize_x(row[x_column]): row.get(column)
                for row in rows
                if row.get(x_column) is not None
            }
            if values_by_x:
                label = (
                    value_labels.get(column, column)
                    if len(value_columns) > 1
                    else value_column
                )
                datasets.append(make_dataset(
                    label,
                    [values_by_x.get(x_value) for x_value in x_values],
                ))

        return {
            "labels": x_values,
            "datasets": datasets,
        }

    datasets = []
    for column in value_columns:
        series_values = defaultdict(dict)
        for row in rows:
            x_value = row.get(x_column)
            series_value = row.get(series_column)
            value = row.get(column)

            if x_value is None or series_value is None:
                continue

            series_values[series_value][normalize_x(x_value)] = value

        for series_value in sorted(series_values, key=str):
            label = str(series_value)
            if len(value_columns) > 1:
                label = f"{value_labels.get(column, column)}: {label}"
            datasets.append(make_dataset(
                label,
                [
                    series_values[series_value].get(x_value)
                    for x_value in x_values
                ],
            ))

    return {
        "labels": x_values,
        "datasets": datasets,
    }