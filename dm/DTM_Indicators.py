    ######################################
    #
    # Covered Call Strategies
    #  Defines Backtrader Strategy classes 
    #  Strategies are all Covered Call 
    #
    ######################################
#
# Module imports
#
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import math     # Super smoother

import numpy as np
import pandas as pd

import backtrader as bt
from backtrader.utils.py3 import filter, string_types, integer_types
from backtrader import date2num
import backtrader.feeds as btfeeds


###############################
# Indicators
###############################
class SwingInd(bt.Indicator):
    '''
    A Simple swing indicator that measures swings (the lowest/highest value)
    within a given time period.
    Coding example only.  Detects swings after the fact.
    '''
    lines = ('swings', 'signal')
    params = (('period', 7),)

    def __init__(self):

        # Set the swing range - The number of bars before and after the swing
        # needed to identify a swing
        self.swing_range = (self.p.period * 2) + 1
        self.addminperiod(self.swing_range)

    def next(self):
        # Get the highs/lows for the period
        highs = self.data.high.get(size=self.swing_range)
        lows = self.data.low.get(size=self.swing_range)
        # check the bar in the middle of the range and check if greater than rest
        if highs.pop(self.p.period) > max(highs):
            self.lines.swings[-self.p.period] = 1  # add new swing
            self.lines.signal[0] = 1  # give a signal
        elif lows.pop(self.p.period) < min(lows):
            self.lines.swings[-self.p.period] = -1  # add new swing
            self.lines.signal[0] = -1  # give a signal
        else:
            self.lines.swings[-self.p.period] = 0
            self.lines.signal[0] = 0

class OverUnderMovAv(bt.Indicator):
    lines = ('overunder',)
    params = dict(period=20, movav=bt.indicators.MovAv.Simple)

    def __init__(self):
        movav = self.p.movav(self.data, period=self.p.period)
        self.l.overunder = bt.Cmp(movav, self.data)

class DTMUltOsc(bt.Indicator):
    lines = ('DTMUltOsc',)
    params = dict(period=10, zlema=bt.indicators.ZeroLagExponentialMovingAverage,
                  UltOsc=bt.indicators.UltimateOscillator)

    def __init__(self):
        dtmult = self.p.UltOsc(self.data)
        self.l.DTMUltOsc = self.p.zlema(dtmult, period=self.p.period)

class DTMUltOscSS(bt.Indicator):
    lines = ('DTMUltOscSS',)
    params = dict(period=10, SSperiod=10, UltOsc=bt.indicators.UltimateOscillator)

    def __init__(self):
        self.dtmult = self.p.UltOsc(self.data)
        ## Calculate the two pole super smooter
        self.a1 = math.exp(-1.414 * 3.14159 / self.p.SSperiod)
        self.b1 = 2 * self.a1 * math.cos(1.414 * 180 / self.p.SSperiod)
        self.coef2 = self.b1
        self.coef3 = -self.a1 * self.a1
        self.coef1 = 1 - self.coef2 - self.coef3
        self.l.DTMUltOscSS[0] = self.coef1 * self.dtmult + self.coef2 * self.l.DTMUltOscSS(-1) + self.coef3 * self.l.DTMUltOscSS(-2)

class ThreeXAvgVolume(bt.Indicator):
    lines = ('ThreeXVolAvg',)

    params = dict(period=20, movvol=bt.indicators.MovAv.Simple)

    def __init__(self):
        self.movvol = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.p.period)
    
    def next(self):
        
        if self.data.volume[0] > 2 * self.movvol:
            self.l.ThreeXVolAvg[0] = 1
        else:
            self.l.ThreeXVolAvg[0] = 0

class ThreeXAvgVolumeUp(bt.Indicator):
    lines = ('ThreeXVolAvg',)

    params = dict(period=20, movvol=bt.indicators.MovAv.Simple)

    def __init__(self):
        self.movvol = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.p.period)
    
    def next(self):
        
        if self.data.volume[0] > 2 * self.movvol and self.data.close[0] > self.data.close[-1]:
            self.l.ThreeXVolAvg[0] = 1
        else:
            self.l.ThreeXVolAvg[0] = 0
            
