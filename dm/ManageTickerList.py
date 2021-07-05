#
# Import my code
#
import FinDataLookUp

import datetime  # For datetime objects
from datetime import timedelta
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

import numpy as np
import pandas as pd
import math
import FundamentalAnalysis     # https://pypi.org/project/FundamentalAnalysis/
api_key = "3d319882a7d958543097ee3985fafada"

# Open NASDAQ
# Open OTCBB
# Merge
# Open NYSE file
# Merge NYSE and NASDAQ
#  strip lines with '-' in ticker
#  strip lines with '.' in ticker
# Create list from Symbol column
# Remove duplicate tickers

    # Website to update the stocks on an exchange
    # https://www.nasdaq.com/market-activity/stocks/screener?exchange=nasdaq&letter=0&render=download
    # http://www.eoddata.com/symbols.aspx?AspxAutoDetectCookieSupport=1
  
def CreateUniverseFromFiles(BacktestParms):
    
    tckrfname = os.getcwd() + '/' + 'Stock Universe' + '/' + 'NASDAQ.csv'
    Universe_df = pd.read_csv(tckrfname, index_col=0)

    tckrfname = os.getcwd() + '/' + 'Stock Universe' + '/' + 'OTCBB.csv'
    Universe_df = Universe_df.append(pd.read_csv(tckrfname, index_col=0))

    tckrfname = os.getcwd() + '/' + 'Stock Universe' + '/' + 'NYSE.csv'
    Universe_df = Universe_df.append(pd.read_csv(tckrfname, index_col=0)).reset_index()
    
    Universe_df = Universe_df[~Universe_df.Symbol.str.contains('-')]
    Universe_df = Universe_df[~Universe_df.Symbol.str.contains('\.')]
    
    Universe_df = Universe_df.reset_index()
    # Universe_df = Universe_df.head(100)
    TckrList = Universe_df['Symbol'].tolist()
    TckrList = list(set(TckrList))      # Convert to set and back to make sure the list is unique tckrs
    TckrList.sort()
    return TckrList

def CreateUniverseFromFMP(BacktestParms, VolThresh):
    
    Companies_df = FundamentalAnalysis.available_companies(api_key)
    Companies_df = Companies_df[Companies_df['price'] >= VolThresh]
    
    # df_Nyse = Companies_df[Companies_df['exchange'].str.contains("New York|NYSE")]
    # df_Nasdaq = Companies_df[Companies_df['exchange'].str.contains("Nasdaq|NASDAQ")]
    # df_Otc = Companies_df[Companies_df['exchange'].str.contains("OTC")]
    Universe_df = Companies_df[Companies_df['exchange'].str.contains("New York|NYSE|Nasdaq|NASDAQ|OTC")]
    
    fname = os.getcwd() + '/' + 'Stock Universe' + '/' + 'StockUniverse.csv'
    Universe_df.to_csv(fname)

    Universe_df = Universe_df.reset_index()
    TckrList = Universe_df['symbol'].tolist()
    TckrList = list(set(TckrList))      # Convert to set and back to make sure the list is unique tckrs
    TckrList.sort()

    return TckrList

def ParseTckrListByVolume(BacktestParms, TckrList, VolThresh = 100000):
    
    #Loop through TckrList and store in a variable, data.
    print('CompanyQuote query for Volume')
    data = map(FinDataLookUp.CompanyQuote, TckrList)
    df_data = pd.DataFrame(data, columns=['Tckr', 'Name', 'Price', 'Volume', 'AvgVolume', 'EPS', 'PE', 'EAdate', 'SharesOutstanding'])     # populate DataFrame with data variable and create columns:

    df_TckrList = pd.DataFrame(TckrList,columns=['Tckr'])
    df_TckrList = pd.merge(df_TckrList, df_data, left_on=['Tckr'], right_on = ['Tckr'])

    # Pull out all the tickers with errors
    df_ErrorTckrList = df_TckrList.loc[df_TckrList['AvgVolume'] == 'Error']
    ErrorTckrList = df_ErrorTckrList['Tckr'].tolist()
    
    # Create ticker list by removing error rows and Vol greater than the thresh
    df_TckrList = df_TckrList.loc[df_TckrList['AvgVolume'] != 'Error']
    df_TckrList = df_TckrList.loc[df_TckrList['AvgVolume'] > VolThresh]
    TckrList = df_TckrList['Tckr'].tolist()
    return TckrList, ErrorTckrList

