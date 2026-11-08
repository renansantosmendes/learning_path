import numpy as np
import pandas as pd
import pytest
from tools import technical
from tools.technical import (
    compute_technical_indicators,
    describe_signals,
    get_technical_indicators,
)


def make_history(bars: int) -> pd.DataFrame:
    base = np.linspace(20.0, 40.0, bars) + np.sin(np.arange(bars)) * 2
    return pd.DataFrame(
        {
            "High": base + 1,
            "Low": base - 1,
            "Close": base,
        },
        index=pd.date_range("2025-01-01", periods=bars),
    )


def test_compute_technical_indicators_returns_all_keys_with_enough_bars() -> None:
    indicators = compute_technical_indicators(make_history(120))
    expected_keys = {
        "current_price",
        "sma_9",
        "sma_21",
        "sma_50",
        "rsi_14",
        "macd",
        "macd_signal",
        "bollinger_percent_b",
        "atr_14",
        "adx_14",
        "plus_di_14",
        "minus_di_14",
        "stochastic_k",
        "stochastic_d",
    }
    assert expected_keys <= indicators.keys()
    assert indicators["sma_50"] is not None
    assert 0 <= indicators["rsi_14"] <= 100


def test_describe_signals_flags_oversold_rsi_and_trend() -> None:
    indicators = {
        "current_price": 10.0,
        "sma_50": 12.0,
        "rsi_14": 25.0,
        "macd": -1.0,
        "macd_signal": 0.5,
        "adx_14": 30.0,
        "plus_di_14": 10.0,
        "minus_di_14": 25.0,
    }
    signals = describe_signals(indicators)
    assert "Preco abaixo da media movel de 50 dias." in signals
    assert "RSI em sobrevenda (abaixo de 30)." in signals
    assert "MACD abaixo da linha de sinal." in signals
    assert any("Tendencia forte (de baixa" in signal for signal in signals)


def test_describe_signals_skips_missing_values() -> None:
    assert describe_signals({"rsi_14": None}) == []


def test_get_technical_indicators_rejects_short_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        technical,
        "fetch_history",
        lambda ticker, period: make_history(20),
    )
    result = get_technical_indicators.invoke({"ticker": "PETR4", "period": "1mo"})
    assert result.startswith("Historico insuficiente para PETR4.SA (20 pregoes)")
