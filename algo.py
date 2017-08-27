import numpy as np
import statsmodels.api as sm
import statsmodels.tsa.stattools as ts
import pandas as pd

# ~~~~~~~~~~~~~~~~~~~~~~ TESTS FOR FINDING PAIR TO TRADE ON ~~~~~~~~~~~~~~~~~~~~~~
class ADF(object):
    """
    Augmented Dickey–Fuller (ADF) unit root test
    Source: http://www.pythonforfinance.net/2016/05/09/python-backtesting-mean-reversion-part-2/
    """

    def __init__(self):
        self.p_value = None
        self.five_perc_stat = None
        self.perc_stat = None
        self.p_min = .0
        self.p_max = .05
        self.look_back = 63

    def apply_adf(self, time_series):
        model = ts.adfuller(time_series, 1)
        self.p_value = model[1]
        self.five_perc_stat = model[4]['5%']
        self.perc_stat = model[0]

    def use_P(self):
        return (self.p_value > self.p_min) and (self.p_value < self.p_max)
    
    def use_critical(self):
        return abs(self.perc_stat) > abs(self.five_perc_stat)


"""  
# DEPRECATED
class KPSS(object):
    #Kwiatkowski-Phillips-Schmidt-Shin (KPSS) stationarity tests
    def __init__(self):
        Exception("Not implemented yet")
        self.p_value = None
        self.ten_perc_stat = None
        self.perc_stat = None
        self.p_min = 0.0
        self.p_max = 0.2
        self.look_back = 50
    
    def apply_kpss(self, time_series):
        self.p_value = ts.adfuller(time_series, 1)[1]
        self.five_perc_stat = ts.adfuller(time_series, 1)[4]['5%'] # possibly make this 10%
        self.perc_stat = ts.adfuller(time_series, 1)[0]
        
    def use(self):
        return (self.p_value > self.p_min) and (self.p_value < self.p_max) and (self.perc_stat > self.five_perc_stat)
"""


class Half_Life(object):
    """
    Half Life test from the Ornstein-Uhlenbeck process 
    Source: http://www.pythonforfinance.net/2016/05/09/python-backtesting-mean-reversion-part-2/
    """

    def __init__(self):
        self.hl_min = 1.0
        self.hl_max = 42.0
        self.look_back = 43
        self.half_life = None

    def apply_half_life(self, time_series):
        lag = np.roll(time_series, 1)
        lag[0] = 0
        ret = time_series - lag
        ret[0] = 0

        # adds intercept terms to X variable for regression
        lag2 = sm.add_constant(lag)

        model = sm.OLS(ret, lag2)
        res = model.fit()

        self.half_life = -np.log(2) / res.params[1]

    def use(self):
        return (self.half_life < self.hl_max) and (self.half_life > self.hl_min)


class Hurst():
    """
    If Hurst Exponent is under the 0.5 value of a random walk, then the series is mean reverting
    Source: https://www.quantstart.com/articles/Basics-of-Statistical-Mean-Reversion-Testing
    """

    def __init__(self):
        self.h_min = 0.0
        self.h_max = 0.4
        self.look_back = 126
        self.lag_max = 100
        self.h_value = None
    
    def apply_hurst(self, time_series):
        """Returns the Hurst Exponent of the time series vector ts"""
        # Create the range of lag values
        lags = range(2, self.lag_max)

        # Calculate the array of the variances of the lagged differences
        tau = [np.sqrt(np.std(np.subtract(time_series[lag:], time_series[:-lag]))) for lag in lags]

        # Use a linear fit to estimate the Hurst Exponent
        poly = np.polyfit(np.log10(lags), np.log10(tau), 1)

        # Return the Hurst exponent from the polyfit output
        self.h_value = poly[0]*2.0 

    def use(self):
        return (self.h_value < self.h_max) and (self.h_value > self.h_min)

# ~~~~~~~~~~~~~~~~~~~~~~ FUNCTIONS FOR FILING AN ORDER ~~~~~~~~~~~~~~~~~~~~~~
def hedge_ratio(Y, X):
    # Look into using Kalman Filter to calculate the hedge ratio
    X = sm.add_constant(X)
    model = sm.OLS(Y, X).fit()
    return model.params[1]

def softmax_order(stock_1_shares, stock_2_shares, stock_1_price, stock_2_price):
    stock_1_cost = stock_1_shares * stock_1_price
    stock_2_cost = stock_2_shares * stock_2_price
    costs = np.array([stock_1_cost, stock_2_cost])
    return np.exp(costs) / np.sum(np.exp(costs), axis=0)

def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    
    context.asset_pairs = [[symbol('MSFT'), symbol('AAPL'), {'in_short': False, 'in_long': False, 'spread': np.array([]), 'hedge_history': np.array([])}], 
                           [symbol('YUM'), symbol('MCD'), {'in_short': False, 'in_long': False, 'spread': np.array([]), 'hedge_history': np.array([])}]]
    context.z_back = 20
    context.hedge_lag = 2
    context.entry_z = 0.5
    
    schedule_function(my_handle_data, date_rules.every_day(),
                      time_rules.market_close(hours=4))
    # Typical slippage and commision I have seen others use and is used in templates by Quantopian
    set_slippage(slippage.VolumeShareSlippage(volume_limit=0.025, price_impact=0.1))
    set_commission(commission.PerShare(cost=0.01, min_trade_cost=1.0))


def my_handle_data(context, data):
    """
    Called every day.
    """
    
    if get_open_orders():
        return
    
    for i in range(len(context.asset_pairs)):
        pair = context.asset_pairs[i]      
        new_pair = process_pair(pair, context, data)
        context.asset_pairs[i] = new_pair

