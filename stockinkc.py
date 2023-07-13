import yfinance as yf
import talib
import pandas as pd

# Define the list of stocks and the list of indicators
stocks = ['AAPL', 'GOOGL', 'TSLA','ABC','BRO','COST']
indicators = ['SMA', 'RSI']

# Define the period for the stock data
period = '1d'

# Define the lookback period for the SMA and RSI
lookback_period = 14

def calculate_indicators(data):
    # Calculate the SMA and the RSI
    data['SMA'] = talib.SMA(data['Close'], timeperiod=lookback_period)
    data['RSI'] = talib.RSI(data['Close'], timeperiod=lookback_period)
    return data

def check_signals(data, stock):
    for i in range(1, len(data)):
        # Check the SMA
        if data['Close'][i] > data['SMA'][i] and data['Close'][i-1] < data['SMA'][i-1]:
            print(f"Buy signal for {stock} on {data.index[i]} based on SMA")
        elif data['Close'][i] < data['SMA'][i] and data['Close'][i-1] > data['SMA'][i-1]:
            print(f"Sell signal for {stock} on {data.index[i]} based on SMA")

        # Check the RSI
        if data['RSI'][i] < 30 and data['RSI'][i-1] >= 30:
            print(f"Buy signal for {stock} on {data.index[i]} based on RSI")
        elif data['RSI'][i] > 70 and data['RSI'][i-1] <= 70:
            print(f"Sell signal for {stock} on {data.index[i]} based on RSI")

# Loop through each stock
for stock in stocks:
    # Fetch the stock data
    data = yf.download(stock, period=period)

    # Calculate the indicators
    data = calculate_indicators(data)

    # Check for signals
    check_signals(data, stock)
