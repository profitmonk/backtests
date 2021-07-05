    ######################################
    #
    # Strategies
    #  Defines Backtrader Strategy classes 
    #  Strategies are not Covered Call strategies
    #
    #  TestStrategy
    #  BBandsStrategy 
    #  BuyHoldStrategy
    #  DTMUltOscStrategy
    #  DTMUltOscOBVtrendStrategy
    #  RAMThreeXVolUpStrategy
    #  RAMThreeXVolUpPVTGapStrategy
    #  RAMThreeXVolUpPVTGapDaveStrategy
    #  rsiStrategy
    #  
    ######################################
#
# Module imports
#
#
# Import my code
#
import DTM_Indicators

import datetime  # For datetime objects
from datetime import timedelta
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

import numpy as np
import pandas as pd
import scipy  # Scaling
import scipy.stats
import random
import math

import backtrader as bt
from backtrader.utils.py3 import filter, string_types, integer_types
from backtrader import date2num
import backtrader.feeds as btfeeds

###############################
# Strategies
###############################
# Create TestStrategy to be used for development
class TestStrategy(bt.Strategy):
    params = (
        ('fastmaperiod', 10),
        ('midmaperiod', 20),
        ('slowmaperiod', 50),
        ('backtestparms', None),
    )

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.high = self.datas[0].high
        self.chandelier_exit_val = bt.ind.Highest(self.high, period=22) - 3 * bt.ind.ATR(
            period=22)  # Stop at 3 ATRs below the highest high since entry

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.fastsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.fastmaperiod)
        self.midsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.midmaperiod)
        self.slowsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.slowmaperiod)

        # Create DTMUltimateOsc which is a ZLEMA smoothed UltimateOsc
        self.DTMultosc = DTM_Indicators.DTMUltOsc(self.datas[0])
        
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Determine if DTUMUltOsc is a local minimum
        # Was the indicator falling?
        if self.DTMultosc[-2] > self.DTMultosc[-1]:
            self.wasfalling = True
        else:
            self.wasfalling = False
        # Is it now rising?
        if self.DTMultosc[0] > self.DTMultosc[-1]:
            self.nowrising = True
        else:
            self.nowrising = False
        # Is it local minimum?
        if self.wasfalling and self.nowrising:
            self.bottomed = True
        else:
            self.bottomed = False

        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            # Determine if the date is after or equal to the WhaleWisdom date
            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowStartDate and self.data.datetime.datetime() < self.params.backtestparms.TradeWindowEndDate:
                if self.bottomed:
                    # BUY, BUY, BUY!!! (with all possible default parameters)
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
    
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

        else:

            if self.dataclose[0] < self.chandelier_exit_val:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
            
            if self.data.datetime.datetime() < self.params.backtestparms.TradeWindowEndDate:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

       # If it is the last bar of the data, close the positions.
           # Actually, one bar before the last to enter the order and execute
        if len(self.datas[0]) == self.datas[0].buflen()-1:
            if self.position:
                self.order = self.sell() 
                self.log('Closed all trades on last day in data')             

