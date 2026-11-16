# Trading Analysis Report: TXN

- Analysis date: 2026-11-16
- Rating: Hold
- Generated: 2026-11-16 16:35:08
- TradingAgents 0.7.1: anthropic, deep claude-haiku-5-5, quick claude-haiku-5-5
- Analysts: market, sentiment, news, fundamentals; research debate rounds 1, risk debate rounds 1
- Data vendors: core_stock_apis yfinance, technical_indicators yfinance, fundamental_data sec_edgar,yfinance, news_data yfinance, macro_data fred, prediction_markets polymarket

## I. Analyst Team Reports

### Market Analyst
# TXN (Texas Instruments Incorporated) Technical Report: 2026-11-16

## Data integrity check

I pulled the daily OHLCV series from 2026-08-03 to 2026-11-16 and the verified snapshot for 2026-11-16. Every indicator value from the indicator tools matches the verified snapshot:

- 10 EMA 300.599, 50 SMA 283.626, 200 SMA 262.83
- MACD 5.294, signal 5.580, histogram -0.286
- RSI 51.97, ATR 13.263, VWMA 299.85
- Bollinger middle 297.365, upper 323.682, lower 271.049 (from the snapshot only, since I did not call the Bollinger tools separately)

**One item to flag:** the 2026-11-16 volume is 1,632,345. That is well below the 5–10 million range of recent sessions, so the row is probably a partial-session or intraday capture rather than a full-day total. Treat today's volume-based readings with caution. The close of 297.84 matches the snapshot, so I have not altered it.

## Latest verified levels (2026-11-16)

- Open 294.47, High 298.12, Low 289.59, Close 297.84

## Trend analysis

**Long-term:** The 200 SMA is rising steadily, from 252.08 on 2026-10-19 to 262.83 now. Price (297.84) sits about 13% above it. The 50 SMA is also rising, from 270.78 on 2026-10-19 to 283.63, and sits above the 200 SMA. Price is above both averages, so the intermediate and long-term structure is bullish.

**Medium-term:** Since early September the stock has moved from the low 250s to a cluster of highs near 317. The intraday high was 316.75 on 2026-11-03 and 316.97 on 2026-11-12. Those two tests of the same zone without a close above it are a resistance area to monitor, not a confirmed breakout.

**Short-term:** The 10 EMA (300.60) has flattened after rising from about 279 in late October. The close is now 2.8 points below it. That is a mild short-term loss of momentum, not a trend break.

## Momentum analysis

- **MACD:** The MACD line has fallen from a peak of 8.81 on 2026-11-04 to 5.29 now. It remains above zero, so the broader momentum is still positive. The signal line (5.58) is now above the MACD line, which is a bearish crossover in progress.
- **Histogram:** It turned negative on 2026-11-16 at -0.286, after a positive reading of 0.484 on 2026-11-12. This is an early warning of fading momentum. It is small, so it needs confirmation.
- **RSI:** RSI peaked at 71.8 on 2026-10-29 (overbought territory) and dropped to 43.0 on 2026-11-06 after the sharp selloff. It has since recovered to 52.0. This is neutral and not extended in either direction. The RSI has not made a new high with price since late October, which is a mild non-confirmation worth watching.

## Volatility and volume

- **ATR (14):** Currently 13.26, up from about 8.7 on 2026-10-19. Volatility has risen about 50% over the past month. Using 2x ATR as an illustrative stop distance gives roughly 26.5 points, but this is a sizing reference, not a recommendation.
- **Bollinger Bands:** The close (297.84) is just above the middle band (297.37). The upper band is at 323.68 and the lower band at 271.05, a width of about 52.6 points. Price is in the middle of the bands with no squeeze, so there is no volatility-breakout setup yet.
- **VWMA (20):** 299.85, very close to the current price. Volume-weighted and simple averages agree, so no sign of volume-driven divergence.

## Key event: 2026-11-05 selloff and recovery

- 2026-11-04 closed at 311.49.
- 2026-11-05 opened at 301.92, made a low of 277.87, and closed at 278.15. That is a drop of about -10.7% on 19.2 million shares, the highest volume in the window.
- 2026-11-06 closed at 277.36, a low-volume follow-through.
- 2026-11-09 through 2026-11-12 recovered to 312.48, reclaiming the pre-selloff level.
- 2026-11-13 closed at 303.60 and 2026-11-16 at 297.84.

The high-volume flush followed by a full recovery is a notable pattern. It shows strong demand at lower prices. However, the stock has since given back about 4.7% from the 2026-11-12 close, with the histogram turning negative. The 2026-10-30 dividend was $1.52 and had no obvious effect on price.

## Outlook and scenarios

- **Bullish case:** A sustained close above the 316–317 resistance area on rising volume would target new highs. The RSI would need to confirm with a move above 60.
- **Base case:** Price consolidates between the 10 EMA (~300) and the 50 SMA (~284). MACD bearish crossover may keep momentum soft for several sessions.
- **Bearish case:** A close below the 50 SMA (283.63), which is also near the Bollinger middle band area, would weaken the short-term structure. The 2026-11-06 close of 277.36 is the next reference low. A loss of the 200 SMA (262.83) would be a more serious warning, though it is far away.

## Practical takeaways

1. The primary trend is up: price is above the 50 and 200 SMAs, and both are rising.
2. Short-term momentum has softened. The MACD bearish crossover and negative histogram suggest waiting for confirmation before adding exposure.
3. The 316–317 zone has capped price twice. A decisive close above it would be the cleanest bullish signal.
4. Volatility is elevated (ATR 13.3). Position sizes should reflect that.
5. Today's volume is likely incomplete, so do not draw volume conclusions from the 2026-11-16 row until a full-session value is available.

I have not made a trade decision here. The other agent will weigh these readings against fundamentals and risk limits.

## Summary table

| Category | Indicator | Latest value (2026-11-16) | Reading |
|---|---|---|---|
| Price | Close / Open / High / Low | 297.84 / 294.47 / 298.12 / 289.59 | Partial-session volume flagged |
| Trend | 10 EMA | 300.60 | Price 2.8 below; flattening |
| Trend | 50 SMA | 283.63 | Price 14.2 above; rising |
| Trend | 200 SMA | 262.83 | Price 35.0 above; rising |
| Momentum | MACD | 5.29 | Falling from 8.81 peak (11/04) |
| Momentum | MACD Signal | 5.58 | MACD below signal (bearish cross) |
| Momentum | MACD Histogram | -0.286 | Turned negative from +0.484 (11/12) |
| Momentum | RSI | 51.97 | Neutral; down from 71.8 (10/29) |
| Volatility | ATR | 13.26 | Up from 8.66 (10/19) |
| Volatility | Bollinger Upper / Middle / Lower | 323.68 / 297.37 / 271.05 | Price mid-band; no squeeze |
| Volume | VWMA | 299.85 | Close near VWMA |
| Key level | Resistance zone | ~316–317 | Intraday highs 11/03 and 11/12 |
| Key level | Reference low | 277.36 | Close on 11/06 after 11/05 selloff |
| Event | 2026-11-05 | -10.7% close-to-close, 19.2M volume | Fully recovered by 11/12 |
| Data flag | 2026-11-16 volume | 1,632,345 | Likely partial; verify |

### Sentiment Analyst
**Overall Sentiment:** **Mixed** (Score: 5.0/10)
**Confidence:** Low

Scope: TXN (Texas Instruments Incorporated, Technology / Semiconductors, NMS), window 2026-11-09 to 2026-11-16.

1) Source-by-source breakdown

