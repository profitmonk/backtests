import datetime  # For datetime objects
from datetime import timedelta
import os.path
import numpy as np
import pandas as pd

import DataLookUp
import DataLookUpProspects
import SP500

'''
  Maintain a file of tickers with their associated financial data
  
      File organization
          Tckr   Quarter  Data date   income-statement data   ...
          
    EPS > 0                        income-statement
    Free cash flow                 cash flow
    PE ratio                       financial ratios
    PEG ratio                      financial ratios
    freeCashFlowPerShareTTM        financial ratios
    priceToBookRatioTTM            financial ratios
    priceEarningsRatioTTM          financial ratios
    priceCashFlowRatioTTM          financial ratios
    priceEarningsToGrowthRatioTTM  financial ratios
    dividendYielPercentageTTM      financial ratios
    sharesOutstanding              company quote
    eps                            company quote
    earningsAnnouncement           company quote
    average volume                 company quote
    epsgrowth                      financial growth quarter
    freeCashFlowGrowth             financial growth
    sector                         company profile
    industry                       company profile
    dividend yield                 key metrics
    earnings surprises             earning surprise
    sector performance             sectors performance  
  Open the file of data that already exists.
  
'''

def GetFinancialData(TckrList, BacktestParms):
    # Confirm the directory exists and create if it doesn't
    if not os.path.exists(BacktestParms.data_path):
        print("Get_data - os.path does not exist, created it")
        os.mkdir(BacktestParms.data_path)

    #
    # Income Statement
    #
    df_IncSt = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    print('Income Statement')
    for tckr in TckrList:
        print('Income Statement', tckr)
        df_IncSt = df_IncSt.append(DataLookUp.IncomeStatementQuarter(tckr, BacktestParms))
    df_IncSt = df_IncSt[1:]
    #
    # Financial ratios
    #
    df_FinRatio = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    print('Financial ratios')
    for tckr in TckrList:
        print('Financial ratios', tckr)
        df_FinRatio = df_FinRatio.append(DataLookUp.FinancialRatiosQuarter(tckr, BacktestParms))
    df_FinRatio = df_FinRatio[1:]
    #
    # Company quote
    #
    '''
    df_Quote = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    for tckr in TckrList:
        print(tckr)
        df_Quote = df_Quote.append(DataLookUp.CompanyQuote(tckr, BacktestParms))
    df_Quote = df_Quote[1:]
    '''
    #
    # Financial growth
    #
    df_Growth = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    print('Financial growth')
    for tckr in TckrList:
        print('Financial growth', tckr)
        df_Growth = df_Growth.append(DataLookUp.FinancialGrowthQuarter(tckr, BacktestParms))
    df_Growth = df_Growth[1:]
    #
    # Profile
    #
    df_Profile = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    print('Sector Industry')
    for tckr in TckrList:
        print('Sector Industry', tckr)
        df_Profile = df_Profile.append(DataLookUpProspects.SectorIndustrydf(tckr))
    df_Profile = df_Profile[1:]
    #
    # Key Metrics
    #
    df_KeyMetrics = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    print('Key Metrics')
    for tckr in TckrList:
        print('Key Metrics', tckr)
        df_KeyMetrics = df_KeyMetrics.append(DataLookUp.KeyMetricsQuarter(tckr, BacktestParms))
    df_KeyMetrics = df_KeyMetrics[1:]
    #
    # EarningSurprise
    #
    df_Esurprise = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    for tckr in TckrList:
        print('Earning Surprise', tckr)
        df_Esurprise = df_Esurprise.append(DataLookUp.EarningsSurprise(tckr, BacktestParms))
    df_Esurprise = df_Esurprise[1:]
    df_Esurprise = df_Esurprise.reset_index(drop=True)
      
    df_data = pd.merge(df_IncSt, df_FinRatio, on=['Tckr', 'date'])
    df_data = pd.merge(df_data, df_Growth, on=['Tckr', 'date'])
    df_data = pd.merge(df_data, df_Profile, on="Tckr")
    df_data = pd.merge(df_data, df_KeyMetrics, on=['Tckr', 'date'])
    df_data = pd.merge(df_data, df_Esurprise, on=['Tckr', 'date'])
    fname = os.getcwd() + '//' + BacktestParms.data_path + '//' + 'FinancialData' + '.csv'
    df_data.to_csv(fname)
    
    return df_data
