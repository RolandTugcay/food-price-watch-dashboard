from sqlalchemy import text, bindparam
from src.connection import db

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

    for param_name in params:
        query = query.bindparams(bindparam(param_name, expanding=True))

    with db.engine.connect() as connection:
        result = connection.execute(query, params)
        return result.scalar_one_or_none()