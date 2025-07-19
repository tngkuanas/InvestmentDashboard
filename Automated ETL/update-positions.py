from dotenv import load_dotenv
import os
import psycopg2
import yfinance as yf
from datetime import datetime

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT')
)
cursor = conn.cursor()

user_id = input("User ID: ")

cursor.execute("""SELECT ticker, 
               SUM(quantity) 
               FROM portfolio_buys 
               GROUP BY ticker""")
quantity_by_ticker = {row[0]: row[1] for row in cursor.fetchall()}
print(quantity_by_ticker)

for ticker, quantity in quantity_by_ticker.items():
    data = yf.download(ticker, period='5d')
    if not data.empty:
        last_row = data.iloc[-1]
        close_val = last_row['Close']
        if hasattr(close_val, 'item'):
            latest_price = float(close_val.item())
        elif hasattr(close_val, 'iloc'):
            latest_price = float(close_val.iloc[0])
        else:
            latest_price = float(close_val)
        market_value = quantity * latest_price
        cursor.execute("""
            INSERT INTO portfolio_positions (user_id, ticker, market_value, quantity)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, ticker) DO UPDATE
            SET market_value = EXCLUDED.market_value,
                quantity = EXCLUDED.quantity
        """, (user_id, ticker, market_value, quantity))
    else:
        print(f"No price data available for ticker: {ticker}")

conn.commit()
cursor.close()
conn.close()

print("Portfolio positions updated successfully.") 