class OBV_MovOBV(bt.Indicator):
    lines = ('OBV', 'movOBV')

    params = dict(OBVperiod=50, movOBV=bt.indicators.MovAv.Simple)

    def __init__(self):
        self.l.OBV = OnBalanceVolume(self.data)
        self.l.movOBV = bt.indicators.SimpleMovingAverage(self.OBV, period=self.p.OBVperiod)

class OBVdif(bt.Indicator):
    lines = ('OBVdif',)

    params = dict(OBVperiod=50, OBVmult=3, movobv=bt.indicators.MovAv.Simple)

    def __init__(self):
        self.obv = OnBalanceVolume(self.data)
        self.movobv = bt.indicators.SimpleMovingAverage(self.obv, period=self.p.OBVperiod)
        self.obvdif = self.obv - self.movobv

    def next(self):
        self.l.OBVdif[0] = self.obvdif[0] / self.obvdif[-1]

class OBVpop(bt.Indicator):
    lines = ('OBVpop',)

    params = dict(thresh=1.5)

    def __init__(self):
        self.obvdif = OBVdif(self.data)
    
    def next(self):
        
        if self.obvdif[0] > self.p.thresh:
            self.l.OBVpop[0] = 1
        else:
            self.l.OBVpop[0] = 0   

class PVT(bt.Indicator):
    lines =('PVT',)
    
    plotlines = dict(
        PVT=dict(
            _name='PVT',
            color='blue',
        )
    )
    
    def nextstart(self):
        # We need to use next start to provide the initial value. This is because
        # we do not have a previous value for the first calcuation. These are
        # known as seed values.
       PVT = self.lines.PVT
       PVT[0] = 1               # Arbitrary starting value
       
    def next(self):
        # [((CurrentClose - PreviousClose) / PreviousClose) x Volume] + PreviousPVT
        # self.l.PVT[0] = (bt.DivByZero((self.data.close[0]-self.data.close[-1]), (self.data.close[-1]), zero=0) * self.data.volume[0]) + self.PVT[-1]
        if self.data.close[-1] == 0:
            self.l.PVT[0] = self.l.PVT[-1]
        else:
            self.l.PVT[0] = (((self.data.close[0]-self.data.close[-1])/self.data.close[-1]) * self.data.volume[0]) + self.PVT[-1]

class PVTpopTest(bt.Indicator):
    lines =('PVTpop','AwesomeOsc')
    
    params = dict(thresh=.25)
    
    plotlines = dict(
        PVTpop=dict(
            _name='PVTpop',
            color='blue',
            alpha = .5,
        ),
        PVTroc=dict(
            _name='PVTroc',
            color='blue',
            # alpha = .5,
        )
    )
    
    def __init__(self):
        self.pvt = PVT(self.data)
    
    def next(self):       
        # Little complicated because the value can go below 0
        # If moving negative to positive take the absolute value
        if self.pvt[-1] < 0:
            self.l.PVTroc[0] = (self.pvt[0] - self.pvt[-1]) / abs(self.pvt[-1])
        else:
            self.l.PVTroc[0] = (self.pvt[0] - self.pvt[-1]) / self.pvt[-1]

        # Logical pop up when the roc > thresh
        if self.PVTroc[0] > self.p.thresh:
            self.l.PVTpop[0] = 5
        elif self.PVTroc[0] < -self.p.thresh:
            self.l.PVTpop[0] = -5 
        else:
            self.l.PVTpop[0] = 0      
            
