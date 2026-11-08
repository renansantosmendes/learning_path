from pathlib import Path
from types import SimpleNamespace

import pytest
from market_chat import session
from market_chat.schema import RelatorioAnaliseMercado


class FakeAgent:
    def __init__(
        self,
        result: dict,
        links_to_collect: list[tuple[str, str]],
        collected_links: list[tuple[str, str]],
    ) -> None:
        self.result = result
        self.links_to_collect = links_to_collect
        self.collected_links = collected_links

    def invoke(self, payload: dict, config: dict) -> dict:
        self.collected_links.extend(self.links_to_collect)
        return self.result


def make_structured_report() -> RelatorioAnaliseMercado:
    return RelatorioAnaliseMercado(
        buscas_realizadas=["1. PETR4 - aceita - ok"],
        panorama_de_noticias=["Fato."],
        indicadores_do_ativo=[],
        analise_tecnica_e_risco=[],
        contexto_macro=None,
        riscos_e_pontos_de_atencao=["Risco."],
        como_isso_pode_influenciar_a_decisao="Pergunte-se.",
        limitacoes_da_analise=None,
    )


def test_run_investor_turn_renders_structured_report() -> None:
    links: list[tuple[str, str]] = []
    agent = FakeAgent(
        {"structured_response": make_structured_report(), "messages": []},
        [("PETR4", "https://a.com")],
        links,
    )
    answer = session.run_investor_turn(agent, "PETR4?", {"configurable": {}}, links)
    assert "**Panorama de noticias**" in answer
    assert '- https://a.com - consulta: "PETR4"' in answer


def test_run_investor_turn_falls_back_to_last_message() -> None:
    last_message = SimpleNamespace(content="Texto livre.")
    links: list[tuple[str, str]] = []
    agent = FakeAgent(
        {"structured_response": None, "messages": [last_message]},
        [("q", "https://b.com")],
        links,
    )
    answer = session.run_investor_turn(agent, "x", {"configurable": {}}, links)
    assert answer.startswith("Texto livre.")
    assert "https://b.com" in answer


def test_run_chat_exits_on_command_and_creates_draft(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    answers = iter(["sair"])
    log_path = session.run_chat(
        log_dir=tmp_path / "logs",
        draft_path=tmp_path / "draft.json",
        read_input=lambda prompt: next(answers),
    )
    assert log_path.exists()
    assert (tmp_path / "draft.json").exists()
