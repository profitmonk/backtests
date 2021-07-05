from datetime import datetime
import os.path
import numpy as np
import pandas as pd
import requests
from time import sleep
import FundamentalAnalysis     # https://pypi.org/project/FundamentalAnalysis/

# Modules

api_key = "3d319882a7d958543097ee3985fafada"

def IncomeStatementQuarterFMPCompleteDataframe(tckr, BacktestParms):   
  
    df = FundamentalAnalysis.income_statement(tckr, api_key, period="quarter")
    df = df.T.reset_index()
    df = df[df['index'].str.contains("-")]                # Fixing some tckr are missing index dates
    df.insert(1, 'Tckr', tckr)                            # Insert tckr to enable merge later
    df.insert(2, 'Year', pd.to_datetime(df['index']).apply(lambda x: x.strftime('%Y')))  # Insert a year to merge MktCap
    df.rename(columns={'index': 'date'}, inplace=True)    # Downstream uses 'date' to merge
                    
    return df

def FinancialRatiosQuarterFMPCompleteDataframe(tckr, BacktestParms):   
  
    df = FundamentalAnalysis.financial_ratios(tckr, api_key, period="quarter")
    df = df.T.reset_index()
    df = df[df['index'].str.contains("-")]                # Fixing some tckr are missing index dates
    df.insert(1, 'Tckr', tckr)                            # Insert tckr to enable merge later
    df.insert(2, 'Year', pd.to_datetime(df['index']).apply(lambda x: x.strftime('%Y')))  # Insert a year to merge MktCap
    df.rename(columns={'index': 'date'}, inplace=True)    # Downstream uses 'date' to merge
    
    return df

def FinancialGrowthQuarterFMPCompleteDataframe(tckr, BacktestParms):   
  
    df = FundamentalAnalysis.financial_statement_growth(tckr, api_key, period="quarter")
    df = df.T.reset_index()
    df = df[df['index'].str.contains("-")]                # Fixing some tckr are missing index dates
    df.insert(1, 'Tckr', tckr)                            # Insert tckr to enable merge later
    df.insert(2, 'Year', pd.to_datetime(df['index']).apply(lambda x: x.strftime('%Y')))  # Insert a year to merge MktCap
    df.rename(columns={'index': 'date'}, inplace=True)    # Downstream uses 'date' to merge
    
    return df

def MarketCapFMPCompleteDataframe(tckr, BacktestParms):   
  
    df = FundamentalAnalysis.enterprise(tckr, api_key)
    df = df.T.reset_index()
    df.insert(1, 'Tckr', tckr)                            # Insert tckr to enable merge later
    df.rename(columns={'index': 'Year'}, inplace=True)    # Downstream uses 'date' to merge

    return df