News (Yahoo Finance, institutional framing; 22 items). Tone is mildly constructive on TXN specifically. Zacks frames the stock as an Average Brokerage Recommendation "buy" candidate but cautions that analyst optimism may be overstated. Zacks also reports TXN's 2027 pricing strategy could lift profitability as tight supply and stronger demand support price hikes, with customer resistance as the risk. Trefis and TIKR contrast TXN favorably with Qualcomm: TIKR cites TXN third-quarter revenue growth of 28% and a 7% dividend raise in September, while QCOM fell about 10% on Nov. 5. Simply Wall St. flags that TXN "looks fully valued" after embedded AI product news, with 121.3% three-year returns, raising the question of whether cash flows support the price. Most of the news flow (roughly two-thirds of items) concerns NVIDIA's leadership change (Jensen Huang's resignation, Colette Kress named interim CEO on Nov 12) and the resulting rotation into other chipmakers (AMD up about 30%, Broadcom up about 24%, per GuruFocus). This is sector-level news, not TXN-specific. Overall news tone: mildly positive to neutral on TXN.

StockTwits (retail; 18 most-recent messages, user tags: 1 Bullish, 1 Bearish, 16 unlabeled). The sample is too small for a reliable ratio; the tagged split is 50/50. Unlabeled posts skew cautious or analytical. Themes: analog chips as a "boring" hedge versus cyclical capex and industrial/auto exposure (two posts from @openclassaction2); a bearish post predicting a "generational dump"; a note of unusual put-heavy options activity on Nov 9 after a 7% up day, with a separate post describing puts leading and the stock down about 8% over a week (both from GTA Terminal, which is promotional). Some posts cite a "Grateful to own under $55" price reference. One post references an MCP-based migration tool that could ease customers moving designs from competitors to TI's 300mm capacity (bullish framing, unverified). Several posts are recycled Techdamentals earnings commentary (Oct 21 report, EPS $2.62 vs about $2.42–2.43 expected, stock down 1.8% the next day). Overall StockTwits tone: mixed to slightly bearish on price action, with low message volume.

Reddit: unavailable (fetch failed for r/wallstreetbets, r/stocks, r/investing). This is an absence of data, not of discussion. No Reddit read is possible.

2) Cross-source divergences and alignments
- Fundamental/news framing (EPS beat, revenue growth, dividend raise, pricing power) is constructive. Retail price-action commentary is more cautious, with put-heavy options flow and a valuation-stretched narrative.
- The biggest headline driver is NVIDIA's CEO transition and sector rotation, which benefits peers more than TXN directly. TXN is largely a bystander in the headlines.
- Both news and social posts reference the "analog as defensive versus cyclical" debate, with no consensus.

3) Dominant narrative themes
- Valuation: "fully valued" after a strong multi-year run.
- Cyclical recovery and pricing power (300mm capacity, 2027 price increases) versus customer resistance.
- Rotation within semis away from NVIDIA-linked names.
- Qualcomm-versus-TXN dividend comparisons.

4) Catalysts and risks
- Catalysts: 2027 pricing actions; the dividend; potential analyst upgrades given positive ABR framing; sector rotation; the next earnings report (not in window).
- Risks: valuation stretch; bearish options positioning; industrial/auto demand durability; customer pushback on price increases; spillover from NVIDIA governance turmoil and export-control headlines (a rumor about Commerce Secretary Lutnick was noted on StockTwits, unverified).

5) Key sentiment signals

| Signal | Direction | Source | Supporting evidence |
|---|---|---|---|
| Analyst consensus framing | Mildly bullish | News (Zacks) | ABR-based "buy" framing, with caveat about optimism |
| Pricing power for 2027 | Bullish | News (Zacks) | Tight supply, stronger demand support price hikes |
| Relative fundamentals vs QCOM | Bullish | News (TIKR, Trefis) | 28% Q3 revenue growth; 7% dividend raise; QCOM -10% |
| Valuation | Bearish | News (Simply Wall St.) | "Fully valued" after 121.3% three-year return |
| Options flow | Bearish | StockTwits (GTA Terminal) | Activity skewed to puts on Nov 9 |
| Retail tags | Neutral | StockTwits | 1 bullish, 1 bearish, 16 unlabeled (n=18) |
| Sector rotation | Neutral to positive for peers | News (GuruFocus, Barchart) | AMD +30%, AVGO +24% on NVDA turmoil |
| Reddit | No data | Reddit | Fetch failed |

Confidence is low: StockTwits has only 18 messages, two of which are tagged, and Reddit is unavailable. News is substantive but largely sector-level. This report reflects sentiment signals only and is not a price forecast; weigh it alongside fundamentals and technicals.

### News Analyst
# TXN (Texas Instruments) News and Macro Report, as of 2026-11-16

## Bottom line
Recent TXN coverage is mostly positive but thin. It centers on pricing power, a dividend increase, and valuation debates. No company-specific catalyst was announced in the past week. The bigger swing factor for semiconductors this week was the Nvidia leadership shock, plus a headline about US semiconductor restrictions that hit chip stocks. Macro data from FRED was unavailable, so this report relies on news and prediction markets only.

## Company-specific developments
- **Pricing and profitability:** A Zacks piece ("Will Texas Instruments' 2027 Pricing Strategy Lift Profitability?") argues that tight chip supply and firm demand support price increases into 2027. It flags customer resistance as the main risk. This is the most fundamentally relevant item.
- **Growth and capital return:** A TIKR article says TXN grew third-quarter revenue 28% and raised its dividend 7% in September. I could not verify the 28% figure against a primary filing, so treat it as unconfirmed until checked against the company's report.
- **Valuation:** Simply Wall St. says the stock "looks fully valued" after fresh embedded and industrial AI product news. It notes a 121.3% three-year return. Zacks says Wall Street's average brokerage recommendation is favorable, but it cautions that consensus ratings can be overly optimistic.
- **Relative performance:** Trefis compares TXN's five-year stock performance favorably with NXP. Peer coverage (Qualcomm, Analog Devices) is mostly about handset weakness, which is a different end market from TXN's industrial and auto exposure.

## Sector and market context
- **Nvidia leadership shock:** Jensen Huang reportedly resigned as Nvidia CEO on about Nov 12, amid reported personal allegations. CFO Colette Kress is interim CEO. Coverage says AMD rose about 30% and Broadcom about 24% as investors reassessed AI-chip competition. Analog and embedded names like TXN are not directly exposed to AI accelerator demand, so the read-through is indirect. Still, this rotation shows the market is sensitive to semiconductor sentiment.
- **Export restrictions:** A Yahoo Finance headline says "chip stocks fall on US semiconductor restrictions." I could only see the headline, not the details. Any restriction affecting TXN's China revenue or its supply chain would matter a lot, so this needs follow-up.
- **Earnings season:** An Investing.com recap says beats were "rewarded selectively" as AI-infrastructure names pulled back.
- **Commodities:** Gold and silver are at their lowest levels in over a year. This is a risk-appetite signal, not a direct TXN factor.

## Macro backdrop
- **Fed policy:** Prediction markets price a 98% probability of no Fed rate cuts in 2026 (about $9.7M volume). A WSJ item also mentions that the Fed will forgo a rate decision at the October 2027 meeting. I could not confirm that detail, and it is unusual enough to verify.
- **Recession risk:** Polymarket puts US recession by end-2026 at 2%, down 1.9pp over the past week. Japan's recession odds are 6%, and UK's are 2%.
- **Data gap:** FRED calls (fed funds, 10-year Treasury, CPI) all failed because no API key is configured. I have no verified current figures for rates, inflation, or yields.
- **Tariffs:** No prediction market exists for semiconductor tariffs, so this risk can only be assessed from news.

## Trading implications
1. **Fundamental tailwind:** The pricing and supply narrative favors margin support into 2027. Watch for any sign of customer pushback.
2. **Valuation is the constraint:** Multiple commentators call the stock fully valued. Upside likely needs earnings beats or guidance raises, not multiple expansion.
3. **Policy risk is the main downside:** Export-restriction headlines are the biggest near-term risk. Confirm their scope before sizing positions.
4. **Rates are a headwind:** With the market pricing essentially no cuts in 2026, rate-sensitive valuations face less support. Verify this once FRED data is available.
5. **Sentiment spillover:** Nvidia-driven rotation can lift or pull peers. TXN is less directly exposed than AI-linked names.

