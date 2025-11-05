import streamlit as st
import pandas as pd
import yfinance as yf 
import time
from datetime import datetime, date
import plotly.graph_objects as go


#SETUP AND CONFIGURATION
st.set_page_config(
    page_title="NexusStream", 
    layout="wide",
    initial_sidebar_state="expanded"
)

#UI Designing
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">

<style>

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* Make cards smoother */
div[data-testid="stMetric"] {
    background: #111111;
    border: 1px solid #222;
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 0 0px #000;
    transition: 0.3s ease;
}
div[data-testid="stMetric"]:hover {
    box-shadow: 0 0 15px rgba(0, 173, 255, 0.35);
}

/* Clean headings */
h1, h2, h3 {
    font-weight: 600 !important;
}

</style>
""", unsafe_allow_html=True)


st.title("NexusStream")

# CURRENCY SYMBOL
def get_currency_symbol(ticker):
    """Get the currency symbol based on the ticker."""
    if ".NS" in ticker.upper():
        return "₹"
    else:
        return "$" # Default to USD

# CORE FUNCTION
def get_market_data_and_vwap(symbol):
    """Fetches 1-year of DAILY "candles" for a symbol and calculates the VWAP."""
    try:
        # We ask for 1 year of 1-day data.
        # We add auto_adjust=True to silence the FutureWarning.
        data = yf.download(tickers=symbol, period='1y', interval='1d', auto_adjust=True)

        data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]

        if data.empty:
            return None, 0, 0 

        #Rename columns
        df = data.rename(columns={'Close': 'p', 'Volume': 'v'})
        
        # Calculate Price * Volume
        df['Price_Volume'] = df['p'] * df['v']
        
        #Group by the index.year (which is a DatetimeIndex) before resetting
        df_grouped = df.groupby(df.index.year)
        df['Cumulative_Volume'] = df_grouped['v'].cumsum()
        df['Cumulative_PV'] = df_grouped['Price_Volume'].cumsum()
        df['VWAP'] = df['Cumulative_PV'] / df['Cumulative_Volume']
        
        #reset the index to create the 'Date' column for plotting
        df = df.reset_index()
        # We rename the new index column to 'Date'
        df = df.rename(columns={df.columns[0]: 'Date'})
        
        # Get latest numbers
        latest_price = float(df.iloc[-1:]['p'].iloc[0]) 
        final_vwap = float(df.iloc[-1:]['VWAP'].iloc[0])

        return df, latest_price, final_vwap

    except Exception as e:
        print(f"Error in get_market_data_and_vwap for {symbol}: {e}")
        return None, 0, 0 # Silently fail

# DASHBOARD LAYOUT 
st.sidebar.header("CONTROLS")
ticker = st.sidebar.text_input("Enter Stock Ticker:", "AAPL").upper()

# Ticker List
st.sidebar.subheader("Popular Tickers")
ticker_list = {
    'Apple': 'AAPL',
    'Microsoft': 'MSFT',
    'Google': 'GOOGL',
    'Tesla': 'TSLA',
    'Amazon': 'AMZN',
    'NVIDIA': 'NVDA',
    'Meta': 'META',
    'Netflix': 'NFLX',
    'Reliance (IND)': 'RELIANCE.NS',
    'TCS (IND)': 'TCS.NS',
    'HDFC Bank (IND)': 'HDFCBANK.NS',
    'Infosys (IND)': 'INFY.NS',
    'Toyota (JP)': '7203.T',
    'Sony (JP)': '6758.T',
    'Samsung (KOR)': '005930.KS',
    'TSMC (Taiwan)': 'TSM',
    'Volkswagen (GER)': 'VOW3.DE',
    'Shell (UK)': 'SHEL.L',
    'AstraZeneca (UK)': 'AZN.L',
    'Vale (Brazil)': 'VALE'
}
st.sidebar.dataframe(
    pd.DataFrame(list(ticker_list.items()), columns=['Company', 'Ticker']), 
    hide_index=True
)
st.sidebar.info("This dashboard shows historical daily data (1-year) and auto-refreshes every 60 seconds.")

currency_symbol = get_currency_symbol(ticker)
placeholder = st.empty()

while True:
    if ticker: 
        
        df_trades, latest_price, vwap = get_market_data_and_vwap(ticker)
        
        with placeholder.container():
            
            if df_trades is not None:
                kpi1, kpi2, kpi3 = st.columns(3)
                
                kpi1.metric(label=f"{ticker} Latest Daily Price", value=f"{currency_symbol}{latest_price:,.2f}")
                kpi2.metric(label="Latest Yearly VWAP", value=f"{currency_symbol}{vwap:,.2f}")
                kpi3.metric(label="Total Days (1-Year)", value=f"{len(df_trades):,}")


                st.subheader("VWAP vs. Price (1-Day Candles)")

                fig = go.Figure()

                fig.add_trace(go.Candlestick(
                    x=df_trades['Date'],
                    open=df_trades['Open'],
                    high=df_trades['High'],
                    low=df_trades['Low'],
                    close=df_trades['p'],  
                    name="Price"
                ))

                # VWAP Line
                fig.add_trace(go.Scatter(
                    x=df_trades['Date'],
                    y=df_trades['VWAP'],
                    mode='lines',
                    line=dict(width=2, color="#FFD700"),  # gold TradingView VWAP line
                    name="VWAP"
                ))

                fig.update_layout(
                    template="plotly_dark",
                    xaxis_rangeslider_visible=False,   # hide range slider
                    hovermode="x unified",
                    showlegend=True,
                    height=600,
                    margin=dict(l=40, r=40, t=40, b=40),
                )
                fig.update_xaxes(showgrid=False)
                fig.update_yaxes(showgrid=False)
                st.plotly_chart(fig, use_container_width=True)
                st.subheader("Latest Daily Candle Data (Last 20 Days)")
                st.dataframe(df_trades[['Date', 'p', 'v', 'VWAP']].tail(20)) 
            
            else:
                st.warning(f"No daily data found for {ticker}. Check your network or the ticker is invalid.")

    time.sleep(60)

