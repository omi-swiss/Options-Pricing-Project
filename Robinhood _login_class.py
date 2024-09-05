#Class to easily login and access Robinhood data for option prices
import robin_stocks.robinhood as rh

class RobinhoodClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.login()

    def login(self):
        rh.login(self.username, self.password)

    def get_option_price(self, ticker, expiration_date, strike_price, option_type='call'):
        options = rh.options.find_options_by_expiration_and_strike(
            ticker, expirationDate=expiration_date, strikePrice=str(strike_price), optionType=option_type
        )
        if options:
            option_data = rh.options.get_option_market_data_by_id(options[0]['id'])
            return option_data['adjusted_mark_price']
        else:
            return None
    
    def logout(self):
        rh.logout()