## Key data gaps
- Verify TXN's latest quarterly revenue, margins, and guidance against the company's filing.
- Confirm the scope of the US semiconductor restrictions and any TXN China exposure.
- Pull current fed funds, 10-year yield, CPI, and unemployment once FRED is configured.

## Summary table

| Area | Key point | Signal for TXN | Confidence |
|---|---|---|---|
| Pricing | 2027 price increases supported by tight supply | Positive for margins | Medium |
| Capital return | Dividend raised 7% in September | Positive, supports income holders | High (reported) |
| Growth | Q3 revenue +28% (per TIKR) | Positive if confirmed | Low (unverified) |
| Valuation | "Fully valued," 121% three-year return | Limits upside | Medium |
| Analysts | Favorable average rating; ratings may be optimistic | Neutral | Medium |
| Nvidia shock | CEO resignation; AMD +30%, AVGO +24% | Indirect sentiment spillover | High |
| Export restrictions | Chip stocks fell on restriction headline | Key downside risk | Low (headline only) |
| Fed policy | 98% odds of no 2026 cuts | Headwind for valuation | High (market-implied) |
| Recession | US 2% by end-2026 | Low demand-shock risk | Medium |
| Macro data | FRED unavailable | Cannot verify rates, CPI, yields | N/A |

### Fundamentals Analyst
# TXN (Texas Instruments Incorporated) Fundamental Report
**As of 2026-11-16** | Sector: Technology / Semiconductors | Exchange: NMS

## 1. Company Snapshot and Valuation

| Metric | Value | Read-through |
|---|---|---|
| Market cap | $272.2B | Large-cap analog/embedded semiconductor leader |
| Implied share price | ~$297 | Derived from market cap and ~915M shares implied by book value; not a quoted price |
| 52-week range | $152.73 – $334.03 | Stock is roughly 11% below its 52-week high |
| 50-day / 200-day average | $283.87 / $264.77 | Price is above both averages, a constructive trend |
| Trailing P/E | 38.6x | Expensive on trailing earnings |
| Forward P/E | 25.6x | Multiple compresses sharply as earnings grow |
| PEG ratio | 0.92 | Growth-adjusted valuation looks reasonable |
| Price/Book | 14.2x | High, reflecting the capital-light return profile and buybacks |
| Dividend yield | 2.0% | Supports income investors |
| Beta | 1.39 | Above-market volatility |

The forward P/E of 25.6x against trailing 38.6x implies consensus expects EPS to rise from $7.71 (TTM) to $11.63 (forward), roughly 51%. That is a large expected step-up and the main thing the stock depends on.

## 2. Profitability

| Metric | Value |
|---|---|
| TTM revenue | $20.77B |
| TTM gross profit | $12.51B (≈60% gross margin) |
| TTM EBITDA | $10.71B |
| TTM net income | $7.07B |
| Profit margin | 34.3% |
| Operating margin | 41.1% |
| Return on equity | 39.7% |
| Return on assets | 14.8% |

**Quarterly trend (discrete quarters, USD millions):**

| Quarter | Revenue | YoY growth | Gross margin | Operating margin | Diluted EPS |
|---|---|---|---|---|---|
| Q1 2025 | 4,069 | – | 56.8% | 32.5% | $1.28 |
| Q2 2025 | 4,448 | – | 57.9% | 35.1% | $1.41 |
| Q3 2025 | 4,742 | – | 57.4% | 35.1% | $1.48 |
| Q1 2026 | 4,825 | +18.6% | 58.0% | 37.5% | $1.68 |
| Q2 2026 | 5,463 | +22.8% | 61.4% | 42.3% | $2.14 |
| Q3 2026 | 6,055 | +27.7% | 64.2% | 47.5% | $2.62 |

**Key observations:**
- **Revenue growth is accelerating.** YoY growth went from +18.6% in Q1 2026 to +22.8% in Q2 and +27.7% in Q3. Sequential revenue rose about 11% from Q2 to Q3.
- **Operating leverage is strong.** Gross margin rose about 6 points in two quarters, and operating margin rose about 12 points year over year. Incremental revenue is dropping through to profit at a high rate.
- **Diluted EPS has nearly doubled** from $1.48 in Q3 2025 to $2.62 in Q3 2026 (+77%).
- Q3 2026 net income was $2.43B.

## 3. Balance Sheet and Financial Health

| Item (Sep 30, 2026, USD M) | Value |
|---|---|
| Total assets | 36,839 |
| Current assets | 16,880 |
| Cash and equivalents | 4,211 |
| Total liabilities | 17,654 |
| Current liabilities | 3,017 |
| Stockholders' equity | 19,185 |
| Current ratio | 5.6x |
| Debt-to-equity | 0.71x |

**Trend:** Equity rose from $16.27B (Dec 2025) to $19.19B (Sep 2026), up about 18% in nine months, driven by retained earnings. Cash rose from $3.23B to $4.21B over the same period. Total liabilities fell from $18.31B to $17.65B. Current liabilities are low relative to current assets. Liquidity is strong and leverage is moderate.

Total assets have been broadly flat near $35–37B since 2024. Growth is coming from earnings rather than balance-sheet expansion.

## 4. Cash Flow and Capital Allocation

**Cash flow (USD M; the source reports cumulative year-to-date figures, so quarterly values are derived by differencing):**

| Period | Operating CF | Capex | Free cash flow (derived) | Financing CF |
|---|---|---|---|---|
| 9M 2025 | 4,899 | 3,625 | 1,274 | -4,025 |
| Q1 2026 | 1,520 | 676 | 844 | -1,149 |
| Q2 2026 | 2,703 | 514 | 2,189 | -890 |
| Q3 2026 | 3,419 | 463 | 2,956 | -1,881 |
| 9M 2026 | 7,642 | 1,653 | 5,989 | -3,920 |

**Key observations:**
- **Operating cash flow up 56%** in 9M 2026 vs 9M 2025 ($7.64B vs $4.90B).
- **Capex has fallen sharply**: 9M 2026 capex is $1.65B vs $3.63B a year earlier, down about 54%. This is the main driver of the free cash flow surge. The 2022–2025 build-out of fabs appears to be winding down, which is a major positive for FCF conversion.
- **Free cash flow rose from about $1.3B to about $6.0B** over nine months, roughly 4.7x. Q3 2026 FCF alone was about $2.96B.
- **Shareholder returns are ongoing.** Financing outflows of $3.9B in 9M 2026 likely reflect dividends and buybacks. The exact split is not broken out in the data.
- Trailing FCF in the fundamentals summary is $4.78B. That figure appears to include a heavier Q4 2025 capex period, so the trend in the quarterly numbers is the more useful read.

## 5. Insider Activity (Last ~2 Years)

**Pattern:** Insider activity is dominated by sales, most of them tied to option exercises ("conversion of exercise of derivative security") followed by same-day sales.

**Recent notable transactions:**
- **Oct 27, 2026:** Directors Robert Sanchez, Pamela Patsley and Janet Clark exercised options and sold at about $302–303 (roughly $1.8M, $1.4M and $1.3M respectively).
- **Aug 27, 2026:** Officer Tsedeniya Abraham sold 7,000 shares at about $264.60 (~$1.85M).
- **May 2026:** CEO Ilan Haviv exercised 20,000 options and sold at $280.32 (~$5.6M). CFO Rafael Lizardi exercised 47,734 options and sold at about $308 (~$14.7M). Director Carrie Cox sold at about $306–307. Director Martin Craighead sold 10,000 shares at about $320.
- **Feb–Apr 2026:** Heavy sales by CFO Lizardi, officers Mark Gary, Mark Roberts, Mohammad Yunus, Ahmad Bahai, and directors Pamela Patsley and Todd Bluedorn, at prices from about $220 to $280.
- **2025:** Large sales by former Chairman Richard Templeton (Feb 2025, roughly $40M+ in aggregate at about $190–205). Director Ronald Kirk sold in Nov 2025 at about $162 and in Nov 2024 at about $203.

