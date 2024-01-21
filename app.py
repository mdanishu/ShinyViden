from shiny import App, ui, render
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import psycopg

# Read the CSV file
hist_df = pd.read_csv('Stock_History.csv')
# Convert the 'Date' column to datetime format (if not already)
hist_df['Date'] = pd.to_datetime(hist_df['Date'])
tickers = hist_df['Ticker'].unique()

# Database credentials
supa_host = os.getenv("supa_host")
supa_database = os.getenv("supa_database")
supa_port = os.getenv("supa_port")
supa_user = os.getenv("supa_user")
supa_password = os.getenv("supa_password")

# Define the UI
app_ui = ui.page_fluid(
    ui.panel_title("Danish Shiny for Equities"),
    ui.input_select("ticker", "Select Ticker", choices=tickers.tolist()),
    ui.input_select("time_period", "Select Time Period", 
                    choices=['3 months', '6 months', '1 year', '5 years', 'All time']),
    ui.output_plot("stock_plot")
)

# Define the server logic
def server(input, output, session):



    @output
    @render.plot
    def stock_plot():
        ticker = input.ticker()
        time_period = input.time_period()
        ticker_df = hist_df[hist_df['Ticker'] == ticker]

        if ticker_df.empty:
            # Handle case with no data
            return

        # Filter based on time period
        if time_period != 'All time':
            end_date = ticker_df['Date'].max()
            start_date = {
                '3 months': end_date - timedelta(days=90),
                '6 months': end_date - timedelta(days=180),
                '1 year': end_date - timedelta(days=365),
                '5 years': end_date - timedelta(days=365 * 5)
            }[time_period]
            ticker_df = ticker_df[ticker_df['Date'] >= start_date]

        ticker_df = ticker_df.sort_values(by='Date')
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(ticker_df['Date'], ticker_df['Price'], label='Price')
        ax.plot(ticker_df['Date'], ticker_df['50d MA'], label='50 Day Moving Average')
        ax.plot(ticker_df['Date'], ticker_df['200d MA'], label='200 Day Moving Average')


        # ... Add other plot elements as in your Streamlit app
        ax.legend()

        return fig

app = App(app_ui, server)