# Bollinger Bands strategy on instrument being traded
class BBandsStrategy(bt.Strategy):
    params = (
        ('fastmaperiod', 10),
        ('midmaperiod', 20),
        ('slowmaperiod', 50),
        ('BBandsperiod', 20),
        ('backtestparms', None),
    )

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.high = self.datas[0].high
        self.chandelier_exit_val = bt.ind.Highest(self.high, period=22) - 3 * bt.ind.ATR(
            period=22)  # Stop at 3 ATRs below the highest high since entry

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.redline = None
        self.blueline = None

        # Add a MovingAverageSimple indicator
        self.fastsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.fastmaperiod)
        self.midsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.midmaperiod)
        self.slowsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.slowmaperiod)

        # Create DTMUltimateOsc which is a ZLEMA smoothed UltimateOsc
        self.DTMultosc = DTM_Indicators.DTMUltOsc(self.datas[0])

        # Add a BBand indicator
        self.bband = bt.indicators.BBands(self.datas[0], period=self.params.BBandsperiod)

        # Indicators for the plotting show
        # bt.indicators.UltimateOscillator(self.datas[0].close)
        # bt.indicators.ExponentialMovingAverage(self.datas[0].close, period=25)
        # bt.indicators.WeightedMovingAverage(self.datas[0].close, period=25,
        #                                    subplot=True)
        # bt.indicators.StochasticSlow(self.datas[0].close)
        # bt.indicators.MACDHisto(self.datas[0].close)
        # rsi = bt.indicators.RSI(self.datas[0].close)
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)
        # bt.indicators.ATR(self.datas[0].close, plot=False)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        if self.dataclose < self.bband.lines.bot and not self.position:
            self.redline = True

        if self.dataclose > self.bband.lines.top and self.position:
            self.blueline = True
                   
        if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowStartDate and self.data.datetime.datetime() < self.params.backtestparms.TradeWindowEndDate:
            if self.dataclose > self.bband.lines.mid and not self.position and self.redline:
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()
    
            if self.dataclose > self.bband.lines.top and not self.position:
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        if self.dataclose < self.bband.lines.mid and self.position and self.blueline:
            # SELL, SELL, SELL!!! (with all possible default parameters)
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.blueline = False
            self.redline = False
            # Keep track of the created order to avoid a 2nd order
            self.order = self.sell()
            
        if self.position and self.data.datetime.datetime() > self.params.backtestparms.TradeWindowEndDate:
            # SELL, SELL, SELL!!! (with all possible default parameters)
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.blueline = False
            self.redline = False
            # Keep track of the created order to avoid a 2nd order
            self.order = self.sell()
            
       # If it is the last bar of the data, close the positions.
           # Actually, one bar before the last to enter the order and execute
        if len(self.datas[0]) == self.datas[0].buflen()-1:
            if self.position:
                self.order = self.sell() 
                self.log('Closed all trades on last day in data')     

# Create Buy and Hold to be used to compare results
# Buy at the first bar and sell on the last bar. Used as a comparison baseline            
class BuyHoldStrategy(bt.Strategy):
    params = (
        ('backtestparms', None),
    )

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):
        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            # Determine if the date is after or equal to the WhaleWisdom date
            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowStartDate and self.data.datetime.datetime() < self.params.backtestparms.TradeWindowEndDate:
                
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:
            # Determine if the date is after the WhaleWisdom end date
            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowEndDate:
                if self.position:
                    self.log('Sell CREATE, %.2f' % self.dataclose[0])
                    # self.log('Closed all trades on last day in data')
                    self.order = self.sell()
           # If it is the last bar of the data, close the positions.
           # Actually, one bar before the last to enter the order and execute
            if len(self.datas[0]) == self.datas[0].buflen()-1:
                if self.position:
                    # self.log('Closed all trades on last day in data')
                    self.order = self.sell()
                    self.log('Closed all trades on last day in data')


