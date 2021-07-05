from datetime import datetime
import os.path
import numpy as np
import pandas as pd
import requests
from time import sleep
import FundamentalAnalysis     # https://pypi.org/project/FundamentalAnalysis/

# Modules

api_key = "3d319882a7d958543097ee3985fafada"


def IncomeStatementQuarterFMP(tckr, BacktestParms):   

    df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    df_IS = FundamentalAnalysis.income_statement(tckr, api_key, period="quarter")
    df_IS = df_IS.T.reset_index()
    
    for idx in range(len(df_IS)):    
        df.loc[idx,'Tckr']  = tckr
        df.loc[idx,'date']  = df_IS.loc[idx,'index']
        try:
            datetime.strptime(df_IS.loc[idx, 'index'], '%Y-%m')
        except ValueError:
            continue
        df.loc[idx,'period']  = df_IS.loc[idx, 'period']
        df.loc[idx,'eps']  = df_IS.loc[idx, 'eps']
        if datetime.strptime(df_IS.loc[idx, 'index'], '%Y-%m').year < BacktestParms.FirstDateFinData:
            break 

    return df

def IncomeStatementQuarter(tckr, BacktestParms):   
    # Try the request.get a few times.  Sometimes throws errors.
    for errorloop in range(10):
        try:
            data = requests.get(f"https://financialmodelingprep.com/api/v3/income-statement/{tckr}?period=quarter&limit=400&apikey=" + api_key)
            
            data = data.json()
            break
        except requests.exceptions.RequestException as e:
            print(e)
            continue

    if 'error' not in data:
        df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
        
        for idx in range(len(data)):    
            df.loc[idx,'Tckr']  = data[idx]['symbol']
            df.loc[idx,'date']  = data[idx]['date']
            try:
                datetime.strptime(data[idx]['date'], '%Y-%m-%d')
            except ValueError:
                continue
            df.loc[idx,'period']  = data[idx]['period']
            df.loc[idx,'eps']  = data[idx]['eps']
            if datetime.strptime(data[idx]['date'], '%Y-%m-%d').year < BacktestParms.FirstDateFinData:
                break 
    else:
        print('Error reading Income Statement Quarter for', tckr)
    return df

def IncomeStatementQuarterdf(tckr, BacktestParms):   
    # Try the request.get a few times.  Sometimes throws errors.
    for errorloop in range(10):
        sleep(1)    # sleep time in sec.
        try:
            data = requests.get(f"https://financialmodelingprep.com/api/v3/income-statement/{tckr}?period=quarter&limit=400&apikey=" + api_key)
            
            data = data.json()
            break
        except requests.exceptions.RequestException as e:
            print(e)
            continue

    df = pd.DataFrame(data)
    fname = os.getcwd() + '//' + BacktestParms.data_path + '//' + 'AAPLIncomeStatementQuarter' + '.csv'
    df.to_csv(fname)

# Pull ouut the data required if not empty
#    if df.empty:
#        MutualFundQtrChg = ''
#        MutualFundQtrChgPer = ''
#    else:
#        MutualFundQtrChg = df['change'].sum()
#        MutualFundQtrChgPer = MutualFundQtrChg / (df['shares'].sum() - MutualFundQtrChg) # Change / previous quarter total

    return df

def FinancialRatiosQuarter(tckr, BacktestParms):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/ratios/{tckr}?period=quarter&limit=140&apikey="+ api_key)
    data = data.json()

    if 'error' not in data:
        df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
        
        for idx in range(len(data)):    
            df.loc[idx,'Tckr']  = data[idx]['symbol']
            df.loc[idx,'date']  = data[idx]['date']
            try:
                datetime.strptime(data[idx]['date'], '%Y-%m-%d')
            except ValueError:
                continue
            df.loc[idx,'pe']  = data[idx]['priceEarningsRatio']
            df.loc[idx,'peg']  = data[idx]['priceEarningsToGrowthRatio']
            df.loc[idx,'FCFperShare']  = data[idx]['freeCashFlowPerShare']
            df.loc[idx,'PTB']  = data[idx]['priceToBookRatio']
            df.loc[idx,'PTFCF']  = data[idx]['priceToFreeCashFlowsRatio']
            if datetime.strptime(data[idx]['date'], '%Y-%m-%d').year < BacktestParms.FirstDateFinData:
                break 
    else:
        print('Error reading Financial Ratios Quarter for', tckr)
    return df

def CompanyQuote(tckr, BacktestParms):
    sleep(1)    # sleep time in sec.
    data = requests.get(f"https://financialmodelingprep.com/api/v3/quote/{tckr}?apikey="+ api_key)
    data = data.json()

    if 'error' not in data:
        df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
          
        df.loc[0,'Tckr']  = data[0]['symbol']
        df.loc[0,'price']  = data[0]['price']
        df.loc[0,'volume']  = data[0]['volume']
        df.loc[0,'avgVolume']  = data[0]['avgVolume']
        df.loc[0,'eps']  = data[0]['eps']
        df.loc[0,'pe']  = data[0]['pe']
        df.loc[0,'eadate']  = data[0]['earningsAnnouncement']
        df.loc[0,'sharesOutstanding']  = data[0]['sharesOutstanding']
    else:
        print('Error reading Company Quote for', tckr)
    return df

