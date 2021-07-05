from datetime import datetime
from datetime import timedelta
from datetime import date

import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import numpy as np
import pandas as pd


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
'''

def Top5perFinData(BacktestParms, FinData_df):

    def TopPerQrtr(df,column_name, per):
        Append_df = pd.DataFrame(index=range(1), columns=['Tckr'])  # Create the dataframe.  Columns are filled out later.
        
        QtrList = df.date.unique().tolist()
        for cnt in range(len(QtrList)):
            # Rows with the current quarter data
            df_qrtr = df.loc[df['date'] == QtrList[cnt]]
            # Take the top 5%
            df_qrtr = df_qrtr.nlargest(int(len(df_qrtr)*per), column_name)       
            # append to the ansswer
            Append_df = Append_df.append(df_qrtr)
        Append_df = Append_df[1:]
        return Append_df

    print('-------------------------------------------')    
    print('Process Financial Data for top 5% / quarter')
    # Limit analysis to year 2000 on until I verify the OHLC data from Yahoo later.
    FinData_df['Year_x'] = FinData_df['Year_x'].astype(int)
    FinData_df = FinData_df.loc[FinData_df['Year_x'] >= BacktestParms.FirstDateFinData]
    # Limit analysis to leave time for the backtest.
    FinData_df = FinData_df.loc[FinData_df['Year_x'] <= BacktestParms.LastDateFinDate]
    #
    # EPS growth quarter top 5 percent
    #
    print('EPS growth quarter')
    df_EPSqtrGwth = FinData_df.filter(['Tckr', 'date', 'Year_x', 'fillingDate', 'period_x', 'epsgrowth'], axis=1)
    df_EPSqtrGwth = TopPerQrtr(df_EPSqtrGwth, 'epsgrowth', .05)
    df_EPSqtrGwth.insert(4, 'Top5FinDatatype', 'EPSqrtrGr')
    #
    # EPS growth year top 5 percent
    #
    print('EPS growth year')
    df_EPSyrGwth = FinData_df.filter(['Tckr', 'date', 'Year_x', 'fillingDate', 'period_x', 'eps'], axis=1)
    df_EPSyrGwth['eps'] = df_EPSyrGwth['eps'].astype(float)
    df_EPSyrGwth['epsyrgrowth'] = (df_EPSyrGwth['eps'] - df_EPSyrGwth['eps'].shift(-3)) / df_EPSyrGwth['eps'].shift(-3)
    df_EPSyrGwth = df_EPSyrGwth.replace([np.inf, -np.inf], np.nan).dropna(subset=['epsyrgrowth'])
    df_EPSyrGwth = TopPerQrtr(df_EPSyrGwth, 'epsyrgrowth', .05)
    df_EPSyrGwth.insert(4, 'Top5FinDatatype', 'EPSyrGr')
    #
    # Gross Profit margin (%) top 5 percent
    #
    print('Gross Profit margin (%)')
    df_GPMper = FinData_df.filter(['Tckr', 'date', 'Year_x', 'fillingDate', 'period_x', 'grossProfitRatio'], axis=1)
    df_GPMper = TopPerQrtr(df_GPMper, 'grossProfitRatio', .05)
    df_GPMper.insert(4, 'Top5FinDatatype', 'GPMper')
    #
    # Revenue % change quarter top 5 percent
    #
    print('Revenue % change quarter')
    df_RevqtrGwth = FinData_df.filter(['Tckr', 'date', 'Year_x', 'fillingDate', 'period_x', 'revenueGrowth'], axis=1)
    df_RevqtrGwth = TopPerQrtr(df_RevqtrGwth, 'revenueGrowth', .05)
    df_RevqtrGwth.insert(4, 'Top5FinDatatype', 'RevqrtrGr')
    #
    # Revenue % change year top 5 percent
    #
    print('Revenue % change year')
    df_RevyrGwth = FinData_df.filter(['Tckr', 'date', 'Year_x', 'fillingDate', 'period_x', 'revenueGrowth'], axis=1)
    df_RevyrGwth['revenueGrowth'] = df_RevyrGwth['revenueGrowth'].astype(float)
    df_RevyrGwth['Revyrgrowth'] = (df_RevyrGwth['revenueGrowth'] - df_RevyrGwth['revenueGrowth'].shift(-3)) / df_RevyrGwth['revenueGrowth'].shift(-3)
    df_RevyrGwth = df_RevyrGwth.replace([np.inf, -np.inf], np.nan).dropna(subset=['Revyrgrowth'])
    df_RevyrGwth = TopPerQrtr(df_RevyrGwth, 'Revyrgrowth', .05)
    df_RevyrGwth.insert(4, 'Top5FinDatatype', 'RevyrGr')
    #
    # ROE TTM top 5 percent
    #
    print('ROE TTM')
    df_ROE = FinData_df.filter(['Tckr', 'date', 'Year_x', 'fillingDate', 'period_x', 'returnOnEquity'], axis=1)
    df_ROE = TopPerQrtr(df_ROE, 'returnOnEquity', .05)
    df_ROE.insert(4, 'Top5FinDatatype', 'ROE')
    #
    # Net profit margin top 5 percent
    #
    print('Net profit margin')
    df_NPM = FinData_df.filter(['Tckr', 'date', 'Year_x', 'fillingDate', 'period_x', 'netProfitMargin'], axis=1)
    df_NPM = TopPerQrtr(df_NPM, 'netProfitMargin', .05)
    df_NPM.insert(4, 'Top5FinDatatype', 'NPM')
    #
    # Debt to equity ratio top 5 percent
    #
    print('Debt to equity ratio')
    df_DER = FinData_df.filter(['Tckr', 'date', 'Year_x', 'fillingDate', 'period_x', 'debtEquityRatio'], axis=1)
    df_DER = TopPerQrtr(df_DER, 'debtEquityRatio', .05)
    df_DER.insert(4, 'Top5FinDatatype', 'DER')
    #
    # Total market cap top 5 percent
    #
    print('Total market cap')
    df_MktCap = FinData_df.filter(['Tckr', 'date', 'Year_x', 'fillingDate', 'period_x', 'marketCapitalization'], axis=1)
    df_MktCap = TopPerQrtr(df_MktCap, 'marketCapitalization', .05)
    df_MktCap.insert(4, 'Top5FinDatatype', 'MktCap')
    #
    # Benchmark
    #
    print('Benchmark')
    df_Bmrk = FinData_df.filter(['Tckr', 'date', 'Year_x', 'fillingDate', 'period_x'], axis=1)
    df_Bmrk = df_Bmrk.loc[df_Bmrk['Tckr'] == 'AMZN']   # Know AMZN has complete data
    df_Bmrk.insert(4, 'Top5FinDatatype', 'Bmrk')
    df_Bmrk['Tckr'] = 'SPY'
   
    FinDataTrade_df = df_EPSqtrGwth
    FinDataTrade_df = FinDataTrade_df.append(df_EPSyrGwth)
    FinDataTrade_df = FinDataTrade_df.append(df_GPMper)
    FinDataTrade_df = FinDataTrade_df.append(df_RevqtrGwth)
    FinDataTrade_df = FinDataTrade_df.append(df_RevyrGwth)
    FinDataTrade_df = FinDataTrade_df.append(df_ROE)
    FinDataTrade_df = FinDataTrade_df.append(df_NPM)
    FinDataTrade_df = FinDataTrade_df.append(df_DER)
    FinDataTrade_df = FinDataTrade_df.append(df_MktCap)
    FinDataTrade_df = FinDataTrade_df.append(df_Bmrk)
    
    FinDataTrade_df = FinDataTrade_df.filter(['Tckr', 'date', 'Year_x', 'fillingDate', 'Top5FinDatatype', 'period_x'], axis=1)
    FinDataTrade_df = FinDataTrade_df.sort_values(by=['Tckr']).reset_index(drop=True)
    FinDataTrade_df = FinDataTrade_df.reset_index(drop=True)
    
    FinDatafname = os.getcwd() + '/' + 'Stock Universe' + '/' + 'FundamentalDataTrade.csv'
    FinDataTrade_df.to_csv(FinDatafname)

    return FinDataTrade_df

def TradeWindowDates(BacktestParms, FinDataTrade_df):
    # FunDatafname = os.getcwd() + '/' + 'Stock Universe' + '/' + 'FundamentalData.csv'
    # FinData_df = pd.read_csv(FunDatafname, index_col=0)
           
    #
    # Add trading windows to the data file
    # Start out simple.  One year trading window
    #  Start - last day of the quarter when it hit's the list
    #  End - one year later
    #FinData_df        

    FinDatafname = os.getcwd() + '/' + 'Stock Universe' + '/' + 'FundamentalDataTrade.csv'
    FinDataTrade_df = pd.read_csv(FinDatafname, index_col=0, parse_dates = ['fillingDate'])
   
    FinDataTrade_df['TradeWindowStartDate_dt'] = FinDataTrade_df['fillingDate']    # Enter date is the date the income statement is accepted.  Info is publically available    
    FinDataTrade_df['TradeWindowEndDate_dt'] = FinDataTrade_df['fillingDate'] + pd.offsets.DateOffset(years=1)
    FinDataTrade_df['TradeWindowStartDate_str'] = FinDataTrade_df['TradeWindowStartDate_dt'].dt.strftime('%m/%d/%Y')  # Merges on string dates downstream
    FinDataTrade_df['TradeWindowEndDate_str'] = FinDataTrade_df['TradeWindowEndDate_dt'].dt.strftime('%m/%d/%Y')
    # FinData_df.to_csv(FinDatafname)
    
    return FinDataTrade_df