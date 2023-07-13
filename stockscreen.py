import threading
import time
from pystray import MenuItem, Menu, Icon
import yfinance as yf
import numpy as np

# List of stock symbols to monitor
stock_symbols = ['AAPL', 'MSFT', 'GOOGL']

# Define the technical signals for each time frame
signals = {
    'Day Trading': ['Momentum', 'Pullback', 'Breakout', 'Macd', 'Bollinger Bands'],
    'Short Term': ['Rsi', 'Stochastic Oscillator'],
    'Long Term': ['Sma', 'Ema']
}

# Function to check technical signals for a given stock
def check_technical_signals(symbol):
    # Retrieve historical stock data
    data = yf.download(symbol, period='1y', interval='1d')

    # Extract price and volume data
    close_prices = data['Close'].to_numpy()
    volumes = data['Volume'].to_numpy()

    # Calculate technical indicators
    rsi = calculate_rsi(close_prices)
    stochastic = calculate_stochastic_oscillator(data['High'].to_numpy(), data['Low'].to_numpy(), close_prices)
    sma = calculate_sma(close_prices)
    ema = calculate_ema(close_prices)
    upper_band, middle_band, lower_band = calculate_bollinger_bands(close_prices)

    # Check for technical signals
    result = {}
    for timeframe, indicators in signals.items():
        result[timeframe] = []
        for indicator in indicators:
            if indicator == 'Momentum':
                if close_prices[-1] > close_prices[-2]:
                    result[timeframe].append(indicator)
            elif indicator == 'Pullback':
                if close_prices[-1] < close_prices[-2]:
                    result[timeframe].append(indicator)
            elif indicator == 'Breakout':
                if close_prices[-1] > upper_band[-1]:
                    result[timeframe].append(indicator)
            elif indicator == 'Macd':
                # Add your MACD calculation logic here using numpy
                pass
            elif indicator == 'Bollinger Bands':
                if close_prices[-1] < lower_band[-1]:
                    result[timeframe].append(indicator)
            elif indicator == 'Rsi':
                if rsi[-1] < 30:
                    result[timeframe].append(indicator)
            elif indicator == 'Stochastic Oscillator':
                if stochastic[-1] < 20:
                    result[timeframe].append(indicator)
            elif indicator == 'Sma':
                if close_prices[-1] > sma[-1]:
                    result[timeframe].append(indicator)
            elif indicator == 'Ema':
                if close_prices[-1] > ema[-1]:
                    result[timeframe].append(indicator)

    return result

# Function to calculate RSI (Relative Strength Index)
def calculate_rsi(prices, window=14):
    deltas = np.diff(prices)
    seed = deltas[:window + 1]
    up = seed[seed >= 0].sum() / window
    down = -seed[seed < 0].sum() / window
    rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:window] = 100. - 100. / (1. + rs)

    for i in range(window, len(prices)):
        delta = deltas[i - 1]  # Use previous delta
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        up = (up * (window - 1) + upval) / window
        down = (down * (window - 1) + downval) / window
        rs = up / down
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi

# Function to calculate Stochastic Oscillator
def calculate_stochastic_oscillator(high, low, close, window=14):
    highest_high = np.max(high[-window:])
    lowest_low = np.min(low[-window:])
    stochastic = (close[-1] - lowest_low) / (highest_high - lowest_low) * 100
    return stochastic

# Function to calculate Simple Moving Average (SMA)
def calculate_sma(prices, window=20):
    sma = np.convolve(prices, np.ones(window) / window, mode='valid')
    return sma

# Function to calculate Exponential Moving Average (EMA)
def calculate_ema(prices, window=20):
    weights = np.exp(np.linspace(-1., 0., window))
    weights /= weights.sum()
    ema = np.convolve(prices, weights, mode='valid')
    return ema

# Function to calculate Bollinger Bands
def calculate_bollinger_bands(prices, window=20, num_std=2):
    sma = calculate_sma(prices, window)
    std = np.std(prices[-window:])
    upper_band = sma + num_std * std
    lower_band = sma - num_std * std
    middle_band = sma
    return upper_band, middle_band, lower_band

# Function to display the ticker information
def display_ticker(icon, item):
    ticker_data = {}
    for symbol in stock_symbols:
        ticker_data[symbol] = check_technical_signals(symbol)

    # Format and display the ticker information
    ticker_text = ''
    for symbol, signals in ticker_data.items():
        ticker_text += f"\n{symbol}\n"
        for timeframe, indicators in signals.items():
            if indicators:
                ticker_text += f"  {timeframe}: {', '.join(indicators)}\n"
        ticker_text += '\n'

    # Display the ticker in a messagebox or any other suitable method
    print(ticker_text)


# Function to check technical signals periodically
def check_signals_periodically(icon, item):
    while True:
        for symbol in stock_symbols:
            signals = check_technical_signals(symbol)
            if any(signals.values()):
                # Display an alert when conditions are met
                print(f"Alert: {symbol} - {signals}")
        time.sleep(60)  # Check every minute


# Create the tray icon and menu
def create_tray_app():
    menu = (MenuItem('Ticker', display_ticker), MenuItem('Quit', lambda icon, item: icon.stop()))
    icon = Icon('icon.ico', 'Stock Monitor', menu=Menu(*menu))

    # Start the thread to check signals periodically
    thread = threading.Thread(target=check_signals_periodically, args=(icon, None), daemon=True)
    thread.start()

    # Run the tray app
    icon.run()


if __name__ == '__main__':
    create_tray_app()
