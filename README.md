# Quantopian_Pairs_Trader
This is my implementation of a Pairs Trading Algorithm on the algorithmic trading research/competition platform [Quantopian](https://www.quantopian.com/home) so I can dive deeper and learn more about [Pairs Trading](http://www.investopedia.com/university/guide-pairs-trading/) and implementing trading algorithms. Some tests/measures I'm currently learning about and using include:

* Kwiatkowski-Phillips-Schmidt-Shin ([KPSS](https://en.wikipedia.org/wiki/KPSS_test)) stationarity test
* Augmented Dickey–Fuller ([ADF](https://en.wikipedia.org/wiki/Augmented_Dickey%E2%80%93Fuller_test)) unit root test
* [Hedge ratio](http://www.investopedia.com/terms/h/hedgeratio.asp)
* Half life of [mean-reversion](http://www.investopedia.com/terms/m/meanreversion.asp) from the [Ornstein-Uhlenbeck process](https://en.wikipedia.org/wiki/Ornstein%E2%80%93Uhlenbeck_process)
* [Hurst exponent](https://en.wikipedia.org/wiki/Hurst_exponent)
* [Softmax function](https://en.wikipedia.org/wiki/Softmax_function) for calculating percent of each security on open order

## Current Results
Currently, my implementation will be able to run on arbitrary amount of possible pairs that a user could provide. However, for current testing purposes, I have only been testing on two possible pairs (and hardcoded some logic that assumes that such as how I record values on the graph). Those two pairs are Microsoft ([MSFT](http://www.google.ca/finance?q=MSFT&ei=FD-ZWcHDKNHejAHt4p-IBA)) + Apple ([AAPL](http://www.google.ca/finance?q=AAPL&ei=-T6ZWaGkKIaO2AbyxbCIBQ)), and McDonalds ([MCD](http://www.google.ca/finance?q=MCD&ei=LT-ZWbHmLIaO2AbyxbCIBQ)) + Yum! Brands ([YUM](http://www.google.ca/finance?q=YUM&ei=PT-ZWcnHCsK42Aac35GoCQ)) which owns chains like KFC, Pizza Hut, and Taco Bell. The former can be seen in the lower graph with the label "\_tech" and the latter with the label "\_food" with corresponding Z and hedge ratio values.

![Current Results Graph](https://raw.githubusercontent.com/bartchr808/Quantopian_Pairs_Trader/master/current_results.png "Current Results Graph")

I had my algorithm run for 13 years from January 1, 2004 to January 1, 2017. However, I'm planning on seeing how extensible my algorithm is to different time periods and different combination of pairs. From the few tests I have done so far, this seems true and I haven't "overfitted" my algorithm by making it only work in a specific instance.

<!--
As my current results stand, I did **10,498.24%** better than the defualt Quantopian benchmark, the SPDR S&P 500 Trust ETF ([SPY](http://www.google.ca/finance?q=SPY&ei=7z6ZWYiaLo2gjAGFs4OYAg)) (103.76%), and **10,510.59%** better than the [Dow](http://www.google.com/finance?q=INDEXDJX:.DJI) (91.41%), with a **10,602%** return.
-->

## Issues/Next Steps
* Quantopian has deprecated version of Statsmodels python library which doesn't have the KPSS test available. I'll need to manually add it myself.
* Look into cleaning up how I'm currently returning a completely new pair object in `process_pair` and replacing the old pair in the for-loop in `my_handle_data`.
* Haven't looked at using Kalman filters for determining hedge ratios. Not sure if I need to or if the way I did it sufficient.
* Need to look into how Quantopian's `order_target_percent` function works when I have several different pairs and not one or two (e.g. will the first opening order take up my entire portfolio?) 
