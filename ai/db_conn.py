from sys import modules
from dotenv import dotenv_values
import psycopg2

env_file = dotenv_values(".env")

def db_conn():
    conn = psycopg2.connect(
        host=env_file["POSTGRES_DB_HOST"],
        database=env_file["POSTGRES_DB_NAME"],
        user=env_file["POSTGRES_DB_USER"],
        password=env_file["POSTGRES_DB_PASSWORD"]
    )

    return conn

modules[__name__] = db_conn