**Assessment:**
- **No open-market insider purchases appear in the record.** All entries are sales, option conversions, gifts, or routine RSU/stock grants.
- Most sales are tied to option exercises (many at $79–$174 strike prices), which means insiders are realizing gains on long-held options rather than signaling a view of the stock. Heavy sales near $300 are still a modest negative signal, because the sales are large and recurring and there are no offsetting buys.
- Sales have continued at higher prices. Insiders sold near $220 in February and near $300 in October, suggesting they are not waiting for a specific price target.
- Stock grants (January each year) are routine compensation.

## 6. Data Quality and Caveats

- Income statement and balance sheet fields have occasional gaps (e.g., no Q4 cost-of-revenue values, and some missing balance-sheet quarters). Figures were used only where populated.
- Cash flow statements report year-to-date cumulative figures, not discrete quarters. Quarterly values above are derived by differencing.
- The Q4 2025 quarter is missing from the quarterly income statement, so trailing sums were reconstructed from the Q1–Q3 2026 data and the TTM totals.
- The insider data covers roughly the last two years, not only the past week. No insider purchases appear.
- The implied share price is derived, not a quoted price. Confirm the current quote before trading.

## 7. Summary and Actionable Takeaways

**Bullish factors:**
1. Revenue growth accelerated to +27.7% YoY in Q3 2026, the fastest in the recent series.
2. Gross margin expanded from about 57% to 64% and operating margin from 35% to 47.5% over four quarters, showing strong operating leverage.
3. Capex dropped about 54% year to date, lifting free cash flow to roughly $6B for nine months (about 4.7x the prior year).
4. Balance sheet is strong: current ratio 5.6x, debt-to-equity 0.71x, cash rising.
5. Forward P/E of 25.6x and PEG of 0.92 suggest the stock is not expensive on growth-adjusted terms.
6. Price is above the 50- and 200-day averages, and about 11% below its 52-week high.

**Bearish or cautionary factors:**
1. Trailing P/E of 38.6x and price-to-book of 14.2x are high. The valuation depends on the forward EPS ramp to about $11.63 being delivered.
2. Insider selling is heavy and recurring, with no open-market buys in the record, and sales continued into October at about $300.
3. Beta of 1.39 means the stock may be volatile in a risk-off market.
4. The 52-week range is very wide ($153–$334), indicating high price sensitivity to sentiment or macro conditions.
5. Growth could be cyclical. Strong recent growth may be partly a recovery effect that could fade.

**Actionable view for traders:**
- The fundamental trend is strongly positive: accelerating revenue, expanding margins, sharply rising FCF, and a healthy balance sheet.
- Valuation is full on trailing numbers but reasonable on forward numbers, so the investment case rests on continued execution toward consensus EPS.
- Watch for: (a) Q4 2026 results confirming the growth and margin trajectory; (b) whether capex stays low, sustaining FCF; (c) any change in insider selling pattern, especially open-market buys; (d) price action around the $280–$300 zone, which sits near the 50-day average and recent insider sale prices.
- Position sizing should reflect the high beta and the premium trailing multiple.

## Key Points Summary

| Category | Metric | Value | Signal |
|---|---|---|---|
| Valuation | Market cap | $272.2B | Large cap |
| Valuation | Trailing P/E | 38.6x | Expensive (trailing) |
| Valuation | Forward P/E | 25.6x | Reasonable on forward EPS |
| Valuation | PEG | 0.92 | Attractive growth-adjusted |
| Valuation | Price/Book | 14.2x | High |
| Income | Dividend yield | 2.0% | Income support |
| Growth | Q3 2026 revenue YoY | +27.7% | Accelerating (Q1 +18.6%, Q2 +22.8%) |
| Growth | Q3 2026 EPS | $2.62 vs $1.48 yr ago | Strong (+77%) |
| Margins | Gross margin (Q3 2026) | 64.2% | Expanding (from 57.4%) |
| Margins | Operating margin (Q3 2026) | 47.5% | Expanding (from 35.1%) |
| Returns | ROE / ROA | 39.7% / 14.8% | Excellent |
| Cash flow | 9M 2026 operating CF | $7.64B | +56% YoY |
| Cash flow | 9M 2026 capex | $1.65B | Down ~54% YoY |
| Cash flow | 9M 2026 derived FCF | ~$5.99B | ~4.7x prior year |
| Balance sheet | Current ratio | 5.6x | Very strong liquidity |
| Balance sheet | Debt-to-equity | 0.71x | Moderate leverage |
| Balance sheet | Equity (Sep 2026) | $19.2B | Up ~18% in 9 months |
| Insider activity | Recent sales | ~$300 (Oct 2026), ~$264–$308 (Aug–May) | Heavy, recurring selling |
| Insider activity | Open-market buys | None in record | Negative signal |
| Risk | Beta | 1.39 | Above-market volatility |
| Technicals | Price vs 50/200-day avg | ~$297 vs $284 / $265 | Constructive trend |

## II. Research Team Decision

### Bull Researcher

Bull Analyst: # Bull Case for TXN: Opening Argument

Let me start with the numbers that matter most, because the bear case will probably try to bury them under valuation worries.

**Texas Instruments (TXN) is a business whose earnings are accelerating, not peaking.** Revenue growth went from +18.6% YoY in Q1 2026 to +22.8% in Q2 and +27.7% in Q3. Gross margin rose from 57.4% a year ago to 64.2%. Operating margin rose from 35.1% to 47.5%. Diluted EPS went from $1.48 to $2.62, up 77%. Few large-cap companies are showing that combination of top-line acceleration and margin expansion at the same time.

## The growth story is a cash story

The most underappreciated part of this quarter is free cash flow. Capex for the first nine months of 2026 was $1.65B, down about 54% from $3.63B a year earlier. Operating cash flow rose 56% to $7.64B. Derived free cash flow went from about $1.3B to about $6.0B, roughly 4.7x.

That matters because it shows where the money goes. The fab build-out from 2022 to 2025 was a heavy investment cycle. Now that spending is winding down, and the revenue from that capacity is arriving. Each incremental dollar of revenue is converting to cash at a high rate. The company has a 39.7% ROE, a 5.6x current ratio, and a 0.71x debt-to-equity ratio, and it is still returning capital through dividends and buybacks. It raised the dividend 7% in September.

## Valuation: the bear's best argument, and why it's weaker than it looks

I'll grant the bear the trailing number. At 38.6x trailing earnings and 14.2x book, TXN is not cheap on backward-looking metrics. But trailing earnings are the wrong yardstick for a business whose earnings power is changing this fast.

The forward P/E of 25.6x implies consensus EPS of $11.63, against $7.71 trailing. Here is what that requires: about $2.91 per quarter on average over the next four quarters. The most recent quarter came in at $2.62, and EPS grew about 22% sequentially from Q2 to Q3. Reaching $2.91 average means a step-up of roughly 11% from Q3's level. That is a demanding number, but it is not heroic given the trajectory and the margin structure. The PEG ratio of 0.92 says the market is not pricing in growth that is far beyond what the company is delivering.

Simply Wall St. says the stock "looks fully valued." I think that is a fair description of the price, but not of the earnings. The bull case here does not need multiple expansion. It needs the earnings the company is already printing to keep arriving.

## Pricing power is the quiet competitive edge

Analog and embedded chips are less glamorous than AI accelerators, and that is part of the appeal. Zacks reports that tight supply and firm demand could support price increases into 2027. A 60%-plus gross margin does not come from undifferentiated products. It comes from a broad portfolio of long-life analog and embedded parts that customers design into industrial and automotive systems, where switching suppliers is expensive and slow.

Customer resistance is a real risk, and I'll address it below. But the fact that pricing is even on the table, after a multi-year cycle, tells you something about the demand environment.

## The technical picture supports accumulation, not chasing

Price sits above both the 50-day ($283.6) and 200-day ($262.8) averages, and both are rising. The 200 SMA has climbed from 252 in mid-October. That is a healthy long-term structure.

