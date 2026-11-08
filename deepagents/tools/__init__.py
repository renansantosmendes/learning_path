"""Tools of the market analysis agent, grouped by data source.

- search: web news through Tavily.
- market_data: prices, returns and fundamental indicators (yfinance).
- technical: technical indicators (pandas-ta-classic).
- risk: risk and return metrics against a benchmark (empyrical-reloaded).
- macro: Brazilian Central Bank indicators (python-bcb).
- draft: local JSON draft of the analysis, read and updated by the agent.

MARKET_ANALYSIS_TOOLS lists the market tools; search_web is listed apart
because it provides the news side of the analysis.
"""

from tools.draft import create_draft_tools
from tools.macro import get_brazil_macro
from tools.market_data import get_stock_fundamentals, get_stock_quote
from tools.risk import get_risk_metrics
from tools.search import search_web
from tools.technical import get_technical_indicators

MARKET_ANALYSIS_TOOLS = [
    get_stock_quote,
    get_stock_fundamentals,
    get_technical_indicators,
    get_risk_metrics,
    get_brazil_macro,
]

__all__ = [
    "MARKET_ANALYSIS_TOOLS",
    "create_draft_tools",
    "get_brazil_macro",
    "get_risk_metrics",
    "get_stock_fundamentals",
    "get_stock_quote",
    "get_technical_indicators",
    "search_web",
]
