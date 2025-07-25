from dotenv import load_dotenv
import os
import psycopg2
import pandas as pd
import numpy as np
import math

# Load environment variables
load_dotenv()

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT')
    )
    cursor = conn.cursor()

    # Clear old risk metrics
    cursor.execute("DELETE FROM risk_metrics;")
    conn.commit()

    # Load portfolio performance data
    query = "SELECT date, portfolio_value, daily_pnl FROM portfolio_performance;"
    portfolio_df = pd.read_sql_query(query, conn)

    if portfolio_df.empty:
        raise ValueError("portfolio_performance table returned no data.")

    # Calculate daily returns
    daily_return_df = portfolio_df[['date']].copy()
    daily_return_df['daily_return'] = portfolio_df['daily_pnl'] / portfolio_df['portfolio_value']

    # Annualized volatility
    std_dev = daily_return_df['daily_return'].std()
    annual_volatility = std_dev * math.sqrt(255)
    print(f"Standard deviation of annual returns: {annual_volatility}")

    # Sharpe ratio
    annual_return = daily_return_df['daily_return'].mean() * 252
    sharpe_ratio = annual_return / annual_volatility if annual_volatility != 0 else 0
    print(f"Sharpe Ratio : {sharpe_ratio}")

    # Max drawdown
    nav = portfolio_df['portfolio_value']
    rolling_max = nav.cummax()
    drawdown = (nav - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    print(f"Max Drawdown: {max_drawdown:.2%}")

    # Insert into risk_metrics table (cast to Python float)
    cursor.execute("""
        INSERT INTO risk_metrics (annual_volatility, sharpe_ratio, max_drawdown)
        VALUES (%s, %s, %s)
    """, (
        float(annual_volatility),
        float(sharpe_ratio),
        float(max_drawdown)
    ))

    conn.commit()
    print("Risk metrics computation completed successfully.")

except Exception as e:
    print(f"Error occurred: {e}")

finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