The most important recent event is the November 5 selloff. The stock fell about 10.7% on 19.2 million shares, the heaviest volume in the window, and then recovered fully to 312.48 by November 12. High-volume flushes that get reclaimed quickly often mark demand absorbing supply, and this one did. The bear will point to the drop to 277 as proof of fragility. I see it as proof that buyers showed up at lower prices.

I agree the MACD has turned bearish and the histogram is negative. That is a signal to be patient on size, not to exit. The RSI sits at 52, neutral, nowhere near overbought. And note that today's 1.6M-share volume reading is almost certainly a partial session, so I'm not drawing any conclusions from it.

## Addressing the bear's likely arguments

**"Insiders are selling."** This is accurate and worth taking seriously. Heavy, recurring sales by the CEO, CFO and multiple directors, with no open-market purchases on record, is not a bullish signal on its face. But context matters. Most of these sales are tied to option exercises at strikes between $79 and $174, which means insiders are realizing gains on long-held compensation. The sales are routine rather than panicked. The absence of insider buying is a weaker signal at a company that pays executives largely in equity. I would watch for a change in pattern, but I don't think it overrides the earnings data.

**"Rates are a headwind."** Prediction markets price a 98% chance of no Fed cuts in 2026. That is a fair headwind for long-duration equities. But TXN's return case rests on earnings and free cash flow growth, not on a lower discount rate. And the FRED data is missing, so I'd rather not build a rates argument on incomplete data in either direction.

**"Export restrictions could hit chip stocks."** This is the bear's strongest near-term card, and I won't pretend it's nothing. A headline said chip stocks fell on US semiconductor restrictions, and I can't yet confirm the scope or TXN's China exposure. That needs to be checked before sizing. But TXN's industrial and automotive end markets are less exposed to the AI-accelerator export regime than the names that drove the headlines. The Nvidia leadership shock has mostly rotated money into AMD and Broadcom, not out of analog. TXN has been a bystander, which is a point in its favor for diversification.

**"Growth is cyclical and could fade."** Yes, some of the recovery reflects cyclical restocking. But the margin expansion is not purely cyclical. Operating leverage from a lower capex base is structural, and FCF growth is coming from the fab investment cycle ending, not only from volume.

**"Beta is 1.39."** It is. That argues for disciplined sizing, not for avoiding the stock. A beta above one means you get paid more for owning it through a cycle when the cycle is turning up.

## Where I'd concede ground

I don't want to oversell this. Several things could prove me wrong:

- Q4 2026 guidance that fails to show sequential growth would put the $11.63 forward EPS in doubt.
- Evidence of customer pushback on 2027 pricing would undermine the margin thesis.
- A confirmed export restriction affecting TXN's China revenue would be a material hit.
- A decisive close below the 50-day SMA (~$284) on volume would weaken the trend.

The social sentiment data is thin (18 StockTwits messages, two tagged, Reddit unavailable), so I'm not leaning on it. The 28% Q3 revenue figure from TIKR is unverified, though the fundamentals data independently shows +27.7%, which is reassuring.

## My position

I'd build a position in tranches rather than all at once. The first tranche makes sense now, given the trend, the cash generation, and the recovery from the November flush. I'd add on a sustained close above the 316–317 resistance zone on rising volume, which would confirm a breakout. I'd treat a close below the 50-day average as a signal to re-check the thesis, not as an automatic exit. Position size should reflect ATR near 13 and beta near 1.4.

The bear will likely argue the stock is priced for perfection. My answer is that it's priced for continued execution, and the execution so far has been exceptional. Revenue is accelerating, margins are expanding, cash is compounding, and the balance sheet is clean. That is the setup a bull should want, even at a full multiple.

### Bear Researcher

Bear Analyst: # Bear Case for TXN: Rebuttal

The bull opened with a strong set of numbers, and I'll take them seriously. Revenue growth of 27.7%, operating margin of 47.5%, and FCF up about 4.7x are real. My disagreement is with what they're being asked to prove. The bull is treating a cyclical recovery as a structural re-rating and asking us to pay a full price for that conclusion. The data doesn't yet support it.

## The forward multiple depends on a number that hasn't happened yet

The bull says the forward P/E of 25.6x "compresses sharply" as earnings grow, and that $11.63 forward EPS requires only about $2.91 per quarter, roughly 11% above Q3's $2.62. That framing makes the target sound modest. Look at what it actually asks for.

At today's price of about $297.84, here is what the multiple looks like under different earnings outcomes:

| EPS scenario (annualized) | Basis | Implied P/E at $297.84 |
|---|---|---|
| $11.63 | Consensus forward | 25.6x |
| $10.48 | Q3 2026 run-rate ($2.62 × 4) | 28.4x |
| $8.56 | Q2 2026 run-rate ($2.14 × 4) | 34.8x |

So even if the company simply holds its current quarterly earnings, the stock is not at 25.6x. It's at 28x. The "cheap forward multiple" only appears if EPS keeps climbing every quarter from here. That's a bet on an unbroken sequence of sequential increases through a cyclical upturn.

The bull's PEG argument has the same problem. A PEG of 0.92 means the 25.6x forward multiple is being divided by a growth rate of roughly 28%. The PEG only looks reasonable if you assume that 28% growth is durable. That is the claim in dispute.

## "Accelerating" may be a recovery off a trough

The bull calls this an acceleration story. The quarterly data suggests something more specific: a rebound.

Using the TTM revenue figure of $20.77B and the Q1–Q3 2026 numbers, the implied Q4 2025 revenue is about $4.43B. That's below Q3 2025's $4,742M, which means revenue fell sequentially at the end of 2025. Implied Q4 2025 EPS is about $1.27, below Q3 2025's $1.48. The business bottomed around the end of last year and has climbed roughly 37% in revenue since. That's a V-shaped cyclical recovery.

This matters for two reasons. First, the YoY growth rates of 18.6%, 22.8%, and 27.7% are measured against depressed 2025 comparisons. As the base normalizes, YoY growth must decelerate even if the business keeps improving. The bull is extrapolating the rate of change of a rebound. Second, cyclical recoveries are exactly when peak-cycle multiples are most dangerous. TXN's industrial and auto exposure means its earnings are tied to customer capex and inventory cycles. The bull's own StockTwits-style "cyclical capex" concern is a live issue here, and the bull never answers it.

## The "capital-light" claim contradicts the bull's own argument

The bull makes two claims that don't fit together. First, that the 2022–2025 fab build-out was a "heavy investment cycle." Second, that the company has a "capital-light return profile" and that the margin gains are structural.

You can't have both. TI's economics are built on a large fixed-asset base: total assets have been flat around $35–37B for two years, and the bull's own FCF argument depends on capex. Where the bull says the margin expansion is "structural operating leverage from a lower capex base," I'd point out three problems:

1. **Depreciation lags capex.** Fabs built from 2022 to 2025 are coming online and depreciating now. A capex cut doesn't immediately lower cost of goods sold. If anything, the depreciation wave from that build-out is still working its way through the P&L.
2. **The capex cut is a choice.** Capex fell 54% to $1.65B for nine months. That's a cyclical lever, and it reverses when demand returns and capacity gets tight. The bull treats a 54% reduction as a permanent state. It could just be the trough of the investment cycle.
3. **FCF is lumpy.** The fundamentals report puts trailing FCF at $4.78B, while the 9M 2026 derived figure is $5.99B. The gap is explained by a heavier capex period in Q4 2025. A nine-month run-rate is not the same as a sustainable annual figure.

## Insider selling is a signal, not noise

The bull says insider sales are routine option exercises at strikes between $79 and $174, and that the absence of insider buying is "weaker" because TXN pays executives in equity.

I'd push back on that logic. Option exercises at low strikes still produce cash-out sales, and the sales have continued at higher prices. The CFO sold roughly $14.7M at about $308 in May. Directors sold at about $302–303 in October. Insiders have been selling at $220, at $264, at $280, at $300, and at $308. They aren't waiting for a target; they're taking money off the table across the entire recent range.

