from market_chat.report import format_fallback_report, format_report_markdown
from market_chat.schema import RelatorioAnaliseMercado


def make_report(**overrides: object) -> RelatorioAnaliseMercado:
    values = {
        "buscas_realizadas": ['1. "PETR4 2026" - aceita - relevante'],
        "panorama_de_noticias": ["Lucro cresceu 10%."],
        "indicadores_do_ativo": ["P/L 4,3"],
        "analise_tecnica_e_risco": ["RSI em sobrevenda."],
        "contexto_macro": "Selic em 13,75%.",
        "riscos_e_pontos_de_atencao": ["Petroleo volatil."],
        "como_isso_pode_influenciar_a_decisao": "Pergunte-se sobre o prazo.",
        "limitacoes_da_analise": None,
    }
    values.update(overrides)
    return RelatorioAnaliseMercado(**values)


def test_format_report_includes_all_filled_sections() -> None:
    markdown = format_report_markdown(make_report(), [("PETR4", "https://a.com")])
    for title in (
        "**Buscas realizadas**",
        "**Panorama de noticias**",
        "**Indicadores do ativo**",
        "**Analise tecnica e risco**",
        "**Contexto macroeconomico**",
        "**Riscos e pontos de atencao**",
        "**Fontes consultadas (links retornados pelas buscas)**",
        "**Aviso:**",
    ):
        assert title in markdown
    assert '- https://a.com - consulta: "PETR4"' in markdown


def test_format_report_skips_empty_optional_sections() -> None:
    report = make_report(
        indicadores_do_ativo=[],
        analise_tecnica_e_risco=[],
        contexto_macro=None,
    )
    markdown = format_report_markdown(report, [])
    assert "**Indicadores do ativo**" not in markdown
    assert "**Analise tecnica e risco**" not in markdown
    assert "**Contexto macroeconomico**" not in markdown


def test_format_report_adds_limitations_when_present() -> None:
    markdown = format_report_markdown(
        make_report(limitacoes_da_analise="Dados defasados."),
        [],
    )
    assert "**Limitacoes da analise**\nDados defasados." in markdown


def test_format_fallback_report_lists_links() -> None:
    text = format_fallback_report("Resposta livre.", [("q", "https://b.com")])
    assert text.startswith("Resposta livre.")
    assert '- https://b.com - consulta: "q"' in text
