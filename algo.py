# Note to self: look into beta neutral instead of dollar neutral for choosing a pair

# ~~~~~~~~~~~~~~~~~~~~~~
import numpy as np
import statsmodels.api as sm
import statsmodels.tsa.stattools as ts
import pandas as pd

# ~~~~~~~~~~~~~~~~~~~~~~ TESTS FOR FINDING PAIR TO TRADE ON ~~~~~~~~~~~~~~~~~~~~~~
class ADF(object):
    """Augmented Dickey–Fuller (ADF) unit root test"""
    def __init__(self):
        self.p_value = None
        self.five_perc_stat = None
        self.perc_stat = None
        self.p_min = .0
        self.p_max = .2
        self.look_back = 50
        
    def apply_adf(self, time_series):
        self.p_value = ts.adfuller(time_series, 1)[1]
        self.five_perc_stat = ts.adfuller(time_series, 1)[4]['5%']
        self.perc_stat = ts.adfuller(time_series, 1)[0]
        
    def use(self):
        # http://www.pythonforfinance.net/2016/05/09/python-backtesting-mean-reversion-part-2/
        return (self.p_value > self.p_min) and (self.p_value < self.p_max) and (self.perc_stat > self.five_perc_stat)

class KPSS(object):
    """Kwiatkowski-Phillips-Schmidt-Shin (KPSS) stationarity tests"""
    def __init__(self):
        self.p_value = None
        self.ten_perc_stat = None
        self.perc_stat = None
        self.p_min = .0
        self.p_max = .2
        self.look_back = 50
    
    
    def apply_kpss(self, time_series):
        self.p_value = ts.adfuller(time_series, 1)[1]
        self.five_perc_stat = ts.adfuller(time_series, 1)[4]['5%'] # possibly make this 10%
        self.perc_stat = ts.adfuller(time_series, 1)[0]
        
    def use(self):
        return (self.p_value > self.p_min) and (self.p_value < self.p_max) and (self.perc_stat > self.five_perc_stat)
        
# Look into using Kalman Filter to calculate the hedge ratio
def hedge_ratio(Y, X):
    X = sm.add_constant(X)
    model = sm.OLS(Y, X).fit()
    return model.params[1]


def half_life(time_series):
    """Half Life test from the Ornstein-Uhlenbeck process 
    http://www.pythonforfinance.net/2016/05/09/python-backtesting-mean-reversion-part-2/"""
    price = pd.DataFrame(time_series)
    #Run OLS regression on spread series and lagged version of itself
    spread_lag = price.spread.shift(1)
    spread_lag.ix[0] = spread_lag.ix[1]
    spread_ret = price.spread - spread_lag
    spread_ret.ix[0] = spread_ret.ix[1]
    spread_lag2 = sm.add_constant(spread_lag)

    model = sm.OLS(spread_ret,spread_lag2)
    res = model.fit()
    
    half_life = round(-np.log(2) / res.params[1],0)
    
    return half_life

def hurst(ts):
    """If Hurst Exponent is under the 0.5 value of a random walk, then the series is mean reverting
    https://www.quantstart.com/articles/Basics-of-Statistical-Mean-Reversion-Testing"""
    # Create the range of lag values
    lags = range(2, 100)
 
    # Calculate the array of the variances of the lagged differences
    tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
 
    # Use a linear fit to estimate the Hurst Exponent
    poly = np.polyfit(log(lags), log(tau), 1)
 
    # Return the Hurst exponent from the polyfit output
    return poly[0]*2.0
 
def initialize(context):
    """
    Called once at the start of the algorithm.
    """   
    context.assets = [sid(5061), sid(24)]
    context.lookback = 40
    context.z_back = 30
    context.hedge_lag = 1
    context.spread = np.array([])
    # Rebalance every day, 1 hour after market open.
    schedule_function(my_rebalance, date_rules.every_day(), time_rules.market_open(hours=1))
     
    # Record tracking variables at the end of each day.
    schedule_function(my_record_vars, date_rules.every_day(), time_rules.market_close())
    
    schedule_function(my_handle_data, date_rules.every_day(), time_rules.market_close(hours=1))
     
    # Create our dynamic stock selector.
    #attach_pipeline(make_pipeline(), 'my_pipeline')
 
def before_trading_start(context, data):
    """
    Called every day before market open.
    """
     
def my_assign_weights(context, data):
    """
    Assign weights to securities that we want to order.
    """
    pass
 
def my_rebalance(context,data):
    """
    Execute orders according to our schedule_function() timing. 
    """
    pass
 
def my_record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    pass
 
def my_handle_data(context,data):
    """
    Called every day.
    """
    if get_open_orders():
        return
    
    # Get stock data
    stock_1 = context.assets[0]
    stock_2 = context.assets[1]        
    prices = data.history([stock_1, stock_2], "price", 300, "1d")
    stock_1_P = prices[stock_1]
    stock_2_P = prices[stock_2]
    
    # Get hedge ratio (look into using Kalman Filter)
    try:
        hedge = hedge_ratio(stock_1_P, stock_2_P)      
    except ValueError as e:
        #log.debug(e)
        return    
    # Wait until a day has passed
    if context.hedge_lag > 0: 
        context.prev_hedge = hedge
        context.hedge_lag -= 1
        return
    
    # May need to switch stock_1/stock_2 places...95% sure this is the correct spread calculation
    context.spread = np.append(context.spread, stock_1_P[-1] - context.prev_hedge * stock_2_P[-1]) 
    spread_length = context.spread.size
    
    for stock in [stock_1_P, stock_2_P]:
        adf = ADF()
        kpss = KPSS()
        
        # Check if current window size is large enough
        if (spread_length < adf.look_back) or (spread_length < kpss.look_back):
            return
        
        adf.apply_adf(stock)
        kpss.apply_kpss(stock)
        
        # Check if they are in fact a stationary (or possibly trend stationary...need to avoid this) time series
        if (adf.use() and kpss.use()):
            log.debug("Stationary")
            #log.debug("ADF: {0}".format((adf.use())))
            #log.debug("KPSS: {0}".format(kpss.use()))
            return
        

        
        
    context.prev_hedge = hedge
    # Record all the values calculated
    record(hedge = hedge)