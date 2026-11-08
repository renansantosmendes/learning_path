import pandas as pd
import pytest
from tools import market_data
from tools.market_data import (
    MarketDataError,
    build_fundamentals_report,
    build_quote_report,
    format_value,
    normalize_ticker,
    percent_change,
)


def make_closes(values: list[float]) -> pd.Series:
    return pd.Series(values, index=pd.date_range("2025-01-01", periods=len(values)))


@pytest.mark.parametrize(
    ("ticker", "expected"),
    [
        ("petr4", "PETR4.SA"),
        (" VALE3 ", "VALE3.SA"),
        ("AAPL", "AAPL"),
        ("^BVSP", "^BVSP"),
        ("PETR4.SA", "PETR4.SA"),
    ],
)
def test_normalize_ticker_adds_suffix_only_to_brazilian_codes(
    ticker: str,
    expected: str,
) -> None:
    assert normalize_ticker(ticker) == expected


def test_percent_change_uses_trading_days_back() -> None:
    closes = make_closes([100.0, 110.0, 121.0])
    assert percent_change(closes, 2) == 21.0


def test_percent_change_returns_none_without_enough_history() -> None:
    assert percent_change(make_closes([100.0, 110.0]), 5) is None


def test_format_value_uses_brazilian_separators_and_fallback() -> None:
    assert format_value(1234.5, "%") == "1.234,50%"
    assert format_value(None) == "n/d"


def test_build_quote_report_contains_price_and_range() -> None:
    closes = make_closes([10.0, 12.0, 11.0])
    report = build_quote_report("TEST3.SA", closes, {"longName": "Teste SA"})
    assert "Preco atual: 11,00" in report
    assert "Minima de 52 semanas: 10,00" in report
    assert "Maxima de 52 semanas: 12,00" in report
    assert "Teste SA" in report


def test_build_fundamentals_report_converts_yahoo_units() -> None:
    info = {
        "trailingAnnualDividendYield": 0.08,
        "returnOnEquity": 0.30,
        "debtToEquity": 76.0,
    }
    report = build_fundamentals_report("TEST3.SA", info)
    assert "Dividend yield (12 meses): 8,00%" in report
    assert "ROE: 30,00%" in report
    assert "Divida liquida / patrimonio: 0,76" in report


def test_get_stock_quote_returns_error_text_when_history_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing_history(ticker: str, period: str) -> pd.DataFrame:
        raise MarketDataError("sem dados")

    monkeypatch.setattr(market_data, "fetch_history", failing_history)
    result = market_data.get_stock_quote.invoke({"ticker": "XXXX3"})
    assert result.startswith("Erro ao consultar cotacao de XXXX3")


def test_get_stock_fundamentals_reports_missing_indicators(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(market_data, "fetch_company_info", lambda ticker: {})
    result = market_data.get_stock_fundamentals.invoke({"ticker": "XXXX3"})
    assert result == "Nenhum indicador fundamentalista disponivel para XXXX3.SA."


def test_fetch_history_rejects_invalid_period() -> None:
    with pytest.raises(MarketDataError, match="Periodo invalido"):
        market_data.fetch_history("PETR4", "10y")
