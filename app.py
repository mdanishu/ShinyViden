
from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import shinyswatch
from services.data_manager import get_available_tickers
from services.analytics import generate_verdict
from services.openbb_manager import get_key_metrics, get_macro_data, get_available_macro_indicators, MACRO_INDICATORS
from services.data_router import fetch_unified_history, calculate_start_date
from pathlib import Path

# --- Branding Constants (Viden "Navy & Gold") ---
COLOR_GOLD = '#fbbf24'  # Amber-400
COLOR_NAVY = '#020b1c'  # Deepest Navy
COLOR_SLATE = '#0f172a' # Slate-900 (Cards)
COLOR_TEXT = '#94a3b8'  # Slate-400
COLOR_TEXT_BRIGHT = '#f8fafc'
COLOR_GRID = '#334155'
COLOR_BENCHMARK = '#9ca3af' # Gray-400

tickers = get_available_tickers()
TICKER_CHOICES = tickers if tickers else ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
MACRO_CHOICES = get_available_macro_indicators()

PLOTLY_DARK_DICT = {
    "plot_bgcolor": 'rgba(0,0,0,0)',
    "paper_bgcolor": 'rgba(0,0,0,0)',
    "font": {"family": "Inter, sans-serif", "color": COLOR_TEXT},
    "xaxis": {"gridcolor": COLOR_GRID, "linecolor": COLOR_GRID, "tickcolor": COLOR_TEXT, "tickfont": {"color": COLOR_TEXT}},
    "yaxis": {"gridcolor": COLOR_GRID, "linecolor": COLOR_GRID, "tickcolor": COLOR_TEXT, "tickfont": {"color": COLOR_TEXT}},
    "legend": {"font": {"color": COLOR_TEXT}},
    "modebar": {"bgcolor": 'rgba(0,0,0,0)', "color": COLOR_GOLD},
}

app_ui = ui.page_sidebar(
    ui.sidebar(
        # 1. Action Button at TOP
        ui.h6("ACTIONS", style=f"color: {COLOR_GOLD}; font-size: 0.7rem; letter-spacing: 0.1em;"),
        ui.input_action_button("analyze_btn", "Run Analysis", class_="btn-primary w-100"),
        ui.p("Fetches Live Data", style="font-size: 0.65rem; color: var(--bs-secondary); text-align: center; margin-top: 5px; margin-bottom: 20px;"),
        
        ui.hr(),
        
        # 2. Asset Selection
        ui.h6("ASSET SELECTION", style=f"color: {COLOR_GOLD}; font-size: 0.7rem; letter-spacing: 0.1em;"),
        ui.input_text("ticker", "Ticker Symbol", value="AAPL", placeholder="e.g. NVDA, BTC-USD"),
        ui.input_text("benchmark", "Benchmark (Optional)", value="", placeholder="e.g. SPY, BTC-USD"), 
        ui.p("Compare performance & metrics", style="font-size: 0.65rem; color: var(--bs-secondary);"),
        
        ui.hr(),
        
        # 3. Time Horizon (Universal)
        ui.h6("TIME HORIZON", style="color: var(--bs-secondary); font-size: 0.7rem; letter-spacing: 0.1em;"),
        ui.input_radio_buttons("time_period", None, 
                        choices=['1d', '1w', '1m', '3m', '6m', '1y', '5y', '10y', 'max'],
                        selected='1y'),
        
        ui.hr(),
        
        # 4. Conditional Macro Controls
        ui.panel_conditional(
            "input.main_tabs === 'MacroContext'",
            ui.h6("MACRO OVERLAY", style=f"color: #3b82f6; font-size: 0.7rem; letter-spacing: 0.1em;"),
            ui.input_checkbox_group("macro_indicators", None,
                choices={k: k for k in MACRO_CHOICES},
                selected=["CPI"]),
            ui.input_checkbox("overlay_price", "Show Stock Price Overlay", value=False),
        ),
        
        title="Configuration",
        bg=COLOR_SLATE,
        fg=COLOR_TEXT_BRIGHT
    ),
    
    ui.head_content(
        ui.tags.link(rel="stylesheet", href="custom.css"),
        ui.tags.style(f"""
            .sidebar {{ border-right: 1px solid {COLOR_GOLD}20 !important; }}
        """)
    ),
    
    ui.card(
        ui.row(
            ui.column(12, 
                ui.div(
                    ui.h2("Viden Insight", style=f"margin-bottom: 0px; font-weight: 800; letter-spacing: -0.5px;"),
                    ui.p("Strategic Market Intelligence", style="color: #64748b; margin-top: 5px; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em;"),
                )
            )
        ),
        full_screen=False,
        style="border: none !important; background: transparent !important; box-shadow: none !important;"
    ),
    
    ui.navset_card_pill(
        ui.nav_panel(
            "The Verdict",
            ui.layout_column_wrap(
                ui.card(
                    ui.card_header("Trend & Volatility Analysis (Live)"),
                    ui.output_ui("verdict_ui"),
                    class_="verdict-box"
                ),
                ui.card(
                    ui.card_header("Price Action Breakdown (Rebased %)" if "input.benchmark()" else "Price Action Breakdown"),
                    ui.output_plot("stock_plot"),
                ),
                width=1/1
            ),
            value="Verdict" 
        ),
        ui.nav_panel(
            "Interactive Chart",
            ui.card(
                ui.card_header("Live Price History (Zoom/Hover)"),
                output_widget("interactive_plot"),
                full_screen=True
            ),
            value="Interactive"
        ),
        ui.nav_panel(
            "Fundamentals",
            ui.card(
                ui.card_header("Key Financial Metrics"),
                ui.output_table("fundamentals_table"),
                full_screen=True
            ),
            value="Fundamentals"
        ),
        ui.nav_panel(
            "Macro Context",
            ui.card(
                ui.card_header("Economic Indicators Overlay"),
                output_widget("macro_plot"),
                full_screen=True
            ),
            value="MacroContext"
        ),
        id="main_tabs"
    ),
    
    theme=shinyswatch.theme.slate,
    title="Viden Insight",
)

