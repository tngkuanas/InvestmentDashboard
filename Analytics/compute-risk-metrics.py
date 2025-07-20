from dotenv import load_dotenv
import os
import psycopg2
import pandas as pd
import numpy as np
import math

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT')
)
cursor = conn.cursor()

cursor.execute("DELETE FROM risk_metrics;")
conn.commit()

portfolio_df = pd.read_sql_query("SELECT date, portfolio_value, daily_pnl FROM portfolio_performance;", conn)

daily_return_df = portfolio_df[['date']].copy()
daily_return_df['daily_return'] = portfolio_df['daily_pnl'] / portfolio_df['portfolio_value']
std_dev = daily_return_df['daily_return'].std()
annual_std_dev = std_dev * math.sqrt(255) 
annual_volatility = annual_std_dev 
print(f"Standard deviation of annual returns: {annual_volatility}")

annual_return = daily_return_df['daily_return'].mean() * 252
sharpe_ratio = annual_return/annual_std_dev
print(f"Sharpe Ratio : {sharpe_ratio}")

nav = portfolio_df['portfolio_value']
rolling_max = nav.cummax()
drawdown = (nav - rolling_max) / rolling_max
max_drawdown = drawdown.min() 
print(f"Max Drawdown: {max_drawdown:.2f}%")

cursor.execute("""
    INSERT INTO risk_metrics (annual_volatility, sharpe_ratio, max_drawdown)
    VALUES (%s, %s, %s)
""", (
    annual_volatility,
    sharpe_ratio,
    max_drawdown
))

conn.commit()
cursor.close()
conn.close()

print("Risk metrics computation placeholder.") 