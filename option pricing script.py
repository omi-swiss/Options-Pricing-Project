import numpy as np
import pandas as pd
from scipy.stats import norm
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta
from fredapi import Fred
import robin_stocks.robinhood as rh
from scipy.stats import norm
from Robinhood_login_class import RobinhoodClient # type: ignore


def get_viable_expiration_dates(ticker, max_months=6):
    stock = yf.Ticker(ticker)
    today = datetime.now()
    max_date = today + timedelta(days=max_months * 30)
    
    # Filter expiration dates efficiently
    viable_dates = [date for date in stock.options if today <= datetime.strptime(date, "%Y-%m-%d") <= max_date]
    return viable_dates

def get_viable_strike_prices(ticker, expiration_date, price_range_percent=10):
    stock = yf.Ticker(ticker)
    current_price = get_live_stock_price(ticker)
    options_chain = stock.option_chain(expiration_date)
    
    min_price = current_price * (1 - price_range_percent / 100)
    max_price = current_price * (1 + price_range_percent / 100)
    
    # Efficient filtering with pandas
    strikes = pd.concat([options_chain.calls['strike'], options_chain.puts['strike']])
    viable_strikes = strikes[(strikes >= min_price) & (strikes <= max_price)].unique()
    
    return sorted(viable_strikes)

# Functions to get stock price, time to maturity, volatility, and Black-Scholes model
def get_live_stock_price(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period="1d")['Close'].iloc[-1]

def get_time_to_maturity(expiration_date):
    today = datetime.now()
    expiration = datetime.strptime(expiration_date, "%Y-%m-%d")
    return (expiration - today).days / 365.0  # Convert days to years

def get_historical_volatility(ticker, period="1y"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    log_returns = np.log(data['Close'] / data['Close'].shift(1))
    return log_returns.std() * np.sqrt(252)  # Annualized volatility

def black_scholes(S, K, T, r, sigma, option_type='call'):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if option_type == 'call':
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def get_risk_free_rate(fred_api_key, series_id='DGS10'):
    """
    Fetches the latest risk-free rate from FRED using the specified series ID.
    
    Parameters:
    fred_api_key (str): Your FRED API key.
    series_id (str): The FRED series ID for the interest rate (default is 'DGS10' for the 10-year Treasury yield).
    
    Returns:
    float: The most recent risk-free rate, expressed as a decimal (e.g., 0.03 for 3%).
    """
    fred = Fred(api_key=fred_api_key)
    risk_free_rate = fred.get_series(series_id)[-1] / 100  # Convert percentage to decimal
    return risk_free_rate

def convert_to_robinhood_price(model_price):
    return model_price  # Price per share, assuming 100 shares per contract


def get_robinhood_option_price(ticker, expiration_date, strike_price, option_type='call'):
    options = rh.options.find_options_by_expiration_and_strike(
        ticker, expirationDate=expiration_date, strikePrice=str(strike_price), optionType=option_type
    )
    if options:
        option_data = rh.options.get_option_market_data_by_id(options[0]['id'])
        return option_data['adjusted_mark_price']
    else:
        return None

def main():
     
    robinhood_client = RobinhoodClient('your_username', 'your_password')

    tickers = ["AAPL", "MSFT"]
    r = risk_free_rate = get_risk_free_rate('d4b18869e97d520eb490a1330829b12f')

    results = []


    for ticker in tickers:
        expiration_dates = get_viable_expiration_dates(ticker, max_months=6)
        
        for expiration_date in expiration_dates:
            strike_prices = get_viable_strike_prices(ticker, expiration_date, price_range_percent=10)
            
            for strike_price in strike_prices:
                S = get_live_stock_price(ticker)
                T = get_time_to_maturity(expiration_date)
                sigma = get_historical_volatility(ticker)
                
                bs_price = black_scholes(S, strike_price, T, r, sigma, option_type='call')
                robinhood_bs_price = convert_to_robinhood_price(bs_price)
                robinhood_price = get_robinhood_option_price(ticker, expiration_date, strike_price, option_type='call')
                
                results.append({
                    "Ticker": ticker,
                    "Expiration Date": expiration_date,
                    "Strike Price": strike_price,
                    "Black-Scholes Price": robinhood_bs_price,
                    "Robinhood  Price": robinhood_price
                })
    rh.logout()
    # Display results efficiently
    # Convert results list to a pandas DataFrame
    df_results = pd.DataFrame(results)

    # Display the DataFrame
    print(df_results)

if __name__ == "__main__":
    main()
