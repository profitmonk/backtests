# 
#
# Original Backtrader code can be found here.  https://github.com/mementum/backtrader
#


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
# Module imports
#
# Import my code
#
import Backtest
import TckrOHLCdata
import ManageTickerList
import ProcessFinData
import FinancialData
import FinancialDataProfitmonk
import DTM_Strategies
import DTM_Indicators
import DTM_Sizers
import SP500


from datetime import datetime
from datetime import timedelta
import time
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

import numpy as np
import pandas as pd
import math
# import matplotlib as plt
# plt.use('TkAgg')
# import matplotlib as plt2
# plt.use('Agg')   #https://github.com/rtfd/readthedocs.org/issues/1195
# plt2.use('Agg')

#
# Import the backtrader platform
#
import backtrader as bt
from backtrader.utils.py3 import filter, string_types, integer_types
from backtrader import date2num
import backtrader.feeds as btfeeds


###############################
# Sizers
###############################
class maxRiskSizer(bt.Sizer):
    '''
    Returns the number of shares rounded down that can be purchased for the
    max risk tolerance
    '''
    params = (('risk', 0.1),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy == True:
            size = math.floor((cash * self.p.risk) / data[0])
        else:
            size = math.floor((cash * self.p.risk) / data[0]) * -1
        return size

def DataFeedExamples():
    # data1 is used to add 'Prediction' to the datafeed.
    # csv file must be modified to add the prediction to the openinterest column.
    # prediction can be accessed as self.datas[0].openinterest
    fname = os.getcwd() + '//' + data_path + '//' + stock_tckr + 'pred.csv'
    data1 = btfeeds.GenericCSVData(
        dataname = fname,
        # Do not pass values before this date
        fromdate = datetime(2014, 1, 1),
        # Do not pass values after this date
        todate = datetime(2016, 1, 1),
        reverse=False,

        dtformat=('%m/%d/%Y'),

        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        adjclose=5,
        volume=6,
        openinterest=7
    )
    # Example loading the data from PandasDataFrame
    data2 = btfeeds.PandasData(
        dataname=df,
        fromdate = datetime(2014, 1, 1),
        todate = datetime(2016, 1, 1)
    )

def SetOHLCLastDate(BacktestParms):
# Determine which variable has the latest date
# If the date is a weekend, set it to Friday
# If the date is today, set it back one day so we know there is a close
# Set BacktestParms.end to the latest date so the data is there to process.
    def ManageDates(date_dt):
        if date_dt.date() == datetime.today().date():
            date_dt = date_dt + timedelta(days = -1)   # Closing data only goes to the last full day
        # date is a weekend?
        if date_dt.weekday() > 4:
            # set to Friday
            if date_dt.weekday() == 5: # If Saturday
                date_dt = date_dt + timedelta(days=-1)
            if date_dt.weekday() == 6: # If Sunday
                date_dt = date_dt + timedelta(days=-2)
        # else:
        #     # set it back ten days.  Yahoo historical is 8 days behind
        #     date_dt = date_dt + timedelta(days=-10)
        return date_dt, date_dt
        
    # If TradeWindowEndDate is after today.  Set to today
    if BacktestParms.TradeWindowEndDate > datetime.today():
        BacktestParms.TradeWindowEndDate = datetime.today()
        
    # Which date is latest?
    if BacktestParms.end >= BacktestParms.btend and BacktestParms.end >= BacktestParms.TradeWindowEndDate:
        latest_dt = BacktestParms.end
    if BacktestParms.btend >= BacktestParms.end and BacktestParms.btend >= BacktestParms.TradeWindowEndDate:
        latest_dt = BacktestParms.btend
    if BacktestParms.TradeWindowEndDate >= BacktestParms.btend  and BacktestParms.TradeWindowEndDate >= BacktestParms.end:
        latest_dt = BacktestParms.TradeWindowEndDate
    BacktestParms.end, BacktestParms.btend = ManageDates(latest_dt)
    return(BacktestParms)

def MultipleTckrs(BacktestParms, FinDataTrade_df):

    # Fundamental data comes from FinancialDataModelling.com
    # Financial data is generated in FinancialData.py
    # WhaleWhisdom data is generated in the WhaleWhisdom project.
    # Backtest collects results of the strategy testing
    # Tried collecting all the results and merging with Financial/Whale data at the end.  It crashes.
    # Now, collect results for each ticker.  Merge with Financial and append it to the final result
    #
    StrategyList = [
                    # DTM_Strategies.TestStrategy,
                    # DTM_Strategies.BBandsStrategy,
                    DTM_Strategies.BuyHoldStrategy,
                    # DTM_Strategies.DTMUltOscStrategy,
                    # DTM_Strategies.DTMUltOscOBVtrendStrategy,
                    # DTM_Strategies.RAMThreeXVolUpPVTGapStrategy,
                    # DTM_Strategies.rsiStrategy
                    ]

    BacktestParms.display_chart = False
    Compile_Results_df = pd.DataFrame(index=range(1), columns=['Tckr'])  # Create the dataframe.  Columns are filled out later.
    PreviousTckr = ''
    start_time = time.time()
    # FinDataTrade_df = FinDataTrade_df[0:10]
    # FinDataTrade_df = FinDataTrade_df.iloc[735:740]
    
    for TckrCnt in range(len(FinDataTrade_df)):
        BacktestParms.stock_tckr = FinDataTrade_df.loc[TckrCnt,'Tckr']
        BacktestParms.TradeWindowStartDate = FinDataTrade_df.loc[TckrCnt,'TradeWindowStartDate_dt']
        BacktestParms.TradeWindowEndDate = FinDataTrade_df.loc[TckrCnt,'TradeWindowEndDate_dt']
        BacktestParms = SetOHLCLastDate(BacktestParms)
        # Download OHLC data once.  
        # Detect change in tckr
        if PreviousTckr != BacktestParms.stock_tckr:
            #On change, download OHLC data
            dfadjohlc, DataReaderError = TckrOHLCdata.Get_data_screener(BacktestParms)
            PreviousTckr = BacktestParms.stock_tckr
            if DataReaderError:
                print('Yahoo and FMD data read error.  Move on')
                continue
        # Check if the OHLC data fits in the tradewindow
        if dfadjohlc.index.min() > BacktestParms.TradeWindowStartDate or dfadjohlc.index.max() <  BacktestParms.TradeWindowEndDate:
            print('OHLC data not available for the trade window')
            continue
        Results_df = pd.DataFrame(index=range(1), columns=['Tckr'])  # Create a fresh dataframe.  Columns are filled out later.        
 
                   
        for BacktestParms.strategy in StrategyList:
            print('-------------------------')
            print('TckrCnt', TckrCnt, 'of', len(FinDataTrade_df), '(', round(TckrCnt/len(FinDataTrade_df)*100,1),'%)')
            print(BacktestParms.stock_tckr)
            m, s = divmod(time.time() - start_time, 60)
            h, m = divmod(m, 60)
            print(f'Elapsed run time {int(h):d}:{int(m):02d}:{int(s):02d}')
            # print('bt start     ', BacktestParms.btstart, '   bt end     ', BacktestParms.btend)
            print('TradeWindow start', BacktestParms.TradeWindowStartDate, '   TradeWindow end', BacktestParms.TradeWindowEndDate)            
            Results_df = Backtest.Backtest(BacktestParms, dfadjohlc, Results_df)
            BacktestParms.iteration = BacktestParms.iteration + 1
        
        # Don't merge if there were no results
        if len(Results_df.columns) != 1:
            # There were results so merge the fundamental data for this ticker and append to the results
            df_result = pd.merge(Results_df, FinDataTrade_df, left_on=['Tckr', 'TradeWindowStartDate', 'TradeWindowEndDate'], right_on = ['Tckr', 'TradeWindowStartDate_str', 'TradeWindowEndDate_str'])
            Compile_Results_df = Compile_Results_df.append(df_result)
    
        fname = os.getcwd() + '//' + BacktestParms.data_path + '//' + BacktestParms.result_fname
        Compile_Results_df.to_csv(fname)
    
    # Drop the first row
    Compile_Results_df = Compile_Results_df[1:]
    Compile_Results_df = Compile_Results_df.reset_index(drop=True)
    fname = os.getcwd() + '//' + BacktestParms.data_path + '//CompiledResults.csv'
    Compile_Results_df.to_csv(fname)            
    return Compile_Results_df

def main():
    # Variable definition
    # ------------- INPUT -------------
    class BacktestParm:

        # start / end are used for requesting data from Yahoo.
        # btstart / bt end is where backtrader starts and stops.  Main point is to run backtrader before the TradeWindow start to get indicators stable
        # TradeWindow Start / End is used in the strategy to programitacally turn on and off windows of time i.e on when EPS >0, off otherwise  

        start = datetime(2000, 1, 1)   # Start date of raw data to be read from Yahoo.com
        end = datetime(2021, 1, 1)     # End date of raw data to be read from Yahoo.com
        btstart = datetime(2000, 1, 1) # Start date of Backtrader (bt) analysis
        btend = datetime(2021, 1, 1)   # End date of Backtrader (bt) analysis
        TradeWindowStartDate = datetime(2009, 8, 14)    # Date to enable trading
        TradeWindowEndDate = datetime(2021, 6, 1)      # Date to disable trading        
        btTimeDesc = 'Default'         # Short text to describe time frame of Backtrader analysis 
        initial_cash = 50000
        stock_tckr = 'AMZN'            # Ticker to process
        data_path = "stock_data"       # Directory under the current directory to store stock data csv files
        result_fname = "BackTraderResults.csv"
        generate_prediction = False    # True, Generate.  False, use existing data
        display_chart = True
        strategy = DTM_Strategies.BuyHoldStrategy      # Set a default strategy
        ppf_percent = 0.8              # Percentage point on the bell curve for calculating the strike price
        std_period = 15                # Period used to calculate standard deviation for option pricing
        iteration = 0                  # Current iteration when doing multipl strategies
        WhaleClass = 'TopTen'          # Class from WhaleWisdom analysis (TopTen, New, inc, ...)
        FirstDateFinData = 2000        # Go back to Jan of this year for financial data
        LastDateFinDate = 2020         # Go to Dec of this year for financial data


    BacktestParms = BacktestParm()
    
    TckrList = ManageTickerList.GetTckrList(BacktestParms, VolThresh = 100000, PriceThresh = 3) # Will update the list once/month

    # Force a smaller list for development
    # TckrList = ['WMPN', 'WMS', 'WMT']
    '''
    TckrList = ['AMZN', 'AAPL', 'GOOG', 'MMM', 'AXP', 'T', 'BA', 'CAT', 'CVX', 'CSCO', 'XOM', 'GE', 'GS', 'HD', 'INTC',
                'IBM', 'JNJ', 'JPM', 'MCD', 'MRK', 'MSFT', 'NKE', 'PFE', 'PG', 'KO', 'TRV', 'UTX', 'UNH', 'VZ', 'WMT']
    '''
    
    FinData_df = FinancialDataProfitmonk.GetFinancialData(TckrList, BacktestParms)      # Erase StockUnivers/FundamentalData.csv if you want to update
    
    FinDataTrade_df = ProcessFinData.Top5perFinData(BacktestParms, FinData_df)  
     
    FinDataTrade_df = ProcessFinData.TradeWindowDates(BacktestParms, FinDataTrade_df)
  
    Results_df = MultipleTckrs(BacktestParms, FinDataTrade_df)
      
    print(Results_df)
    fname = os.getcwd() + '//' + BacktestParms.data_path + '//' + BacktestParms.result_fname
    Results_df.to_csv(fname)
 
    # ManageData(BacktestParms)
    
    return 

if __name__ == '__main__':
    main()