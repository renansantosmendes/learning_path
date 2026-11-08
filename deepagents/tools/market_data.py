"""Stock prices, returns and fundamental indicators from Yahoo Finance.

Brazilian tickers such as PETR4 are converted to the Yahoo format (PETR4.SA)
automatically.
"""

import re
from typing import Any

import pandas as pd
import yfinance as yf
from langchain_core.tools import tool

BRAZILIAN_TICKER_PATTERN = re.compile(r"[A-Z]{4}\d{1,2}")
VALID_PERIODS = ("1mo", "3mo", "6mo", "1y", "2y", "5y")
TRADING_DAYS_PER_MONTH = 21
TRADING_DAYS_PER_SIX_MONTHS = 126
TRADING_DAYS_PER_YEAR = 252


class MarketDataError(ValueError):
    """Raised when market data for a ticker cannot be loaded."""


def normalize_ticker(
    ticker: str,
) -> str:
    """Converts a ticker to the Yahoo Finance format.

    Parameters
    ----------
    ticker : str
        Ticker typed by the user, such as ``petr4``, ``AAPL`` or ``^BVSP``.

    Returns
    -------
    str
        Upper-case ticker. B3 codes receive the ``.SA`` suffix.

    Example
    -------
    >>> normalize_ticker("petr4")
    'PETR4.SA'
    """
    symbol = ticker.strip().upper()
    if BRAZILIAN_TICKER_PATTERN.fullmatch(symbol):
        return f"{symbol}.SA"
    return symbol


def fetch_history(
    ticker: str,
    period: str,
) -> pd.DataFrame:
    """Loads the daily price history of a ticker, adjusted for dividends.

    Parameters
    ----------
    ticker : str
        Ticker of the asset, in any format accepted by normalize_ticker.
    period : str
        History length, one of VALID_PERIODS.

    Returns
    -------
    pd.DataFrame
        Daily rows with Open, High, Low, Close and Volume columns.

    Raises
    ------
    MarketDataError
        If the period is invalid or Yahoo Finance returns no prices.
    """
    if period not in VALID_PERIODS:
        raise MarketDataError(
            f"Periodo invalido '{period}'. Use um de: {', '.join(VALID_PERIODS)}."
        )
    symbol = normalize_ticker(ticker)
    history = yf.Ticker(symbol).history(period=period, auto_adjust=True)
    if history.empty:
        raise MarketDataError(f"Nenhum preco encontrado para {symbol}.")
    return history


def fetch_company_info(
    ticker: str,
) -> dict[str, Any]:
    """Loads the company profile and reported indicators of a ticker.

    Parameters
    ----------
    ticker : str
        Ticker of the asset, in any format accepted by normalize_ticker.

    Returns
    -------
    dict[str, Any]
        Fields reported by Yahoo Finance. Empty when the request fails, so
        price data can still be shown.
    """
    try:
        return dict(yf.Ticker(normalize_ticker(ticker)).info or {})
    except Exception:
        return {}


def percent_change(
    closes: pd.Series,
    trading_days: int,
) -> float | None:
    """Percent change of the close over a number of trading days.

    Parameters
    ----------
    closes : pd.Series
        Closing prices in chronological order.
    trading_days : int
        Number of trading days back from the last close.

    Returns
    -------
    float | None
        Change in percent rounded to two decimals, or ``None`` when there is
        not enough history.
    """
    if len(closes) <= trading_days:
        return None
    start = closes.iloc[-1 - trading_days]
    return round((closes.iloc[-1] / start - 1) * 100, 2)


def format_value(
    value: Any,
    suffix: str = "",
) -> str:
    """Formats an optional number for the report, with a fallback.

    Parameters
    ----------
    value : Any
        Number to show, or ``None`` when the source has no value.
    suffix : str
        Text appended after the number, such as ``%``.

    Returns
    -------
    str
        The formatted number, or ``n/d`` (not available).
    """
    if value is None or pd.isna(value):
        return "n/d"
    formatted = f"{value:,.2f}".translate(str.maketrans({",": ".", ".": ","}))
    return f"{formatted}{suffix}"


def build_quote_report(
    symbol: str,
    closes: pd.Series,
    info: dict[str, Any],
) -> str:
    """Builds the text report of the price and profile of an asset.

    Parameters
    ----------
    symbol : str
        Ticker shown in the report.
    closes : pd.Series
        Closing prices of the last year, in chronological order.
    info : dict[str, Any]
        Company profile from Yahoo Finance; missing fields are shown as n/d.

    Returns
    -------
    str
        Report with the last price, returns, 52-week range and profile.
    """
    last_close = closes.iloc[-1]
    previous_close = closes.iloc[-2] if len(closes) > 1 else None
    day_change = (
        round((last_close / previous_close - 1) * 100, 2)
        if previous_close
        else None
    )
    market_cap = info.get("marketCap")
    lines = [
        f"Cotacao de {symbol} ({info.get('longName', 'nome n/d')})",
        f"Preco atual: {format_value(last_close)} {info.get('currency', '')}".rstrip(),
        f"Variacao no dia: {format_value(day_change, '%')}",
        f"Retorno 1 mes: {format_value(percent_change(closes, TRADING_DAYS_PER_MONTH), '%')}",
        "Retorno 6 meses: "
        f"{format_value(percent_change(closes, TRADING_DAYS_PER_SIX_MONTHS), '%')}",
        "Retorno no periodo de 12 meses: "
        f"{format_value(percent_change(closes, min(TRADING_DAYS_PER_YEAR, len(closes) - 1)), '%')}",
        f"Minima de 52 semanas: {format_value(closes.min())}",
        f"Maxima de 52 semanas: {format_value(closes.max())}",
        f"Valor de mercado: {format_value(market_cap)}",
        f"Setor: {info.get('sector', 'n/d')} / {info.get('industry', 'n/d')}",
        "Fonte: Yahoo Finance (yfinance). Os dados podem estar defasados.",
    ]
    return "\n".join(lines)


