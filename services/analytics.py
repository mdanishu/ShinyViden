
import pandas as pd
import numpy as np

def calculate_regime(df):
    """
    Determines the market regime based on Price relative to 50d and 200d Moving Averages.
    Returns a tuple: (Regime Name, Description)
    """
    if df.empty:
        return ("Unknown", "No data available")
    
    # Get latest row
    latest = df.iloc[-1]
    price = latest['Price']
    ma50 = latest['50d MA']
    ma200 = latest['200d MA']
    
    # Check for NaN
    if pd.isna(ma50) or pd.isna(ma200):
        return ("Uncertain", "Insufficient data for moving averages")

    # Logic
    if price > ma200:
        if price > ma50:
            if ma50 > ma200:
                return ("Markup", "Bullish trend confirmed. Price and 50d MA above 200d MA.")
            else:
                return ("Accumulation", "Early bullish signs. Price above 200d MA, but 50d MA lagging.")
        else:
            return ("Pullback", "Price above 200d MA but below 50d MA. Possible buying opportunity or trend weakening.")
    else: # Price <= ma200
        if price < ma50:
            if ma50 < ma200:
                return ("Decline", "Bearish trend confirmed. Price and 50d MA below 200d MA.")
            else:
                return ("Distribution", "Early bearish signs. Price below 200d MA, though 50d MA still elevated.")
        else:
            return ("Recovery/Bounce", "Price below 200d MA but reclaiming 50d MA. Potential reversal or dead cat bounce.")

def calculate_volatility(df, window=20):
    """
    Calculates volatility based on rolling standard deviation of daily returns.
    Returns: (Level, Annualized Volatility %)
    """
    if len(df) < window:
        return ("Unknown", 0.0)
    
    # Calculate daily returns
    df = df.copy()
    df['Returns'] = df['Price'].pct_change()
    
    # Annualized volatility (assuming 252 trading days)
    # We take the vol of the last 'window' days
    recent_vol = df['Returns'].tail(window).std() * np.sqrt(252) * 100
    
    if pd.isna(recent_vol):
         return ("Unknown", 0.0)

    if recent_vol < 15:
        return ("Low", recent_vol)
    elif recent_vol < 35:
        return ("Medium", recent_vol)
    else:
        return ("High", recent_vol)

def generate_verdict(ticker, df):
    """
    Generates a plain-english summary of the stock's status.
    """
    regime, regime_desc = calculate_regime(df)
    vol_level, vol_val = calculate_volatility(df)
    
    verdict = f"**{ticker}** is currently in a **{regime}** phase. "
    verdict += f"{regime_desc} "
    verdict += f"\n\nVolatility is **{vol_level}** ({vol_val:.1f}% annualized). "
    
    if regime in ["Markup", "Accumulation"] and vol_level == "Low":
        verdict += "Conditions favor trend following strategies."
    elif regime in ["Decline", "Distribution"]:
        verdict += "Caution is advised. Defensive positioning recommended."
    elif vol_level == "High":
        verdict += "High volatility suggests reduced position sizing."
        
    return verdict, regime, vol_level
