"""Risk and return metrics of an asset, computed with empyrical-reloaded.

Metrics use 252 trading days per year, as in the finbrain-server project.
Beta and alpha are measured against a benchmark index, ^BVSP (Ibovespa) by
default.
"""

import math
from typing import Any

import empyrical
import numpy as np
import pandas as pd
from langchain_core.tools import tool

from tools.market_data import (
    MarketDataError,
    fetch_history,
    format_value,
    normalize_ticker,
)

TRADING_DAYS_PER_YEAR = 252
DEFAULT_BENCHMARK = "^BVSP"
VALUE_AT_RISK_CUTOFF = 0.05
MINIMUM_OBSERVATIONS = 30


def _finite_or_none(
    value: float | np.floating | None,
) -> float | None:
    """Keeps a finite number and drops NaN or infinite values.

    Parameters
    ----------
    value : float | np.floating | None
        Value returned by empyrical.

    Returns
    -------
    float | None
        The value rounded to four decimals, or ``None``.
    """
    if value is None or not math.isfinite(float(value)):
        return None
    return round(float(value), 4)


def _percent_or_none(
    value: float | np.floating | None,
) -> float | None:
    """Converts a fraction returned by empyrical into percent.

    Parameters
    ----------
    value : float | np.floating | None
        Fraction returned by empyrical.

    Returns
    -------
    float | None
        Percent rounded to two decimals, or ``None``.
    """
    finite = _finite_or_none(value)
    return None if finite is None else round(finite * 100, 2)


def daily_returns(
    closes: pd.Series,
) -> pd.Series:
    """Simple daily returns of a close series.

    Parameters
    ----------
    closes : pd.Series
        Closing prices in chronological order, indexed by date.

    Returns
    -------
    pd.Series
        Daily returns as fractions, without the first undefined day.
    """
    return closes.pct_change().dropna()


def compute_risk_metrics(
    returns: np.ndarray,
    benchmark_returns: np.ndarray | None,
    risk_free_daily: float,
) -> dict[str, float | int | None]:
    """Computes return, risk and ratio metrics of a daily return series.

    Parameters
    ----------
    returns : np.ndarray
        Daily returns of the asset, as fractions.
    benchmark_returns : np.ndarray | None
        Daily returns of the benchmark over the same days, or ``None``.
    risk_free_daily : float
        Risk-free rate per trading day, as a fraction.

    Returns
    -------
    dict[str, float | int | None]
        Metrics keyed by name. Percent values are already multiplied by 100.
        A metric that cannot be computed is ``None``.

    Example
    -------
    >>> metrics = compute_risk_metrics(returns, None, 0.0)
    >>> metrics["observations"] == len(returns)
    True
    """
    volatility = empyrical.annual_volatility(returns)
    downside = empyrical.downside_risk(returns, required_return=risk_free_daily)
    max_drawdown = empyrical.max_drawdown(returns)
    beta = alpha = None
    if benchmark_returns is not None:
        beta = _finite_or_none(empyrical.beta(returns, benchmark_returns))
        alpha = _percent_or_none(
            empyrical.alpha(returns, benchmark_returns, risk_free=risk_free_daily)
        )
    sharpe = empyrical.sharpe_ratio(returns, risk_free=risk_free_daily)
    sortino = empyrical.sortino_ratio(returns, required_return=risk_free_daily)
    return {
        "observations": len(returns),
        "annual_return_percent": _percent_or_none(empyrical.annual_return(returns)),
        "annual_volatility_percent": _percent_or_none(volatility),
        "sharpe_ratio": _finite_or_none(sharpe) if _is_non_degenerate(volatility) else None,
        "sortino_ratio": _finite_or_none(sortino) if _is_non_degenerate(downside) else None,
        "max_drawdown_percent": _percent_or_none(max_drawdown),
        "value_at_risk_95_percent": _percent_or_none(
            empyrical.value_at_risk(returns, cutoff=VALUE_AT_RISK_CUTOFF)
        ),
        "beta": beta,
        "alpha_annual_percent": alpha,
    }


def _is_non_degenerate(
    risk: float | np.floating,
) -> bool:
    """Tells whether a risk measure is finite and greater than zero.

    Parameters
    ----------
    risk : float | np.floating
        Volatility or downside risk.

    Returns
    -------
    bool
        ``True`` when the ratio that divides by this risk can be shown.
    """
    return math.isfinite(float(risk)) and abs(float(risk)) > 1e-12