def build_fundamentals_report(
    symbol: str,
    info: dict[str, Any],
) -> str:
    """Builds the text report of the fundamental indicators of a company.

    Parameters
    ----------
    symbol : str
        Ticker shown in the report.
    info : dict[str, Any]
        Company profile from Yahoo Finance. Yahoo reports percentages as
        fractions and debt to equity in percent; this function converts them.

    Returns
    -------
    str
        Report with valuation, profitability, leverage and liquidity.
    """
    dividend_yield = info.get("trailingAnnualDividendYield")
    debt_to_equity = info.get("debtToEquity")
    lines = [
        f"Indicadores fundamentalistas de {symbol}",
        f"P/L (12 meses): {format_value(info.get('trailingPE'))}",
        f"P/L (projetado): {format_value(info.get('forwardPE'))}",
        f"P/VP: {format_value(info.get('priceToBook'))}",
        f"EV/EBITDA: {format_value(info.get('enterpriseToEbitda'))}",
        f"Dividend yield (12 meses): {format_value(_as_percent(dividend_yield), '%')}",
        f"ROE: {format_value(_as_percent(info.get('returnOnEquity')), '%')}",
        f"ROA: {format_value(_as_percent(info.get('returnOnAssets')), '%')}",
        f"Margem liquida: {format_value(_as_percent(info.get('profitMargins')), '%')}",
        f"Margem operacional: {format_value(_as_percent(info.get('operatingMargins')), '%')}",
        f"Divida liquida / patrimonio: {format_value(_as_ratio(debt_to_equity))}",
        f"Liquidez corrente: {format_value(info.get('currentRatio'))}",
        "Fonte: Yahoo Finance (yfinance). Os indicadores podem estar defasados "
        "ou inconsistentes entre si.",
    ]
    return "\n".join(lines)


def _as_percent(value: Any) -> float | None:
    """Converts a fraction reported by Yahoo Finance into percent.

    Parameters
    ----------
    value : Any
        Fraction such as ``0.30``, or ``None``.

    Returns
    -------
    float | None
        Percent such as ``30.0``, or ``None``.
    """
    if value is None or pd.isna(value):
        return None
    return round(float(value) * 100, 2)


def _as_ratio(value: Any) -> float | None:
    """Converts a debt to equity value reported in percent into a ratio.

    Parameters
    ----------
    value : Any
        Value in percent such as ``76.0``, or ``None``.

    Returns
    -------
    float | None
        Ratio such as ``0.76``, or ``None``.
    """
    if value is None or pd.isna(value):
        return None
    return round(float(value) / 100, 2)


@tool
def get_stock_quote(ticker: str) -> str:
    """Current price, daily change, returns, 52-week range and company profile.

    Returns over 1, 6 and 12 months of a stock or index.

    Use it to check how an asset is trading now. Accepts B3 tickers such as
    PETR4 or VALE3, US tickers such as AAPL, and indices such as ^BVSP.

    Parameters
    ----------
    ticker : str
        Ticker of the asset.

    Returns
    -------
    str
        Text report with the quote, or an error message when it fails.
    """
    try:
        history = fetch_history(ticker, "1y")
    except Exception as error:
        return f"Erro ao consultar cotacao de {ticker}: {error}"
    return build_quote_report(
        normalize_ticker(ticker),
        history["Close"],
        fetch_company_info(ticker),
    )


@tool
def get_stock_fundamentals(ticker: str) -> str:
    """Fundamental indicators of a company.

    P/E, P/B, EV/EBITDA, dividend yield, ROE, ROA, margins, debt to equity
    and current ratio.

    Use it to judge valuation and financial health of a company before
    investing. Values come from Yahoo Finance and may be delayed.

    Parameters
    ----------
    ticker : str
        Ticker of the company, such as PETR4 or AAPL.

    Returns
    -------
    str
        Text report with the indicators, or an error message when the
        company has no data.
    """
    symbol = normalize_ticker(ticker)
    info = fetch_company_info(ticker)
    has_indicators = info.get("trailingPE") is not None or info.get("returnOnEquity") is not None
    if not has_indicators:
        return f"Nenhum indicador fundamentalista disponivel para {symbol}."
    return build_fundamentals_report(symbol, info)
