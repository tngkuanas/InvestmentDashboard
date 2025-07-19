from dotenv import load_dotenv
import os
import psycopg2
import pandas as pd

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT')
)
cursor = conn.cursor()

cursor.execute("DELETE FROM portfolio_performance;")
conn.commit()

buys_df = pd.read_sql_query("SELECT ticker, quantity, buy_date, buy_value FROM portfolio_buys;", conn)
prices_df = pd.read_sql_query("SELECT date, ticker, close FROM daily_prices;", conn)

buys_df['buy_date'] = pd.to_datetime(buys_df['buy_date'])
prices_df['date'] = pd.to_datetime(prices_df['date'])

all_dates = prices_df['date'].sort_values().unique()
all_tickers = prices_df['ticker'].unique()

portfolio_values = []

debug_dates = set(all_dates[-5:])  

for date in all_dates:
    total_value = 0
    if date in debug_dates:
        print(f'\nDate: {date}')
    for ticker in all_tickers:
        qty = buys_df[(buys_df['ticker'] == ticker) & (buys_df['buy_date'] <= date)]['quantity'].sum()
        price_row = prices_df[(prices_df['ticker'] == ticker) & (prices_df['date'] == date)]
        if not price_row.empty:
            close_price = price_row.iloc[0]['close']
            value = qty * close_price
            total_value += value
            if date in debug_dates:
                print(f"  {ticker}: qty={qty}, close={close_price}, value={value}")
        else:
            if date in debug_dates:
                print(f"  {ticker}: qty={qty}, close=N/A, value=0 (no price)")
    total_buy_value_up_to_date = buys_df[buys_df['buy_date'] <= date]['buy_value'].sum()
    portfolio_values.append({'date': date, 'portfolio_value': total_value, 'total_buy_value': total_buy_value_up_to_date})

portfolio_df = pd.DataFrame(portfolio_values)
print(portfolio_df)
print(portfolio_df.columns)
buy_value_df = pd.read_sql_query("SELECT SUM(buy_value) as total_buy_value FROM portfolio_buys;", conn)
total_buy_value = buy_value_df['total_buy_value'].iloc[0]

portfolio_df['daily_pnl'] = portfolio_df['portfolio_value'].diff()
portfolio_df['cumulative_return'] = ((portfolio_df['portfolio_value'] - portfolio_df['total_buy_value']) / portfolio_df['total_buy_value']) * 100

for _, row in portfolio_df.iterrows():
    cursor.execute("""
        INSERT INTO portfolio_performance (date, portfolio_value, daily_pnl, cumulative_return)
        VALUES (%s, %s, %s, %s)
    """, (
        row['date'],
        round(row['portfolio_value'], 2),
        round(row['daily_pnl'], 2) if pd.notnull(row['daily_pnl']) else 0,
        round(row['cumulative_return'], 4)
    ))

print("\n--- Per-Ticker Returns (latest date) ---")
last_date = all_dates[-1]
for ticker in all_tickers:
    qty = buys_df[(buys_df['ticker'] == ticker) & (buys_df['buy_date'] <= last_date)]['quantity'].sum()
    total_buy_value = buys_df[(buys_df['ticker'] == ticker) & (buys_df['buy_date'] <= last_date)]['buy_value'].sum()
    avg_buy_price = total_buy_value / qty if qty > 0 else 0
    price_row = prices_df[(prices_df['ticker'] == ticker) & (prices_df['date'] == last_date)]
    if not price_row.empty:
        latest_price = price_row.iloc[0]['close']
        current_value = qty * latest_price
        return_pct = ((current_value - total_buy_value) / total_buy_value * 100) if total_buy_value > 0 else None
        print(f"{ticker}: qty={qty:.4f}, total_buy_value={total_buy_value:.2f}, avg_buy_price={avg_buy_price:.2f}, latest_price={latest_price:.2f}, current_value={current_value:.2f}, return={return_pct:.2f}%")
    else:
        print(f"{ticker}: No price for latest date.")

conn.commit()
cursor.close()
conn.close()

print("Portfolio performance wiped and recomputed successfully (as-of-date logic).") 