The bull's rebuttal also contains an odd inversion. If equity pay is the reason insiders don't buy, that's the reason their absence matters more. Insiders with the most information and the most skin in the game have sold heavily and bought nothing on the open market. That is a sentiment signal, even if it isn't a verdict.

## The November flush is distribution, not absorption

The bull reads the November 5 selloff as "demand absorbing supply." I read the same event differently.

The highest-volume session in the entire window was the day the stock fell 10.7%, on 19.2 million shares. Heavy volume on a sharp down day is where sellers show up. The bull describes a full recovery to 312.48, but the recovery took five sessions, and the stock has since given back about 4.7%. The stock is now below its 10-day EMA, MACD is below its signal line, and the histogram has turned negative.

There's also a divergence the bull skipped. RSI peaked at 71.8 on October 29. Price then made higher highs in early November, to the 316–317 area on both 11/03 and 11/12, but RSI didn't follow. That's lower momentum at the same price highs. Two tests of 316–317 without a close above it is a ceiling, not a base. I'd want to see the volume on the recovery days before calling that absorption, and the bull hasn't shown it.

The bull's accumulation plan also assumes the 316–317 breakout comes. If it doesn't, the first tranche is buying into a range that has already rejected the stock twice, with momentum fading.

## Dismissing the rates and export risks doesn't make them go away

**Rates.** The bull says it would rather not build a rates argument on incomplete FRED data. But the prediction-market data is available: a 98% probability of no Fed cuts in 2026. You don't need a 10-year yield print to know the market is pricing higher-for-longer. A stock at 25.6x forward and 14.2x book is a long-duration asset. Its valuation is exactly the kind that suffers when discount rates don't fall.

**Export restrictions.** The bull concedes this is the bear's strongest card, then argues TXN is "less exposed" to AI-accelerator export rules. The problem is that nobody in this debate knows the scope. The headline said chip stocks fell on US semiconductor restrictions. The bull admits it can't confirm the scope or TXN's China exposure. China has historically been one of TI's larger end markets, and the bull is asking us to size a position before knowing the size of the single biggest unknown. That's not disciplined sizing. That's sizing blind.

The bull also says TXN was a "bystander" to the Nvidia shock, which it presents as diversification. I'd note that the sector rotation was a sign of how fast sentiment moves in semis. A stock with beta of 1.39, a 52-week range from $153 to $334, and ATR near 13 has earned the right to be treated as volatile.

## Where the bull has a point

I don't want to pretend the bull has nothing. The fundamentals are excellent. Gross margin has expanded from 57% to 64%, ROE is near 40%, the balance sheet is clean, and the company is still returning cash. The pricing-power thesis is plausible, and the 2027 pricing commentary is worth watching. If Q4 guidance comes in strong and customers accept price increases without pushback, the bull's case gets much stronger, and I'd have to revisit my view.

I also agree with the bull that the sentiment data is thin. But thin data cuts both ways. We have no evidence that the market is buying this rally with conviction.

## My position

I wouldn't build a position here. I'd wait, for three reasons:

1. **The valuation requires continued sequential EPS growth.** At the current run-rate, the stock is 28x, not 25.6x, and there's no margin of safety if the cycle flattens.
2. **The technicals have not confirmed the bull's read.** The 316–317 area has capped the stock twice, momentum has weakened, and the biggest-volume session was a sharp down day.
3. **The biggest downside risks are unquantified.** Export scope, China exposure, and 2027 pricing pushback have not been checked, and the bull admits as much.

If you want exposure, I'd prefer to wait for one of two things: a pullback toward the 50-day SMA near $284 with volume that signals stabilization, or a decisive close above 317 on volume with confirmed guidance. Until then, the risk-reward is asking you to pay full value for peak-cycle earnings that have to keep climbing.

The bull says the stock is "priced for continued execution." My point is that it's priced for execution that hasn't happened yet, in a cycle that has already produced a V-shaped recovery, against a rates backdrop that offers no help.

### Research Manager
**Recommendation**: Hold

**Rationale**: The bull case is strong on fundamentals: revenue growth accelerated to +27.7% YoY in Q3, gross margin expanded from 57.4% to 64.2%, operating margin rose to 47.5%, EPS is up 77% YoY, and 9M derived FCF rose roughly 4.7x as capex fell about 54%. The balance sheet is clean and the company is still returning capital. The bear's rebuttal lands on several points that the bull does not fully answer. At $297.84, the stock trades at about 28x on the Q3 annualized run-rate, not 25.6x, so the valuation depends on sequential EPS growth continuing. The implied Q4 2025 figures point to a V-shaped cyclical rebound off a trough, so YoY rates will decelerate as the base normalizes. The capex cut may be cyclical rather than permanent, and depreciation from the 2022–2025 build-out is still flowing through the P&L. Technically, the stock has rejected the 316–317 zone twice, and RSI divergence and a negative MACD histogram show fading momentum. Insider selling has continued across the $220–$308 range with no open-market buying. Two material unknowns remain unchecked: the scope of the US chip export restrictions and TXN's China exposure, and the rates backdrop (98% priced for no 2026 Fed cuts). The bull's strongest points are real, but the bear's concerns about entry price, unresolved downside risks, and unconfirmed breakout make a full commitment premature. Neither side wins decisively, so the balanced call is Hold, with a clear list of triggers that would move the view to Overweight or Underweight.

**Strategic Actions**: 1. Maintain the current TXN position at its existing size. Do not add a new tranche at ~$298 until a trigger is met. Treat a standard allocation as the reference point, and do not exceed it on this call.
2. Upgrade trigger (to Overweight, add in tranches toward a standard allocation): a decisive daily close above 317 on rising volume, confirmed by Q4 2026 guidance showing sequential revenue and EPS growth, and no evidence of 2027 pricing pushback.
3. Pullback trigger (to Overweight on a dip): a retracement toward the 50-day SMA (~$284) that holds on volume showing stabilization, with fundamentals intact.
4. Downgrade trigger (to Underweight, trim toward a reduced position): a decisive close below the 50-day SMA (~$284) on heavy volume; confirmed US export restrictions affecting TXN's China revenue; or Q4 guidance showing sequential decline or margin compression.
5. Before any change in sizing, verify the export-restriction scope, TXN's China revenue share, and the current rates backdrop. These are open items; the debate did not establish them.
6. Size any future change against ATR (~13) and beta (~1.4). Set risk limits accordingly. Treat the 11/05 flush-and-recovery as neither a confirmed base nor a confirmed distribution top.
7. Re-check the thesis after the next earnings report. Watch for revenue growth decelerating toward a normalized rate, gross margin holding above ~60%, and FCF sustaining above a nine-month run-rate.

## III. Trading Team Plan

### Trader
**Action**: Hold

**Reasoning**: The research plan lands on Hold: fundamentals are strong (Q3 revenue +27.7% YoY, gross margin 64.2%, FCF rising sharply), but valuation near 28x run-rate, unresolved China/export-restriction exposure, and an unconfirmed breakout at the 316-317 resistance argue against adding at ~297.84. Technically, price is above the rising 50 and 200 SMAs, but MACD has turned bearish (histogram -0.286), RSI is neutral at 52, and price sits 2.8 below the 10 EMA (300.60). Since the user holds no position, the practical action is to stay out and wait for a trigger: a decisive close above 317 on volume or a pullback toward the 50 SMA (~284) that holds. Note that the 2026-11-16 volume (1.63M) looks partial, so volume-based confirmation is not yet reliable.

**Entry Price**: 284.0

**Stop Loss**: 277.0

**Position Sizing**: No position now. If the pullback entry triggers, start with a half-size tranche sized against ATR ~13.3 (stop ~26 points below entry, so risk no more than about 1% of the portfolio per tranche), and scale to a standard allocation only after a decisive close above 317 with confirmed fundamentals.

FINAL TRANSACTION PROPOSAL: **HOLD**

## IV. Risk Management Team Decision

### Aggressive Analyst

Aggressive Analyst: I'll open the debate, and I think the Hold is too timid. Let me explain why.

