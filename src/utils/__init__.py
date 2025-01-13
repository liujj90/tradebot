from .utils import *
from .db import postgres_utils

conf = load_yaml()

def postgres_engine():
    """ returns postgres connection engine
    """
    pg_engine = postgres_utils.PgEngine(config = conf['postgres'])

    return pg_engine

pg_engine = postgres_engine()

__all__ = [
    'conf',
    'load_yaml',
    'postgres_engine',
    'pg_engine'
]
