# execfile('TckrOHLCdata.py')
#
# Original source from here appears to work well
# https://www.kaggle.com/pablocastilla/predict-stock-prices-with-lstm
#
# Generates the prediction based on LSTM and writes to a dataframe and csv file.
#

import FinDataHistPrices

import numpy as np
import os.path
import pandas as pd
import pandas_datareader.data as web
from sklearn.metrics import mean_squared_error, classification_report
from sklearn import preprocessing
from sklearn.preprocessing import Normalizer, MinMaxScaler, RobustScaler  # Scaling
from sklearn.decomposition import FastICA                                 # Scaling
import scipy                                                              # Scaling
import matplotlib.pylab as plt
#import matplotlib.pylab as plt2
from datetime import datetime
from datetime import timedelta
import time

import tensorflow as tf
from tensorflow import keras
#from keras import Dense, Activation
#from tensorflow.keras import layers
#from tensorflow.keras.models import Sequential, load_model
#from tensorflow.keras.layers.recurrent import LSTM, GRU

import backtrader as bt

######################################
# Get data
######################################
def Get_data(BacktestParms, pred_len):

    #
    # Routine to check the integrity of the data
    #
    def is_number(num):
        for a in str(num):
            if not a.isdigit() and a != '.':
                return 0
        return float(num)
    #
    # Confirm the directory exists and create if it doesn't
    #
    if not os.path.exists(BacktestParms.data_path):
        print("Get_data - os.path does not exist, created it")
        os.mkdir(BacktestParms.data_path)

    tckrfname = os.getcwd() + '//' + BacktestParms.data_path + '//' + BacktestParms.stock_tckr + '.csv'
    if os.path.isfile(tckrfname):
        print("Get_data - Files exists and are readable")
        #
        # Read the file
        #
        df = pd.read_csv(tckrfname, parse_dates=True, index_col=0)
        # Limit the data to the date range
        df = df[(df.index > BacktestParms.start) & (df.index <= BacktestParms.end)]
    else:
        print("Get_data - Either files are missing or not readable")
        #
        # Get the stock data from 'Yahoo' and write to a file.
        #
        df = web.DataReader(BacktestParms.stock_tckr, 'yahoo', BacktestParms.start, BacktestParms.end)
                            # If today's date in the filename
                            #today = dt.date.today()
                            #file_name = BacktestParms.stock_tckr + '_stock_%s.csv' % today
                            #df.to_csv(file_name)
        df.to_csv(tckrfname)
    return df
######################################
# Get data
######################################
def Get_data_simple(BacktestParms, pred_len):

    #
    # Routine to check the integrity of the data
    #
    def is_number(num):
        for a in str(num):
            if not a.isdigit() and a != '.':
                return 0
        return float(num)
    #
    # Confirm the directory exists and create if it doesn't
    #
    if not os.path.exists(BacktestParms.data_path):
        print("Get_data - os.path does not exist, created it")
        os.mkdir(BacktestParms.data_path)

    tckrfname = os.getcwd() + '//' + BacktestParms.data_path + '//' + BacktestParms.stock_tckr + '.csv'
    if os.path.isfile(tckrfname):
        print("Get_data - Files exists and are readable")
        #
        # Read the file
        #
        df = pd.read_csv(tckrfname, parse_dates=True, index_col=0)
        # Limit the data to the date range
        df = df[(df.index > BacktestParms.start) & (df.index <= BacktestParms.end)]
    else:
        print("Get_data - Either files are missing or not readable")
        #
        # Get the stock data from 'Yahoo' and write to a file.
        #
        df = web.DataReader(BacktestParms.stock_tckr, 'yahoo', BacktestParms.start, BacktestParms.end)
                            # If today's date in the filename
                            #today = dt.date.today()
                            #file_name = BacktestParms.stock_tckr + '_stock_%s.csv' % today
                            #df.to_csv(file_name)
        df.to_csv(tckrfname)
    # if df.index.min() > BacktestParms.start:
    #     error = 1
    #     return df, error
    #
    #  df now contains something like this
    #
    #                    Open       High        Low      Close      Volume      Adj Close
    #   Date
    #   2004-08-19  50.050049  52.082081  48.028027  50.220219      4465900     50.220219
    #
    df['Open'] = [is_number(a) for a in df['Open']]
    df['High'] = [is_number(a) for a in df['High']]
    df['Low'] = [is_number(a) for a in df['Low']]
    df['Close'] = [is_number(a) for a in df['Close']]
    df['Volume'] = [is_number(a) for a in df['Volume']]
    df['Adj Close'] = [is_number(a) for a in df['Adj Close']]

    # Reverse the order.  Oldest data at the top
    #df = df.iloc[::-1]
        #
    # Adj the O, H, L to the adjClose
    #
    def calculate_adj(row, Adj_C, C, Col):
        return row[Adj_C] / row[C] * row[Col]

    df['Adj Open'] = df.apply(calculate_adj, args=('Adj Close', 'Close', 'Open'), axis=1)
    df['Adj High'] = df.apply(calculate_adj, args=('Adj Close', 'Close', 'High'), axis=1)
    df['Adj Low'] = df.apply(calculate_adj, args=('Adj Close', 'Close', 'Low'), axis=1)
    #
    # Create OHLC for BacktestParms.stock_tckr using Adj OHLC
    #
    df = df.filter(['Adj Open', 'Adj High', 'Adj Low', 'Close', 'Adj Close', 'Volume'], axis=1)
    # Backtrader requires column names = Open, High, Low, Close, Adj Close, Volume
    df = df.rename(columns={'Adj Open': 'Open', 'Adj High': 'High', 'Adj Low': 'Low', 'Close': 'Close',
                                    'Adj Close': 'Adj Close', 'Volume': 'Volume'})
    #
    # Add the unscaled target value pred_len days in the future
    #
    df['Target'] = df['Adj Close'].shift(-1 * pred_len)

    return df

