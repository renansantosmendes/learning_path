"""Technical indicators computed with pandas-ta-classic on Yahoo Finance prices.

The indicators and their default lengths follow the finbrain-server project:
moving averages of 9, 21 and 50 days, RSI 14, MACD 12/26/9, Bollinger bands
20/2, ATR 14, ADX 14 and stochastic 14/3/3.
"""

import math
from typing import Any

import pandas as pd
import pandas_ta_classic
from langchain_core.tools import tool

from tools.market_data import (
    MarketDataError,
    fetch_history,
    format_value,
    normalize_ticker,
)

TA_LIBRARY = pandas_ta_classic
MINIMUM_BARS = 50
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
ADX_STRONG_TREND = 25


def _column_starting_with(
    frame: pd.DataFrame | pd.Series | None,
    prefix: str,
) -> pd.Series | None:
    """Finds the output column of an indicator by the start of its name.

    Parameters
    ----------
    frame : pd.DataFrame | pd.Series | None
        Output of a pandas-ta-classic indicator, or ``None``.
    prefix : str
        Start of the column name, such as ``BBP_``.

    Returns
    -------
    pd.Series | None
        The matching column, or ``None`` when it is missing.
    """
    if frame is None:
        return None
    if isinstance(frame, pd.Series):
        return frame
    matches = [name for name in frame.columns if str(name).startswith(prefix)]
    return frame[matches[0]] if matches else None


def _last_value(
    column: pd.Series | None,
) -> float | None:
    """Returns the last finite value of an indicator column.

    Parameters
    ----------
    column : pd.Series | None
        Indicator values in chronological order.

    Returns
    -------
    float | None
        The last value rounded to four decimals, or ``None``.
    """
    if column is None or column.empty:
        return None
    value = column.iloc[-1]
    if pd.isna(value) or not math.isfinite(float(value)):
        return None
    return round(float(value), 4)


def compute_technical_indicators(
    history: pd.DataFrame,
) -> dict[str, float | None]:
    """Computes the technical indicators of the last close of a history.

    Parameters
    ----------
    history : pd.DataFrame
        Daily prices with High, Low and Close columns, in chronological order.

    Returns
    -------
    dict[str, float | None]
        Indicator values keyed by name. Indicators without enough bars are
        ``None``.

    Example
    -------
    >>> indicators = compute_technical_indicators(history)
    >>> indicators["rsi_14"]
    """
    frame = pd.DataFrame(
        {
            "high": history["High"].to_numpy(),
            "low": history["Low"].to_numpy(),
            "close": history["Close"].to_numpy(),
        }
    )
    close = frame["close"]
    macd = frame.ta.macd(fast=12, slow=26, signal=9)
    bands = frame.ta.bbands(length=20, std=2)
    adx = frame.ta.adx(length=14)
    stochastic = frame.ta.stoch(k=14, d=3, smooth_k=3)
    return {
        "current_price": round(float(close.iloc[-1]), 4),
        "sma_9": _last_value(frame.ta.sma(length=9)),
        "sma_21": _last_value(frame.ta.sma(length=21)),
        "sma_50": _last_value(frame.ta.sma(length=50)),
        "rsi_14": _last_value(frame.ta.rsi(length=14)),
        "macd": _last_value(_column_starting_with(macd, "MACD_")),
        "macd_signal": _last_value(_column_starting_with(macd, "MACDs_")),
        "bollinger_percent_b": _last_value(_column_starting_with(bands, "BBP_")),
        "atr_14": _last_value(frame.ta.atr(length=14)),
        "adx_14": _last_value(_column_starting_with(adx, "ADX_")),
        "plus_di_14": _last_value(_column_starting_with(adx, "DMP_")),
        "minus_di_14": _last_value(_column_starting_with(adx, "DMN_")),
        "stochastic_k": _last_value(_column_starting_with(stochastic, "STOCHk_")),
        "stochastic_d": _last_value(_column_starting_with(stochastic, "STOCHd_")),
    }


