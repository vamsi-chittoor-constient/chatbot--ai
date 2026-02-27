"""
Script to generate SQLAlchemy models from PostgreSQL SQL dump
Parses new-a24.sql and generates models for all 146 tables
"""

import re
from typing import Dict, List, Tuple
from pathlib import Path


# SQL to SQLAlchemy type mapping
SQL_TO_SQLALCHEMY_TYPE = {
    'uuid': 'UUID(as_uuid=True)',
    'character varying': 'String',
    'varchar': 'String',
    'text': 'Text',
    'integer': 'Integer',
    'bigint': 'BigInteger',
    'smallint': 'SmallInteger',
    'boolean': 'Boolean',
    'numeric': 'DECIMAL',
    'decimal': 'DECIMAL',
    'real': 'Float',
    'double precision': 'Float',
    'timestamp with time zone': 'DateTime(timezone=True)',
    'timestamptz': 'DateTime(timezone=True)',
    'timestamp without time zone': 'DateTime',
    'timestamp': 'DateTime',
    'date': 'Date',
    'time without time zone': 'Time',
    'time with time zone': 'Time',
    'time': 'Time',
    'jsonb': 'JSONB',
    'json': 'JSON',
}


def parse_column_type(column_def: str) -> Tuple[str, str, bool]:
    """
    Parse column definition to extract type, length/precision, and nullable
    Returns: (sqlalchemy_type, extra_params, nullable)
    """
    # Extract column type - improved regex to handle simple types like "uuid," or "timestamptz,"
    # First try to match type with parameters or keywords
    match = re.search(r'^([a-z_]+(?:\s+[a-z_]+)*)(?:\(([^)]+)\))?\s*', column_def, re.IGNORECASE)

    if not match:
        return 'String', '', True

    sql_type = match.group(1).lower().strip()
    params = match.group(2) if match.group(2) else ''

    # Check if nullable
    nullable = 'NOT NULL' not in column_def.upper()

    # Map SQL type to SQLAlchemy type
    sa_type = None
    extra_params = ''

    for sql_key, sa_value in SQL_TO_SQLALCHEMY_TYPE.items():
        if sql_type.startswith(sql_key):
            sa_type = sa_value
            break

    if sa_type is None:
        sa_type = 'String'

    # Handle length/precision
    if params:
        if 'String' in sa_type:
            extra_params = f'({params})'
        elif 'DECIMAL' in sa_type or 'NUMERIC' in sa_type:
            extra_params = f'(precision={params.split(",")[0].strip()}, scale={params.split(",")[1].strip() if "," in params else "2"})'

    return sa_type, extra_params, nullable


def extract_default_value(column_def: str) -> str:
    """Extract default value from column definition"""
    default_match = re.search(r'DEFAULT\s+([^,\n]+)', column_def, re.IGNORECASE)
    if default_match:
        default_val = default_match.group(1).strip()

        # Handle common defaults
        if 'uuid_generate_v4()' in default_val:
            return 'default=uuid.uuid4'
        elif 'CURRENT_TIMESTAMP' in default_val.upper() or 'now()' in default_val.lower():
            return 'server_default=func.now()'
        elif default_val.lower() == 'false':
            return 'default=False'
        elif default_val.lower() == 'true':
            return 'default=True'
        elif default_val.isdigit():
            return f'default={default_val}'
        else:
            return f'server_default=text("{default_val}")'

    return ''


def parse_table_from_sql(sql_content: str) -> Dict[str, Dict]:
    """Parse all tables from SQL dump"""
    tables = {}

    # Find all CREATE TABLE statements
    table_pattern = r'CREATE TABLE "public"\."(\w+)"\s*\((.*?)\)\s*WITH'
    matches = re.finditer(table_pattern, sql_content, re.DOTALL | re.IGNORECASE)

    for match in matches:
        table_name = match.group(1)
        table_body = match.group(2)

        # Find primary key from CONSTRAINT (handles composite keys)
        pk_columns = []
        pk_match = re.search(r'CONSTRAINT\s+"\w+"\s+PRIMARY\s+KEY\s+\(([^)]+)\)', table_body, re.IGNORECASE)
        if pk_match:
            # Extract all column names from the primary key definition
            pk_cols_str = pk_match.group(1)
            pk_cols = re.findall(r'"([^"]+)"', pk_cols_str)
            pk_columns.extend(pk_cols)

        # Parse columns
        columns = []
        for line in table_body.split('\n'):
            line = line.strip()
            if not line or line.startswith('CONSTRAINT'):
                continue

            col_match = re.match(r'"(\w+)"\s+(.+?)(?:,\s*)?$', line)
            if col_match:
                col_name = col_match.group(1)
                col_def = col_match.group(2)

                sa_type, params, nullable = parse_column_type(col_def)
                default_val = extract_default_value(col_def)
                is_primary = col_name in pk_columns or 'PRIMARY KEY' in col_def.upper()
                is_unique = 'UNIQUE' in col_def.upper()

                columns.append({
                    'name': col_name,
                    'type': sa_type + params,
                    'nullable': nullable,
                    'default': default_val,
                    'primary_key': is_primary,
                    'unique': is_unique
                })

        tables[table_name] = {
            'columns': columns
        }

    return tables


