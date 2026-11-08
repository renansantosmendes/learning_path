"""Brazilian macroeconomic indicators from the Central Bank (SGS, via python-bcb).

The series codes follow the finbrain-server project: Selic target rate
(432), CDI annualized on a 252-day basis (4389) and IPCA accumulated in 12
months (13522).
"""

from datetime import date, timedelta
from typing import Any

import pandas as pd
from bcb import sgs
from langchain_core.tools import tool

from tools.market_data import format_value

SELIC_CODE = 432
CDI_ANNUAL_CODE = 4389
IPCA_12_MONTHS_CODE = 13522
LOOKBACK_DAYS = 400


def fetch_latest_observation(
    code: int,
    today: date,
) -> tuple[date, float] | None:
    """Loads the latest observation of a Central Bank series up to a date.

    Parameters
    ----------
    code : int
        SGS code of the series.
    today : date
        Last day accepted; observations dated after it are ignored, since
        the Central Bank publishes future projections in some series.

    Returns
    -------
    tuple[date, float] | None
        Date and value of the latest observation, or ``None`` when there is
        none.
    """
    frame = sgs.get(
        {"value": code},
        start=(today - timedelta(days=LOOKBACK_DAYS)).isoformat(),
        end=today.isoformat(),
    )
    if frame.empty:
        return None
    values = frame.iloc[:, 0].dropna()
    values = values[values.index <= pd.Timestamp(today)]
    if values.empty:
        return None
    return values.index[-1].date(), float(values.iloc[-1])


def compute_real_rate(
    cdi_annual_percent: float | None,
    ipca_12_months_percent: float | None,
) -> float | None:
    """Real interest rate: CDI discounted by the 12-month inflation.

    Parameters
    ----------
    cdi_annual_percent : float | None
        CDI annualized, in percent per year.
    ipca_12_months_percent : float | None
        IPCA accumulated in 12 months, in percent.

    Returns
    -------
    float | None
        Real rate in percent per year, or ``None`` when an input is missing.

    Example
    -------
    >>> round(compute_real_rate(14.9, 4.5), 2)
    9.95
    """
    if cdi_annual_percent is None or ipca_12_months_percent is None:
        return None
    real = (1 + cdi_annual_percent / 100) / (1 + ipca_12_months_percent / 100) - 1
    return round(real * 100, 2)


def build_macro_report(
    observations: dict[str, tuple[date, float] | None],
) -> str:
    """Builds the text report of the Brazilian macro indicators.

    Parameters
    ----------
    observations : dict[str, tuple[date, float] | None]
        Latest observation of each series, keyed by name: selic, cdi and
        ipca_12m. ``None`` marks a series without data.

    Returns
    -------
    str
        Report with the latest value, its date and the real interest rate.
    """
    labels = {
        "selic": "Selic (meta, % a.a.)",
        "cdi": "CDI anualizado (% a.a.)",
        "ipca_12m": "IPCA acumulado em 12 meses (%)",
    }
    lines = ["Indicadores macroeconomicos do Brasil (Banco Central)"]
    for key, label in labels.items():
        observation = observations.get(key)
        if observation is None:
            lines.append(f"{label}: n/d")
        else:
            observed_on, value = observation
            lines.append(
                f"{label}: {format_value(value)} (data {observed_on.strftime('%d/%m/%Y')})"
            )
    real = compute_real_rate(
        observations["cdi"][1] if observations.get("cdi") else None,
        observations["ipca_12m"][1] if observations.get("ipca_12m") else None,
    )
    lines.append(f"Juro real (CDI descontado do IPCA 12 meses): {format_value(real, '% a.a.')}")
    lines.append("Fonte: Banco Central do Brasil (SGS).")
    return "\n".join(lines)


@tool
def get_brazil_macro() -> str:
    """Latest Brazilian macro indicators: Selic, CDI, IPCA and real rate.

    The Selic target rate, the annualized CDI, the IPCA over 12 months and
    the real interest rate.

    Use it to put stocks in context: interest rates affect valuation,
    banks and companies with debt, and inflation affects margins and
    consumption.

    Returns
    -------
    str
        Text report with the indicators and their dates, or an error message.
    """
    today = date.today()
    try:
        observations: dict[str, Any] = {
            "selic": fetch_latest_observation(SELIC_CODE, today),
            "cdi": fetch_latest_observation(CDI_ANNUAL_CODE, today),
            "ipca_12m": fetch_latest_observation(IPCA_12_MONTHS_CODE, today),
        }
    except Exception as error:
        return f"Erro ao consultar indicadores do Banco Central: {error}"
    return build_macro_report(observations)