def server(input, output, session):
    
    @reactive.Calc
    @reactive.event(input.analyze_btn, ignore_none=False)
    def get_live_data():
        ticker = input.ticker().strip().upper()
        period = input.time_period()
        if not ticker: return pd.DataFrame()
        ui.notification_show(f"Fetching Live Data: {ticker} ({period})...", duration=2)
        return fetch_unified_history(ticker, period=period)

    @reactive.Calc
    @reactive.event(input.analyze_btn, ignore_none=False)
    def get_benchmark_data():
        bench = input.benchmark().strip().upper()
        period = input.time_period()
        if not bench: return pd.DataFrame()
        ui.notification_show(f"Fetching Benchmark: {bench}...", duration=2)
        return fetch_unified_history(bench, period=period)

    @output
    @render.ui
    def verdict_ui():
        df = get_live_data() 
        if df.empty: return ui.p("Enter a ticker and click 'Run Analysis'.")
        
        ticker = input.ticker().strip().upper()
        
        df_calc = df.copy()
        df_calc['Price'] = df_calc['close']
        df_calc['50d MA'] = df_calc['close'].rolling(window=50).mean()
        df_calc['200d MA'] = df_calc['close'].rolling(window=200).mean()
        
        verdict_text, regime, vol = generate_verdict(ticker, df_calc)
        
        regime_class = "badge-bullish" if "Markup" in regime or "Accumulation" in regime else "badge-bearish" if "Decline" in regime or "Distribution" in regime else "badge-neutral"
        vol_class = "badge-bearish" if vol == "High" else "badge-bullish" if vol == "Low" else "badge-neutral"

        return ui.TagList(
            ui.div(
                ui.span(regime, class_=f"badge {regime_class}", style="margin-right: 0.5rem;"),
                ui.span(f"Vol: {vol}", class_=f"badge {vol_class}"),
                style="margin-bottom: 1rem;"
            ),
            ui.markdown(verdict_text)
        )

    @output
    @render.plot
    def stock_plot():
        df = get_live_data()
        df_bench = get_benchmark_data()
        
        if df.empty: return
        
        x_col = 'date' if 'date' in df.columns else df.index.name
        
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLOR_SLATE)
        ax.set_facecolor(COLOR_SLATE)
        
        if not df_bench.empty:
            # Comparative Mode (Rebased to %)
            # Align dates
            df = df.set_index(x_col).sort_index()
            df_bench = df_bench.set_index(x_col).sort_index()
            
            # Common Index
            common_idx = df.index.intersection(df_bench.index)
            if len(common_idx) > 0:
                df = df.loc[common_idx]
                df_bench = df_bench.loc[common_idx]
                
                # Rebase
                df['pct_change'] = (df['close'] / df['close'].iloc[0] - 1) * 100
                df_bench['pct_change'] = (df_bench['close'] / df_bench['close'].iloc[0] - 1) * 100
                
                ax.plot(df.index, df['pct_change'], label=f"{input.ticker().upper()} (%)", color=COLOR_GOLD, linewidth=2)
                ax.plot(df_bench.index, df_bench['pct_change'], label=f"{input.benchmark().upper()} (%)", color=COLOR_BENCHMARK, linestyle='--', linewidth=1.5)
                ax.set_ylabel("Performance (%)", color=COLOR_TEXT)
            else:
                # Fallback if no overlap
                 ax.text(0.5, 0.5, "No overlapping date range for comparison", ha='center', color=COLOR_TEXT)
        else:
            # Standard Mode (Absolute Price)
            df['Price'] = df['close']
            df['50d MA'] = df['close'].rolling(window=50).mean()
            df['200d MA'] = df['close'].rolling(window=200).mean()
            
            ax.plot(df[x_col], df['Price'], label='Price', color=COLOR_GOLD, linewidth=1.5)
            ax.plot(df[x_col], df['50d MA'], label='50d MA', color='#2dd4bf', linestyle='--', alpha=0.7)
            ax.plot(df[x_col], df['200d MA'], label='200d MA', color='#f87171', alpha=0.7)
            ax.set_ylabel("Price ($)", color=COLOR_TEXT)
            
        ax.legend(facecolor=COLOR_SLATE, edgecolor=COLOR_GRID, labelcolor=COLOR_TEXT_BRIGHT)
        ax.grid(True, color=COLOR_GRID, linestyle=':', alpha=0.3)
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.tick_params(colors=COLOR_TEXT)
        return fig

    @output
    @render_widget
    def interactive_plot():
        df = get_live_data()
        df_bench = get_benchmark_data()
        if df.empty: return go.Figure().update_layout(template="plotly_dark", **PLOTLY_DARK_DICT)
        
        x_col = 'date' if 'date' in df.columns else df.columns[0]
        
        fig = go.Figure()
        
        # Primary Asset
        fig.add_trace(go.Scatter(x=df[x_col], y=df['close'], name=input.ticker().upper(), line=dict(color=COLOR_GOLD, width=2)))
        
        # Benchmark (Secondary Y-Axis for Price comparison vs Percentage?? 
        # For interactive plot, usually better to keep absolute prices but maybe dual axis or rebase?
        # Let's do dual axis for absolute prices to see correlation of movement, simplified)
        
        if not df_bench.empty:
            x_b = 'date' if 'date' in df_bench.columns else df_bench.columns[0]
            fig.add_trace(go.Scatter(x=df_bench[x_b], y=df_bench['close'], name=input.benchmark().upper(), 
                                     line=dict(color=COLOR_BENCHMARK, width=1.5, dash='dash'), yaxis='y2'))
            
            fig.update_layout(yaxis2=dict(title=dict(text=input.benchmark().upper(), font=dict(color=COLOR_BENCHMARK)), 
                                          overlaying='y', side='right', showgrid=False, tickfont=dict(color=COLOR_BENCHMARK)))

        fig.update_layout(template="plotly_dark", **PLOTLY_DARK_DICT)
        fig.update_layout(yaxis=dict(title=dict(text=input.ticker().upper(), font=dict(color=COLOR_GOLD))))
        fig.update_layout(legend=dict(orientation="h", y=1.1))
        return fig

    @output
    @render.table
    def fundamentals_table():
        # Triggered by analysis button
        input.analyze_btn()
        ticker = input.ticker().strip().upper()
        bench = input.benchmark().strip().upper()
        
        if not ticker: return pd.DataFrame()
        
        df = get_key_metrics(ticker)
        
        # Merge Benchmark if exists
        if bench:
            df_b = get_key_metrics(bench)
            if not df_b.empty:
                # Merge on Metric
                # df has columns [Metric, Value]
                # we rename Value -> Ticker
                df = df.rename(columns={"Value": ticker})
                df_b = df_b.rename(columns={"Value": bench})
                
                df = pd.merge(df, df_b, on="Metric", how="left")
        
        # Format large numbers (M/B/T)
        def format_large_num(x):
            try:
                num = float(x)
                if abs(num) >= 1e12: return f"{num/1e12:.2f}T"
                if abs(num) >= 1e9: return f"{num/1e9:.2f}B"
                if abs(num) >= 1e6: return f"{num/1e6:.2f}M"
                return f"{num:.2f}"
            except:
                return x

        # Apply formatting to all columns except 'Metric'
        for col in df.columns:
            if col != "Metric":
                df[col] = df[col].apply(format_large_num)
            
        return df

    @output
    @render_widget
    def macro_plot():
        input.analyze_btn()
        selected = input.macro_indicators()
        overlay = input.overlay_price()
        ticker = input.ticker().strip().upper()
        
        # Get start date for filtering
        period = input.time_period()
        start_date = calculate_start_date(period)
        
        fig = go.Figure()
        
        for indicator in selected:
            # Pass start_date to filter data!
            df = get_macro_data(indicator, start_date=start_date)
            
            if not df.empty:
                if 'date' not in df.columns: df = df.reset_index()
                x_col = 'date' if 'date' in df.columns else df.columns[0]
                y_col = 'value' if 'value' in df.columns else df.select_dtypes(include='number').columns[0]
                color = MACRO_INDICATORS.get(indicator, {}).get("color", "#FFFFFF")
                fig.add_trace(go.Scatter(x=df[x_col], y=df[y_col], name=indicator, line=dict(color=color)))
        
        if overlay and ticker:
            price_df = get_live_data()
            if not price_df.empty:
                x_p = 'date' if 'date' in price_df.columns else price_df.columns[0]
                fig.add_trace(go.Scatter(x=price_df[x_p], y=price_df['close'], name=f"{ticker} Price", line=dict(color=COLOR_GOLD, width=1), yaxis="y2"))
                fig.update_layout(yaxis2=dict(title=f"{ticker} Price", overlaying="y", side="right", showgrid=False, tickfont=dict(color=COLOR_GOLD)))

        fig.update_layout(template="plotly_dark", **PLOTLY_DARK_DICT)
        fig.update_layout(legend=dict(orientation="h", y=1.1))
        return fig

app = App(app_ui, server, static_assets=str(Path(__file__).parent / "www"))