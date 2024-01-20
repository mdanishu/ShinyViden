import os
import psycopg2
from psycopg2 import sql
import pandas as pd
from shiny import ui, App, render
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Database credentials
supa_host = os.getenv("supa_host")
supa_database = os.getenv("supa_database")
supa_port = os.getenv("supa_port")
supa_user = os.getenv("supa_user")
supa_password = os.getenv("supa_password")

# Read the CSV file into a DataFrame
df = pd.read_csv('Stock_History.csv')

# Get a list of all unique tickers
tickers = df['Ticker'].unique()

# Define the UI
app_ui = ui.page_fluid(
    ui.panel_title("Danish Shiny for Equities"),
    ui.input_select("ticker", "Select Ticker", choices=tickers.tolist()),
    ui.input_select("time_period", "Select Time Period", 
                    choices=['3 months', '6 months', '1 year', '5 years', 'All time']),
    ui.output_plot("stock_plot"),
    ui.input_action_button("update_button", "Update Data")  # Add this line
)

# Define the server logic
def server(input, output, session):
    @input("update_button")
    def update_data():
        # Connect to the database
        conn = psycopg2.connect(
            host=supa_host,
            database=supa_database,
            user=supa_user,
            password=supa_password,
            port=supa_port
        )

        # Create a cursor object
        cur = conn.cursor()

        # Execute the query
        cur.execute(sql.SQL("SELECT * FROM public.stock_history"))

        # Fetch all rows from the cursor
        rows = cur.fetchall()

        # Convert the rows into a pandas DataFrame
        df = pd.DataFrame(rows)

        # Save the DataFrame as a CSV file
        df.to_csv('Stock_History.csv', index=False)

        # Close the cursor and connection
        cur.close()
        conn.close()

    @output("stock_plot")
    def plot():
        ticker = input("ticker")
        time_period = input("time_period")
        ticker_df = pd.read_csv('Stock_History.csv')
        ticker_df = ticker_df[ticker_df['Ticker'] == ticker]

        if time_period != 'All time':
            end_date = datetime.now()
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