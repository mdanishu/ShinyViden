# Viden Analytics Transformation Plan

## 1. Executive Summary
- **Goal:** Transform a basic stock charter into **Viden Insight**, a branded business showcase that demonstrates analytical rigor and strategic clarity.
- **Value Prop:** Moves beyond "what happened?" (charts) to "what does it mean?" (regime identification & risk assessment).
- **Architecture:** Zero-cost storage via **Supabase (Free Tier)** and zero-cost compute via **Shiny for Python on generic free hosting (e.g., Hugging Face Spaces)**.
- **Data Strategy:** **Batch-over-stream**. Pre-calculate insights daily to ensure instant app load times and zero runtime calculation costs.
- **Key Feature:** The "Viden Verdict"—a logic-based plain-English summary of the stock's trend and volatility profile.
- **Brand Alignment:** Dark-mode, professional UI with clear CTAs driving traffic to Viden Strategy consulting services.
- **Timeline:** Core migration in Week 1, Business features in Week 2, Polish & Launch in Week 3-4.

## 2. Product Spec: "Viden Insight"

### Product Positioning
- **The Question:** "Is the market environment currently favorable for this asset?"
- **The Answer:** A clear, objective assessment of Trend (Direction) and Volatility (Risk).
- **The "So What?":** empowers users to validate their gut feel with data, establishing Viden Strategy as a trusted partner for data-driven decision making.

### Feature Set
#### P0: Core Modernization (The Foundation)
- **Supabase Integration:** Replace local CSV with Supabase generic query.
- **Performance Optimization:** Fetch only necessary columns/rows (SQL filtering).

#### P1: Business Insight Features (The Value)
- **"The Viden Verdict" Box:** A text component that generates a sentence like: *"TSLA is currently in a **Bullish Volatile** regime. Price is above the 200-day average, but daily variance suggests caution."*
- **Regime Badges:** Visual tags: `Accumulation`, `Markup`, `Distribution`, `Decline` (based on MA crossovers).
- **Risk Gauge:** Simple Low/Medium/High volatility indicator.

#### P2: Engagement & Conversion (The Growth)
- **"Download Brief" Button:** Generates a simple HTML/PDF 1-page summary of the current view (branded).
- **Consulting CTA:** Persistent sidebar or footer: *"Need this depth for your private data? Partner with Viden Strategy."*

## 3. Technical Architecture

### Data Flow (Batch ETL)
```mermaid
graph LR
    A[Market Data API (Yahoo/Finance)] -->|Daily Cron Job| B[Python ETL Script]
    B -->|Calculate Signals| C[(Supabase DB)]
    C -->|Store: Raw Hist + Daily Summary| C
    D[Shiny App] -->|Read-Only Query| C
```

### Schema Design
**Table 1: `market_summary` (The specific insight table)**
- `ticker` (PK)
- `last_close`
- `trend_status` (Enum: Bull/Bear)
- `volatility_score` (Float)
- `moving_avg_50`
- `moving_avg_200`
- `updated_at`

**Table 2: `price_history` (The raw data for charts)**
- `ticker` (Composite PK)
- `date` (Composite PK)
- `price`
- `ma_50`
- `ma_200`

### Deployment
- **Database:** Supabase (Free Tier).
- **App Hosting:** Hugging Face Spaces (Free Docker hosting for Streamlit/Shiny) or ShinyApps.io (Free tier).
- **Automation:** GitHub Actions (Free tier) running a daily Python script to update Supabase.

## 4. Prioritized Implementation Backlog

| ID | Priority | Item | Description | Effort | Technical Risk |
|---|---|---|---|---|---|
| **DAT-1** | P0 | Database Setup | Create Supabase project & tables. Seed with `Stock_History.csv`. | 1 Day | Low |
| **APP-1** | P0 | Connect App | Refactor `app.py` to fetch from Supabase instead of CSV. | 1 Day | Med |
| **BIZ-1** | P1 | Signal Logic | Implement "Regime" logic (e.g., Price > 200MA) in Python. | 2 Days | Low |
| **UI-1** | P1 | Brand Overhaul | Apply "Viden" styling (CSS, fonts, layout) to Shiny. | 2 Days | Low |
| **OPS-1** | P1 | Auto-Update | create `etl.py` and GitHub Action for daily updates. | 1 Day | Med |
| **UI-2** | P2 | Download PDF | Add "Download One-Pager" feature. | 3 Days | High (Dependencies) |

## 5. 30-Day Rollout Plan

- **Week 1: Foundation.**
    - Setup Supabase.
    - Upload historical data.
    - Connect Shiny app to DB.
    - Deploy "Alpha" to hosting to prove connectivity.
- **Week 2: Insight Engine.**
    - Code the "Viden Verdict" logic.
    - Build `etl.py` for daily data fetching.
    - Verify data quality.
- **Week 3: Branding & UX.**
    - Implement custom CSS.
    - Add consulting CTAs.
    - Refine chart aesthetics (remove default matplotlib look).
- **Week 4: Launch & Automation.**
    - Setup GitHub Actions cron.
    - Final QA.
    - Link from main videnstrategy.com site.

## 6. "What NOT to Build" (Cost Safeguards)
- **Real-time streaming:** Expensive and unnecessary for strategic views. Daily close is sufficient.
- **User Accounts/Auth:** Adds complexity and friction. Keep it public logic.
- **Complex ML forecasting:** High compute cost, low reliability. Stick to deterministic trend following.
- **News Sentiment Analysis:** expensive APIs.
