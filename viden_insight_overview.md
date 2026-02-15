# Viden Insight - System Overview & Architecture

## 1. Mission & Purpose
**Viden Insight** is a proprietary market intelligence dashboard built for **Viden Strategy**. It transforms raw financial data into branded, high-level business insights ("The Viden Verdict").
- **Goal**: Provide institutional-grade analysis of Trend, Volatility, and Fundamentals.
- **User**: Portfolio managers and analysts at Viden Strategy.
- **Brand Identity**: Premium, dark-mode aesthetic (Teal/Slate) matching `videnstrategy.com`.

## 2. Technology Stack
- **Framework**: `Shiny for Python` (Server-side rendering, reactive state).
- **Database**: `Supabase` (PostgreSQL) - Primary source of truth for historical price data.
- **External Data**: `OpenBB Platform (SDK)` - Integration with Yahoo Finance and FRED (St. Louis Fed).
- **Visualization**:
    - `Matplotlib`: Static, stylized charts for "The Verdict" (Brand aligned).
    - `Plotly`: Interactive, zoomable charts for "Deep Dive" analysis.
- **Caching**: `diskcache` (Local file-based caching) for OpenBB API calls.
- **Authentication**: (Planned) Supabase Auth.

## 3. Application Structure
The application follows a modular architecture:

### **A. Core Logic**
- **`app.py`**: The entry point. Handles UI layout (Sidebar, Tabs) and Server logic (Reactive wiring).
- **`analytics.py`**: The "Business Brain". Contains the logic for:
    - **Regime Detection**: Markup/Decline based on MA crossovers (50/200).
    - **Volatility Analysis**: Rolling standard deviation characterization.
    - **Viden Verdict**: Generates the plain-English summary text.

### **B. Data Layer**
- **`data_manager.py`**: **Supabase Interface**.
    - Fetches `price_history` for the "Verdict" tab.
    - Logic: *Fetch Latest Date -> Calculate Lookback -> Query DB*.
- **`openbb_manager.py`**: **OpenBB Interface**.
    - Fetches Live Price, Fundamentals (P/E, Margins), and Macro (CPI).
    - Wraps calls in `cache_manager` logic to prevent rate limits.
- **`cache_manager.py`**: Handles local persistence of OpenBB responses (JSON serialization).

### **C. Frontend / Assets**
- **`www/custom.css`**: The Design System. Defines variables (`--viden-teal`, `--bg-dark`), glassmorphism cards, and typography (`Inter`).

## 4. Current Data Flow
The app operates in two distinct modes:

### **Mode 1: The Verdict (Internal Data)**
1.  **Source**: Supabase (`price_history` table).
2.  **Trigger**: App Load / Ticker Change.
3.  **Flow**: `app.py` -> `data_manager.py` -> **Supabase** -> `analytics.py` -> UI.
4.  **Purpose**: Instant, low-latency trend analysis on curated data.

### **Mode 2: Deep Dive (External Data)**
1.  **Source**: OpenBB (Yahoo Finance, FRED).
2.  **Trigger**: User clicks "Run Deep Dive" button.
3.  **Flow**: `app.py` -> `openbb_manager.py` -> **Local Disk Cache** -> (if miss) **OpenBB SDK** -> UI.
4.  **Purpose**: Real-time exploration and fundamental research.

## 5. Future Data Strategy: "The Knowledge Base"
Currently, "Deep Dive" research is ephemeral (cached locally). The strategic vision is to move this to **Supabase**.

### **Proposal: Research-as-an-Asset**
Instead of just displaying external data, Viden Insight should **ingest** it.

**New Workflow:**
1.  **User** requests analysis for "NVDA".
2.  **App** checks Supabase table `research_reports` for a recent entry (e.g., < 24 hours old).
3.  **If Found**: Returns stored data (zero API cost, instant load).
4.  **If Missing/Stale**:
    - App calls OpenBB (Yahoo/FRED).
    - App **writes** the result to Supabase (`research_reports`, `macro_indicators`).
    - App displays data to user.

**Benefit**: Over time, Viden Strategy builds a proprietary, queryable database of fundamentals and macro indicators without paying for expensive historical data subscriptions, simply by capturing the research its users perform.
