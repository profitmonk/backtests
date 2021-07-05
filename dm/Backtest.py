    ######################################
    #
    # Backtest
    #  First, read the data with prediction done or run the prediction
    #  if not available
    #
    ######################################

# Module imports
#
# Import my code
#
import TckrOHLCdata
import DTM_Strategies
import DTM_Sizers
import TradeAnalysis

from datetime import datetime
from datetime import timedelta
import os.path  # To manage paths

import numpy as np
import pandas as pd
import pandas_datareader.data as web

import matplotlib
import matplotlib.pyplot as plt

# The following (between ****) in that order to get the cerebro.plot to plot in Spyder
# ******
import backtrader as bt
import backtrader.indicators as btind
import backtrader.analyzers as btanalyzers
from backtrader.utils.py3 import filter, string_types, integer_types
from backtrader import date2num
import backtrader.feeds as btfeeds
import backtrader.strategies as btstrats
import backtrader.plot

matplotlib.use('Qt5Agg')
plt.switch_backend('Qt5Agg')
# ******

class SmaCross(bt.SignalStrategy):
    def __init__(self):
        sma1, sma2 = bt.ind.SMA(period=10), bt.ind.SMA(period=30)
        crossover = bt.ind.CrossOver(sma1, sma2)
        self.signal_add(bt.SIGNAL_LONG, crossover)

def Backtest(BacktestParms, dfadjohlc, Results_df):   
    #
    # Start the back testing
    #
    cerebro = bt.Cerebro()
        
    # OHLC for stock_tckr
    stkdata = btfeeds.PandasData(
    dataname = dfadjohlc,
    # fromdate = datetime(2013, 4, 1),  # Start date of trading analysis
    fromdate = datetime(BacktestParms.btstart.year,BacktestParms.btstart.month,BacktestParms.btstart.day),  # Start date of trading analysis
    todate = datetime(BacktestParms.btend.year,BacktestParms.btend.month,BacktestParms.btend.day),    # End date of trading analysis
    # todate = datetime(2016, 12, 30),
    )
    # Add the Data Feed(s) to Cerebro
    print("Add", BacktestParms.stock_tckr, " to cerebro")
    cerebro.adddata(stkdata, name="StockData")
    
    if str(BacktestParms.strategy).find("SP500")>=0:
        temp = BacktestParms.stock_tckr
        BacktestParms.stock_tckr = 'SPY'
        dfSP500adjohlc = TckrOHLCdata.Get_data_update_to_latest(BacktestParms, 5)
        BacktestParms.stock_tckr = temp
        # OHLC for stock_tckr
        spydata = btfeeds.PandasData(
        dataname = dfSP500adjohlc,
        # fromdate = datetime(2013, 4, 1),  # Start date of trading analysis
        fromdate = datetime(BacktestParms.btstart.year,BacktestParms.btstart.month,BacktestParms.btstart.day),  # Start date of trading analysis
        todate = datetime(BacktestParms.btend.year,BacktestParms.btend.month,BacktestParms.btend.day),    # End date of trading analysis
        # todate = datetime(2016, 12, 30),
        )
        print("Add SPY to cerebro")
        cerebro.adddata(spydata, name="SPY") 

    # Add a strategy
    print("Add Strategy ", BacktestParms.strategy)
    
    cerebro.addstrategy(BacktestParms.strategy, backtestparms = BacktestParms)
    # Set our desired cash start
    cerebro.broker.setcash(BacktestParms.initial_cash)

    # Add a sizer based on how much capital to risk
    # cerebro.addsizer(DTM_Sizers.maxRiskSizer, risk=.5)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.PercentSizerInt, percents=50)

    # Add a FixedSize sizer according to the stake
    #cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    # Set the commission
    cerebro.broker.setcommission(commission=0.0)

    # Add the analyzers
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name="sharpe_annual")  # Gets the annualized Sharpe ratio
    # cerebro.addanalyzer(btanal.AnnualReturn)                                  # Annualized returns (does not work?)
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")  # Returns
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdwn")  # Drawdown statistics

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    print("Run")
    strategies = cerebro.run()
    StrategyResults = strategies[0]

    # Print out the final result
    print(BacktestParms.stock_tckr)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    Results_df = TradeAnalysis.RecordResults(StrategyResults, cerebro, BacktestParms, Results_df)

    if BacktestParms.display_chart:  
        # Plot the result
        cerebro.plot(iplot= False)              # Plots 100% of the time available
        # cerebro.plot(start=BacktestParms.btstart, end=BacktestParms.btend)
        # cerebro.plot(start=datetime.date(2007, 1, 1), end=datetime.date(2008, 1, 1))
        # cerebro.plot(iplot= False, style='candlestick', barup='green', bardown='red')
        # cerebro.plot(iplot= False, style='candlestick', barup='green', bardown='red', start=BacktestParms.btstart, end=BacktestParms.btend)

    return Results_df
