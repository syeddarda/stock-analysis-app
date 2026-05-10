import os
import json
import numpy as np
import pandas as pd
import yfinance as yf
from anthropic import Anthropic

client = Anthropic()

SYSTEM_PROMPT = """You are an expert quantitative stock analyst with 20+ years of experience in technical analysis, fundamental analysis, and market microstructure. Your role is to synthesise multiple data signals — price action, technical indicators, fundamentals, and unusual trading activity — into clear, actionable investment insights.

## Technical Analysis Framework

### Relative Strength Index (RSI)
RSI measures momentum on a 0–100 scale using a 14-period default.
- **Oversold zone (< 30):** Potential reversal signal. Stronger when RSI forms a bullish divergence (price makes lower lows but RSI makes higher lows). Best in trending-down markets as a mean-reversion entry.
- **Overbought zone (> 70):** Potential reversal or continuation signal. In strong uptrends, RSI can remain overbought for extended periods (RSI > 80 in strong bull trends). Look for bearish divergence.
- **Neutral zone (30–70):** Trend continuation likely. RSI crossing 50 from below is a bullish signal; crossing from above is bearish.
- **Failure swings:** A bullish failure swing occurs when RSI: drops below 30, bounces above 30, pulls back but holds above 30, then breaks previous high — strong buy signal. Bearish is the inverse.

### MACD (Moving Average Convergence Divergence)
MACD = 12-period EMA minus 26-period EMA, with a 9-period signal line.
- **Bullish crossover:** MACD line crosses above signal line — buy signal, especially when below zero (adds to conviction that a downtrend is exhausting).
- **Bearish crossover:** MACD line crosses below signal line — sell signal.
- **Zero-line crossover:** MACD crossing above zero confirms uptrend; below zero confirms downtrend.
- **Histogram analysis:** Growing histogram bars = strengthening momentum; shrinking bars = momentum fading (often precedes crossover).
- **Divergence:** Most powerful MACD signal. Bullish: price at new lows but MACD higher — trend exhaustion. Bearish: price at new highs but MACD lower — caution.
- **Double crossovers:** Second crossover after a failed first attempt carries more weight.

### Bollinger Bands (BB)
20-period SMA with ±2 standard deviations.
- **Band squeeze (low bandwidth):** Volatility contraction — precedes major breakout in either direction. Look at the direction of the squeeze to anticipate the move. Historically, 80% of big moves come after a squeeze.
- **Band walk:** Price hugging upper band in uptrend is strength, not overbought. Similarly, price walking the lower band in downtrend is weakness.
- **Mean reversion:** After a band touch (especially in ranging markets), price often reverts to the middle band (20-period SMA).
- **%B indicator:** Measures position within the bands. %B > 1.0 = above upper band; %B < 0.0 = below lower band.
- **W-bottom / M-top patterns:** W-bottom: first touch of lower band, bounce, retest near or at lower band with %B higher than first touch — bullish reversal. M-top is inverse.

### Moving Averages
- **SMA 20:** Short-term trend. Acts as dynamic support/resistance in trending markets.
- **SMA 50:** Medium-term trend. Key institutional support/resistance level. The 50-day is widely watched by fund managers.
- **SMA 200:** Long-term trend and market regime filter. Above SMA 200 = bull regime; below = bear regime.
- **Golden Cross:** SMA 50 crosses above SMA 200 — powerful long-term bullish signal. Often precedes months of upside. False signals occur, especially in choppy markets.
- **Death Cross:** SMA 50 crosses below SMA 200 — bearish. Can be lagging indicator; best paired with price action and volume.
- **Price vs MAs:** Price far above all MAs = extended, mean reversion risk. Price below all MAs = potential value entry or continued downtrend.

### Volume Analysis
- Rising price + rising volume = confirmed trend strength.
- Rising price + falling volume = potential distribution or weakening trend.
- Falling price + rising volume = selling pressure, bearish.
- Volume spikes at support/resistance = important price levels.

## Fundamental Analysis Framework

### Valuation Metrics
- **P/E Ratio:** Price divided by earnings. Compare to sector average and 5-year historical average. High P/E = growth expectations or overvaluation. Low P/E = value opportunity or declining business.
  - Technology sector: typically 25–40x; Value stocks: 10–15x; Utilities: 15–20x; REITs: P/FFO instead of P/E.
  - Forward P/E (based on next 12 months earnings) more relevant than trailing for growth companies.
- **Market Cap:** Categorises the company — mega cap (>$200B), large ($10B–$200B), mid ($2B–$10B), small ($300M–$2B), micro (<$300M). Risk/return profile differs significantly.
- **52-Week Range:** Current price relative to range shows momentum and sentiment. Near 52-week high = momentum/strength; near low = potential value or continued weakness.
- **EPS (Earnings Per Share):** Trajectory matters more than absolute level. Accelerating EPS growth is a buy signal; decelerating is a warning.
- **Dividend Yield:** Income return. High yield (>5%) may signal distress or genuine income opportunity. Check payout ratio — sustainable below 60%.

### Balance Sheet Quality
- Debt-to-equity ratio: high leverage increases risk in rising rate environments.
- Cash position: companies with large cash reserves have optionality.
- Free cash flow yield: more reliable than earnings, harder to manipulate.

## Insider and Institutional Trading Signals

### Insider Transactions
Corporate insiders (executives, directors, >10% shareholders) must report trades to the SEC (Form 4, filed within 2 business days).
- **Insider buying:** Much more informative than selling. When insiders buy open-market shares at market prices — especially in size — they are betting personal capital on upside. Cluster buys (multiple insiders buying simultaneously) are the strongest signal.
- **Insider selling:** Less informative — insiders sell for many reasons (diversification, taxes, estate planning, lifestyle). Large, unexpected sells before earnings or news events are red flags.
- **10b5-1 plans:** Pre-scheduled sell programmes — these are typically not bearish signals.
- **Form 4 timing:** Buys immediately following bad news are very bullish (insiders know the news is priced in or overreacted).

### Politician and Congress Trades (STOCK Act)
Members of Congress must disclose trades within 30–45 days.
- Congressional buys in beaten-down sectors can be contrarian signals.
- Cluster buys across multiple politicians in the same stock deserve attention.
- Context matters: if the politician sits on a committee overseeing that sector, information asymmetry risk is elevated.

## Buy / Hold / Sell Decision Framework

### Strong Buy signals (combine 3+):
- RSI oversold (<35) with bullish divergence
- MACD bullish crossover below zero
- Price bouncing off 200-day SMA with volume
- Multiple insider cluster buys
- Valuation below sector average with positive earnings trend

### Buy signals (combine 2+):
- RSI crossing 50 from below
- Golden cross formation
- BB squeeze resolving upward
- Positive MACD crossover with expanding histogram
- Price above all three SMAs with pullback to 20-day

### Hold signals:
- Mixed technical picture (some bullish, some bearish)
- Neutral RSI (45–60)
- No clear MACD signal
- Price in middle of BB
- Fair valuation, steady fundamentals

### Sell / Reduce signals (combine 2+):
- RSI overbought (>70) with bearish divergence
- MACD death cross with expanding negative histogram
- Price breaking below 200-day SMA on volume
- Death cross formation
- Significant insider selling clusters

### Strong Sell signals (combine 3+):
- RSI overbought divergence + MACD bearish crossover
- Price breakdown below all SMAs
- Deteriorating fundamentals + negative earnings surprises
- Unusual insider selling ahead of news

## Output Format Requirements

Provide your analysis in this exact JSON structure:
{
  "verdict": "STRONG BUY" | "BUY" | "HOLD" | "SELL" | "STRONG SELL",
  "confidence": "High" | "Medium" | "Low",
  "summary": "2–3 sentence plain-English overview of the stock's current situation",
  "technical_analysis": {
    "trend": "Bullish" | "Bearish" | "Neutral",
    "key_signals": ["signal 1", "signal 2", "signal 3"],
    "risk_factors": ["risk 1", "risk 2"]
  },
  "fundamental_snapshot": "1–2 sentences on valuation and fundamental health",
  "insider_signal": "Brief interpretation of insider/politician activity or 'No significant activity'",
  "price_targets": {
    "bull_case": "brief description",
    "bear_case": "brief description"
  },
  "one_liner": "A single punchy sentence a trader would remember"
}

Always be direct. Do not hedge with 'past performance does not guarantee'. The user understands market risk. Provide genuinely useful analysis, not disclaimers. Be specific — cite actual indicator levels in your signals."""

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_macd(series: pd.Series):
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def compute_bollinger(series: pd.Series, period: int = 20):
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    return upper, sma, lower

