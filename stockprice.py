import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf  # Yahoo Finance API to fetch stock data
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM

# Fetch stock price data
stock_symbol = 'AAPL'  # Choose any stock symbol
start_date = '2015-01-01'
end_date = '2024-06-01'

data = yf.download(stock_symbol, start=start_date, end=end_date)
print(data.head())

# Plot the stock price
plt.figure(figsize=(14, 5))
plt.plot(data['Close'], label='Closing Price')
plt.title(f"{stock_symbol} Stock Price")
plt.xlabel("Time")
plt.ylabel("Price (USD)")
plt.legend()
plt.show()

# Extract 'Close' price column
close_prices = data['Close'].values.reshape(-1, 1)

# Normalize the data
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_prices = scaler.fit_transform(close_prices)

# Split data into training and testing sets
train_size = int(len(scaled_prices) * 0.8)
train_data = scaled_prices[:train_size]
test_data = scaled_prices[train_size:]

# Function to create input sequences
def create_sequences(data, time_step=60):
  X, y = [], []
  for i in range(len(data) - time_step):
      X.append(data[i:i+time_step])
      y.append(data[i+time_step])
  return np.array(X), np.array(y)

# Define time step (number of past days to consider)
time_step = 60

# Create sequences
X_train, y_train = create_sequences(train_data, time_step)
X_test, y_test = create_sequences(test_data, time_step)

# Reshape input for LSTM: [samples, time steps, features]
X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))

print("Training data shape:", X_train.shape)
print("Testing data shape:", X_test.shape)

# LSTM Model
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(time_step, 1)))
model.add(LSTM(50, return_sequences=False))
model.add(Dense(25))
model.add(Dense(1))

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model
history = model.fit(X_train, y_train, batch_size=32, epochs=20, verbose=1)

# Predictions
train_predictions = model.predict(X_train)
test_predictions = model.predict(X_test)

# Inverse transform predictions back to original scale
train_predictions = scaler.inverse_transform(train_predictions)
y_train = scaler.inverse_transform(y_train.reshape(-1, 1))

test_predictions = scaler.inverse_transform(test_predictions)
y_test = scaler.inverse_transform(y_test.reshape(-1, 1))

# Plot predictions vs actual
plt.figure(figsize=(14, 6))
plt.plot(data.index[:len(y_train)], y_train, label='Actual Training Prices')
plt.plot(data.index[:len(train_predictions)], train_predictions, label='Training Predictions')

plt.plot(data.index[-len(y_test):], y_test, label='Actual Test Prices')
plt.plot(data.index[-len(test_predictions):], test_predictions, label='Test Predictions')

plt.title("LSTM Stock Price Prediction")
plt.xlabel("Time")
plt.ylabel("Price (USD)")
plt.legend()
plt.show()

# Predict future prices
future_steps = 30  # Number of future days to predict
last_sequence = scaled_prices[-time_step:]  # Start from the last available data

future_predictions = []
for _ in range(future_steps):
  # Reshape and predict next step
  last_sequence = last_sequence.reshape((1, time_step, 1))
  next_prediction = model.predict(last_sequence)
  future_predictions.append(next_prediction[0, 0])

  # Update sequence with the new prediction
  next_prediction = np.array(next_prediction).reshape(1, 1, 1)
last_sequence = np.append(last_sequence[:, 1:, :], next_prediction, axis=1)
# Or
# last_sequence = np.concatenate((last_sequence[:, 1:, :], next_prediction), axis=1)

# Inverse transform predictions to original scale
future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))

# Plot the predictions
plt.figure(figsize=(12, 5))
plt.plot(data.index, data['Close'], label="Historical Prices")
future_dates = pd.date_range(data.index[-1], periods=future_steps + 1, freq='B')[1:]
plt.plot(future_dates, future_predictions, label="Future Predictions", linestyle="dashed")

plt.title("Future Stock Price Prediction")
plt.xlabel("Time")
plt.ylabel("Price (USD)")
plt.legend()
plt.show()

model.save('stock_price_lstm_model.h5')

def save_data(historical_prices, future_dates, predicted_prices):
    historical_prices["Type"] = "Historical"
    predictions_df = pd.DataFrame({
        "Date": future_dates,
        "Close": predicted_prices.flatten(),
        "Type": "Predicted"
    })

    # Combine historical and predicted data
    combined_data = pd.concat([historical_prices, predictions_df])
    combined_data.to_csv("stock_prediction_data.csv", index=False)
