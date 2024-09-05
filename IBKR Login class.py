#Class to easily login and access IBKR data for option prices
from ib_insync import IB, Option

class IBKRClient:
    def __init__(self, host='127.0.0.1', port=7497, clientId=1):
        self.ib = IB()
        self.ib.connect(host, port, clientId)
    
    def get_option_price(self, ticker, expiration_date, strike_price, option_type='C'):
        contract = Option(ticker, expiration_date.replace('-', ''), strike_price, option_type, 'SMART')
        self.ib.qualifyContracts(contract)
        ticker_data = self.ib.reqMktData(contract, '', False, False)
        self.ib.sleep(2)
        return ticker_data.last
    
    def disconnect(self):
        self.ib.disconnect()

#Example
#ibkr_client = IBKRClient()
#price = ibkr_client.get_option_price("AAPL", "2024-12-20", 100, "C")
#print(f"IBKR Option Price: {price}")
#ibkr_client.disconnect()