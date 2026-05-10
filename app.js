// Replace this with your Render API URL after deployment
const API_BASE = "https://stock-analysis-api.onrender.com";

let chart = null;
let candleSeries = null;
let overlays = { sma20: null, sma50: null, sma200: null, bbUpper: null, bbLower: null };
let activeOverlays = { sma20: true, sma50: true, sma200: false, bb: false };
let currentData = null;

function quickPick(ticker) {
  document.getElementById("ticker-input").value = ticker;
  runAnalysis();
}

document.getElementById("ticker-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") runAnalysis();
});

async function runAnalysis() {
  const ticker = document.getElementById("ticker-input").value.trim().toUpperCase();
  if (!ticker) return;

  const btn = document.getElementById("analyse-btn");
  const btnText = document.getElementById("btn-text");
  const btnSpinner = document.getElementById("btn-spinner");
  const overlay = document.getElementById("loading-overlay");
  const errorMsg = document.getElementById("error-msg");

  btn.disabled = true;
  btnText.classList.add("hidden");
  btnSpinner.classList.remove("hidden");
  overlay.classList.remove("hidden");
  errorMsg.classList.add("hidden");
  document.getElementById("results").classList.add("hidden");

  try {
    const res = await fetch(`${API_BASE}/analyse/${encodeURIComponent(ticker)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    currentData = data;
    renderResults(data);
    document.getElementById("results").classList.remove("hidden");
  } catch (e) {
    errorMsg.textContent = `Error: ${e.message}`;
    errorMsg.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btnText.classList.remove("hidden");
    btnSpinner.classList.add("hidden");
    overlay.classList.add("hidden");
  }
}

function renderResults(data) {
  const { ticker, candlestick, indicators, fundamentals, insider_trades, ai_analysis } = data;

  // --- Verdict ---
  const verdictBadge = document.getElementById("verdict-badge");
  const verdictText = ai_analysis.verdict || "HOLD";
  verdictBadge.textContent = verdictText;
  verdictBadge.className = "verdict-badge " + verdictText.toLowerCase().replace(" ", "-");

  document.getElementById("confidence-badge").textContent = ai_analysis.confidence || "—";
  document.getElementById("verdict-summary").textContent = ai_analysis.summary || "—";
  document.getElementById("verdict-oneliner").textContent = `"${ai_analysis.one_liner || "—"}"`;

  // --- Fundamentals ---
  document.getElementById("stock-name").textContent = fundamentals.name || ticker;
  document.getElementById("f-price").textContent = `$${indicators.current_price}`;

  const p1w = fundamentals.price_change_1w;
  const p1wEl = document.getElementById("f-1w");
  p1wEl.textContent = `${p1w > 0 ? "+" : ""}${p1w}%`;
  p1wEl.className = "fund-val " + (p1w >= 0 ? "green" : "red");

  const p1m = fundamentals.price_change_1m;
  const p1mEl = document.getElementById("f-1m");
  p1mEl.textContent = `${p1m > 0 ? "+" : ""}${p1m}%`;
  p1mEl.className = "fund-val " + (p1m >= 0 ? "green" : "red");

  document.getElementById("f-mcap").textContent = fundamentals.market_cap || "—";
  document.getElementById("f-pe").textContent = fundamentals.pe_ratio ? fundamentals.pe_ratio.toFixed(1) + "x" : "—";
  document.getElementById("f-fpe").textContent = fundamentals.forward_pe ? fundamentals.forward_pe.toFixed(1) + "x" : "—";
  document.getElementById("f-eps").textContent = fundamentals.eps ? `$${fundamentals.eps.toFixed(2)}` : "—";
  document.getElementById("f-div").textContent = fundamentals.dividend_yield ? `${fundamentals.dividend_yield}%` : "—";
  document.getElementById("f-beta").textContent = fundamentals.beta ? fundamentals.beta.toFixed(2) : "—";
  document.getElementById("f-52w").textContent = (fundamentals["52w_low"] && fundamentals["52w_high"])
    ? `$${fundamentals["52w_low"]} – $${fundamentals["52w_high"]}` : "—";

  // --- Chart ---
  renderChart(candlestick, indicators);

  // --- RSI ---
  const rsi = indicators.rsi;
  document.getElementById("rsi-val").textContent = rsi.toFixed(1);
  const rsiMarker = document.getElementById("rsi-marker");
  rsiMarker.style.left = `${rsi}%`;
  rsiMarker.style.background = rsi < 30 ? "var(--green)" : rsi > 70 ? "var(--red)" : "var(--accent)";

  const rsiLabelEl = document.getElementById("rsi-label");
  if (rsi < 30) {
    rsiLabelEl.textContent = "Oversold — potential reversal zone";
    rsiLabelEl.className = "indicator-label oversold";
  } else if (rsi > 70) {
    rsiLabelEl.textContent = "Overbought — watch for reversal signals";
    rsiLabelEl.className = "indicator-label overbought";
  } else if (rsi > 50) {
    rsiLabelEl.textContent = "Neutral-bullish — momentum above midpoint";
    rsiLabelEl.className = "indicator-label bullish";
  } else {
    rsiLabelEl.textContent = "Neutral-bearish — momentum below midpoint";
    rsiLabelEl.className = "indicator-label bearish";
  }

  // --- MACD ---
  const macd = indicators.macd;
  const signal = indicators.macd_signal;
  const hist = indicators.macd_histogram;
  document.getElementById("macd-line").textContent = macd.toFixed(4);
  document.getElementById("macd-signal").textContent = signal.toFixed(4);
  const histEl = document.getElementById("macd-hist");
  histEl.textContent = (hist >= 0 ? "+" : "") + hist.toFixed(4);
  histEl.style.color = hist >= 0 ? "var(--green)" : "var(--red)";

  const macdLabelEl = document.getElementById("macd-label");
  if (macd > signal) {
    macdLabelEl.textContent = hist > 0 ? "Bullish crossover — momentum building" : "Bearish momentum fading";
    macdLabelEl.className = "indicator-label bullish";
  } else {
    macdLabelEl.textContent = hist < 0 ? "Bearish crossover — downside momentum" : "Bullish momentum emerging";
    macdLabelEl.className = "indicator-label bearish";
  }

  // --- Bollinger Bands ---
  document.getElementById("bb-upper").textContent = `$${indicators.bb_upper}`;
  document.getElementById("bb-mid").textContent = `$${indicators.bb_mid}`;
  document.getElementById("bb-lower").textContent = `$${indicators.bb_lower}`;
  const price = indicators.current_price;
  const bbWidth = ((indicators.bb_upper - indicators.bb_lower) / indicators.bb_mid * 100).toFixed(1);
  const bbLabelEl = document.getElementById("bb-label");
  if (price > indicators.bb_upper) {
    bbLabelEl.textContent = `Price above upper band — extended (band width: ${bbWidth}%)`;
    bbLabelEl.className = "indicator-label overbought";
  } else if (price < indicators.bb_lower) {
    bbLabelEl.textContent = `Price below lower band — oversold (band width: ${bbWidth}%)`;
    bbLabelEl.className = "indicator-label oversold";
  } else {
    bbLabelEl.textContent = `Price within bands — band width: ${bbWidth}%`;
    bbLabelEl.className = "indicator-label neutral";
  }

  // --- Moving Averages ---
  const smas = [
    { id: "sma20", val: indicators.sma20 },
    { id: "sma50", val: indicators.sma50 },
    { id: "sma200", val: indicators.sma200 },
  ];
  smas.forEach(({ id, val }) => {
    document.getElementById(`${id}-val`).textContent = val ? `$${val}` : "—";
    const relEl = document.getElementById(`${id}-rel`);
    if (!val) {
      relEl.textContent = "N/A";
      relEl.className = "ma-rel";
    } else if (price > val) {
      relEl.textContent = "Above";
      relEl.className = "ma-rel above";
    } else {
      relEl.textContent = "Below";
      relEl.className = "ma-rel below";
    }
  });

  // --- AI Technical Analysis ---
  const ta = ai_analysis.technical_analysis || {};
  const trendEl = document.getElementById("ai-trend");
  trendEl.textContent = ta.trend || "—";
  trendEl.style.color = ta.trend === "Bullish" ? "var(--green)" : ta.trend === "Bearish" ? "var(--red)" : "var(--yellow)";

  const signalsList = document.getElementById("ai-signals");
  signalsList.innerHTML = (ta.key_signals || []).map(s => `<div class="signal-item">✓ ${s}</div>`).join("") || "—";

  const riskList = document.getElementById("ai-risks");
  riskList.innerHTML = (ta.risk_factors || []).map(r => `<div class="risk-item">⚠ ${r}</div>`).join("") || "—";

  // --- Fundamental Snapshot ---
  document.getElementById("ai-fundamental").textContent = ai_analysis.fundamental_snapshot || "—";
  document.getElementById("pt-bull").textContent = (ai_analysis.price_targets || {}).bull_case || "—";
  document.getElementById("pt-bear").textContent = (ai_analysis.price_targets || {}).bear_case || "—";

  // --- Insider Activity ---
  document.getElementById("ai-insider-signal").textContent = ai_analysis.insider_signal || "—";
  renderInsiderTable(insider_trades || []);
}

function renderChart(candleData, indicators) {
  const container = document.getElementById("chart-container");
  container.innerHTML = "";

  chart = LightweightCharts.createChart(container, {
    width: container.clientWidth,
    height: 350,
    layout: { background: { color: "#0D1117" }, textColor: "#7982A9" },
    grid: { vertLines: { color: "#1E2A45" }, horzLines: { color: "#1E2A45" } },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
    rightPriceScale: { borderColor: "#1E2A45" },
    timeScale: { borderColor: "#1E2A45", timeVisible: true },
  });

  candleSeries = chart.addCandlestickSeries({
    upColor: "#9ECE6A", downColor: "#F7768E",
    borderUpColor: "#9ECE6A", borderDownColor: "#F7768E",
    wickUpColor: "#9ECE6A", wickDownColor: "#F7768E",
  });
  candleSeries.setData(candleData);

  // Add overlays from computed last-90-day data
  // We need time-series for the chart; compute from candle prices
  const closes = candleData.map(d => ({ time: d.time, value: d.close }));

  overlays.sma20 = chart.addLineSeries({ color: "#7AA2F7", lineWidth: 1.5, priceLineVisible: false, lastValueVisible: false });
  overlays.sma50 = chart.addLineSeries({ color: "#E0AF68", lineWidth: 1.5, priceLineVisible: false, lastValueVisible: false });
  overlays.sma200 = chart.addLineSeries({ color: "#BB9AF7", lineWidth: 1.5, priceLineVisible: false, lastValueVisible: false });
  overlays.bbUpper = chart.addLineSeries({ color: "rgba(106,211,247,0.5)", lineWidth: 1, priceLineVisible: false, lastValueVisible: false, lineStyle: 2 });
  overlays.bbLower = chart.addLineSeries({ color: "rgba(106,211,247,0.5)", lineWidth: 1, priceLineVisible: false, lastValueVisible: false, lineStyle: 2 });

  overlays.sma20.setData(computeSMA(closes, 20));
  overlays.sma50.setData(computeSMA(closes, 50));
  overlays.sma200.setData(computeSMA(closes, 200));
  const { upper, lower } = computeBB(closes, 20);
  overlays.bbUpper.setData(upper);
  overlays.bbLower.setData(lower);

  // Apply initial visibility
  overlays.sma20.applyOptions({ visible: activeOverlays.sma20 });
  overlays.sma50.applyOptions({ visible: activeOverlays.sma50 });
  overlays.sma200.applyOptions({ visible: activeOverlays.sma200 });
  overlays.bbUpper.applyOptions({ visible: activeOverlays.bb });
  overlays.bbLower.applyOptions({ visible: activeOverlays.bb });

  chart.timeScale().fitContent();

  window.addEventListener("resize", () => {
    if (chart) chart.applyOptions({ width: container.clientWidth });
  });
}

function computeSMA(data, period) {
  const result = [];
  for (let i = period - 1; i < data.length; i++) {
    const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b.value, 0);
    result.push({ time: data[i].time, value: sum / period });
  }
  return result;
}

function computeBB(data, period = 20) {
  const sma = computeSMA(data, period);
  const upper = [], lower = [];
  sma.forEach((pt, idx) => {
    const dataIdx = idx + period - 1;
    const slice = data.slice(dataIdx - period + 1, dataIdx + 1).map(d => d.value);
    const mean = pt.value;
    const std = Math.sqrt(slice.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / period);
    upper.push({ time: pt.time, value: mean + 2 * std });
    lower.push({ time: pt.time, value: mean - 2 * std });
  });
  return { upper, lower };
}

function toggleOverlay(btn, key) {
  activeOverlays[key] = !activeOverlays[key];
  btn.classList.toggle("active", activeOverlays[key]);

  if (key === "bb") {
    overlays.bbUpper?.applyOptions({ visible: activeOverlays.bb });
    overlays.bbLower?.applyOptions({ visible: activeOverlays.bb });
  } else {
    overlays[key]?.applyOptions({ visible: activeOverlays[key] });
  }
}

function renderInsiderTable(trades) {
  const wrap = document.getElementById("insider-table-wrap");
  if (!trades.length) {
    wrap.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">No recent insider transactions available.</p>';
    return;
  }
  const rows = trades.map(t => {
    const isBuy = t.transaction.toLowerCase().includes("buy") || t.transaction.toLowerCase().includes("purchase");
    const cls = isBuy ? "txn-buy" : "txn-sell";
    const shares = t.shares ? t.shares.toLocaleString() : "—";
    return `<tr>
      <td>${truncate(t.insider, 20)}</td>
      <td class="${cls}">${t.transaction}</td>
      <td>${shares}</td>
      <td>${t.value || "—"}</td>
      <td style="color:var(--text-muted)">${t.date}</td>
    </tr>`;
  }).join("");
  wrap.innerHTML = `
    <table class="insider-table">
      <thead><tr>
        <th>Insider</th><th>Type</th><th>Shares</th><th>Value</th><th>Date</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function truncate(str, n) {
  return str && str.length > n ? str.substring(0, n) + "…" : (str || "—");
}