def generate_model_class(table_name: str, table_def: Dict) -> str:
    """Generate SQLAlchemy model class code"""
    class_name = ''.join(word.capitalize() for word in table_name.split('_'))

    # Reserved keywords in SQLAlchemy
    RESERVED_KEYWORDS = {'metadata', 'query', 'class'}

    # Start class definition
    code = f'''
class {class_name}(Base):
    """Auto-generated model for {table_name} table"""
    __tablename__ = "{table_name}"

'''

    # Generate columns
    for col in table_def['columns']:
        col_args = []
        col_name = col['name']
        attr_name = col_name

        # Check if column name is reserved
        if col_name.lower() in RESERVED_KEYWORDS:
            attr_name = f'{col_name}_'
            col_args.append(f'name="{col_name}"')  # Map to actual column name

        # Type
        col_type = col['type']

        # Primary key
        if col['primary_key']:
            col_args.append('primary_key=True')

        # Nullable
        if not col['nullable'] and not col['primary_key']:
            col_args.append('nullable=False')

        # Unique
        if col['unique']:
            col_args.append('unique=True')

        # Default
        if col['default']:
            col_args.append(col['default'])

        # Index for ID columns and foreign keys
        if col_name.endswith('_id') or col_name == 'id':
            col_args.append('index=True')

        args_str = ', '.join(col_args)
        code += f'    {attr_name} = Column({col_type}, {args_str})\n'

    return code


def group_tables_by_category(tables: Dict[str, Dict]) -> Dict[str, List[str]]:
    """Group tables into logical categories"""
    categories = {
        'chain': [],
        'branch': [],
        'customer': [],
        'menu': [],
        'order': [],
        'payment': [],
        'feedback': [],
        'user': [],
        'integration': [],
        'location': [],
        'other': []
    }

    for table_name in sorted(tables.keys()):
        if table_name.startswith('chain_'):
            categories['chain'].append(table_name)
        elif table_name.startswith('branch_'):
            categories['branch'].append(table_name)
        elif table_name.startswith('customer_'):
            categories['customer'].append(table_name)
        elif table_name.startswith('menu_') or table_name in ['combo_item', 'combo_item_components']:
            categories['menu'].append(table_name)
        elif table_name.startswith('order_'):
            categories['order'].append(table_name)
        elif table_name.startswith('payment_'):
            categories['payment'].append(table_name)
        elif table_name.startswith('feedback_'):
            categories['feedback'].append(table_name)
        elif table_name.startswith('user_'):
            categories['user'].append(table_name)
        elif table_name.startswith('integration_'):
            categories['integration'].append(table_name)
        elif table_name.endswith('_table'):
            if any(x in table_name for x in ['city', 'state', 'country', 'pincode']):
                categories['location'].append(table_name)
            else:
                categories['other'].append(table_name)
        else:
            categories['other'].append(table_name)

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def main():
    # Read SQL dump
    sql_file = Path('new-a24.sql')
    if not sql_file.exists():
        print(f"Error: {sql_file} not found!")
        return

    print(f"Reading {sql_file}...")
    sql_content = sql_file.read_text(encoding='utf-8')

    print("Parsing tables...")
    tables = parse_table_from_sql(sql_content)
    print(f"Found {len(tables)} tables")

    print("\nGrouping tables by category...")
    categories = group_tables_by_category(tables)

    for category, table_list in categories.items():
        print(f"{category}: {len(table_list)} tables")

    # Generate models for each category
    output_dir = Path('app/models')
    output_dir.mkdir(exist_ok=True, parents=True)

    print("\nGenerating model files...")

    for category, table_list in categories.items():
        file_path = output_dir / f'{category}_models.py'

        # Header
        content = f'''"""
{category.capitalize()} Models - Auto-generated from SQL dump
Generated by scripts/generate_models.py
"""

from sqlalchemy import Column, String, Text, Integer, BigInteger, SmallInteger
from sqlalchemy import Boolean, DECIMAL, Float, DateTime, Date, Time
from sqlalchemy import ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, JSON
from sqlalchemy.sql import func
from app.core.db_session import Base
import uuid

'''

        # Generate model classes
        for table_name in table_list:
            content += generate_model_class(table_name, tables[table_name])

        # Write file
        file_path.write_text(content, encoding='utf-8')
        print(f"Generated: {file_path}")

    # Generate __init__.py
    init_file = output_dir / '__init__.py'
    init_content = '''"""
Generated models package
Auto-generated from SQL dump
"""

# Import all model classes for easy access
'''

    for category in categories.keys():
        init_content += f'from .{category}_models import *\n'

    init_file.write_text(init_content, encoding='utf-8')
    print(f"\nGenerated: {init_file}")

    print(f"\nSuccessfully generated models for {len(tables)} tables!")
    print(f"Output directory: {output_dir}")


if __name__ == '__main__':
    main()