# DTM Ult Osc strategy on instrument being traded
class DTMUltOscStrategy(bt.Strategy):
    params = (
        ('fastmaperiod', 10),
        ('midmaperiod', 20),
        ('slowmaperiod', 50),
        ('backtestparms', None),
    )

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.high = self.datas[0].high
        self.chandelier_exit_val = bt.ind.Highest(self.high, period=22) - 3 * bt.ind.ATR(
            period=22)  # Stop at 3 ATRs below the highest high since entry

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.fastsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.fastmaperiod)
        self.midsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.midmaperiod)
        self.slowsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.slowmaperiod)

        # Create DTMUltimateOsc which is a ZLEMA smoothed UltimateOsc
        self.DTMultosc = DTM_Indicators.DTMUltOsc(self.datas[0])

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Determine if DTUMUltOsc is a local minimum
        # Was the indicator falling?
        if self.DTMultosc[-2] > self.DTMultosc[-1]:
            self.wasfalling = True
        else:
            self.wasfalling = False
        # Is it now rising?
        if self.DTMultosc[0] > self.DTMultosc[-1]:
            self.nowrising = True
        else:
            self.nowrising = False
        # Is it local minimum?
        if self.wasfalling and self.nowrising:
            self.bottomed = True
        else:
            self.bottomed = False

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowStartDate and self.data.datetime.datetime() < self.params.backtestparms.TradeWindowEndDate:
                if self.bottomed:
                    # BUY, BUY, BUY!!! (with all possible default parameters)
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])

                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

        # In the market
        else:

            if self.dataclose[0] < self.chandelier_exit_val:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowEndDate:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL OUTSIDE TRADEWINDOW Ult, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

        # If it is the last bar of the data, close the positions.
        # Actually, one bar before the last to enter the order and execute
        if len(self.datas[0]) == self.datas[0].buflen()-1:
            if self.position:
                self.order = self.sell()
                self.log('Closed all trades on last day in data')

# Enter DTMUltOsc bottoms
# Exit OBVtrend turns down
class DTMUltOscOBVtrendStrategy(bt.Strategy):
    params = (
        ('fastmaperiod', 14),
        ('midmaperiod', 21),
        ('slowmaperiod', 50),
        ('backtestparms', None),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.high = self.datas[0].high
        self.chandelier_exit_val = bt.ind.Highest(self.high, period=22, plot=False) - 3 * bt.ind.ATR(
            period=22, plot = False)  # Stop at 3 ATRs below the highest high since entry

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.fastsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.fastmaperiod)
        self.midsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.midmaperiod)
        self.slowsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.slowmaperiod)

        # Create DTMUltimateOsc which is a ZLEMA smoothed UltimateOsc
        self.DTMultosc = DTM_Indicators.DTMUltOsc(self.datas[0])
        self.obv = DTM_Indicators.OnBalanceVolume(self.data)
        self.obvtrend = DTM_Indicators.OnBalanceVolumeTrend(self.data)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Determine if DTUMUltOsc is a local minimum
        # Was the indicator falling?
        if self.DTMultosc[-2] > self.DTMultosc[-1]:
            self.wasfalling = True
        else:
            self.wasfalling = False
        # Is it now rising?
        if self.DTMultosc[0] > self.DTMultosc[-1]:
            self.nowrising = True
        else:
            self.nowrising = False
        # Is it local minimum?
        if self.wasfalling and self.nowrising:
            self.bottomed = True
        else:
            self.bottomed = False

        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowStartDate and self.data.datetime.datetime() < self.params.backtestparms.TradeWindowEndDate:
                if self.bottomed:
                    # BUY, BUY, BUY!!! (with all possible default parameters)
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

        else:

            if self.obvtrend[0] == 0 and self.obvtrend[-1] == 1:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE OBVtrend %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowEndDate:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL OUTSIDE TRADEWINDOW Ult, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

        # If it is the last bar of the data, close the positions.
        # Actually, one bar before the last to enter the order and execute
        if len(self.datas[0]) == self.datas[0].buflen()-1:
            if self.position:
                self.order = self.sell()
                self.log('Closed all trades on last day in data')