######################################
# Get data
######################################
def Get_data_screener(BacktestParms):
#
#  Update the downloaded date to the latest of end, btend, or TradeWindowEndDate
#
#   end                   datetime
#   btebd                 datetime
#   TradeWindowEndDate    str
    #
    # Function to check the integrity of the data
    #
    def is_number(num):
        for a in str(num):
            if not a.isdigit() and a != '.':
                return 0
        return float(num)
    
    #
    # Function to read stock data from Yahoo or FMP if error
    #
    def ReadData(BacktestParms, DataReaderError):

        # Try using Yahoo 
        print('Reading Yahoo')
        for i in range(5):
            try:
                #
                # Get the stock data from 'Yahoo' and write to a file.
                #
                df = web.DataReader(BacktestParms.stock_tckr, 'yahoo', BacktestParms.start, BacktestParms.end)
                                    # If today's date in the filename
                                    #today = dt.date.today()
                                    #file_name = BacktestParms.stock_tckr + '_stock_%s.csv' % today
                                    #df.to_csv(file_name)
                df.to_csv(tckrfname)
                DataReaderError = False
                continue
            except Exception as ex:
                print('Error:', ex)
                print('Error reading Yahoo data service. Trial#', i+1, 'of 5')
                 
        if DataReaderError or BacktestParms.start < df.index.min():
        # Try using FMP.  Faster, but dates often limited
            print('Reading FMP')
            for i in range(5):
                try:
                    df = FinDataHistPrices.OHLCdf(BacktestParms.stock_tckr)
                    df.to_csv(tckrfname)
                    DataReaderError = False
                    continue
                except Exception as ex:
                    print('Error:', ex)
                    print('Error reading FMP data service. Trial#', i+1, 'of 5')
                    
        if DataReaderError:
            df = pd.DataFrame(index=range(1), columns=
                              ['Open']) # Create a dummy dataframe
            
        return df, DataReaderError
    #
    # Initialize to assume there will be an error
    #
    DataReaderError = True
    #
    # Confirm the directory exists and create if it doesn't
    #
    if not os.path.exists(BacktestParms.data_path):
        print("Get_data - os.path does not exist, created it")
        os.mkdir(BacktestParms.data_path)

    tckrfname = os.getcwd() + '//' + BacktestParms.data_path + '//' + BacktestParms.stock_tckr + '.csv'
    if os.path.isfile(tckrfname):
        print("Get_data - Files exists and is readable")
        #
        # Read the file
        #
        df = pd.read_csv(tckrfname, parse_dates=True, index_col=0)
        if df.index.max() < BacktestParms.end.date():
            # Update the stock date to the new end date
            print("Get_data - get data to the end date")
            #
            # Get the stock data from 'FMP' and write to a file.
            #
            df, DataReaderError = ReadData(BacktestParms, DataReaderError)
        else:
            DataReaderError = False
    else:
        print("Get_data - Either files are missing or not readable")
        #
        # Get the stock data and write to a file.
        #
        df, DataReaderError = ReadData(BacktestParms, DataReaderError)

    print('Shape of the read data file', df.shape)

    # Confirm data exists from start to end
    if df.shape[0] < 30:        # Min 30 days of data required
        DataReaderError = True
        print('Less than 30 trading days available')
    if df.index.max() < BacktestParms.end + timedelta(days = -3):
        print('Stock end date from yahoo before Backtestparms.end')
        DataReaderError = True
    # if df.index.min() > BacktestParms.start:
    #     error = 1
    #     return df, error
    #
    #  df now contains something like this
    #
    #                    Open       High        Low      Close      Volume      Adj Close
    #   Date
    #   2004-08-19  50.050049  52.082081  48.028027  50.220219      4465900     50.220219
    #
    df['Open'] = [is_number(a) for a in df['Open']]
    df['High'] = [is_number(a) for a in df['High']]
    df['Low'] = [is_number(a) for a in df['Low']]
    df['Close'] = [is_number(a) for a in df['Close']]
    df['Volume'] = [is_number(a) for a in df['Volume']]
    df['Adj Close'] = [is_number(a) for a in df['Adj Close']]

    # Reverse the order.  Oldest data at the top
    #df = df.iloc[::-1]
        #
    # Adj the O, H, L to the adjClose
    #
    def calculate_adj(row, Adj_C, C, Col):
        return row[Adj_C] / row[C] * row[Col]

    df['Adj Open'] = df.apply(calculate_adj, args=('Adj Close', 'Close', 'Open'), axis=1)
    df['Adj High'] = df.apply(calculate_adj, args=('Adj Close', 'Close', 'High'), axis=1)
    df['Adj Low'] = df.apply(calculate_adj, args=('Adj Close', 'Close', 'Low'), axis=1)

    # Found that some data downloaded from Yahoo had big gaps
    # Routine looks for more than 5 day gaps in the data
    # Routine looks for volume data = 0
    # Routine looks for adj close < 0.05

    df['Date'] = df.index
    df['DateDif'] = df['Date'].diff().dt.days
    df['GrThan'] = df['DateDif'].gt(10)
    df['VolZero'] = df['Volume'].eq(0)
    df['AdjCloseZero'] = df['Adj Close'].le(0.05)

    if df['GrThan'].any(axis=None):
        print(BacktestParms.stock_tckr, 'file is not complete. Missing days')
        DataReaderError = True


    elif df['VolZero'].any(axis=None):
        print(BacktestParms.stock_tckr, 'file is not complete. Some zero volumes')
        DataReaderError = True

    elif df['AdjCloseZero'].any(axis=None):
        print(BacktestParms.stock_tckr, 'file errors.  Adj Close has values < 0.05')
        DataReaderError = True
    #
    # Create OHLC for BacktestParms.stock_tckr using Adj OHLC
    #
    df = df.filter(['Adj Open', 'Adj High', 'Adj Low', 'Close', 'Adj Close', 'Volume'], axis=1)
    # Backtrader requires column names = Open, High, Low, Close, Adj Close, Volume
    df = df.rename(columns={'Adj Open': 'Open', 'Adj High': 'High', 'Adj Low': 'Low', 'Close': 'Close',
                                    'Adj Close': 'Adj Close', 'Volume': 'Volume'})
    #
    # Add the unscaled target value pred_len days in the future
    #
    # df['Target'] = df['Adj Close'].shift(-1 * pred_len)

    return df, DataReaderError