def process_pair(pair, context, data):
    """
    Main function that will execute an order for every pair.
    """
    
    # Get stock data
    stock_1 = pair[0]
    stock_2 = pair[1]
    prices = data.history([stock_1, stock_2], "price", 300, "1d")
    stock_1_P = prices[stock_1]
    stock_2_P = prices[stock_2]
    in_short = pair[2]['in_short']
    in_long = pair[2]['in_long']
    spread = pair[2]['spread']
    hedge_history = pair[2]['hedge_history']

    # Get hedge ratio (look into using Kalman Filter)
    try:
        hedge = hedge_ratio(stock_1_P, stock_2_P)
    except ValueError as e:
        log.error(e)
        return [stock_1, stock_2, {'in_short': in_short, 'in_long': in_long, 'spread': spread, 'hedge_history': hedge_history}]
    
    hedge_history = np.append(hedge_history, hedge)
    
    if hedge_history.size < context.hedge_lag:
        log.debug("Hedge history too short!")
        return [stock_1, stock_2, {'in_short': in_short, 'in_long': in_long, 'spread': spread, 'hedge_history': hedge_history}]

    hedge = hedge_history[-context.hedge_lag]
    spread = np.append(
        spread, stock_1_P[-1] - hedge * stock_2_P[-1])
    spread_length = spread.size

    adf = ADF()
    half_life = Half_Life()
    hurst = Hurst()

    # Check if current window size is large enough for adf, half life, and hurst exponent
    if (spread_length < adf.look_back) or (spread_length < half_life.look_back) or (spread_length < hurst.look_back):
        return [stock_1, stock_2, {'in_short': in_short, 'in_long': in_long, 'spread': spread, 'hedge_history': hedge_history}]

    
    # possible "SVD did not converge" error because of OLS
    try:
        adf.apply_adf(spread[-adf.look_back:])
        half_life.apply_half_life(spread[-half_life.look_back:])
        hurst.apply_hurst(spread[-hurst.look_back:])
    except:
        return [stock_1, stock_2, {'in_short': in_short, 'in_long': in_long, 'spread': spread, 'hedge_history': hedge_history}]

    # Check if they are in fact a stationary (or possibly trend stationary...need to avoid this) time series
    # * Only cancel if all measures believe it isn't stationary
    if not adf.use_P() and not adf.use_critical() and not half_life.use() and not hurst.use():
        if in_short or in_long:
            # Enter logic here for how to handle open positions after mean reversion
            # of spread breaks down.
            log.info('Tests have failed. Exiting open positions')
            order_target(stock_1, 0)
            order_target(stock_2, 0)
            in_short = in_long = False
            return [stock_1, stock_2, {'in_short': in_short, 'in_long': in_long, 'spread': spread, 'hedge_history': hedge_history}]
            
        log.debug("Not Stationary!")
        return [stock_1, stock_2, {'in_short': in_short, 'in_long': in_long, 'spread': spread, 'hedge_history': hedge_history}]
    
    # Check if current window size is large enough for Z score
    if spread_length < context.z_back:
        return [stock_1, stock_2, {'in_short': in_short, 'in_long': in_long, 'spread': spread, 'hedge_history': hedge_history}]

    spreads = spread[-context.z_back:]
    z_score = (spreads[-1] - spreads.mean()) / spreads.std()
    
    # Record measures
    if stock_1 == sid(5061):
        record(Z_tech=z_score)
        record(Hedge_tech=hedge)
    else:
        record(Z_food=z_score)
        record(Hedge_food=hedge)
    
    # Close order logic
    if in_short and z_score < 0.0:
        order_target(stock_1, 0)
        order_target(stock_2, 0)
        in_short = False
        in_long = False
        return [stock_1, stock_2, {'in_short': in_short, 'in_long': in_long, 'spread': spread, 'hedge_history': hedge_history}]
    elif in_long and z_score > 0.0:
        order_target(stock_1, 0)
        order_target(stock_2, 0)
        in_short = False
        in_long = False
        return [stock_1, stock_2, {'in_short': in_short, 'in_long': in_long, 'spread': spread, 'hedge_history': hedge_history}]
    
    # Open order logic
    if (z_score < -context.entry_z) and (not in_long):
        stock_1_shares = 1
        stock_2_shares = -hedge
        in_long = True
        in_short = False
        (stock_1_perc, stock_2_perc) = softmax_order(stock_1_shares, stock_2_shares, stock_1_P[-1], stock_2_P[-1])
        order_target_percent(stock_1, stock_1_perc)
        order_target_percent(stock_2, stock_2_perc)
        return [stock_1, stock_2, {'in_short': in_short, 'in_long': in_long, 'spread': spread, 'hedge_history': hedge_history}]
    elif z_score > context.entry_z and (not in_short):
        stock_1_shares = -1
        stock_2_shares = hedge
        in_short = True
        in_long = False
        (stock_1_perc, stock_2_perc) = softmax_order(stock_1_shares, stock_2_shares, stock_1_P[-1], stock_2_P[-1])
        order_target_percent(stock_1, stock_1_perc)
        order_target_percent(stock_2, stock_2_perc)
        return [stock_1, stock_2, {'in_short': in_short, 'in_long': in_long, 'spread': spread, 'hedge_history': hedge_history}]

    return [stock_1, stock_2, {'in_short': in_short, 'in_long': in_long, 'spread': spread, 'hedge_history': hedge_history}]
