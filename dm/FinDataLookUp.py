import datetime  # For datetime objects
import os.path
import numpy as np
import pandas as pd
import requests
from time import sleep

'''
# Modules
from details import available_companies
from details import profile
from details import quote
from details import enterprise
from details import rating
from details import discounted_cash_flow
from details import earnings_calendar

from financial_statements import balance_sheet_statement
from financial_statements import income_statement
from financial_statements import cash_flow_statement

from ratios import key_metrics
from ratios import financial_ratios
from ratios import financial_statement_growth

from stock_data import stock_data
from stock_data import stock_data_detailed
'''

api_key = "3d319882a7d958543097ee3985fafada"

def SectorIndustry(tckr):
    sleep(5)    # sleep time in sec.
    data = requests.get(f"https://financialmodelingprep.com/api/v3/profile/{tckr}?apikey="+ api_key)
    data = data.json()

    if 'error' not in data:
        sector = data[0]['sector']
        industry = data[0]['industry']
        exchange = data[0]['exchange']
    else:
        print('Error reading Sector Industry for', tckr)
        
    return (sector, industry, exchange)


def SectorIndustrydf(tckr):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/profile/{tckr}?apikey="+ api_key)
    data = data.json()
    
    df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    try:
        data[0]['symbol']
        if 'error' not in data:
            df.loc[0,'Tckr']  = data[0]['symbol']
            df.loc[0,'sector'] = data[0]['sector']
            df.loc[0,'industry'] = data[0]['industry']
            df.loc[0,'exchange'] = data[0]['exchange']
        else:
            print('Error reading Sector Industry df for', tckr)
        return df
    except IndexError:
        print('Sector Industry Error')
        return df

def CompanyQuote(tckr):
    print(tckr)
    data = requests.get(f"https://financialmodelingprep.com/api/v3/quote/{tckr}?apikey="+ api_key)
    data = data.json()

    if data:    # Check if data is a valid list
        Tckr = data[0]['symbol']
        Name = data[0]['name']
        Price = data[0]['price']
        Volume = data[0]['volume']
        AvgVolume = data[0]['avgVolume']
        EPS = data[0]['eps']
        PE = data[0]['pe']
        EAdate = data[0]['earningsAnnouncement']
        SharesOutstanding  = data[0]['sharesOutstanding']

    else:
        print('Error reading', tckr)
        Tckr = tckr
        Name = 'Error'
        Price = 'Error'
        Volume = 'Error'
        AvgVolume = 'Error'
        EPS = 'Error'
        PE = 'Error'
        EAdate = 'Error'
        SharesOutstanding  = 'Error'

    return Tckr, Name, Price, Volume, AvgVolume, EPS, PE, EAdate, SharesOutstanding

def CompanyQuotedf(tckr):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/quote/{tckr}?apikey="+ api_key)
    data = data.json()
    
    df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis 
          
    df.loc[0,'Price'] = data[0]['price']
    
    df.loc[0,'Volume'] = data[0]['volume']
    df.loc[0,'AvgVolume']  = data[0]['avgVolume']
    df.loc[0,'EPS'] = data[0]['eps']
    df.loc[0,'PE'] = data[0]['pe']
    df.loc[0,'EAdate'] = data[0]['earningsAnnouncement']
    df.loc[0,'SharesOutstanding'] = data[0]['sharesOutstanding']

    return df

def FinancialRatiosQuarter(tckr):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/ratios/{tckr}?period=quarter&limit=140&apikey="+ api_key)
    data = data.json()
    
    # If recent IPO the list will be empty
    if len(data) == 0:
        return tckr, np.nan, np.nan, np.nan, np.nan, np.nan

    Tckr = data[0]['symbol']
    PE = data[0]['priceEarningsRatio']
    PEG = data[0]['priceEarningsToGrowthRatio']
    FCFperShare = data[0]['freeCashFlowPerShare']
    PTB = data[0]['priceToBookRatio']
    PTFCF = data[0]['priceToFreeCashFlowsRatio']

    return Tckr, PE, PEG, FCFperShare, PTB, PTFCF

