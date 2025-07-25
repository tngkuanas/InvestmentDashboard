from dotenv import load_dotenv
import os
import yfinance as yf
import pandas as pd
import psycopg2
import numpy as np
from datetime import datetime, timedelta

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT')
)
cursor = conn.cursor()

cursor.execute("DELETE FROM daily_prices;")
conn.commit()

cursor.execute("SELECT DISTINCT ticker FROM portfolio_positions;")
tickers = [row[0] for row in cursor.fetchall()]

for ticker in tickers:
    end_date = datetime.today()
    start_date = (end_date - timedelta(days=730)).strftime('%Y-%m-%d') 
    end_date = end_date.strftime('%Y-%m-%d')
    print(f"Fetching {ticker} from {start_date} to {end_date}")
    df = yf.download(ticker, start=start_date, end=end_date)
    df = df.reset_index()  
    print('COLUMNS:', df.columns)
    if not df.empty:
        print(f"{ticker} - Downloaded date range: {df['Date'].min()} to {df['Date'].max()}")
    else:
        print(f"{ticker} - No data downloaded.")
    for index, row in df.iterrows():
        date_value = pd.to_datetime(row[('Date', '')])
        if hasattr(date_value, 'date'):
            date_value = date_value.date()
        open_value = row[('Open', ticker)]
        high_value = row[('High', ticker)]
        low_value = row[('Low', ticker)]
        close_value = row[('Close', ticker)]
        volume_value = row[('Volume', ticker)]
        try:
            cursor.execute("""
                INSERT INTO daily_prices (ticker, date, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, date) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume
            """, (
                ticker,
                date_value,
                round(open_value, 2),
                round(high_value, 2),
                round(low_value, 2),
                round(close_value, 2),
                int(volume_value)
            ))
        except Exception as e:
            print(f"Error inserting {ticker} {date_value}: {e}")

conn.commit()
cursor.close()
conn.close()

print("Data inserted successfully.")