class PVTpop(bt.Indicator):
    lines =('PVTpop','PVTroc')
    
    params = dict(thresh=.25)
    
    plotlines = dict(
        PVTpop=dict(
            _name='PVTpop',
            color='blue',
            alpha = .5,
        ),
        PVTroc=dict(
            _name='PVTroc',
            color='blue',
            # alpha = .5,
        )
    )
    
    def __init__(self):
        self.pvt = PVT(self.data)
    
    def next(self):       
        # Little complicated because the value can go below 0 and PVT can = 0 (div 0)
        # If PVT = 0, just use the last value
        # If moving negative to positive take the absolute value
        if self.pvt[-1] == 0:
            self.l.PVTroc[0] = self.PVTroc[-1]
        elif self.pvt[-1] < 0 and self.pvt[0] > 0:
                self.l.PVTroc[0] = abs((self.pvt[0] - self.pvt[-1]) / self.pvt[-1])
        else:
            self.l.PVTroc[0] = (self.pvt[0] - self.pvt[-1]) / self.pvt[-1]

        # Logical pop up when the roc > thresh
        if self.PVTroc[0] > self.p.thresh:
            self.l.PVTpop[0] = 5
        else:
            self.l.PVTpop[0] = 0  

class PVTroc(bt.Indicator):
    lines =('PVTroc',)
    
    params = dict(thresh=.25)
    
    plotlines = dict(
        PVTroc=dict(
            _name='PVTroc',
            color='blue',
            # alpha = .5,
        )
    )
    
    def __init__(self):
        self.pvt = PVT(self.data)
    
    def next(self):       
        # Little complicated because the value can go below 0
        # If moving negative to positive take the absolute value
        if self.pvt[-1] < 0 and self.pvt[0] > 0:
            self.l.PVTroc[0] = abs((self.pvt[0] - self.pvt[-1]) / self.pvt[-1])
        else:
            self.l.PVTroc[0] = (self.pvt[0] - self.pvt[-1]) / self.pvt[-1]

class returns(bt.Indicator):
    lines = ('returns',)
  
    def next(self):
        self.l.returns[0] = (self.data.close[0] - self.data.close[-1])/self.data.close[-1]


class GapUp(bt.Indicator):
    lines = ('GapUp',)
  
    def next(self):
        
        if self.data.open[0] > self.data.close[-1]:
            self.l.GapUp[0] = 1
        else:
            self.l.GapUp[0] = 0
'''
Center of Gravity
Source: https://www.motivewave.com/studies/center_of_gravity.htm

x = 0;
for (i = index-cogPeriod+1; i++)
    iprice = price[i];
    sumNum = sumNum + (iprice * (x + 1));
    sumDen = sumDen + iprice;
    x++;
end;
cog = 100 * sumNum / sumDen;
sig = ma(index, method, sigPeriod, cog);
//Signals
sell = crossedBelow(cog, sig) AND cog MT topGuide  AND (cog MT highSell);
buy = crossedAbove(cog, sig) AND cog LT bottGuide  AND (cog LT lowBuy);

Numerator = sum of Price[i] (i+1)
Denominator = sum of Price[i]
Where Price[i] is the close of the ith bar back.  Price[0] is the current close
'''
# Center of Gravity
class CenterOfGravity(bt.Indicator):
    lines = ('COG',)
    params = dict(period=10)
    
    plotlines = dict(
        PVTpop=dict(
            _name='COG',
            color='blue',
            # alpha = .5,
        ),
    )
    
    def __init__(self):
        # sma = bt.indicators.SimpleMovingAverage(self.data, self.params.period)
        self.addminperiod(self.p.period+1)
        
    def next(self):
        self.numerator = 0
        self.denominator = 0
        for i in range(self.params.period):
            self.numerator = self.numerator + self.data.close[-i] * (i+1)
            self.denominator = self.denominator + self.data.close[-i]
        self.l.COG[0] = self.numerator / self.denominator * 100