# Enter 2x avg Vol when close is up and OBV pops and slow stochatstic > 50
# Exit two years after the trigger
class RAMThreeXVolUpStrategy(bt.Strategy):

    params = (
        ('fastmaperiod', 14),
        ('midmaperiod', 21),
        ('slowmaperiod', 50),
        ('backtestparms', None),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        '''
        # Add a MovingAverageSimple indicator
        self.fastsma = bt.indicators.StochasticSlow(
            self.datas[0].close, period=self.params.fastmaperiod)
        self.midsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.midmaperiod)
        self.slowsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.slowmaperiod)
        '''
        # Add additional indicators
        self.ThreeXAvgVolume = DTM_Indicators.ThreeXAvgVolumeUp(self.data)
        # self.obvmovobv = DTM_Indicators.OBV_MovOBV(self.data)
        self.obvdif = DTM_Indicators.OBVdif(self.data, plot=False)
        # self.obv = DTM_Indicators.OnBalanceVolume(self.data)
        self.obvpop = DTM_Indicators.OBVpop(self.data)
        # self.obvtrend = DTM_Indicators.OnBalanceVolumeTrend(self.data)
        self.slowstochastic = bt.indicators.StochasticSlow(self.data)
        self.aroon = bt.indicators.AroonIndicator(self.data)
        self.aroonosc = bt.indicators.AroonOscillator(self.data, plot=False)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Record triggers to the console
        if self.ThreeXAvgVolume == 1:
            self.log('Trigger, 3x Avg Vol obvdif: %.2f, Stochastic: %.2f, AroonOsc %.2f' %
                     (self.obvdif[0],
                      self.slowstochastic[0],
                      self.aroonosc[0]))

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowStartDate and self.data.datetime.datetime() < self.params.backtestparms.TradeWindowEndDate:
                if self.ThreeXAvgVolume == 1 and self.obvpop == 1 and self.slowstochastic[0]>50:
                    # BUY, BUY, BUY!!! (with all possible default parameters)
                    self.log('BUY CREATE 3x Avg Vol Close:, %.2f' % self.dataclose[0])
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

        else:
            # Sell if past the Exit date
            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowEndDate:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL OUTSIDE TRADEWINDOW Ult, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

       # If it is the last bar of the data, close the positions.
           # Actually, one bar before the last to enter the order and execute
        if len(self.datas[0]) == self.datas[0].buflen()-1:
            if self.position:
                self.order = self.sell()
                self.log('Closed all trades on last day in data')

# Enter 2x avg Vol when close is up and PVT pops and slow stochatstic > 50 and Gap Up
# Exit two years after the trigger
class RAMThreeXVolUpPVTGapStrategy(bt.Strategy):

    params = (
        ('fastmaperiod', 14),
        ('midmaperiod', 21),
        ('slowmaperiod', 50),
        ('backtestparms', None),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        '''
        # Add a MovingAverageSimple indicator
        self.fastsma = bt.indicators.StochasticSlow(
            self.datas[0].close, period=self.params.fastmaperiod)
        self.midsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.midmaperiod)
        self.slowsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.slowmaperiod)
        '''
        # Add additional indicators
        self.ThreeXAvgVolume = DTM_Indicators.ThreeXAvgVolumeUp(self.data)
        self.slowstochastic = bt.indicators.StochasticSlow(self.data)
        self.pvt = DTM_Indicators.PVT(self.data)
        self.PVTpop = DTM_Indicators.PVTpop(self.data)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Record triggers to the console
        if self.ThreeXAvgVolume == 1:
            self.log('Trigger, 3x Avg Vol - Stochastic: %.2f, PVTpop %.2f' %
                     (self.slowstochastic[0],
                      self.PVTpop[0]))

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowStartDate and self.data.datetime.datetime() < self.params.backtestparms.TradeWindowEndDate:
                if self.ThreeXAvgVolume == 1 and self.PVTpop == 1 and self.slowstochastic[0]>50 and self.data.open[0] > self.data.close[-1]:
                    # BUY, BUY, BUY!!! (with all possible default parameters)
                    self.log('BUY CREATE 3x Avg Vol Close:, %.2f' % self.dataclose[0])
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

        else:
            # Sell if past the Exit date
            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowEndDate:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL OUTSIDE TRADEWINDOW Ult, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

       # If it is the last bar of the data, close the positions.
           # Actually, one bar before the last to enter the order and execute
        if len(self.datas[0]) == self.datas[0].buflen()-1:
            if self.position:
                self.order = self.sell()
                self.log('Closed all trades on last day in data')

# Trade Enabled when 2x avg Vol when close is up and OBV pops and slow stochatstic > 50
# Enter: DTMUltOsc bottoms
# Exit OBVtrend
class RAMThreeXVolUpPVTGapDaveStrategy(bt.Strategy):
    params = (
        ('fastmaperiod', 14),
        ('midmaperiod', 21),
        ('slowmaperiod', 50),
        ('backtestparms', None),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.high = self.datas[0].high
        self.chandelier_exit_val = bt.ind.Highest(self.high, period=22, plot=False) - 3 * bt.ind.ATR(
            period=22, plot = False)  # Stop at 3 ATRs below the highest high since entry


        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        '''
        # Add a MovingAverageSimple indicator
        self.fastsma = bt.indicators.StochasticSlow(
            self.datas[0].close, period=self.params.fastmaperiod)
        self.midsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.midmaperiod)
        self.slowsma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.slowmaperiod)
        '''
        # Add additional indicators
        self.ThreeXAvgVolume = DTM_Indicators.ThreeXAvgVolumeUp(self.data)
        self.slowstochastic = bt.indicators.StochasticSlow(self.data)
        self.TradeEnable = False
        # Create DTMUltimateOsc which is a ZLEMA smoothed UltimateOsc
        self.DTMultosc = DTM_Indicators.DTMUltOsc(self.datas[0])
        self.pvt = DTM_Indicators.PVT(self.data)
        self.PVTpop = DTM_Indicators.PVTpop(self.data)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Enable trading on RAM's trigger
        if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowStartDate and self.data.datetime.datetime() < self.params.backtestparms.TradeWindowEndDate:
            if self.ThreeXAvgVolume == 1 and self.PVTpop == 1 and self.slowstochastic[0]>50 and self.data.open[0] > self.data.close[-1]:
                self.TradeEnable = True
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE TradeEnabled, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        # Determine if DTUMUltOsc is a local minimum
        # Was the indicator falling?
        if self.DTMultosc[-2] > self.DTMultosc[-1]:
            self.wasfalling = True
        else:
            self.wasfalling = False
        # Is it now rising?
        if self.DTMultosc[0] > self.DTMultosc[-1]:
            self.nowrising = True
        else:
            self.nowrising = False
        # Is it local minimum?
        if self.wasfalling and self.nowrising:
            self.bottomed = True
        else:
            self.bottomed = False

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowStartDate and self.data.datetime.datetime() < self.params.backtestparms.TradeWindowEndDate:
                if self.bottomed and self.TradeEnable:
                    # BUY, BUY, BUY!!! (with all possible default parameters)
                    self.log('BUY CREATE UltOsc, %.2f' % self.dataclose[0])
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

        else:

            if self.dataclose[0] < self.chandelier_exit_val:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE Chandelier, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowEndDate:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL OUTSIDE TRADEWINDOW Ult, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

        # If it is the last bar of the data, close the positions.
        # Actually, one bar before the last to enter the order and execute
        if len(self.datas[0]) == self.datas[0].buflen()-1:
            if self.position:
                self.order = self.sell()
                self.log('Closed all trades on last day in data')

class rsiStrategy(bt.Strategy):
    params = (
        ('backtestparms', None),
    )
    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.high = self.datas[0].high
        self.chandelier_exit_val = bt.ind.Highest(self.high, period=22) - 3 * bt.ind.ATR(
            period=22)  # Stop at 3 ATRs below the highest high since entry

        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=21)

    def next(self):
        if not self.position:
            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowStartDate and self.data.datetime.datetime() < self.params.backtestparms.TradeWindowEndDate:
                if self.rsi < 40:
                    self.buy()
        else:
            if self.rsi > 70:
                self.sell()
                
            if self.data.datetime.datetime() > self.params.backtestparms.TradeWindowEndDate:
                self.sell()
                
       # If it is the last bar of the data, close the positions.
           # Actually, one bar before the last to enter the order and execute
        if len(self.datas[0]) == self.datas[0].buflen()-1:
            if self.position:
                # self.log('Closed all trades on last day in data')
                self.order = self.sell()
                