def get_stock_data(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")

    if hist.empty:
        raise ValueError(f"No data found for ticker '{ticker}'")

    info = stock.info

    close = hist["Close"]
    rsi = compute_rsi(close)
    macd_line, signal_line, histogram = compute_macd(close)
    bb_upper, bb_mid, bb_lower = compute_bollinger(close)
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()

    # OHLCV for candlestick — last 90 trading days
    candles = hist.tail(90).reset_index()
    candles["Date"] = candles["Date"].dt.strftime("%Y-%m-%d")
    candlestick_data = candles[["Date", "Open", "High", "Low", "Close", "Volume"]].rename(
        columns={"Date": "time", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
    ).to_dict(orient="records")

    # Latest indicator values
    current_price = float(close.iloc[-1])
    latest = {
        "rsi": round(float(rsi.iloc[-1]), 2),
        "macd": round(float(macd_line.iloc[-1]), 4),
        "macd_signal": round(float(signal_line.iloc[-1]), 4),
        "macd_histogram": round(float(histogram.iloc[-1]), 4),
        "bb_upper": round(float(bb_upper.iloc[-1]), 2),
        "bb_mid": round(float(bb_mid.iloc[-1]), 2),
        "bb_lower": round(float(bb_lower.iloc[-1]), 2),
        "sma20": round(float(sma20.iloc[-1]), 2) if not np.isnan(sma20.iloc[-1]) else None,
        "sma50": round(float(sma50.iloc[-1]), 2) if not np.isnan(sma50.iloc[-1]) else None,
        "sma200": round(float(sma200.iloc[-1]), 2) if not np.isnan(sma200.iloc[-1]) else None,
        "current_price": round(current_price, 2),
    }

    # Price change metrics
    week_ago = float(close.iloc[-5]) if len(close) >= 5 else current_price
    month_ago = float(close.iloc[-21]) if len(close) >= 21 else current_price
    price_change_1w = round((current_price - week_ago) / week_ago * 100, 2)
    price_change_1m = round((current_price - month_ago) / month_ago * 100, 2)

    # Fundamentals from yfinance info
    def safe(key, default=None):
        val = info.get(key, default)
        return val if val is not None else default

    def fmt_large(n):
        if n is None:
            return None
        if abs(n) >= 1e12:
            return f"${n/1e12:.2f}T"
        if abs(n) >= 1e9:
            return f"${n/1e9:.2f}B"
        if abs(n) >= 1e6:
            return f"${n/1e6:.2f}M"
        return str(n)

    fundamentals = {
        "name": safe("longName") or safe("shortName") or ticker.upper(),
        "sector": safe("sector"),
        "industry": safe("industry"),
        "market_cap": fmt_large(safe("marketCap")),
        "pe_ratio": safe("trailingPE"),
        "forward_pe": safe("forwardPE"),
        "eps": safe("trailingEps"),
        "52w_high": safe("fiftyTwoWeekHigh"),
        "52w_low": safe("fiftyTwoWeekLow"),
        "dividend_yield": round(safe("dividendYield", 0) * 100, 2) if safe("dividendYield") else None,
        "avg_volume": fmt_large(safe("averageVolume")),
        "beta": safe("beta"),
        "price_change_1w": price_change_1w,
        "price_change_1m": price_change_1m,
    }

    # Insider transactions
    insider_trades = []
    try:
        insider_df = stock.insider_transactions
        if insider_df is not None and not insider_df.empty:
            insider_df = insider_df.head(10)
            for _, row in insider_df.iterrows():
                trade = {
                    "insider": str(row.get("Insider Trading", "")),
                    "shares": int(row.get("Shares", 0)) if pd.notna(row.get("Shares")) else 0,
                    "value": fmt_large(row.get("Value", None)) if pd.notna(row.get("Value", None)) else None,
                    "transaction": str(row.get("Transaction", "")),
                    "date": str(row.get("Start Date", "")),
                }
                insider_trades.append(trade)
    except Exception:
        pass

    return {
        "ticker": ticker.upper(),
        "candlestick": candlestick_data,
        "indicators": latest,
        "fundamentals": fundamentals,
        "insider_trades": insider_trades,
    }

def get_ai_analysis(ticker: str, indicators: dict, fundamentals: dict, insider_trades: list) -> dict:
    insider_summary = json.dumps(insider_trades[:5], indent=2) if insider_trades else "No recent insider transactions available."

    user_message = f"""Analyse {ticker} ({fundamentals.get('name', ticker)}) using the following live market data:

**SECTOR:** {fundamentals.get('sector', 'Unknown')} | {fundamentals.get('industry', 'Unknown')}

**PRICE & PERFORMANCE:**
- Current Price: ${indicators['current_price']}
- 1-Week Change: {fundamentals['price_change_1w']}%
- 1-Month Change: {fundamentals['price_change_1m']}%
- 52-Week Range: ${fundamentals.get('52w_low')} – ${fundamentals.get('52w_high')}

**TECHNICAL INDICATORS (latest values):**
- RSI (14): {indicators['rsi']}
- MACD Line: {indicators['macd']} | Signal: {indicators['macd_signal']} | Histogram: {indicators['macd_histogram']}
- Bollinger Bands: Upper ${indicators['bb_upper']} | Mid ${indicators['bb_mid']} | Lower ${indicators['bb_lower']}
- SMA 20: ${indicators.get('sma20')} | SMA 50: ${indicators.get('sma50')} | SMA 200: ${indicators.get('sma200')}
- Price vs SMAs: {"Above" if indicators['current_price'] > (indicators.get('sma20') or 0) else "Below"} 20-day, {"Above" if indicators['current_price'] > (indicators.get('sma50') or 0) else "Below"} 50-day, {"Above" if indicators['current_price'] > (indicators.get('sma200') or 0) else "Below"} 200-day

**FUNDAMENTALS:**
- Market Cap: {fundamentals.get('market_cap')}
- P/E (Trailing): {fundamentals.get('pe_ratio')}
- P/E (Forward): {fundamentals.get('forward_pe')}
- EPS: {fundamentals.get('eps')}
- Dividend Yield: {fundamentals.get('dividend_yield')}%
- Beta: {fundamentals.get('beta')}

**RECENT INSIDER TRANSACTIONS (last 5):**
{insider_summary}

Apply your full analytical framework and return a JSON analysis object as specified in your instructions."""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    # Extract JSON from response (Claude may wrap in markdown code block)
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    return json.loads(raw)

def analyse_stock(ticker: str) -> dict:
    data = get_stock_data(ticker)
    ai = get_ai_analysis(
        ticker=data["ticker"],
        indicators=data["indicators"],
        fundamentals=data["fundamentals"],
        insider_trades=data["insider_trades"],
    )
    return {**data, "ai_analysis": ai}