######################################
# Get data
######################################
def Get_data_screener_fmp(BacktestParms):
#
#  Update the downloaded date to the latest of end, btend, or TradeWindowEndDate
#
#   end                   datetime
#   btebd                 datetime
#   TradeWindowEndDate    str
    #
    # Routine to check the integrity of the data
    #
    def is_number(num):
        for a in str(num):
            if not a.isdigit() and a != '.':
                return 0
        return float(num)
    #
    # Initialize to assume there will be an error
    #
    DataReaderError = True
    #
    # Confirm the directory exists and create if it doesn't
    #
    if not os.path.exists(BacktestParms.data_path):
        print("Get_data - os.path does not exist, created it")
        os.mkdir(BacktestParms.data_path)

    tckrfname = os.getcwd() + '//' + BacktestParms.data_path + '//' + BacktestParms.stock_tckr + '.csv'
    if os.path.isfile(tckrfname):
        print("Get_data - Files exists and is readable")
        #
        # Read the file
        #
        df = pd.read_csv(tckrfname, parse_dates=True, index_col=0)
        # Check if the data goes to the end date
        if df.index.max() <= BacktestParms.end.date():
            # Update the stock date to the new end date
            print("Get_data - get data to the end date")
            #
            # Get the stock data from 'FMP' and write to a file.
            #
            for i in range(10):
                try:
                    df = FinDataHistPrices.OHLCdf(BacktestParms.stock_tckr)
                    df.to_csv(tckrfname)
                    DataReaderError = False
                    continue
                except Exception as ex:
                    print('Error:', ex)
                    print('Error reading FMP data service. Trial#', i+1, 'of 10')
                    time.sleep(1)

            if DataReaderError:
                df = pd.DataFrame(index=range(1), columns=
                                  ['Open']) # Create a dummy dataframe
                return df, DataReaderError

    else:
        print("Get_data - Either files are missing or not readable")
        #
        # Get the stock data from 'FMP' and write to a file.
        #
        for i in range(10):
            try:
                df = FinDataHistPrices.OHLCdf(BacktestParms.stock_tckr)
                df.to_csv(tckrfname)
                DataReaderError = False
                continue
            except Exception as ex:
                print('Error:', ex)
                print('Error reading FMP data service. Trial#', i+1, 'of 10')
                time.sleep(1)

        if DataReaderError:
            df = pd.DataFrame(index=range(1), columns=
                              ['Open']) # Create a dummy dataframe
            return df, DataReaderError

    # Limit the data to the date range
    df = df[(df.index > BacktestParms.start) & (df.index <= BacktestParms.end)]
    DataReaderError = False
    print('Shape of the read data file', df.shape)

    # Confirm data exists from start to end
    if df.shape[0] < 30:        # Min 30 days of data required
        DataReaderError = True
        print('Less than 30 trading days available')
    if df.index.max() < BacktestParms.end + timedelta(days = -3):
        print('Stock end date from yahoo before Backtestparms.start')
        DataReaderError = True
    # if df.index.min() > BacktestParms.start:
    #     error = 1
    #     return df, error
    #
    #  df now contains something like this
    #
    #                    Open       High        Low      Close      Volume      Adj Close
    #   Date
    #   2004-08-19  50.050049  52.082081  48.028027  50.220219      4465900     50.220219
    #
    df['Open'] = [is_number(a) for a in df['Open']]
    df['High'] = [is_number(a) for a in df['High']]
    df['Low'] = [is_number(a) for a in df['Low']]
    df['Close'] = [is_number(a) for a in df['Close']]
    df['Volume'] = [is_number(a) for a in df['Volume']]
    df['Adj Close'] = [is_number(a) for a in df['Adj Close']]

    # Reverse the order.  Oldest data at the top
    #df = df.iloc[::-1]
        #
    # Adj the O, H, L to the adjClose
    #
    def calculate_adj(row, Adj_C, C, Col):
        return row[Adj_C] / row[C] * row[Col]

    df['Adj Open'] = df.apply(calculate_adj, args=('Adj Close', 'Close', 'Open'), axis=1)
    df['Adj High'] = df.apply(calculate_adj, args=('Adj Close', 'Close', 'High'), axis=1)
    df['Adj Low'] = df.apply(calculate_adj, args=('Adj Close', 'Close', 'Low'), axis=1)

    # Found that some data downloaded from Yahoo had big gaps
    # Routine looks for more than 5 day gaps in the data
    # Routine looks for volume data = 0
    # Routine looks for adj close < 0.05

    df['Date'] = df.index
    df['DateDif'] = df['Date'].diff().dt.days
    df['GrThan'] = df['DateDif'].gt(10)
    df['VolZero'] = df['Volume'].eq(0)
    df['AdjCloseZero'] = df['Adj Close'].le(0.05)

    if df['GrThan'].any(axis=None):
        print(BacktestParms.stock_tckr, 'file is not complete. Missing days')
        DataReaderError = True


    elif df['VolZero'].any(axis=None):
        print(BacktestParms.stock_tckr, 'file is not complete. Some zero volumes')
        DataReaderError = True

    elif df['AdjCloseZero'].any(axis=None):
        print(BacktestParms.stock_tckr, 'file errors.  Adj Close has values < 0.05')
        DataReaderError = True
    #
    # Create OHLC for BacktestParms.stock_tckr using Adj OHLC
    #
    df = df.filter(['Adj Open', 'Adj High', 'Adj Low', 'Close', 'Adj Close', 'Volume'], axis=1)
    # Backtrader requires column names = Open, High, Low, Close, Adj Close, Volume
    df = df.rename(columns={'Adj Open': 'Open', 'Adj High': 'High', 'Adj Low': 'Low', 'Close': 'Close',
                                    'Adj Close': 'Adj Close', 'Volume': 'Volume'})
    #
    # Add the unscaled target value pred_len days in the future
    #
    # df['Target'] = df['Adj Close'].shift(-1 * pred_len)

    return df, DataReaderError

