import io
from types import SimpleNamespace

from langchain_core.messages import AIMessage, ToolMessage
from market_chat.middleware import RunLogMiddleware


def make_request(name: str, arguments: dict) -> SimpleNamespace:
    return SimpleNamespace(tool_call={"name": name, "args": arguments, "id": "call-1"})


def test_wrap_tool_call_collects_search_links() -> None:
    log_file = io.StringIO()
    links: list[tuple[str, str]] = []
    middleware = RunLogMiddleware(log_file, links)
    output = "Resultados:\n\nURL: https://a.com\nURL: https://b.com"
    result = ToolMessage(content=output, tool_call_id="call-1", name="search_web")

    returned = middleware.wrap_tool_call(
        make_request("search_web", {"query": "PETR4"}),
        lambda request: result,
    )

    assert returned is result
    assert links == [("PETR4", "https://a.com"), ("PETR4", "https://b.com")]
    assert "[observacao] 2 links recebidos" in log_file.getvalue()


def test_wrap_tool_call_logs_other_tools_without_collecting() -> None:
    log_file = io.StringIO()
    links: list[tuple[str, str]] = []
    middleware = RunLogMiddleware(log_file, links)
    result = ToolMessage(
        content="Cotacao de PETR4.SA", tool_call_id="call-1", name="get_stock_quote"
    )

    request = make_request("get_stock_quote", {"ticker": "PETR4"})
    middleware.wrap_tool_call(request, lambda _: result)

    assert links == []
    assert "[ferramenta] get_stock_quote" in log_file.getvalue()


def test_after_model_logs_text_and_tool_calls() -> None:
    log_file = io.StringIO()
    middleware = RunLogMiddleware(log_file, [])
    message = AIMessage(
        content="Vou buscar as cotacoes.",
        tool_calls=[{"name": "get_stock_quote", "args": {"ticker": "PETR4"}, "id": "c1"}],
    )

    middleware.after_model({"messages": [message]}, None)

    logged = log_file.getvalue()
    assert "[raciocinio] Vou buscar as cotacoes." in logged
    assert "[acao] get_stock_quote {'ticker': 'PETR4'}" in logged