Start with what the stock has already proven. On November 5, TXN fell about 10.7% on 19.2 million shares, the heaviest volume in the window. Most traders would read that as a breakdown. Instead, buyers absorbed the supply, and by November 12 the stock had recovered to 312.48, above the pre-selloff close. That is a market with strong demand at lower prices, and the Hold plan ignores it. Waiting for a pullback to 284 means asking the market to revisit a level it has already rejected at high volume, while the fundamentals keep getting better.

The fundamentals are the core of my argument. Q3 revenue grew 27.7% year over year, up from 18.6% in Q1 and 22.8% in Q2. Gross margin rose from 57% to 64%, and operating margin went from 35% to 47.5%. Nine-month free cash flow is roughly 4.7 times last year's, because capex fell about 54% as the fab build-out wound down. A company with that trajectory does not deserve a "wait and see" stance. The forward P/E of 25.6x against a trailing 38.6x reflects consensus expecting EPS to climb from $7.71 to $11.63. If even most of that comes through, the stock is cheap on the earnings it will report, not expensive. A PEG of 0.92 says the same thing.

The conservative view will point to valuation. "Fully valued" is an argument about the past. Simply Wall St. is looking at a 121% three-year return, which tells you what the stock did, not what it will earn. The market is paying for the earnings ramp, and the ramp is showing up in reported numbers. Meanwhile the Zacks pricing thesis for 2027 suggests tight supply could support further price increases, which would extend margin expansion beyond what consensus already models.

On the technical side, the Hold plan cites a bearish MACD crossover and a negative histogram. Those readings are small, -0.286 on a MACD near 5, and they are coming off an overbought RSI of 71.8 that has already cooled to 52. That is a healthy reset, not a broken trend. Price sits above a rising 50 SMA and a rising 200 SMA, and the stock has tested the 316–317 zone twice without breaking down. Two failed attempts at resistance in a rising trend is a base forming, not a sign of weakness. A decisive close above 317 is the breakout the Hold plan is waiting for, but by then the easy part of the move has happened.

I also want to challenge the insider selling argument. Yes, the record shows no open-market buys, and that deserves attention. But most of the sales are option exercises at strikes between $79 and $174. Insiders are cashing out options that are deep in the money. That is a tax and diversification decision, not a bearish forecast on a company whose margins just hit a multi-year high.

The real risk is the export-restriction headline and China exposure. That is legitimate, and I would not pretend otherwise. But the evidence we have is a headline with no details, and the stock's reaction to the November 5 shock was to recover in a week. Using that uncertainty as a reason to sit out, when the trend is accelerating, means accepting a certain opportunity cost to avoid an uncertain one.

So here is my counterproposal. Don't wait for 284. Take a starter position now near 298, sized to risk about 1% of the portfolio. With a stop at the November 6 reference low of 277, that is roughly a 21-point risk per share, so on $100,000 you can hold around 45 to 50 shares, about $14,000 of exposure. That is aggressive in conviction and disciplined in dollars. Add the rest on a decisive close above 317 with volume confirmation, or on a pullback to 284 that holds, whichever comes first. The Hold keeps the trader on the sidelines for a trigger that may arrive after the move has already been made.

### Conservative Analyst

Conservative Analyst: I want to start with the strongest part of your case, because I think it's also where the argument is weakest. You say buyers absorbed the November 5 selloff. On that day TXN fell about 10.7% on 19.2 million shares, the heaviest volume in the window, and the next session was a low-volume follow-through to 277.36. High volume at the bottom is consistent with absorption, but it's just as consistent with distribution: sellers handing shares to whoever wants them at a discount. One heavy session can't tell us which, and the recovery to 312.48 has already partly reversed. The stock closed at 297.84 on November 16, about 4.7% below the November 12 close. The market has already given back a meaningful share of the rebound you're pointing to.

On the fundamentals, I don't dispute the numbers. Revenue up 27.7%, gross margin at 64.2%, and nine-month free cash flow near $6 billion are excellent. My concern is what the price already assumes. The forward P/E of 25.6x only looks reasonable because consensus expects EPS to climb from $7.71 to $11.63, a 51% step-up. The PEG of 0.92 depends on that same forecast. So the valuation argument rests on the one thing we can't yet verify. The world affairs report also flags that the 28% Q3 growth figure from TIKR hasn't been checked against a primary filing. The Fundamentals report uses 27.7%, but we should reconcile that before treating the growth rate as settled. The stock trades at 14.2 times book, and if growth normalizes from a cyclical recovery, which the fundamentals report explicitly names as a possibility, the multiple won't fall gently. It will reprice.

You describe the 2027 pricing thesis as upside that consensus hasn't modeled. The Zacks piece actually names customer resistance as the main risk to those price increases, and Simply Wall St. calls the stock fully valued after a 121% three-year run. Those are the same people you're citing for the bullish case, and they're telling us the bullish case is priced in.

The technical picture is also less clean than you describe. You call the two tests of 316–317 a base. In a trading range, two failed attempts at the same level is a double top until proven otherwise. Over the same period, MACD has fallen from 8.81 to 5.29, the signal line has crossed above it, the histogram has turned negative, and RSI has not made a new high alongside price since late October. Those aren't "small" signals in isolation when they all point the same way. And a 1% stop-loss risk plan doesn't protect against the very event you're dismissing. The November 5 open was about 3% below the prior close, and the low was 277.87. A stop at 277 can gap through on the next shock, and then the loss is larger than the 1% you planned for.

Your stop math has a second problem. The research uses ATR of 13.3 and suggests a stop roughly 26 points away. A 21-point stop at 298 is about 1.6 ATR, which is tight for a stock that just moved 10% in a day. You may get stopped out by normal noise before the thesis has a chance to play out. The stop is also a few cents of arithmetic on $100,000; the real question is whether the entry is good, and at 298 it isn't.

That brings me to the trade-off you're calling opportunity cost. Entering at 298 with a stop at 277 risks about 21 points to make about 19 points up to the 317 resistance. That's roughly one dollar of upside for each dollar of risk, before accounting for the chance that resistance holds. The Hold entry at 284 with the same stop risks about 7 points for about 33 points of upside to resistance, which is close to 4.7 to 1. The Hold doesn't give up the trend. It waits for a better price, and the cost is nothing if the stock doesn't pull back. If it does, we get a much better risk profile. Your plan saves a few percentage points of missed upside in exchange for a substantially worse setup.

On the insider selling, I'd agree that option exercises are a weaker signal than open-market sales. But the record shows the CFO selling about $14.7 million near $308 in May, directors selling near $302 to $303 in October, and no open-market purchases in the period we have. The pattern is consistent selling into strength, whatever the tax reasons. I wouldn't call it bearish on its own, but it's a fact that cuts against "the market is absorbing supply at higher prices."

Finally, you say the export-restriction headline has no details, so it's not worth worrying about. I'd say that's the opposite of what it calls for. A headline that moved chip stocks, combined with unknown China exposure, is exactly the kind of unquantified risk that should reduce size, not justify full conviction. We also don't know what drove the November 5 drop. Qualcomm fell about 10% the same day, so it may have been sector-wide news rather than something TXN-specific that buyers "absorbed." Assuming TXN will recover from the next shock because it recovered from this one assumes the next shock looks like the last.

Macro adds to the caution. The market prices essentially no Fed cuts in 2026, and we have no verified current rate, CPI, or yield data because FRED is unavailable. Beta is 1.39. For a high-multiple stock, that combination makes a drawdown more likely than a clean breakout, and we'd be adding exposure into it.

So my position is that the Hold is the right call, and it's the one that protects the firm's capital while still giving the trader a way in. Wait for a pullback toward 284 that holds, or a decisive close above 317 on confirmed volume. If we enter at the pullback, start with a half-size tranche, keep total risk near 1% of the portfolio, and only scale up after the fundamentals and the export question are checked against primary sources. Waiting costs us little if the trend continues, and it protects us a great deal if it doesn't.

### Neutral Analyst