def UpdateTckrList(BacktestParms, VolThresh, PriceThresh):   
    #TckrList = CreateUniverseFromFiles(BacktestParms)
    TckrList = CreateUniverseFromFMP(BacktestParms, VolThresh)
    TckrList, ErrorTckrList = ParseTckrListByVolume(BacktestParms, TckrList, VolThresh)

    TckrListfname = os.getcwd() + '/' + 'Stock Universe' + '/' + 'TckrList.csv'
    pd.DataFrame(TckrList,columns=['Tckr']).to_csv(TckrListfname)

    ErrorTckrListfname = os.getcwd() + '/' + 'Stock Universe' + '/' + 'ErrorTckrList.csv'
    pd.DataFrame(ErrorTckrList,columns=['Tckr']).to_csv(ErrorTckrListfname)
    return TckrList

def GetTckrList(BacktestParms, VolThresh, PriceThresh):
    # 
    # Update the stock exchange csv file manually
    # Only update the tickerlist with volume information once a month
    
    Cookiefname = os.getcwd() + '/' + 'Stock Universe' + '/' + 'Cookie.csv'
    TckrListfname = os.getcwd() + '/' + 'Stock Universe' + '/' + 'TckrList.csv'
    FinDatafname = os.getcwd() + '/' + 'Stock Universe' + '/' + 'FundamentalData.csv'      

    #
    # Confirm the directory exists and create if it doesn't
    #
    if not os.path.exists(BacktestParms.data_path):
        print("Get_data - os.path does not exist, created it")
        os.mkdir('Stock Universe')
    #
    # Check if cookie file exists
    #
    if os.path.isfile(Cookiefname):
        print("Get_data - Cookie File Exists")
        #
        # Read the file
        # Cookie has the date of the last update.
        # Updates the stock universe once/month.  Takes a while...
        #
        Cookie_df = pd.read_csv(Cookiefname, index_col=0)
        # Leave the current date in a cookie file
        CookieDate_dt = datetime.datetime.strptime(Cookie_df.loc[0,'Date'], "%m/%d/%Y")
        
        CookieMonth = CookieDate_dt.month
        CookieYear = CookieDate_dt.year
        
        TodayMonth = datetime.datetime.now().month
        TodayYear = datetime.datetime.now().year
        
        # Update every month
        if TodayYear != CookieYear or TodayMonth > CookieMonth:
            print('TckrList is more than a month old.  Update')
            TckrList = UpdateTckrList(BacktestParms, VolThresh, PriceThresh)
            Cookie_df.loc[0,'Date'] = datetime.datetime.now().strftime("%m/%d/%Y")
            Cookie_df.to_csv(Cookiefname)
            # Delete the Fundamental Data file to force a new download
            try:
                os.remove(FinDatafname)
            except OSError:
                pass
        else:
            print('Open the TckrList')
            df_TckrList = pd.read_csv(TckrListfname, index_col=0)
            TckrList = df_TckrList['Tckr'].tolist()
    else:
        print('Create a cookie file')
        Cookie_df = pd.DataFrame(index=range(1), columns=['Date'])  # Create the dataframe.  Columns are filled out later.
        Cookie_df.loc[0,'Date'] = datetime.datetime.now().strftime("%m/%d/%Y")
        Cookie_df.to_csv(Cookiefname)
        TckrList = UpdateTckrList(BacktestParms, VolThresh, PriceThresh)

    return TckrList
