
import pytest
import re
from config import TABLE_INFO, VIEW_INFO

# Helper function to parse SQL schema
def parse_sql_schema(sql_content):
    """Parses a SQL schema file to extract table and column names."""
    schema = {}
    # Regex to find CREATE TABLE statements and capture table name and columns
    table_regex = re.compile(r"CREATE TABLE IF NOT EXISTS (\w+)\s*\((.*?)\);", re.DOTALL | re.IGNORECASE)
    # Regex to find column definitions (simplified)
    column_regex = re.compile(r"^\s*(\w+)", re.MULTILINE)

    for match in table_regex.finditer(sql_content):
        table_name = match.group(1)
        columns_sql = match.group(2)
        
        # Extract column names from the captured group
        columns = [col.strip() for col in column_regex.findall(columns_sql)]
        
        # Filter out constraints like PRIMARY KEY, FOREIGN KEY, etc. that might be caught
        columns = [col for col in columns if col.lower() not in ('primary', 'foreign', 'unique', 'constraint', 'check')]

        schema[table_name] = set(columns)
    return schema

def parse_sql_views(sql_content):
    """Parses a SQL file to extract view names."""
    # Regex to find CREATE OR REPLACE VIEW statements and capture view name
    view_regex = re.compile(r"CREATE OR REPLACE VIEW (\w+)", re.IGNORECASE)
    views = view_regex.findall(sql_content)
    return set(views)

# Read the schema definition file
with open("c:\\Users\\70254057\\Desktop\\basic-hub\\tenantsUnion\\build\\postgreSQL\\init-scripts-dev\\01-init-schemaDBdef.sql", "r", encoding="utf-8") as f:
    schema_sql = f.read()

# Read the views definition file
with open("c:\\Users\\70254057\\Desktop\\basic-hub\\tenantsUnion\\build\\postgreSQL\\init-scripts-dev\\03-init-createViews.sql", "r", encoding="utf-8") as f:
    views_sql = f.read()

# Parse the SQL to get the actual schema
db_schema = parse_sql_schema(schema_sql)
db_views = parse_sql_views(views_sql)

# Test cases for each table in TABLE_INFO
@pytest.mark.parametrize("table_name, config_info", TABLE_INFO.items())
def test_table_fields_alignment(table_name, config_info):
    """Tests that the fields in config.py match the DB schema for each table."""
    assert table_name in db_schema, f"Table '{table_name}' from config.py not found in the database schema."

    config_fields = set(config_info.get("fields", []) + config_info.get("hidden_fields", []))
    
    # The id_field might be a composite key, so handle that.
    id_fields = set(config_info.get("id_field", "").split(','))
    config_fields.update(id_fields)
    
    schema_columns = db_schema[table_name]

    # Normalize to lowercase for comparison
    config_fields_lower = {field.lower() for field in config_fields}
    schema_columns_lower = {col.lower() for col in schema_columns}

    assert config_fields_lower == schema_columns_lower, \
        f"Field mismatch for table '{table_name}'.\n" \
        f"Fields in config but not in schema: {config_fields_lower - schema_columns_lower}\n" \
        f"Columns in schema but not in config: {schema_columns_lower - config_fields_lower}"

# Test case for views in VIEW_INFO
def test_view_existence():
    """Tests that views in config.py exist in the database schema."""
    config_views = set(VIEW_INFO.keys())
    
    # Normalize to lowercase for comparison
    config_views_lower = {view.lower() for view in config_views}
    db_views_lower = {view.lower() for view in db_views}

    missing_views = config_views_lower - db_views_lower
    assert not missing_views, f"Views from config.py not found in the database schema: {missing_views}"