######################################
# Get data
######################################
def Get_data_screener_yahoo(BacktestParms):
#
#  Update the downloaded date to the latest of end, btend, or TradeWindowEndDate
#
#   end                   datetime
#   btebd                 datetime
#   TradeWindowEndDate    str
    #
    # Routine to check the integrity of the data
    #
    def is_number(num):
        for a in str(num):
            if not a.isdigit() and a != '.':
                return 0
        return float(num)
    #
    # Initialize to assume there will be an error
    #
    DataReaderError = True
    #
    # Confirm the directory exists and create if it doesn't
    #
    if not os.path.exists(BacktestParms.data_path):
        print("Get_data - os.path does not exist, created it")
        os.mkdir(BacktestParms.data_path)

    tckrfname = os.getcwd() + '//' + BacktestParms.data_path + '//' + BacktestParms.stock_tckr + '.csv'
    if os.path.isfile(tckrfname):
        print("Get_data - Files exists and is readable")
        #
        # Read the file
        #
        df = pd.read_csv(tckrfname, parse_dates=True, index_col=0)
        print('Shape of the read data file', df.shape)
        # Check if the data goes to the end date
        if df.index.max() < BacktestParms.end.date():
            # Update the stock date to the new end date
            #
            # Get the stock data from 'Yahoo' and write to a file.
            #
            for i in range(5):
                try:
                    df = web.DataReader(BacktestParms.stock_tckr, 'yahoo', BacktestParms.start, BacktestParms.end)
                                        # If today's date in the filename
                                        #today = dt.date.today()
                                        #file_name = BacktestParms.stock_tckr + '_stock_%s.csv' % today
                                        #df.to_csv(file_name)
                    df.to_csv(tckrfname)
                    DataReaderError = False
                    continue
                except Exception as ex:
                    print('Error:', ex)
                    print('Error reading yahoo data service. Trial#', i+1, 'of 10')
                    time.sleep(1)

            if DataReaderError:
                df = pd.DataFrame(index=range(1), columns=
                                  ['Open']) # Create a dummy dataframe
                return df, DataReaderError

    else:
        print("Get_data - Either files are missing or not readable")
        #
        # Get the stock data from 'Yahoo' and write to a file.
        #
        for i in range(10):
            try:
                df = web.DataReader(BacktestParms.stock_tckr, 'yahoo', BacktestParms.start, BacktestParms.end)
                                    # If today's date in the filename
                                    #today = dt.date.today()
                                    #file_name = BacktestParms.stock_tckr + '_stock_%s.csv' % today
                                    #df.to_csv(file_name)
                df.to_csv(tckrfname)
                DataReaderError = False
                continue
            except Exception as ex:
                print('Error:', ex)
                print('Error reading yahoo data service. Trial#', i+1, 'of 10')
                time.sleep(1)

        if DataReaderError:
            df = pd.DataFrame(index=range(1), columns=
                              ['Open']) # Create a dummy dataframe
            return df, DataReaderError

    # Limit the data to the date range
    df = df[(df.index > BacktestParms.start) & (df.index <= BacktestParms.end)]
    DataReaderError = False
    print("Get_data - get data to the end date")

    # Confirm data exists from start to end
    if df.shape[0] < 30:        # Min 30 days of data required
        DataReaderError = True
        print('Less than 30 trading days available')
    if df.index.max() < BacktestParms.end + timedelta(days = -3):
        print('Stock end date from yahoo before Backtestparms.start')
        DataReaderError = True
    # if df.index.min() > BacktestParms.start:
    #     error = 1
    #     return df, error
    #
    #  df now contains something like this
    #
    #                    Open       High        Low      Close      Volume      Adj Close
    #   Date
    #   2004-08-19  50.050049  52.082081  48.028027  50.220219      4465900     50.220219
    #
    df['Open'] = [is_number(a) for a in df['Open']]
    df['High'] = [is_number(a) for a in df['High']]
    df['Low'] = [is_number(a) for a in df['Low']]
    df['Close'] = [is_number(a) for a in df['Close']]
    df['Volume'] = [is_number(a) for a in df['Volume']]
    df['Adj Close'] = [is_number(a) for a in df['Adj Close']]

    # Reverse the order.  Oldest data at the top
    #df = df.iloc[::-1]
        #
    # Adj the O, H, L to the adjClose
    #
    def calculate_adj(row, Adj_C, C, Col):
        return row[Adj_C] / row[C] * row[Col]

    df['Adj Open'] = df.apply(calculate_adj, args=('Adj Close', 'Close', 'Open'), axis=1)
    df['Adj High'] = df.apply(calculate_adj, args=('Adj Close', 'Close', 'High'), axis=1)
    df['Adj Low'] = df.apply(calculate_adj, args=('Adj Close', 'Close', 'Low'), axis=1)

    # Found that some data downloaded from Yahoo had big gaps
    # Routine looks for more than 5 day gaps in the data
    # Routine looks for volume data = 0
    # Routine looks for adj close < 0.05

    df['Date'] = df.index
    df['DateDif'] = df['Date'].diff().dt.days
    df['GrThan'] = df['DateDif'].gt(10)
    df['VolZero'] = df['Volume'].eq(0)
    df['AdjCloseZero'] = df['Adj Close'].le(0.05)

    if df['GrThan'].any(axis=None):
        print(BacktestParms.stock_tckr, 'file is not complete. Missing days')
        DataReaderError = True


    elif df['VolZero'].any(axis=None):
        print(BacktestParms.stock_tckr, 'file is not complete. Some zero volumes')
        DataReaderError = True

    elif df['AdjCloseZero'].any(axis=None):
        print(BacktestParms.stock_tckr, 'file errors.  Adj Close has values < 0.05')
        DataReaderError = True
    #
    # Create OHLC for BacktestParms.stock_tckr using Adj OHLC
    #
    df = df.filter(['Adj Open', 'Adj High', 'Adj Low', 'Close', 'Adj Close', 'Volume'], axis=1)
    # Backtrader requires column names = Open, High, Low, Close, Adj Close, Volume
    df = df.rename(columns={'Adj Open': 'Open', 'Adj High': 'High', 'Adj Low': 'Low', 'Close': 'Close',
                                    'Adj Close': 'Adj Close', 'Volume': 'Volume'})
    #
    # Add the unscaled target value pred_len days in the future
    #
    # df['Target'] = df['Adj Close'].shift(-1 * pred_len)

    return df, DataReaderError

######################################
# Calculate the Historical Volatility.  Choose the window size in DataFeatureParms
######################################
def Add_Volatility_to_data(df_adjohlc, DataFeatureParms):
    df_adjohlc = df_adjohlc.copy()
    # Compute the logarithmic returns using the Closing price
    df_adjohlc['Log_Ret'] = np.log(df_adjohlc['Close'] / df_adjohlc['Close'].shift(1))
    # Compute Volatility using the pandas rolling standard deviation function
    df_adjohlc['Volatility'] = df_adjohlc['Log_Ret'].rolling(DataFeatureParms.Volatility_window).std() * np.sqrt(DataFeatureParms.Volatility_window)
    #print(df_adjohlc.tail(15))
    return df_adjohlc

######################################
# Calculate option price
######################################
def BinomialOption(n, S, K, r, v, t, PutCall):
    # n = 10  # input("Enter number of binomial steps: ")           #number of steps
    # S = 100  # input("Enter the initial underlying asset price: ") #initial underlying asset price
    # r = 0.06  # input("Enter the risk-free interest rate: ")        #risk-free interest rate
    # K = 105  # input("Enter the option strike price: ")            #strike price
    # v = 0.4  # input("Enter the volatility factor: ")              #volatility
    # t = 1.

    At = t / n
    u = np.exp(v * np.sqrt(At))
    d = 1. / u
    p = (np.exp(r * At) - d) / (u - d)

    # Binomial price tree
    stockvalue = np.zeros((n + 1, n + 1))
    stockvalue[0, 0] = S
    for i in range(1, n + 1):
        stockvalue[i, 0] = stockvalue[i - 1, 0] * u
        for j in range(1, i + 1):
            stockvalue[i, j] = stockvalue[i - 1, j - 1] * d

    # option value at final node
    optionvalue = np.zeros((n + 1, n + 1))
    for j in range(n + 1):
        if PutCall == "C":  # Call
            optionvalue[n, j] = max(0, stockvalue[n, j] - K)
        elif PutCall == "P":  # Put
            optionvalue[n, j] = max(0, K - stockvalue[n, j])

    # backward calculation for option price
    for i in range(n - 1, -1, -1):
        for j in range(i + 1):
            if PutCall == "P":
                optionvalue[i, j] = max(0, K - stockvalue[i, j], np.exp(-r * At) * (
                            p * optionvalue[i + 1, j] + (1 - p) * optionvalue[i + 1, j + 1]))
            elif PutCall == "C":
                optionvalue[i, j] = max(0, stockvalue[i, j] - K, np.exp(-r * At) * (
                            p * optionvalue[i + 1, j] + (1 - p) * optionvalue[i + 1, j + 1]))
    return optionvalue[0, 0]

######################################
# Calculate the option price and add to data
######################################
def Add_Option_Price_to_data(df_adjohlc, DataFeatureParms):
    n = 10  # input("Enter number of binomial steps: ")           #number of steps
    S = 100  # input("Enter the initial underlying asset price: ") #initial underlying asset price
    r = 0.02  # input("Enter the risk-free interest rate: ")        #risk-free interest rate
    Strike = 105  # input("Enter the option strike price: ")            #strike price
    Vol = 0.4  # input("Enter the volatility factor: ")              #volatility
    t = 1.

    df_adjohlc = df_adjohlc.copy()
    # Add a column to the datafram for OptionPrice
    df_adjohlc["OptionPrice"] = 0
    for i in range(len(df_adjohlc)):
        Price = df_adjohlc.iloc[i,df_adjohlc.columns.get_loc('Adj Close')]
        # Update the strike price every Thur
        #   Mon:0, Tue:1, Wed:2, Thur:3, Fri:4, Sat:5, Sun:6
        if df_adjohlc.index[i].weekday() == 3:
            Strike = round(Price*1.1,0)
        vol = df_adjohlc.iloc[i,df_adjohlc.columns.get_loc('Volatility')]
        df_adjohlc.iloc[i,df_adjohlc.columns.get_loc('OptionPrice')] = BinomialOption(n, Price, Strike, r, Vol, t, PutCall="C")

    return df_adjohlc