def describe_signals(
    indicators: dict[str, float | None],
) -> list[str]:
    """Turns indicator values into plain-language signals.

    Parameters
    ----------
    indicators : dict[str, float | None]
        Output of compute_technical_indicators.

    Returns
    -------
    list[str]
        One sentence per signal that can be derived from the values. The
        signals describe the chart; they are not investment advice.
    """
    signals = []
    price = indicators.get("current_price")
    sma_50 = indicators.get("sma_50")
    rsi = indicators.get("rsi_14")
    macd = indicators.get("macd")
    macd_signal = indicators.get("macd_signal")
    adx = indicators.get("adx_14")
    plus_di = indicators.get("plus_di_14")
    minus_di = indicators.get("minus_di_14")
    if price is not None and sma_50 is not None:
        position = "acima" if price > sma_50 else "abaixo"
        signals.append(f"Preco {position} da media movel de 50 dias.")
    if rsi is not None:
        if rsi >= RSI_OVERBOUGHT:
            signals.append("RSI em sobrecompra (acima de 70).")
        elif rsi <= RSI_OVERSOLD:
            signals.append("RSI em sobrevenda (abaixo de 30).")
        else:
            signals.append("RSI em faixa neutra (entre 30 e 70).")
    if macd is not None and macd_signal is not None:
        direction = "acima" if macd > macd_signal else "abaixo"
        signals.append(f"MACD {direction} da linha de sinal.")
    if adx is not None and plus_di is not None and minus_di is not None:
        strength = "forte" if adx >= ADX_STRONG_TREND else "fraca"
        direction = "de alta" if plus_di > minus_di else "de baixa"
        signals.append(f"Tendencia {strength} ({direction}, ADX {format_value(adx)}).")
    return signals


def build_technical_report(
    symbol: str,
    indicators: dict[str, Any],
    period: str,
) -> str:
    """Builds the text report of the technical indicators.

    Parameters
    ----------
    symbol : str
        Ticker shown in the report.
    indicators : dict[str, Any]
        Output of compute_technical_indicators.
    period : str
        History length used in the computation.

    Returns
    -------
    str
        Report with the values and the plain-language signals.
    """
    lines = [
        f"Indicadores tecnicos de {symbol} (historico de {period})",
        f"Preco atual: {format_value(indicators.get('current_price'))}",
        f"Media movel 9 dias: {format_value(indicators.get('sma_9'))}",
        f"Media movel 21 dias: {format_value(indicators.get('sma_21'))}",
        f"Media movel 50 dias: {format_value(indicators.get('sma_50'))}",
        f"RSI 14: {format_value(indicators.get('rsi_14'))}",
        f"MACD: {format_value(indicators.get('macd'))} "
        f"(sinal {format_value(indicators.get('macd_signal'))})",
        f"Bollinger %B: {format_value(indicators.get('bollinger_percent_b'))}",
        f"ATR 14: {format_value(indicators.get('atr_14'))}",
        f"ADX 14: {format_value(indicators.get('adx_14'))}",
        f"Estocastico %K / %D: {format_value(indicators.get('stochastic_k'))} / "
        f"{format_value(indicators.get('stochastic_d'))}",
        "Sinais:",
    ]
    lines.extend(f"- {signal}" for signal in describe_signals(indicators))
    lines.append("Sinais tecnicos nao sao recomendacao de investimento.")
    return "\n".join(lines)


@tool
def get_technical_indicators(ticker: str, period: str = "6mo") -> str:
    """Technical indicators of a stock or index, with plain-language signals.

    Moving averages 9/21/50, RSI 14, MACD, Bollinger %B, ATR, ADX and
    stochastic.

    Use it to understand the price trend and momentum of an asset. Needs at
    least 50 trading days, so use period 3mo or longer.

    Parameters
    ----------
    ticker : str
        Ticker of the asset, such as PETR4, AAPL or ^BVSP.
    period : str
        History length: 3mo, 6mo, 1y, 2y or 5y. Defaults to 6mo.

    Returns
    -------
    str
        Text report with the indicators, or an error message.
    """
    symbol = normalize_ticker(ticker)
    try:
        history = fetch_history(ticker, period)
    except MarketDataError as error:
        return f"Erro ao calcular indicadores de {symbol}: {error}"
    if len(history) < MINIMUM_BARS:
        return (
            f"Historico insuficiente para {symbol} ({len(history)} pregoes). "
            "Use um periodo maior, como 3mo ou 6mo."
        )
    indicators = compute_technical_indicators(history)
    return build_technical_report(symbol, indicators, period)