def FinancialRatiosQuarterdf(tckr):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/ratios/{tckr}?period=quarter&limit=140&apikey="+ api_key)
    data = data.json()
    
    df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    df.loc[0,'PE'] = data[0]['priceEarningsRatio']
    df.loc[0,'PEG'] = data[0]['priceEarningsToGrowthRatio']
    df.loc[0,'FCFperShare'] = data[0]['freeCashFlowPerShare']
    df.loc[0,'PTB'] = data[0]['priceToBookRatio']
    df.loc[0,'PTFCF'] = data[0]['priceToFreeCashFlowsRatio']

    return df

def FinancialGrowthQuarter(tckr):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/financial-growth/{tckr}?period=quarter&limit=80&apikey="+ api_key)
    data = data.json()
    
    # If recent IPO the list will be empty
    if len(data) == 0:
        return tckr, np.nan, np.nan, np.nan, np.nan, np.nan

    Tckr = data[0]['symbol']
    RevenueGrowth = data[0]['revenueGrowth']
    GrossProfitGrowth = data[0]['grossProfitGrowth']
    EPSgrowth = data[0]['epsgrowth']
    DividendsperShareGrowth = data[0]['dividendsperShareGrowth']
    FreeCashFlowGrowth = data[0]['freeCashFlowGrowth']

    return Tckr, RevenueGrowth, GrossProfitGrowth, EPSgrowth, DividendsperShareGrowth, FreeCashFlowGrowth

def FinancialGrowthQuarterdf(tckr):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/financial-growth/{tckr}?period=quarter&limit=80&apikey="+ api_key)
    data = data.json()
    
    df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    df.loc[0,'RevenueGrowth'] = data[0]['revenueGrowth']
    df.loc[0,'GrossProfitGrowth'] = data[0]['grossProfitGrowth']
    df.loc[0,'EPSgrowth'] = data[0]['epsgrowth']
    df.loc[0,'DividendsperShareGrowth'] = data[0]['dividendsperShareGrowth']
    df.loc[0,'FreeCashFlowGrowth'] = data[0]['freeCashFlowGrowth']

    return df

def KeyMetricsQuarter(tckr):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/key-metrics/{tckr}?period=quarter&limit=130&apikey="+ api_key)
    data = data.json()
    
    # If recent IPO the list will be empty
    if len(data) == 0:
        return tckr, np.nan
    
    Tckr = data[0]['symbol']
    DividendYield = data[0]['dividendYield']

    return Tckr, DividendYield

def KeyMetricsQuarterdf(tckr):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/key-metrics/{tckr}?period=quarter&limit=130&apikey="+ api_key)
    data = data.json()

    df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    df.loc[0,'DividendYield'] = data[0]['dividendYield']

    return df

def EarningsSurprise(tckr):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/earnings-surpises/{tckr}?apikey="+ api_key)
    data = data.json()
    
    # If recent IPO the list will be empty
    if len(data) == 0:
        return tckr, np.nan, np.nan, np.nan

    Tckr = data[0]['symbol']
    ActualEarningResult = data[0]['actualEarningResult']
    EstimatedEarning = data[0]['estimatedEarning']
    EarningsSurprise = round((data[0]['actualEarningResult'] - data[0]['estimatedEarning']) / data[0]['estimatedEarning'],2)

    return Tckr, ActualEarningResult, EstimatedEarning, EarningsSurprise

def EarningsSurprisedf(tckr):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/earnings-surpises/{tckr}?apikey="+ api_key)
    data = data.json()

    df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    df.loc[0,'ActualEarningResult'] = data[0]['actualEarningResult']
    df.loc[0,'EstimatedEarning'] = data[0]['estimatedEarning']
    df.loc[0,'EarningsSurprise'] = round((data[0]['actualEarningResult'] - data[0]['estimatedEarning']) / data[0]['estimatedEarning'],2)

    return df

def ProspectsSectorIndustry(tckr):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/profile/{tckr}?apikey="+ api_key)
    data = data.json()

    Tckr = data[0]['symbol']
    Sector = data[0]['sector']
    Industry = data[0]['industry']
    Exchange = data[0]['exchange']
    Website = data[0]['website']

    return (Tckr, Sector, Industry, Exchange, Website)

def ProspectsSectorIndustrydf(tckr):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/profile/{tckr}?apikey="+ api_key)
    data = data.json()
    
    df = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis

    df.loc[0,'Sector'] = data[0]['sector']
    df.loc[0,'Industry'] = data[0]['industry']
    df.loc[0,'Exchange'] = data[0]['exchange']
    df.loc[0,'Website'] = data[0]['website']

    return df
