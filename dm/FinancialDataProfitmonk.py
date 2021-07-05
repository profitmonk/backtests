import datetime  # For datetime objects
from datetime import timedelta
import os.path
import numpy as np
import pandas as pd

import DataLookUp
import DataLookUpProspects
import DataLookUpCompleteDataframe
import SP500


'''
List of financial data
- EPS% change quarter
- EPS% change year
- Gross Profit margin (%)
- Revenue % change quarter
- Revenue % change year
- ROE
- EPS as %ge of sales <OR> net profit margin
- Debt to equity ratio
- Total market cap

- EPS                        income-statement
- Gross Profit               income-statement
- CostOfRevenue              income-statement
- revenue                    income-statement
- returnOnEquityTTM          financial ratios
- grossProfitMarginTTM       financial ratios
- netProfitMarginTTM         financial ratios
- debtEquityRatioTTM         financial ratios
- epsgrowth                  financial growth
- MarketCap                  Market Cap
'''

def GetFinancialData(TckrList, BacktestParms):
    # Confirm the directory exists and create if it doesn't
    if not os.path.exists(BacktestParms.data_path):
        print("Get_data - os.path does not exist, created it")
        os.mkdir(BacktestParms.data_path)
    
    FinDatafname = os.getcwd() + '/' + 'Stock Universe' + '/' + 'FundamentalData.csv'
    if os.path.isfile(FinDatafname):
        print("Fundamental data file exists and is readable")
        FinData_df = pd.read_csv(FinDatafname, index_col=0)
        return FinData_df

    #
    # Income Statement
    #
    df_IncSt = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    for tckr in TckrList:
        print('Income Statement', tckr)
        df_IncSt = df_IncSt.append(DataLookUpCompleteDataframe.IncomeStatementQuarterFMPCompleteDataframe(tckr, BacktestParms))
    df_IncSt = df_IncSt[1:]
    
    #
    # Financial ratios
    #
    df_FinRatio = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    for tckr in TckrList:
        print('Financial ratios', tckr)
        df_FinRatio = df_FinRatio.append(DataLookUpCompleteDataframe.FinancialRatiosQuarterFMPCompleteDataframe(tckr, BacktestParms))
    df_FinRatio = df_FinRatio[1:]

    #
    # Financial growth
    #
    df_Growth = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    for tckr in TckrList:
        print('Financial growth', tckr)
        df_Growth = df_Growth.append(DataLookUpCompleteDataframe.FinancialGrowthQuarterFMPCompleteDataframe(tckr, BacktestParms))
    df_Growth = df_Growth[1:]

    #
    # Market cap
    #
    df_MrktCap = pd.DataFrame(index=range(1), columns=['Tckr'])   # Create a dataframe to hold the analysis
    
    for tckr in TckrList:
        print('Market Cap', tckr)
        df_MrktCap = df_MrktCap.append(DataLookUpCompleteDataframe.MarketCapFMPCompleteDataframe(tckr, BacktestParms))
    df_MrktCap = df_MrktCap[1:]
        
    df_data = pd.merge(df_IncSt, df_FinRatio, on=['Tckr', 'date'])
    df_data = pd.merge(df_data, df_Growth, on=['Tckr', 'date'])
    df_data = pd.merge(df_data, df_MrktCap, on=['Tckr', 'Year'])
    df_data = df_data.reset_index()
    df_data.to_csv(FinDatafname)
    
    return df_data