def build_risk_report(
    symbol: str,
    benchmark: str,
    metrics: dict[str, Any],
    risk_free_annual_percent: float,
) -> str:
    """Builds the text report of the risk metrics of an asset.

    Parameters
    ----------
    symbol : str
        Asset ticker shown in the report.
    benchmark : str
        Benchmark ticker used for beta and alpha.
    metrics : dict[str, Any]
        Output of compute_risk_metrics.
    risk_free_annual_percent : float
        Risk-free rate used in the ratios, in percent per year.

    Returns
    -------
    str
        Report with return, volatility, ratios, drawdown and VaR.
    """
    lines = [
        f"Metricas de risco de {symbol} (referencia {benchmark}, "
        f"{metrics['observations']} pregoes, taxa livre de risco "
        f"{format_value(risk_free_annual_percent, '% a.a.')})",
        f"Retorno anualizado: {format_value(metrics['annual_return_percent'], '%')}",
        f"Volatilidade anualizada: {format_value(metrics['annual_volatility_percent'], '%')}",
        f"Indice de Sharpe: {format_value(metrics['sharpe_ratio'])}",
        f"Indice de Sortino: {format_value(metrics['sortino_ratio'])}",
        f"Drawdown maximo: {format_value(metrics['max_drawdown_percent'], '%')}",
        f"Valor em risco (95%, um dia): {format_value(metrics['value_at_risk_95_percent'], '%')}",
        f"Beta contra {benchmark}: {format_value(metrics['beta'])}",
        f"Alfa anualizado contra {benchmark}: {format_value(metrics['alpha_annual_percent'], '%')}",
        "Metricas calculadas sobre retornos diarios historicos; nao preveem resultados futuros.",
    ]
    return "\n".join(lines)


@tool
def get_risk_metrics(
    ticker: str,
    period: str = "1y",
    benchmark: str = DEFAULT_BENCHMARK,
    risk_free_annual_percent: float = 0.0,
) -> str:
    """Risk and return metrics of a stock against a benchmark.

    Annual return, volatility, Sharpe, Sortino, max drawdown, 95% VaR, beta
    and alpha.

    Use it to judge how much an asset oscillates and how its return compares
    with the market. Beta and alpha are measured against the benchmark, which
    defaults to the Ibovespa (^BVSP). For a Selic-based risk-free rate, get the
    value from get_brazil_macro and pass it as risk_free_annual_percent.

    Parameters
    ----------
    ticker : str
        Ticker of the asset, such as PETR4 or AAPL.
    period : str
        History length: 6mo, 1y, 2y or 5y. Defaults to 1y.
    benchmark : str
        Benchmark ticker for beta and alpha. Defaults to ^BVSP.
    risk_free_annual_percent : float
        Risk-free rate in percent per year. Defaults to 0.

    Returns
    -------
    str
        Text report with the metrics, or an error message.
    """
    symbol = normalize_ticker(ticker)
    benchmark_symbol = normalize_ticker(benchmark)
    try:
        asset_closes = fetch_history(ticker, period)["Close"]
        benchmark_closes = fetch_history(benchmark, period)["Close"]
    except MarketDataError as error:
        return f"Erro ao calcular risco de {symbol}: {error}"

    asset_returns = daily_returns(asset_closes)
    aligned = pd.concat(
        [asset_returns.rename("asset"), daily_returns(benchmark_closes).rename("benchmark")],
        axis=1,
        join="inner",
    )
    if len(aligned) < MINIMUM_OBSERVATIONS:
        return (
            f"Poucos pregoes em comum entre {symbol} e {benchmark_symbol} "
            f"({len(aligned)}). Use um periodo maior."
        )

    risk_free_daily = (1 + risk_free_annual_percent / 100) ** (1 / TRADING_DAYS_PER_YEAR) - 1
    metrics = compute_risk_metrics(
        aligned["asset"].to_numpy(),
        aligned["benchmark"].to_numpy(),
        risk_free_daily,
    )
    return build_risk_report(
        symbol,
        benchmark_symbol,
        metrics,
        risk_free_annual_percent,
    )