######################################
# Select data columns to use in this run
######################################
def Select_features(df, features):
    #  0:'ohlc', 1:'ohlcv', 2:'ohlcvMA', 3:'ohlcvMAgrthan',4:'ohlcvMArising', 5:'ohlcvMAgrthanrising',
    #        6:'ohlcret', 7:'ohlcvret', 8:'ohlcvMAret', 9:'ohlcvMAretgrthan',10:'ohlcvMAretrising', 11:'ohlcvMAretgrthanrising',
    #        12:'close'
    #
    # list(df) will list the column names in the console
    # ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Open', 'Adj High', 'Adj Low','Adj Close',
    # 'MovCslow', 'MovCmid', 'MovCfast', 'Adj Open ret', 'Adj High ret', 'Adj Low ret', 'Adj Close ret', 'Volume ret',
    # 'MovCslow ret', 'MovCmid ret', 'MovCfast ret', 'GrthanSlow', 'GrthanMid', 'GrthanFast', 'SlowRising', 'MidRising', 'FastRising']

    ### ??? Fix
    if features == 'ohlc':  # 0
        print('Featues selected = ohlc')
        dfnew = df.filter(['Adj Open', 'Adj High', 'Adj Low', 'Adj Close'], axis=1)
    elif features == 'ohlcv':  # 1
        print('Featues selected = ohlcv')
        dfnew = df.filter(['Adj Open', 'Adj High', 'Adj Low', 'Adj Close', 'Volume'], axis=1)
    elif features == 'ohlcMA':  # 2
        print('Featues selected = ohlcMA')
        dfnew = df.filter(['Adj Open', 'Adj High', 'Adj Low', 'Adj Close', 'MovCslow', 'MovCmid', 'MovCfast'],
                          axis=1)
    elif features == 'ohlcvMA':  # 3
        print('Featues selected = ohlcvMA')
        dfnew = df.filter(
            ['Adj Open', 'Adj High', 'Adj Low', 'Adj Close', 'Volume', 'MovCslow', 'MovCmid', 'MovCfast'],
            axis=1)
    elif features == 'ohlcvMAgrthan':  # 4
        print('Featues selected = ohlcvMAgrthan')
        dfnew = df.filter(
            ['Adj Open', 'Adj High', 'Adj Low', 'Adj Close', 'Volume', 'MovCslow', 'MovCmid', 'MovCfast',
             'GrthanSlow', 'GrthanMid', 'GrthanFast'], axis=1)
    elif features == 'ohlcvMArising':  # 5
        print('Featues selected = ohlcvMArising')
        dfnew = df.filter(
            ['Adj Open', 'Adj High', 'Adj Low', 'Adj Close', 'Volume', 'MovCslow', 'MovCmid', 'MovCfast',
             'SlowRising', 'MidRising', 'FastRising'], axis=1)
    elif features == 'ohlcvMAgrthanrising':  # 6
        print('Featues selected = ohlcvMAgrthanrising')
        dfnew = df.filter(
            ['Adj Open', 'Adj High', 'Adj Low', 'Adj Close', 'Volume', 'MovCslow', 'MovCmid', 'MovCfast',
             'GrthanSlow', 'GrthanMid', 'GrthanFast', 'SlowRising', 'MidRising', 'FastRising'], axis=1)
    elif features == 'ohlcret':  # 7
        print('Featues selected = ohlcret')
        dfnew = df.filter(['Adj Open ret', 'Adj High ret', 'Adj Low ret', 'Adj Close ret'], axis=1)
    elif features == 'ohlcvret':  # 8
        print('Featues selected = ohlcvret')
        dfnew = df.filter(['Adj Open ret', 'Adj High ret', 'Adj Low ret', 'Adj Close ret', 'Volume ret'], axis=1)
    elif features == 'ohlcMAret':  # 9
        print('Featues selected = ohlcMAret')
        dfnew = df.filter(
            ['Adj Open ret', 'Adj High ret', 'Adj Low ret', 'Adj Close ret', 'MovCslow ret', 'MovCmid ret',
             'MovCfast ret'], axis=1)
    elif features == 'ohlcvMAret':  # 10
        print('Featues selected = ohlcvMAret')
        dfnew = df.filter(
            ['Adj Open ret', 'Adj High ret', 'Adj Low ret', 'Adj Close ret', 'Volume ret', 'MovCslow ret',
             'MovCmid ret', 'MovCfast ret'], axis=1)
    elif features == 'ohlcvMAretgrthan':  # 11
        print('Featues selected = ohlcvMAretgrthan')
        dfnew = df.filter(
            ['Adj Open ret', 'Adj High ret', 'Adj Low ret', 'Adj Close ret', 'Volume ret', 'MovCslow ret',
             'MovCmid ret', 'MovCfast ret', 'GrthanSlow', 'GrthanMid', 'GrthanFast'], axis=1)
    elif features == 'ohlcvMAretrising':  # 12
        print('Featues selected = ohlcvMAretrising')
        dfnew = df.filter(
            ['Adj Open ret', 'Adj High ret', 'Adj Low ret', 'Adj Close ret', 'Volume ret', 'MovCslow ret',
             'MovCmid ret', 'MovCfast ret', 'SlowRising', 'MidRising', 'FastRising'], axis=1)
    elif features == 'ohlcvMAretgrthanrising':  # 13
        print('Featues selected = ohlcvMAretgrthanrising')
        dfnew = df.filter(
            ['Adj Open ret', 'Adj High ret', 'Adj Low ret', 'Adj Close ret', 'Volume ret', 'MovCslow ret',
             'MovCmid ret', 'MovCfast ret', 'GrthanSlow', 'GrthanMid', 'GrthanFast', 'SlowRising',
             'MidRising', 'FastRising'], axis=1)
    elif features == 'grthanrising':  # 14
        print('Featues selected = grthanrising')
        dfnew = df.filter(['GrthanSlow', 'GrthanMid', 'GrthanFast', 'SlowRising', 'MidRising', 'FastRising'],
                          axis=1)
    elif features == 'close':  # 15
        print('Featues selected = Adj Close')
        dfnew = df.filter(['Adj Close', 'Target'], axis=1)
    else:  # Error
        print("Error in feature selection \n")

    return dfnew
