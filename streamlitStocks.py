import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import yfinance as yf
import talib
st.set_page_config(layout="wide")
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]

# Function to download and process data for a single stock
def process_stock(ticker):
    # Download historical data
    data = yf.download(ticker, start="2018-01-01", end="2023-12-31")
  
    # Calculate daily returns
    data['Return'] = data['Close'].pct_change()

    # Identify sharp downturns
    data['Downturn'] = data['Return'] < -0.05

    # Check for consistent recovery
    data['Recovery'] = (data['Return'].shift(-1) > 0) & (data['Return'].shift(-2) > 0) & (data['Return'].shift(-3) > 0)

    # Find cases where a sharp downturn was followed by a consistent recovery
    data['Downturn_Recovery'] = data['Downturn'] & data['Recovery']

    # Calculate moving average upward trend
    data['SMA'] = talib.SMA(data['Close'], timeperiod=20)
    data['Upward_Trend'] = data['Close'] > data['SMA']

    # Calculate RSI
    data['RSI'] = talib.RSI(data['Close'])

    # Calculate ADX
    data['ADX'] = talib.ADX(data['High'], data['Low'], data['Close'])

    # Calculate Bollinger Bands
    data['upper_band'], data['middle_band'], data['lower_band'] = talib.BBANDS(data['Close'], timeperiod=20)

    return data

# Process all stocks and save the results in CSV files
for ticker in tickers:
    data = process_stock(ticker)
    data.to_csv(f"{ticker}_historical_data.csv")

# Define the list of tickers to check

days = 5  # Number of recent days to consider

# Function to check recent activity for different conditions
def check_conditions(ticker_data, days=5):
    # Calculate additional columns needed for conditions
    ticker_data['Volume_Ratio'] = ticker_data['Volume'] / ticker_data['Volume'].rolling(20).mean()
    ticker_data['52_Week_High'] = ticker_data['Close'].rolling(252).max()
    ticker_data['20_Day_Return'] = ticker_data['Close'].pct_change(20)
    ticker_data['Price_Change'] = ticker_data['Close'].diff()

    # Define short-term trend indicators
    short_term_indicators = {
        'Short_Term_Upward_Trend': ticker_data['Close'] > ticker_data['Close'].shift(),
        'Short_Term_Price_Gap_Up': ticker_data['Open'] > ticker_data['Close'].shift(),
        'Short_Term_Volume_Spike': ticker_data['Volume'] > ticker_data['Volume'].rolling(10).mean() * 1.5,
        # Add more short-term trend indicators as needed
    }

    # Define long-term trend indicators
    long_term_indicators = {
        'Long_Term_Upward_Trend': ticker_data['Close'] > ticker_data['Close'].shift(5),
        'Long_Term_Bullish_Crossover': ticker_data['Close'] > ticker_data['Close'].rolling(10).mean(),
        'Long_Term_52_Week_High': ticker_data['Close'] == ticker_data['52_Week_High'],
        # Add more long-term trend indicators as needed
    }

    # Define day trading conditions
    day_trading_conditions = {
        'Price_Gap_Up': ticker_data['Open'] > ticker_data['Close'].shift(),
        'Price_Gap_Down': ticker_data['Open'] < ticker_data['Close'].shift(),
        'Price_Change_Above_Threshold': abs(ticker_data['Price_Change']) > 0.02 * ticker_data['Close'].shift(),
        # Add more day trading conditions as needed
    }

    # Check short-term indicators
    short_term_activity = {indicator: short_term_indicators[indicator].rolling(days).sum() > 0 for indicator in short_term_indicators}

    # Check long-term indicators
    long_term_activity = {indicator: long_term_indicators[indicator].rolling(days).sum() > 0 for indicator in long_term_indicators}

    # Check day trading conditions
    day_trading_activity = {condition: day_trading_conditions[condition].rolling(days).sum() > 0 for condition in day_trading_conditions}

    # Combine short-term, long-term, and day trading activity into a single DataFrame
    recent_activity = pd.DataFrame({**short_term_activity, **long_term_activity, **day_trading_activity})

    return recent_activity

@st.cache_data
def load_data(ticker):
    return pd.read_csv(f"{ticker}_historical_data.csv", index_col=0)

def main():
    # Set Streamlit app title
    st.title("Stock Analysis")

    # Load cached data, check recent activity for all stocks, and save the results
    for ticker in tickers:
        data = load_data(ticker)
        recent_activity = check_conditions(data, days)
        recent_activity.to_csv(f"{ticker}_recent_activity.csv")

        # Display the ticker
        st.header(ticker)

        # Checkbox to show/hide the chart
        show_chart = st.checkbox("Show Chart", value=False, key=f"chart_{ticker}")

        if show_chart:
            # Create interactive Plotly chart
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Candlestick(x=data.index,
                                         open=data['Open'],
                                         high=data['High'],
                                         low=data['Low'],
                                         close=data['Close'],
                                         name='Stock Price'))

            # Display the chart
            st.plotly_chart(fig)

        # Create interactive table
        table_data = {
                    'Open':data['Open'].tail(days).to_list(),
                    'Moving Average Upward Trend': data['Upward_Trend'].tail(days).to_list(),
                    'RSI': data['RSI'].tail(days).to_list(),
                    'ADX': data['ADX'].tail(days).to_list(),
                   # 'Bollinger Bands': data[['upper_band', 'middle_band', 'lower_band']].tail(days).apply(lambda x: dict(x), axis=1),
                    'Short Term Upward Trend': data['Close'] > data['Close'].shift(),
                    'Short Term Price Gap Up': data['Open'] > data['Close'].shift(),
                    'Short Term Volume Spike': data['Volume'] > data['Volume'].rolling(10).mean() * 1.5,
                    'Long Term Upward Trend': data['Close'] > data['Close'].shift(5),
                    'Long Term Bullish Crossover': data['Close'] > data['Close'].rolling(10).mean(),
                    'Long Term 52 Week High': data['Close'] == data['52_Week_High'],
                    'Day Trading Price Gap Up': data['Open'] > data['Close'].shift(),
                    'Day Trading Price Gap Down': data['Open'] < data['Close'].shift(),
                    'Day Trading Price Change Above Threshold': abs(data['Price_Change']) > 0.02 * data['Close'].shift()
                    }

            #table = pd.DataFrame(table_data, index=data.index[-days:])
            #st.write(table)
        table = pd.DataFrame(table_data, index=data.index[-days:])

            # Calculate buy  scores
        buy_score = (
            table['Moving Average Upward Trend'].astype(int) +
            table['RSI'].astype(int) +
            table['ADX'].astype(int) +
            #table['Bollinger Bands'].apply(lambda x: int(x['middle_band'] < x['lower_band'])).astype(int) +
            table['Short Term Upward Trend'].astype(int) +
            table['Short Term Price Gap Up'].astype(int) +
            table['Short Term Volume Spike'].astype(int) +
            table['Long Term Upward Trend'].astype(int) +
            table['Long Term Bullish Crossover'].astype(int) +
            table['Long Term 52 Week High'].astype(int) +
            table['Day Trading Price Gap Up'].astype(int) +
            table['Day Trading Price Gap Down'].astype(int) +
            table['Day Trading Price Change Above Threshold'].astype(int)
        )

      
       

    # Add buy and sell scores to the table
        table['Buy Score'] = buy_score
        #table['Sell Score'] = sell_score
        st.table(table)

        # Print the file paths for the chart and table
    
if __name__ == '__main__':
    main()
