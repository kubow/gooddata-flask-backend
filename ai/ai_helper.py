# from schedule import every, run_pending
from dotenv import dotenv_values
# from time import sleep
# from threading import Thread

# from boto3 import client
# from boto3.s3.transfer import S3Transfer
# import pptx
# import pptx.util
# import glob
# import imageio
# import fitz  # PyMuPDF, imported as fitz for backward compatibility reasons
# import boto3
import sagemaker
from sys import modules

import psycopg2


env_file = dotenv_values(".env")

def db_conn():
    return psycopg2.connect(
        host=env_file["POSTGRES_DB_HOST"],
        database=env_file["POSTGRES_DB_NAME"],
        user=env_file["POSTGRES_DB_USER"],
        password=env_file["POSTGRES_DB_PASSWORD"]
    )