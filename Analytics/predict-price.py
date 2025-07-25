import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import layers
from copy import deepcopy
from dotenv import load_dotenv
import os
import psycopg2

# Load credentials from .env
load_dotenv()

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT')
)
cursor = conn.cursor()

# === Wipe existing data from table ===
cursor.execute("TRUNCATE TABLE price_predictions")

# === 1. Download Apple stock data ===
data = yf.download('AAPL', start='2010-01-01', end=datetime.datetime.today().strftime('%Y-%m-%d'))
df = data[['Close']].copy()
df.reset_index(inplace=True)

# === 2. Convert dates ===
df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
def str_to_datetime(s):
    year, month, day = map(int, s.split('-'))
    return datetime.datetime(year=year, month=month, day=day)

df['Date'] = df['Date'].apply(str_to_datetime)
df.index = df.pop('Date')

# === 3. Visualize closing prices ===
plt.plot(df.index, df['Close'])
plt.title("AAPL Closing Price History")
plt.show()

# === 4. Windowing for LSTM input ===
def df_to_windowed_df(dataframe, first_date_str, last_date_str, n=3):
    first_date = str_to_datetime(first_date_str)
    last_date = str_to_datetime(last_date_str)

    target_date = first_date
    dates = []
    X, Y = [], []

    last_time = False
    while True:
        df_subset = dataframe.loc[:target_date].tail(n+1)
        if len(df_subset) != n+1:
            break

        values = df_subset['Close'].to_numpy()
        x, y = values[:-1], values[-1]
        dates.append(target_date)
        X.append(x)
        Y.append(y)

        next_week = dataframe.loc[target_date:target_date+datetime.timedelta(days=7)]
        if len(next_week.head(2)) < 2:
            break
        next_datetime_str = str(next_week.head(2).tail(1).index.values[0])
        next_date_str = next_datetime_str.split('T')[0]
        year, month, day = map(int, next_date_str.split('-'))
        next_date = datetime.datetime(year, month, day)

        if last_time:
            break
        target_date = next_date
        if target_date == last_date:
            last_time = True

    ret_df = pd.DataFrame({'Target Date': dates})
    X = np.array(X)
    for i in range(0, n):
        ret_df[f'Target-{n-i}'] = X[:, i]
    ret_df['Target'] = Y
    return ret_df

# Use latest 2 years for training windowing
windowed_df = df_to_windowed_df(df, '2021-01-01', df.index[-1].strftime('%Y-%m-%d'), n=3)

# === 5. Convert to model inputs ===
def windowed_df_to_date_X_y(windowed_dataframe):
    df_as_np = windowed_dataframe.to_numpy()
    dates = df_as_np[:, 0]
    X = df_as_np[:, 1:-1].reshape((len(dates), df_as_np.shape[1]-2, 1))
    Y = df_as_np[:, -1]
    return dates, X.astype(np.float32), Y.astype(np.float32)

dates, X, y = windowed_df_to_date_X_y(windowed_df)

# === 6. Train/val/test split ===
q_80 = int(len(dates) * .8)
q_90 = int(len(dates) * .9)

dates_train, X_train, y_train = dates[:q_80], X[:q_80], y[:q_80]
dates_val, X_val, y_val = dates[q_80:q_90], X[q_80:q_90], y[q_80:q_90]
dates_test, X_test, y_test = dates[q_90:], X[q_90:], y[q_90:]

# === 7. LSTM model ===
model = Sequential([
    layers.Input((3, 1)),
    layers.LSTM(64),
    layers.Dense(32, activation='relu'),
    layers.Dense(32, activation='relu'),
    layers.Dense(1)
])
model.compile(loss='mse', optimizer=Adam(learning_rate=0.001), metrics=['mae'])

model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=100)

# === 8. Plot predictions (optional) ===
def plot_predictions(dates_, actual, predicted, label):
    plt.plot(dates_, predicted)
    plt.plot(dates_, actual)
    plt.legend([f'{label} Predictions', f'{label} Observations'])
    plt.title(f"{label} Performance")
    plt.show()

train_predictions = model.predict(X_train).flatten()
val_predictions = model.predict(X_val).flatten()
test_predictions = model.predict(X_test).flatten()

plot_predictions(dates_train, y_train, train_predictions, "Training")
plot_predictions(dates_val, y_val, val_predictions, "Validation")
plot_predictions(dates_test, y_test, test_predictions, "Testing")

# === 9. Future Forecasting ===
def predict_next_n_days(model, last_window, n_days=30):
    predictions = []
    window = deepcopy(last_window)
    for _ in range(n_days):
        pred = model.predict(np.array([window]), verbose=0).flatten()[0]
        predictions.append(pred)
        window = np.roll(window, -1)
        window[-1] = pred
    return predictions

# Use the latest known data window to predict forward
latest_window = X[-1]
future_preds = predict_next_n_days(model, latest_window, n_days=30)

# === 10. Extract exact predictions ===
next_day_pred = future_preds[0]
next_week_pred = future_preds[6]
next_month_pred = future_preds[29]

# === 11. Print/store the results ===
print(f"📈 Next Day Prediction: ${next_day_pred:.2f}")
print(f"📈 Next Week Prediction: ${next_week_pred:.2f}")
print(f"📈 Next Month Prediction: ${next_month_pred:.2f}")


# === Insert new prediction row ===
insert_query = """
INSERT INTO price_predictions (next_day_pred, next_week_pred, next_month_pred)
VALUES (%s, %s, %s)
"""
cursor.execute(
    insert_query,
    (float(next_day_pred), float(next_week_pred), float(next_month_pred))
)

# Commit and close
conn.commit()
cursor.close()
conn.close()

print("✅ Predictions inserted into `price_predictions` table.")