BacktestExec is the main()

Order of Operations
===================
Generate the stock universe
  - Start with all US stocks
    - Limit by price (> $3)
    - Limit by volume (100,000)
Fundamental data for all stocks
  - Download from FinacialModelingPrep.com
Process Financial data
  - Select the top 5% of tickers in each fundamental category
  - Add the trading window dates 
Execute backtest

Stock universe files
====================
ManageTickerList
  - Two ways to create a stock universe
    - Several excel files in Stock Universe directory.  
    - Look up the universe from FinancialModelingPrep.com
      - Using this one now
      
Finacial Data files
====================
FinancialDataProfitmonk
  - Accumulates financial data
DataLookUpCompleteDataframe
  - Queries to FinancialModelingPrep.com
  - Returns all the data from Income Statement, Financial ratios, Financial growth and enterprise value
  - Has to be filtered and analyzed
ProcessFinData
  - Parses the Financial data by quarter
    - Finds top 5% of the fundamental data categories
    - Adds SPY each quarter as a benchmark
  - Adds the EnterDate and ExitDate
    - Used in the backtesting
    - Started out with a simple one year trading window

Backtest files
===============
BacktestExec
  - Executes the Order of Operations described above
Backtest
  - Executes the backtest
  - Originates from backtrader.  Can be viewed as the backtrader exec
DTM_Indicators
  - Indicators for backtrader written by DTM
DTM_Strategies
  - Trading strategies for backtrader written by DTM
DTM_Sizers
  - Position sizers for backtrader written by DTM
TckrOHLCdata
  - Reads historical data from Yahoo and FMP
  - Different alternatives with different checks of dates and data
  
To Do
=====
  - Add a log file for errors reading OHLC data (TckrOHLCdata)