'''
Author: www.backtest-rookies.com

MIT License

Copyright (c) 2018 backtest-rookies.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

class OnBalanceVolume(bt.Indicator):
    '''
    REQUIREMENTS
    ----------------------------------------------------------------------
    Investopedia:
    ----------------------------------------------------------------------
    https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:on_balance_volume_obv

    1. If today's closing price is higher than yesterday's closing price,
       then: Current OBV = Previous OBV + today's volume

    2. If today's closing price is lower than yesterday's closing price,
       then: Current OBV = Previous OBV - today's volume

    3. If today's closing price equals yesterday's closing price,
       then: Current OBV = Previous OBV
    ----------------------------------------------------------------------
    '''

    alias = 'OBV'
    lines = ('obv',)

    plotlines = dict(
        obv=dict(
            _name='OBV',
            color='purple',
            # alpha=0.50
        )
    )

    def __init__(self):

        # Plot a horizontal Line
        self.plotinfo.plotyhlines = [0]

    def nextstart(self):
        # We need to use next start to provide the initial value. This is because
        # we do not have a previous value for the first calcuation. These are
        # known as seed values.

        # Create some aliases
        c = self.data.close
        v = self.data.volume
        obv = self.lines.obv

        if c[0] > c[-1]:
            obv[0] = v[0]
        elif c[0] < c[-1]: 
            obv[0] = -v[0] 
        else: 
            obv[0] = 0 
        
    def next(self): # Aliases to avoid long lines c = self.data.close v = self.data.volume obv = self.lines.obv 
        # Create some aliases
        c = self.data.close
        v = self.data.volume
        obv = self.lines.obv
    
        if c[0] > c[-1]:
            obv[0] = obv[-1] + v[0]
        elif c[0] < c[-1]:
            obv[0] = obv[-1] - v[0]
        else:
            obv[0] = obv[-1]
            
class OnBalanceVolumeTrend(bt.Indicator):

    alias = 'OBVtrend'
    lines = ('obvtrend',)

    plotlines = dict(
        obv=dict(
            _name='OBVtrend',
            color='purple',
            alpha=0.50
        )
    )

    def __init__(self):

        # On balance voume indicator
         self.obv = OnBalanceVolume(self.data)

        
    def next(self): # Aliases to avoid long lines c = self.data.close v = self.data.volume obv = self.lines.obv 
        # Create some aliases
        obv = self.obv
        obvtrend = self.lines.obvtrend
        
        # Three days falling means down trend
        if obv[-3] > obv[-2] and obv[-2] > obv[-1] and obv[-1] > obv[0]:
            obvtrend[0] = 0
        # Three days increasing means up trend
        elif obv[-3] < obv[-2] and obv[-2] < obv[-1] and obv[-1] < obv[0]:
            obvtrend[0] = 1
        # Same state
        else:
            obvtrend[0] = obvtrend[-1]
        
class OnBalanceVolumeTrend2day(bt.Indicator):

    alias = 'OBVtrend'
    lines = ('obvtrend',)

    plotlines = dict(
        obv=dict(
            _name='OBVtrend',
            color='purple',
            alpha=0.50
        )
    )

    def __init__(self):

        # On balance voume indicator
         self.obv = OnBalanceVolume(self.data)

        
    def next(self): # Aliases to avoid long lines c = self.data.close v = self.data.volume obv = self.lines.obv 
        # Create some aliases
        obv = self.obv
        obvtrend = self.lines.obvtrend
        
        # Two days falling means down trend
        if obv[-2] > obv[-1] and obv[-1] > obv[0]:
            obvtrend[0] = 0
        # Two days increasing means up trend
        elif obv[-2] < obv[-1] and obv[-1] < obv[0]:
            obvtrend[0] = 1
        # Same state
        else:
            obvtrend[0] = obvtrend[-1]

class PVTTrend3days(bt.Indicator):

    alias = 'PVTtrend'
    lines = ('PVTtrend',)

    def __init__(self):

        # PVT indicator
         self.PVT = PVT(self.data)

        
    def next(self):
        # Create some aliases
        PVT = self.PVT
        PVTtrend = self.lines.PVTtrend
        
        # Three days falling means down trend
        if PVT[-3] > PVT[-2] and PVT[-2] > PVT[-1] and PVT[-1] > PVT[0]:
            PVTtrend[0] = 0
        # Three days increasing means up trend
        elif PVT[-3] < PVT[-2] and PVT[-2] < PVT[-1] and PVT[-1] < PVT[0]:
            PVTtrend[0] = 1
        # Same state
        else:
            PVTtrend[0] = PVTtrend[-1]