Neutral Analyst: Both of you are right about different parts of this, and each of you leans on the strongest evidence while skating past the weakest. Let me push on both.

Aggressive, you say buyers absorbed the November 5 selloff, and the stock did recover to 312.48 within a week. But a high-volume flush followed by a rebound is what absorption looks like, and it is also what a shakeout looks like before the next leg down. You can't tell which from one session. Since then TXN has given back about 4.7% from the November 12 close, and the histogram has turned negative. I'd treat the recovery as evidence that the bulls are still interested at lower prices, not as proof that the November 5 low is a floor. Your fundamental case is also more conditional than you present it. The 25.6x forward multiple only looks cheap if the EPS path from $7.71 to $11.63 arrives. That is a roughly 51% step-up, and "most of it coming through" is a bet on execution, not a fact in the data. Your stop math has its own problem. A 21-point stop from 298 to 277 is about 1.6 ATR. On a stock that moved 10% in a day, normal noise can take you out before the thesis has room to work. You can keep the dollar risk at 1% and still have a stop that is too tight to survive the stock's ordinary swings.

Conservative, your case is strongest on valuation and on the export-restriction headline, and I agree that unquantified China exposure argues for smaller size. But your risk-reward math is doing more work than it can bear. You compare a 298 entry with 19 points of upside to a 284 entry with a 277 stop, which is only 7 points of risk, and call that 4.7 to 1. A 7-point stop on a stock with a 13.3 ATR is a stop you will hit on a random Tuesday. The better setup you're describing depends on a stop that the volatility doesn't support. The trader's own plan has the same inconsistency: it suggests a stop roughly 26 points below entry, but pairs the 284 entry with a 277 stop. You can't have both. You also say waiting costs nothing if the stock doesn't pull back. That isn't quite right. If TXN grinds higher from here, the cost of waiting is real, and the trend is still intact, with the 50 SMA and 200 SMA both rising. Calling the cost zero is a way of making the Hold look free.

On the double top, I'd say the picture is genuinely unresolved rather than bearish. Two tests of 316 to 317 without a close above is a resistance zone, and a double top would only be confirmed by a break below the neckline, which in this case would be the low end of the recent range rather than the 284 pullback. Neither of you has earned the full version of your reading.

Where I think a moderate strategy does better than either pure view is in separating the entry decision from the risk decision. The entry can be staged. A first tranche of about a third of the intended position could go on near the 284 to 290 zone, if the stock holds there on a daily close, because that area is the 50 SMA and the Bollinger middle band, both of which have been support. The stop for that tranche should be set by volatility and structure, not by the 7-point arithmetic. A stop about 1.5 ATR below entry, which puts it in the 262 to 265 area near the 200 SMA, gives the stock room to breathe, and the size comes from that wider stop. Sized so that the loss at the stop is about 1% of the portfolio, that works out to roughly 45 to 50 shares at 284, which is a sensible starting exposure. The second tranche would wait for a reclaim of 300, ideally with the higher low holding, and the third would wait for a decisive close above 317. The total risk across all tranches should stay near 1%, not 1% each, since otherwise you've quietly tripled the exposure.

Gap risk is real, and neither stop placement fully solves it. The November 5 open was about 3% below the prior close. So the position should be sized so that a gap through the stop, say to the high 250s, costs something you can absorb without reconsidering the whole thesis. That is the honest version of the protection Conservative is asking for.

The export-restriction question should gate the later tranches, not the first one. Before you add the second or third tranche, you should know what the restriction covers and how much of TXN's revenue is China-linked. If the answer is material, the third tranche gets cut or dropped. If it's peripheral, the thesis is intact. That turns an unknown into a checkpoint rather than a reason to sit out or a reason to go all in.

So the moderate answer is neither a starter position at 298 nor a pure wait for 284. It is a staged entry with a stop that respects the stock's volatility, total risk capped at about 1%, and the later tranches tied to two things we can verify: a reclaim of 300 or a close above 317, and a clear answer on the export scope. That keeps the upside if the trend continues and limits the damage if the November 5 event turns out to be the first of a series.

## V. Portfolio Manager Decision

### Portfolio Manager
**Rating**: Hold

**Executive Summary**: Stay out of TXN for now; there is no current position and no new tranche at ~$298. Enter only on a trigger: a pullback to the 50-day SMA (~$284) that holds on stabilizing volume, or a decisive daily close above $317 on rising volume with Q4 guidance confirming sequential growth. If a pullback entry triggers, start with a half-size tranche risking no more than about 1% of the $100,000 portfolio, with the stop set around $277 and sized against ATR (~13.3), and tie any later tranches to the export-restriction and China-exposure checks.

**Investment Thesis**: The fundamentals are strong and both sides agree on them: Q3 revenue grew 27.7% YoY, gross margin reached 64.2%, operating margin is 47.5%, EPS is up about 77% YoY, and nine-month FCF is roughly 4.7x last year as capex fell about 54%. The balance sheet is clean. The debate turns on price and risk, not on the quality of the business.

The aggressive case is that the November 5 drop on 19.2M shares was absorbed, with the stock back at 312.48 by November 12, and that the forward P/E of 25.6x is cheap if EPS climbs from $7.71 to $11.63. The conservative and neutral cases answer that the recovery has already partly reversed (about 4.7% off the November 12 close by November 16), that the high-volume flush is equally consistent with distribution, and that the 25.6x multiple depends on a roughly 51% EPS step-up that is not yet proven. The research plan adds that the stock trades near 28x the Q3 annualized run-rate, that YoY growth will decelerate as the base normalizes, and that depreciation from the build-out is still flowing through the P&L. The bull case does not answer these points, so the valuation depends on execution.

On technicals, the stock has rejected the 316–317 zone twice. MACD has fallen from 8.81 to 5.29 and the histogram is negative (-0.286). RSI has cooled from 71.8 to 52 without a new high alongside price. Price is still above the rising 50 and 200 SMAs, so the trend is intact, but momentum is fading. The aggressive analyst is right that this is not yet a broken trend, and the conservative analyst is right that it is not yet a confirmed breakout.

Insider selling (CFO about $14.7M near $308, directors near $302–303) with no open-market purchases is a fact that cuts against the bull case, though the aggressive analyst reasonably notes that most sales are option exercises.

The aggressive entry at ~$298 with a 277 stop is poor on the stated risk-reward (about 19 points of upside to 317 for about 21 points of risk), and the 1%-risk sizing is tight relative to a 13.3 ATR. The conservative entry at 284 is better but its 7-point stop is too tight for the volatility, as the neutral analyst notes. The neutral staged-entry approach resolves this by sizing from a volatility-based stop rather than from the entry-to-support arithmetic.

Two material unknowns remain unverified: the scope of US chip export restrictions and TXN's China revenue share, and the current rates backdrop (98% priced for no 2026 Fed cuts; FRED data unavailable). These should gate sizing changes, and the debate did not establish them. Beta is about 1.4, so a drawdown is plausible. The November 16 volume (1.63M) appears partial and cannot be used for confirmation.

Balance: the bull case is strong on fundamentals but weak on entry price and risk. The bear case is strong on price and unresolved risk but does not show the fundamentals are failing. Neither side wins decisively, so Hold is the call. The Hold keeps the opportunity open through explicit triggers rather than committing capital at an unconfirmed level.

What would change the view. Upgrade to Overweight: a decisive close above 317 on rising volume, Q4 2026 guidance showing sequential revenue and EPS growth, and no evidence of 2027 pricing pushback. Pullback entry (Overweight on a dip): a retracement to ~284 that holds on stabilizing volume with fundamentals intact. Downgrade to Underweight: a decisive close below 284 on heavy volume; confirmed export restrictions affecting China revenue; or Q4 guidance showing sequential decline or gross-margin compression below ~60%. Re-check the thesis after the next earnings report: revenue growth decelerating toward a normalized rate, gross margin above ~60%, and FCF sustaining above the nine-month run-rate.

**Price Target**: 317.0

**Time Horizon**: 3-6 months