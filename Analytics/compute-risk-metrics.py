from dotenv import load_dotenv
import os
import psycopg2
import pandas as pd
import numpy as np

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT')
)
cursor = conn.cursor()



cursor.close()
conn.close()

print("Risk metrics computation placeholder.") 