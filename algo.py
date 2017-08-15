"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume
from quantopian.pipeline.filters.morningstar import Q1500US
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
        self.ten_perc_stat = None
        self.perc_stat = None
        self.look_back = 60
        self.p_min = .0
        slef.p_max = .2
        
	def apply_adf(self, time_series):
        self.p_value = ts.adfuller(time_series, 1)[1]
        self.ten_perc_stat = ts.adfuller(time_series, 1)[4]['10%']
        self.perc_stat = ts.adfuller(time_series, 1)[0]
        
    def use(self):
        # http://www.pythonforfinance.net/2016/05/09/python-backtesting-mean-reversion-part-2/
        return (self.p_value > self.p_min) and (self.p_value < self.p_max) and (abs(self.perc_stat) > abs(self.ten_perc_stat))

class KPSS(object):
    """Kwiatkowski-Phillips-Schmidt-Shin (KPSS) stationarity tests"""
    def __init__(self):
        self.p_value = None
        self.ten_perc_stat = None
        self.perc_stat = None
        self.look_back = 60
        self.p_min = .0
        slef.p_max = .2
    
    
    def apply_kpss(self, time_series):
        self.p_value = ts.adfuller(time_series, 1)[1]
        self.ten_perc_stat = ts.adfuller(time_series, 1)[4]['10%']
        self.perc_stat = ts.adfuller(time_series, 1)[0]
        
    def use(self):
        return (self.p_value > self.p_min) and (self.p_value < self.p_max) and (abs(self.perc_stat) > abs(self.ten_perc_stat))
        
        
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
    tau = [sqrt(std(subtract(ts[lag:], ts[:-lag]))) for lag in lags]
 
    # Use a linear fit to estimate the Hurst Exponent
    poly = polyfit(log(lags), log(tau), 1)
 
    # Return the Hurst exponent from the polyfit output
    return poly[0]*2.0
 
def initialize(context):
    """
    Called once at the start of the algorithm.
    """   
    # Rebalance every day, 1 hour after market open.
    schedule_function(my_rebalance, date_rules.every_day(), time_rules.market_open(hours=1))
     
    # Record tracking variables at the end of each day.
    schedule_function(my_record_vars, date_rules.every_day(), time_rules.market_close())
     
    # Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'my_pipeline')
         
def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation on
    pipeline can be found here: https://www.quantopian.com/help#pipeline-title
    """
    
    # Base universe set to the Q500US
    base_universe = Q1500US()

    # Factor of yesterday's close price.
    yesterday_close = USEquityPricing.close.latest
     
    pipe = Pipeline(
        screen = base_universe,
        columns = {
            'close': yesterday_close,
        }
    )
    return pipe
 
def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = pipeline_output('my_pipeline')
  
    # These are the securities that we are interested in trading each day.
    context.security_list = context.output.index
     
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
 
def handle_data(context,data):
    """
    Called every minute.
    """
    pass