def FinancialGrowthQuarter(tckr, BacktestParms):
    sleep(1)    # sleep time in sec.
    data = requests.get(f"https://financialmodelingprep.com/api/v3/financial-growth/{tckr}?period=quarter&limit=80&apikey="+ api_key)
    data = data.json()

    if 'error' not in data:
        df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
        
        for idx in range(len(data)):    
            df.loc[idx,'Tckr']  = data[idx]['symbol']
            df.loc[idx,'date']  = data[idx]['date']
            try:
                datetime.strptime(data[idx]['date'], '%Y-%m-%d')
            except ValueError:
                print('Error')
                continue
            df.loc[idx,'revenueGrowth']  = data[idx]['revenueGrowth']
            df.loc[idx,'grossProfitGrowth']  = data[idx]['grossProfitGrowth']
            df.loc[idx,'epsgrowth']  = data[idx]['epsgrowth']
            df.loc[idx,'dividendsperShareGrowth']  = data[idx]['dividendsperShareGrowth']
            df.loc[idx,'freeCashFlowGrowth']  = data[idx]['freeCashFlowGrowth']
            if datetime.strptime(data[idx]['date'], '%Y-%m-%d').year < BacktestParms.FirstDateFinData:
                break 
    else:
        print('Error reading Financial Growth Quarter for', tckr)
    return df

def KeyMetricsQuarter(tckr, BacktestParms): 
   # key_metrics_quarterly = FundamentalAnalysis.key_metrics(tckr, api_key, period="quarter")
    
    data = requests.get(f"https://financialmodelingprep.com/api/v3/key-metrics/{tckr}?period=quarter&limit=130&apikey="+ api_key)
    data = data.json()

    df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis

    for idx in range(len(data)):    
        df.loc[idx,'Tckr']  = data[idx]['symbol']
        df.loc[idx,'date']  = data[idx]['date']
        try:
            datetime.strptime(data[idx]['date'], '%Y-%m-%d')
        except ValueError:
            continue
        df.loc[idx,'dividendYield']  = data[idx]['dividendYield']
        if datetime.strptime(data[idx]['date'], '%Y-%m-%d').year < BacktestParms.FirstDateFinData:
            break 

    return df

def EndofQrtrDate(date_dt):
    quarter = round((date_dt.month-1)/3+1,0)
    if quarter == 1:
       end_date_dt = datetime(date_dt.year,3,31).date()
    elif quarter == 2:
        end_date_dt = datetime(date_dt.year,6,30).date()
    elif quarter == 3:
        end_date_dt = datetime(date_dt.year,9,30).date()
    else:
        end_date_dt = datetime(date_dt.year,12,31).date()
    return end_date_dt

def EarningsSurprise(tckr, BacktestParms):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/earnings-surpises/{tckr}?apikey="+ api_key)
    data = data.json()

    df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
        
    for idx in range(len(data)):    
        df.loc[idx,'Tckr']  = data[idx]['symbol']
        df.loc[idx,'EAdate']  = data[idx]['date']
        end_date_dt = EndofQrtrDate(datetime.strptime(data[idx]['date'], '%Y-%m-%d'))
        df.loc[idx,'date']  = end_date_dt.strftime('%Y-%m-%d')
        df.loc[idx,'actualEarningResult']  = data[idx]['actualEarningResult']
        df.loc[idx,'estimatedEarning']  = data[idx]['estimatedEarning']
        if data[idx]['estimatedEarning'] == 0:
            df.loc[idx,'earningsSurprise'] = 0
        else:
            df.loc[idx,'earningsSurprise']  = round((data[idx]['actualEarningResult'] - data[idx]['estimatedEarning']) / data[idx]['estimatedEarning'],2)
        if datetime.strptime(data[idx]['date'], '%Y-%m-%d').year < BacktestParms.FirstDateFinData:
            break 
    return df

def SectorsPerformance(tckr, BacktestParms):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/historical-sectors-performance?limit=50&apikey="+ api_key)
    data = data.json()
    #
    # Successfully read the data.  It only contained the last 4 days.  Paid subscription accesses more history?
    #

    if 'error' not in data:
        df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
        
        for idx in range(len(data)):    
            df.loc[idx,'Tckr']  = data[idx]['symbol']
            df.loc[idx,'date']  = data[idx]['date']
            try:
                datetime.strptime(data[idx]['date'], '%Y-%m-%d')
            except ValueError:
                continue
            df.loc[idx,'actualEarningResult']  = data[idx]['actualEarningResult']
            df.loc[idx,'estimatedEarning']  = data[idx]['estimatedEarning']
            df.loc[idx,'earningsSurprise']  = round((data[idx]['actualEarningResult'] - data[idx]['estimatedEarning']) / data[idx]['estimatedEarning'],2)
            if datetime.strptime(data[idx]['date'], '%Y-%m-%d').year < BacktestParms.FirstDateFinData:
                break
    else:
        print('Error reading SectorsPerformance for', tckr)
    return df

def IncomeStatementQuarterFMPCompleteDataframe(tckr, BacktestParms):   
  
    df = FundamentalAnalysis.income_statement(tckr, api_key, period="quarter")
    df = df.T.reset_index()
    
    return df