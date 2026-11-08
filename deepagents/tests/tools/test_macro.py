from datetime import date

import pandas as pd
import pytest
from tools import macro
from tools.macro import (
    build_macro_report,
    compute_real_rate,
    fetch_latest_observation,
)


def test_compute_real_rate_discounts_inflation_from_cdi() -> None:
    assert compute_real_rate(14.9, 4.5) == pytest.approx(9.95, abs=0.01)


def test_compute_real_rate_returns_none_without_inputs() -> None:
    assert compute_real_rate(None, 4.5) is None


def test_fetch_latest_observation_ignores_future_projections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {"value": [13.75, 14.0]},
        index=pd.to_datetime(["2026-11-05", "2026-12-09"]),
    )
    monkeypatch.setattr(macro.sgs, "get", lambda codes, start, end: frame)
    observation = fetch_latest_observation(432, date(2026, 11, 8))
    assert observation == (date(2026, 11, 5), 13.75)


def test_fetch_latest_observation_returns_none_for_empty_series(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        macro.sgs,
        "get",
        lambda codes, start, end: pd.DataFrame(),
    )
    assert fetch_latest_observation(432, date(2026, 11, 8)) is None


def test_build_macro_report_marks_missing_series_as_not_available() -> None:
    report = build_macro_report(
        {
            "selic": None,
            "cdi": (date(2026, 11, 5), 13.65),
            "ipca_12m": None,
        }
    )
    assert "Selic (meta, % a.a.): n/d" in report
    assert "CDI anualizado (% a.a.): 13,65 (data 05/11/2026)" in report
    assert "Juro real (CDI descontado do IPCA 12 meses): n/d" in report
