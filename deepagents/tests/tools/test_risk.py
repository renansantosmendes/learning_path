import numpy as np
import pandas as pd
import pytest
from tools import risk
from tools.risk import compute_risk_metrics, daily_returns, get_risk_metrics


def make_returns(size: int, seed: int) -> np.ndarray:
    generator = np.random.default_rng(seed)
    return generator.normal(0.0005, 0.01, size)


def test_compute_risk_metrics_without_benchmark_has_no_beta() -> None:
    metrics = compute_risk_metrics(make_returns(300, 1), None, 0.0)
    assert metrics["observations"] == 300
    assert metrics["beta"] is None
    assert metrics["alpha_annual_percent"] is None
    assert metrics["annual_volatility_percent"] > 0
    assert metrics["max_drawdown_percent"] <= 0


def test_compute_risk_metrics_beta_of_identical_series_is_one() -> None:
    returns = make_returns(300, 2)
    metrics = compute_risk_metrics(returns, returns, 0.0)
    assert metrics["beta"] == pytest.approx(1.0, abs=1e-3)


def test_daily_returns_drops_first_undefined_day() -> None:
    closes = pd.Series([10.0, 11.0, 12.1])
    returns = daily_returns(closes)
    assert len(returns) == 2
    assert returns.iloc[0] == pytest.approx(0.1)


def test_get_risk_metrics_rejects_too_few_common_days(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    short_closes = pd.DataFrame(
        {"Close": np.linspace(10.0, 12.0, 10)},
        index=pd.date_range("2025-01-01", periods=10),
    )
    monkeypatch.setattr(risk, "fetch_history", lambda ticker, period: short_closes)
    result = get_risk_metrics.invoke({"ticker": "PETR4", "period": "1y"})
    assert result.startswith("Poucos pregoes em comum entre PETR4.SA e ^BVSP")
