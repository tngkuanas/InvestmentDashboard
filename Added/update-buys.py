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
ticker = input("Ticker: ")
buy_value = float(input("Buy value (USD): "))

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
    quantity = buy_value / latest_price
    buy_date = datetime.today().strftime('%Y-%m-%d')
    print(f"User ID: {user_id}, Ticker: {ticker}, Buy value: {buy_value}, Latest price: {latest_price}, Quantity: {quantity}, Buy date: {buy_date}")
    cursor.execute(""" INSERT INTO portfolio_buys (user_id, ticker, quantity, buy_value, buy_date)
                    VALUES (%s, %s, %s, %s, %s)""", (user_id, ticker, quantity, buy_value, buy_date))
else:
    print(f"No price data available for ticker: {ticker}")

conn.commit()
cursor.close()
conn.close()

print("Position added successfully.") 