import psycopg2
import pandas as pd
from sqlalchemy import create_engine 
from sqlalchemy import text

def get_engine(config):
    user = config['user']
    password = config['password']
    database = config['database']
    host = config['host']
    port = config['port']
    engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")
    return engine

class PgEngine:
    """ pg engine connection class
    """
    def __init__(self, config = None, engine=None):
        """ INIT
        """
        if config is None:
            from src.utils import conf
            self.config = conf
        else: 
            self.config = config 

        if engine is None:
            self.connect()
        else:
            self.engine=engine

    def connect(self):
        self.engine = get_engine(self.config)
    
    def query_data(self, query:str) -> pd.DataFrame: 
        """ perform query 
        """
        return pd.read_sql_query(query, self.engine)
    
    def write_data(self, df: pd.DataFrame, table: str, **kwargs):
        """ write data from pandas dataframe
        """
        if_exists = kwargs.get('if_exists', "replace")
        index = kwargs.get("index", False)

        return df.to_sql(table, self.engine, if_exists=if_exists, index=index, )

    def execute(self, query:str):
        """ execute query
        """
        with self.engine.connect() as connection:
            res = connection.execute(text(query))
            connection.commit()
        
        return res

    def list_tables(self):
        """ List Tables in db
        """
        q = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """

        res = self.execute(query = q)
        return res.fetchall()

    def drop_table(self, table_name):
        """ Drop table in db
        """
        q = f"DROP TABLE if exists {table_name}"
        res = self.execute(q)


        