######################################
# Scale_data and Target = Close pred_len days in the future
######################################
def Scale_data(df):
    # 'none', 'prepro', 'minmax ,'norm', 'robust', 'fastica'
    #
    # Scikit page                                   http://scikit-learn.org/stable/modules/preprocessing.html
    # Feature Scaling with sckikit-learn            http://benalexkeen.com/feature-scaling-with-scikit-learn/
    # Should I normalize / standardize / rescale     http://www.faqs.org/faqs/ai-faq/neural-nets/part2/section-16.html

    #
    # Scalers operate on an array
    #
    ohlc_data = np.array(df)                # Convert data to an array
    Num_of_features = ohlc_data.shape[1]
    #
    # Scale with MinMax
    #
    print('Scale selected = minmax')
    scaler = preprocessing.MinMaxScaler(feature_range=(0, 1))
    #scaler = scaler.fit(ohlc_data)
    #print('Min: %f, Max: %f' % (scaler.data_min_, scaler.data_max_))
    ohlc_data_scaled = scaler.fit_transform(ohlc_data)

    #ohlc_data_scaled = ohlc_data       # Sometimes easier to look at unscaled data

    return ohlc_data_scaled, scaler

######################################
# UnScale_data and Target
######################################
def UnScale_data(df_full, p, Y_test, scaler, scale_type):
    # 'none', 'prepro', 'minmax ,'norm', 'robust', 'fastica'
    #
    # Scikit page                                   http://scikit-learn.org/stable/modules/preprocessing.html
    # Feature Scaling with sckikit-learn            http://benalexkeen.com/feature-scaling-with-scikit-learn/
    # Should I normalize / standardize / rescale     http://www.faqs.org/faqs/ai-faq/neural-nets/part2/section-16.html

    if scale_type == "Dave":  # Divide by the max 'Adj High'
        print('Scale selected = Dave')
        div_val = round(max(df_full['Adj High']), -2)
        print('Div value of scaler = ', div_val)
        for i in range(p.shape[0]):
            p[i] = p[i] * div_val
        for i in range(Y_test.shape[0]):
            Y_test[i] = Y_test[i] * div_val

    #
    # Scale with none
    #
    if scale_type == 'none':
        print('Scale selected = none')
        print('Fix the unscale')
    #
    # Scale with FastICA
    #
    if scale_type == 'fastica':
        print('Scale selected = fastica')
        print('Fix the unscale')
    #
    # Scale with standard scale function
    #
    if scale_type == "prepro":
        print('Scale selected = Standard')
        print('Fix the unscale')
    #
    # Scale with norm
    #
    # https://plot.ly/python/normalization/#
    if scale_type == "norm":
        print('Scale selected = norm')
        print('Fix the unscale')
    #
    # Scale with MinMax
    #
    if scale_type == "minmax":
        print('Scale selected = minmax')
        print('Fix the unscale')
        p = scaler.inverse_transform(p)
        Y_test = scaler.inverse_transform(Y_test)
    #
    # Scale with robust
    #
    if scale_type == "robust":              # Works better with outliers
        print('Scale selected = robust')
        print('Fix the unscale')

    #
    # Separate Target and ohlc
    #

    return p, Y_test

######################################
# Convert an array of values into a dataset matrix for LSTM algo
######################################

def create_Train_Test_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-1, look_back, -1):  # Start, End, step
        a = []
        for k in range(look_back, 0, -1):
            a.insert(0, dataset[i-look_back-k+1, 0])
        dataX.insert(0, a)
        dataY.insert(0, dataset[i, 0])
    return np.array(dataX), np.array(dataY)

def create_search_for_trade_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-1, look_back, -1):  # Start, End, step
        a=[]
        for k in range(look_back,0,-1):
            a.insert(0,dataset[i-k+1, 0])
        dataX.insert(0, a)
    return np.array(dataX)

######################################
# Execute the LSTM prediction
######################################

def run_LSTM_Prediction(df_adjohlc, ModelParms, pred_len):

    df = df_adjohlc.copy()
    #print("Scale selected before Scale_data call ", scale_list[scale_selected])
    ohlc_data, scaler = Scale_data(df.filter(['Adj Close'], axis=1))
    print("len ohlc_data ", len(ohlc_data))
    #
    # Create training and testing sets
    #
    # print("\n", "Create training and testing sets")
    train_size = int(len(ohlc_data) * 0.5)
    test_size = len(ohlc_data) - train_size
    train, test = ohlc_data[0:train_size, :], ohlc_data[train_size:len(ohlc_data), :]

    # Create train and test datasets
    # reshape into Input=t and Target=t+pred_len
    trainInput, trainTarget = create_Train_Test_dataset(train, pred_len)
    testInput, testTarget = create_Train_Test_dataset(test, pred_len)

    # Create a dataset to search for trade opportunites
    # Input uses the most recent samples

    # Remove the top 'pred_len' samples from test and train to align
    #    train, test = train[pred_len+1:], test[pred_len+1:]
    tradeSearchInput = create_search_for_trade_dataset(test, pred_len)

    # reshape input to be [samples, time steps, features]
    trainInput = np.reshape(trainInput, (trainInput.shape[0], 1, trainInput.shape[1]))
    testInput = np.reshape(testInput, (testInput.shape[0], 1, testInput.shape[1]))
    tradeSearchInput = np.reshape(tradeSearchInput, (tradeSearchInput.shape[0], 1, tradeSearchInput.shape[1]))

    model = keras.Sequential()
    model.add(keras.layers.LSTM(50, input_shape=(trainInput.shape[1], trainInput.shape[2]), return_sequences=True))
    model.add(keras.layers.Dropout(0.2))
    model.add(keras.layers.LSTM(100, return_sequences=False))
    model.add(keras.layers.Dropout(0.2))
    #model.add(keras.Dense(1, activation='linear'))
    model.add(keras.layers.Dense(1))
    model.add(keras.layers.Activation('linear'))

    # start = time.time()
    model.compile(loss=ModelParms.LossType, optimizer=ModelParms.OptType)
    # print ('compilation time : ', time.time() - start)

    model.fit(
        trainInput,
        trainTarget,
        batch_size=ModelParms.Batch,
        epochs=ModelParms.NumEpochs,
        verbose=2,
        validation_split=0.05)

    trainmse = model.evaluate(trainInput, trainTarget, verbose=0)
    testmse = model.evaluate(testInput, testTarget, verbose=0)

    print("trainmse = ", trainmse)
    print("testmse = ", testmse)

    p = model.predict(testInput)
    tradeSearchPred = model.predict(tradeSearchInput)

    # Align df with the prediction output
    if df.shape[0] != p.shape[0]:
        df = df[(df.shape[0]-p.shape[0]):]
    # Add the prediction to df
    df['Scaled Target'] = testTarget
    df['p'] = p
    df['tradeSearchPred'] = tradeSearchPred

    '''
    plotstart = int(len(p)-len(p) * 0.80)   # View the last x% of the plot
    plt.plot(p[plotstart:, 0], color='red', label='predicted AdjClose')
    plt.plot(testTarget[plotstart:], color='blue', label='Target')
    plt.plot(tradeSearchPred[plotstart:], color='green', label='TradeSearch - AdjClose 5 days in future')
    plt.legend(loc='upper left')
    plt.title('Compare predicted value to actual value')
    plt.show()
    '''
    # Save Figure
    #plt.savefig(os.getcwd() + '//' + BacktestParms.data_path + '//'+ BacktestParms.stock_tckr + '.png')

    return trainmse, testmse, df, scaler


