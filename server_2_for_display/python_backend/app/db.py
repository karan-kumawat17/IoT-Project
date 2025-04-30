import os
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=os.getenv("DATABASE_URL")
)

def get_conn():
    return db_pool.getconn()

def return_conn(conn):
    db_pool.putconn(conn)
