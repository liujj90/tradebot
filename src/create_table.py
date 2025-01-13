import sys
sys.path.append(".")
from src.utils import load_yaml, pg_engine

BASE_DDL = """
    CREATE TABLE {table_name} (
    {column_def}
    )
    {partition_def}
    """

def compose_ddl(schema, table_name): 
    """ create the ddl for given table name and schema
    """
    columns = schema['columns']
    partition_cols = [k for k, v in columns.items() if 'is_index' in v.keys()] 

    column_def = ""
    for column_name, metadata in columns.items():
        c = f"{column_name} {metadata['ttype']},\n"
        column_def += c
    column_def = column_def[:-2]

    partition_def = ""
    if len(partition_cols) > 0:

        PARTITION_BASE = "PARTITION BY RANGE ({partition_def});"
        for p in partition_cols:
            partition_def += f"{p}, "
        partition_def = partition_def[:-2]
        partition_def = PARTITION_BASE.format(partition_def=partition_def)


    ddl = BASE_DDL.format(
        table_name=table_name,
        column_def=column_def,
        partition_def=partition_def
    )
    return ddl


def create_tables(schemafpath="/home/jj/workspace/src/schema/snapshot.yaml", override=True):
    """ create table from schema
    """
    complete_schema = load_yaml(filepath=schemafpath) 

    for table_name, schema in complete_schema.items():
        ddl = compose_ddl(schema, table_name)
        print(f"Create table statement for {table_name}:")
        print(ddl)
        if override:
            drop_table_query = f"DROP TABLE if exists {table_name}"
            pg_engine.execute(drop_table_query)

        try:
            res = pg_engine.execute(ddl)
        except Exception as e:
            print(e)
            print(f"Failed to create {table_name}. Does it already exist?")

        # check
        print("checking available tables")
        print(pg_engine.list_tables())

        print(f"checking table for {table_name}")
        q = f"select * from {table_name} limit 10"
        df = pg_engine.query_data(q)
        print(df)

if __name__ == "__main__":
    create_tables(schemafpath = "/home/jj/workspace/src/schema/ticker.yaml")

        