######################################
# Save the Target and Prediction for later analysis
######################################
def SaveTargetPrediction(df_IncPred, scaler, BacktestParms, DataFeatureParms):
    df_full = df_IncPred.copy()

    ###################################
    # Scale up the test prediction, and the trade search prediction
    ###################################

    dfIndex = df_full.index
    # Unscale p and Y_test
    df_scale = df_full.filter(['Scaled Target', 'p', 'tradeSearchPred'], axis=1)
    df_scale = scaler.inverse_transform(df_scale) # Inverse transmform returns an array
    df_scale = df_scale.round(2)
    # Convert the array back to dataframe
    df_scale = pd.DataFrame(data=df_scale, index=dfIndex, columns=['Scaled up Target', 'Scaled up Prediction', 'Scaled up tradeSearchPred'])
    df_full = pd.concat([df_full, df_scale], axis=1)

    ###################################
    # Calculate OHLCV for the Scaled up trade search prediciton
    ###################################
    def calculate_adj(row, PredAdj_C, AdjC, Col):
        return row[PredAdj_C] / row[AdjC] * row[Col]

    df_full['Pred Open'] = df_full.apply(calculate_adj, args=('Scaled up tradeSearchPred', 'Close', 'Open'), axis=1)
    df_full['Pred High'] = df_full.apply(calculate_adj, args=('Scaled up tradeSearchPred', 'Close', 'High'), axis=1)
    df_full['Pred Low'] = df_full.apply(calculate_adj, args=('Scaled up tradeSearchPred', 'Close', 'Low'), axis=1)

    df_full['Pred Close'] = df_full['Scaled up tradeSearchPred']
    df_full['Pred Adj Close'] = df_full['Scaled up tradeSearchPred']   #Close and Adj Close will be identical
    df_full['Pred Volume'] = df_full['Volume']

    # Write df_full to csv file
    fname = os.getcwd() + '//' + BacktestParms.data_path + '//' + 'TrainingPrediction' + DataFeatureParms.features_list[DataFeatureParms.features_selected] + DataFeatureParms.scale_list[DataFeatureParms.scale_selected] + BacktestParms.stock_tckr + '.csv'
    df_full.to_csv(fname)

    ###################################
    # Create adjusted ohlc based on the trade search prediction
    # Save to a file useable by Backtrader
    # Backtrader requires OHLCV
    ###################################
    dfpredohlc = df_full.filter(['Pred Open', 'Pred High', 'Pred Low', 'Pred Close', 'Pred Adj Close', 'Pred Volume'], axis=1)
    # Backtrader requires column names = Open, High, Low, Close, Adj Close, Volume
    dfpredohlc = dfpredohlc.rename(columns={'Pred Open': 'Open', 'Pred High': 'High', 'Pred Low': 'Low',
                                                       'Pred Close': 'Close', 'Pred Adj Close': 'Adj Close',
                                                       'Pred Volume': 'Volume'})
    dfpredohlc = dfpredohlc.round(2)
    fname = os.getcwd() + '//' + BacktestParms.data_path + '//'+'predohlc' + BacktestParms.stock_tckr + '.csv'
    dfpredohlc.to_csv(fname)

    #######################################
    # Calculate OHLCV for the Option Price
    #######################################
    df_full['Opt Open'] = df_full.apply(calculate_adj, args=('OptionPrice', 'Adj Close', 'Open'), axis=1)
    df_full['Opt High'] = df_full.apply(calculate_adj, args=('OptionPrice', 'Adj Close', 'High'), axis=1)
    df_full['Opt Low'] = df_full.apply(calculate_adj, args=('OptionPrice', 'Adj Close', 'Low'), axis=1)

    df_full['Opt Close'] = df_full['OptionPrice']
    df_full['Opt Adj Close'] = df_full['OptionPrice']   #Close and Adj Close will be identical
    df_full['Opt Volume'] = df_full['Volume']
    ###################################
    # Create adjusted ohlc of the underlying stock
    # The adjustment was done in Getdata()
    # Filter the columns needed and save to a file useable by Backtrader
    # Backtrader requires OHLCV
    ###################################
    dfoptionohlc = df_full.filter(['Opt Open', 'Opt High', 'Opt Low', 'Opt Close', 'Opt Adj Close', 'Opt Volume'], axis=1)

    dfoptionohlc = dfoptionohlc.rename(columns={'Opt Open': 'Open', 'Opt High': 'High', 'Opt Low': 'Low',
                                                       'Opt Close': 'Close', 'Opt Adj Close': 'Adj Close',
                                                       'Opt Volume': 'Volume'})
    dfoptionohlc = dfoptionohlc.round(2)
    fname = os.getcwd() + '//' + BacktestParms.data_path + '//'+'Optionohlc' + BacktestParms.stock_tckr + '.csv'
    dfoptionohlc.to_csv(fname)

    ###################################
    # Create adjusted ohlc of the underlying stock
    # The adjustment was done in Getdata()
    # Filter the columns needed and save to a file useable by Backtrader
    # Backtrader requires OHLCV
    ###################################
    dfohlc = df_full.filter(['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'], axis=1)

    dfohlc = dfohlc.round(2)
    fname = os.getcwd() + '//' + BacktestParms.data_path + '//'+'adjohlc' + BacktestParms.stock_tckr + '.csv'
    dfohlc.to_csv(fname)


    return dfohlc, dfpredohlc, dfoptionohlc

######################################
# Run LSTM steps
######################################
def RunLSTMsteps(BacktestParms, pred_len, ModelParms, DataFeatureParms):

    print("Tckr = ", BacktestParms.stock_tckr)

    df_adjohlc, FirstDate = Get_data(BacktestParms, pred_len)  # Get data from internet or local file.  Function returns Adj Open, Adj Close, ...

    df_adjohlc = Add_Volatility_to_data(df_adjohlc, DataFeatureParms)

    df_adjohlc = Add_Option_Price_to_data(df_adjohlc, DataFeatureParms)

    trainmse, testmse, df_IncPred, scaler = run_LSTM_Prediction(df_adjohlc, ModelParms, pred_len)

    dfohlc, dfpredohlc, dfoptionohlc  = SaveTargetPrediction(df_IncPred, scaler, BacktestParms, DataFeatureParms)

    return dfohlc, dfpredohlc, dfoptionohlc, df_adjohlc

######################################
# Run LSTM Prediction
######################################
def RunLSTM(BacktestParms):
    # Variable definition
    # ------------- INPUT -------------
#    start = dt.datetime(2000, 1, 1)
#    end = dt.datetime(2018, 12, 31)
#    stock_tckr = 'AMZN'                # Ticker to process
#    data_path = "stock_data"           # Directory under the current directory to store stock data csv files
    pred_len = 10                       # How many days into the future to predict
    class ModelParm:
        Batch = 512
        NumEpochs = 10
        LossType = 'mean_squared_logarithmic_error'
        OptType = 'Adagrad'
    ModelParms = ModelParm()

    class DataFeatureParm:
        features_selected = 12       # Index into features_list [0...n]
        features_list = ['ohlc', 'ohlcv', 'ohlcvMA', 'ohlcvMAgrthan','ohlcvMArising', 'ohlcvMAgrthanrising',
                'ohlcret', 'ohlcvret', 'ohlcvMAret', 'ohlcvMAretgrthan','ohlcvMAretrising', 'ohlcvMAretgrthanrising',
                'close']   #'logicgrthanrising'
        scale_selected = 2          # Index into scale_list [0...n]
        scale_list = ['none', 'prepro', 'minmax', 'norm', 'robust', 'Dave']
        Volatility_window = 10      # Number of samples used to calculate volatility for option pricing
    DataFeatureParms = DataFeatureParm()

    class BacktestParm:
        start = dt.datetime(2000, 1, 1)  # Start date of raw data to be read from Yahoo.com
        end = dt.datetime(2018, 12, 31)  # End date of raw data to be read from Yahoo.com
        initial_cash = 250000
        stock_tckr = 'GOOG'  # Ticker to process
        data_path = "stock_data"  # Directory under the current directory to store stock data csv files
        result_fname = "BackTraderResults.csv"
        generate_prediction = False  # True, Generate.  False, use existing data
        display_chart = True
#        strategy = DTM_Strategies.TestStrategy      # Set a default strategy
        ppf_percent = 0.8         # Percentage point on the bell curve for calculating the strike price
        std_period = 15           # Period used to calculate standard deviation for option pricing
        iteration = 0             # Current iteration when doing multipl strategies

    # BacktestParms = BacktestParm()
    #
    # Code Execution from here
    #
    # Prediction algo yields just under half (.49x) of the data as a valid prediction
    # Running it 3 times will yield almost 90% of the original data with a valid prediction

    # First Run
    # Run the predicion on the full data set available.
    EndDate = BacktestParms.end               # Temporary storage so it can be restored on exit
    BacktestParms.iteration = 0
    PredResults_df = pd.DataFrame(index=range(1), columns=['PredRnd'])  # Create the dataframe.  Columns are filled out later.

    print("Prediction round = ", BacktestParms.iteration + 1)
    dfohlc, dfpredohlc, dfoptionohlc, df_adjohlc = RunLSTMsteps(BacktestParms, pred_len, ModelParms, DataFeatureParms)

    TotalYears = dfohlc.index.max().year-df_adjohlc.index.min().year
    SliceofTime = (dfohlc.index.max().year-round(TotalYears/2))+1
    Lowmask = dt.datetime(SliceofTime, 1, 1)
    Highmask = dt.datetime(dfohlc.index.max().year, 12, 31)
    # print("Start ",df_adjohlc.index.min(), "End ", BacktestParms.end)
    # print("TotalYears ",TotalYears, "SliceofTime ", SliceofTime)
    # print("Highmask ",Highmask, "Lowmask ", Lowmask)
    dfohlcfinal = dfohlc[(dfohlc.index >= Lowmask) & (dfohlc.index <= Highmask) ]
    dfpredohlcfinal = dfpredohlc[(dfpredohlc.index >= Lowmask) & (dfpredohlc.index <= Highmask) ]
    dfoptionohlcfinal = dfoptionohlc[(dfoptionohlc.index >= Lowmask) & (dfoptionohlc.index <= Highmask) ]
    # print(dfohlcfinal.head())
    # print(dfohlcfinal.tail())

    PredResults_df.loc[BacktestParms.iteration, 'PredRnd'] = BacktestParms.iteration + 1
    PredResults_df.loc[BacktestParms.iteration, 'StartDate'] = dfohlc.index.min()
    PredResults_df.loc[BacktestParms.iteration, 'EndDate'] = BacktestParms.end
    PredResults_df.loc[BacktestParms.iteration, 'TotalYears'] = TotalYears
    PredResults_df.loc[BacktestParms.iteration, 'SliceofTime'] = SliceofTime
    PredResults_df.loc[BacktestParms.iteration, 'Highmask'] = Highmask
    PredResults_df.loc[BacktestParms.iteration, 'Lowmask'] = Lowmask
    BacktestParms.iteration = BacktestParms.iteration + 1

    for i in range(2):
        # Second Run, half the data set
        # Third Run, quarter the data set
        print("Prediction round = ", BacktestParms.iteration + 1)
        BacktestParms.end = dt.datetime(SliceofTime-1, 12, 31)
        dfohlc, dfpredohlc, dfoptionohlc, df_adjohlc = RunLSTMsteps(BacktestParms, pred_len, ModelParms, DataFeatureParms)

        TotalYears = dfohlc.index.max().year-df_adjohlc.index.min().year
        SliceofTime = (dfohlc.index.max().year-round(TotalYears/2))+1
        Lowmask = dt.datetime(SliceofTime, 1, 1)
        Highmask = dt.datetime(dfohlc.index.max().year, 12, 31)
        # print("Start ", df_adjohlc.index.min().year, "End ", BacktestParms.end)
        # print("TotalYears ",TotalYears, "SliceofTime ", SliceofTime)
        # print("Highmask ",Highmask, "Lowmask ", Lowmask)
        df1 = dfohlc[(dfohlc.index >= Lowmask) & (dfohlc.index <= Highmask) ]
        dfohlcfinal = pd.concat([df1,dfohlcfinal],axis=0)
        df1 = dfpredohlc[(dfpredohlc.index >= Lowmask) & (dfpredohlc.index <= Highmask) ]
        dfpredohlcfinal = pd.concat([df1, dfpredohlcfinal], axis=0)
        df1 = dfoptionohlc[(dfoptionohlc.index >= Lowmask) & (dfoptionohlc.index <= Highmask) ]
        dfoptionohlcfinal = pd.concat([df1, dfoptionohlcfinal], axis=0)
        # print(dfohlcfinal.head())
        # print(dfohlcfinal.tail())

        PredResults_df.loc[BacktestParms.iteration, 'PredRnd'] = BacktestParms.iteration + 1
        PredResults_df.loc[BacktestParms.iteration, 'StartDate'] = dfohlc.index.min()
        PredResults_df.loc[BacktestParms.iteration, 'EndDate'] = BacktestParms.end
        PredResults_df.loc[BacktestParms.iteration, 'TotalYears'] = TotalYears
        PredResults_df.loc[BacktestParms.iteration, 'SliceofTime'] = SliceofTime
        PredResults_df.loc[BacktestParms.iteration, 'Highmask'] = Highmask
        PredResults_df.loc[BacktestParms.iteration, 'Lowmask'] = Lowmask
        BacktestParms.iteration = BacktestParms.iteration + 1

    # print(PredResults_df)

    dfohlcfinal.to_csv(os.getcwd() + '//' + BacktestParms.data_path + '//'+'adjohlc' + BacktestParms.stock_tckr + '.csv')

    dfpredohlcfinal.to_csv(os.getcwd() + '//' + BacktestParms.data_path + '//'+'predohlc' + BacktestParms.stock_tckr + '.csv')

    dfoptionohlcfinal.to_csv(os.getcwd() + '//' + BacktestParms.data_path + '//'+'Optionohlc' + BacktestParms.stock_tckr + '.csv')

    BacktestParms.end = EndDate                      # Restore

    return dfohlcfinal, dfpredohlcfinal, dfoptionohlcfinal
