"""Markdown rendering of the market analysis answer."""

from market_chat.schema import RelatorioAnaliseMercado

DISCLAIMER = (
    "**Aviso:** este conteudo e educacional e nao constitui recomendacao "
    "de investimento. Decisoes devem considerar o perfil do investidor e, "
    "se necessario, o apoio de um profissional habilitado."
)


def format_numbered(
    lines: list[str],
) -> str:
    """Numbers the items of a list for the Markdown report.

    Parameters
    ----------
    lines : list[str]
        Text of each item.

    Returns
    -------
    str
        One numbered line per item, starting at 1.
    """
    return "\n".join(f"{index}. {line}" for index, line in enumerate(lines, 1))


def format_bullets(
    lines: list[str],
) -> str:
    """Formats the items of a list as Markdown bullets.

    Parameters
    ----------
    lines : list[str]
        Text of each item.

    Returns
    -------
    str
        One bullet per item.
    """
    return "\n".join(f"- {line}" for line in lines)


def format_links(
    links: list[tuple[str, str]],
) -> str:
    """Formats the collected links with the query that found each one.

    Parameters
    ----------
    links : list[tuple[str, str]]
        Pairs of (query, url) collected during the turn.

    Returns
    -------
    str
        One bullet per link.
    """
    return "\n".join(f"- {url} - consulta: \"{query}\"" for query, url in links)


def section(
    title: str,
    body: str,
) -> str:
    """Builds a Markdown section with a bold title.

    Parameters
    ----------
    title : str
        Section title.
    body : str
        Section content.

    Returns
    -------
    str
        Title line followed by the content.
    """
    return f"**{title}**\n{body}"


def format_report_markdown(
    report: RelatorioAnaliseMercado,
    links: list[tuple[str, str]],
) -> str:
    """Renders the structured answer and the collected links as Markdown.

    Parameters
    ----------
    report : RelatorioAnaliseMercado
        Structured answer produced by the agent.
    links : list[tuple[str, str]]
        Pairs of (query, url) collected during the turn.

    Returns
    -------
    str
        Markdown report. Optional sections without content are left out.
    """
    sections = [
        section("Buscas realizadas", format_numbered(report.buscas_realizadas)),
        section("Panorama de noticias", format_numbered(report.panorama_de_noticias)),
    ]
    optional_sections = [
        ("Indicadores do ativo", format_bullets(report.indicadores_do_ativo)),
        ("Analise tecnica e risco", format_bullets(report.analise_tecnica_e_risco)),
        ("Contexto macroeconomico", report.contexto_macro or ""),
    ]
    sections.extend(section(title, body) for title, body in optional_sections if body)
    sections.append(
        section("Riscos e pontos de atencao", format_bullets(report.riscos_e_pontos_de_atencao))
    )
    sections.append(
        section(
            "Como isso pode influenciar a decisao de investir",
            report.como_isso_pode_influenciar_a_decisao,
        )
    )
    if report.limitacoes_da_analise:
        sections.append(section("Limitacoes da analise", report.limitacoes_da_analise))
    sections.append(
        section("Fontes consultadas (links retornados pelas buscas)", format_links(links))
    )
    sections.append(DISCLAIMER)
    return "\n\n".join(sections)


def format_fallback_report(
    final_message: str,
    links: list[tuple[str, str]],
) -> str:
    """Renders a plain answer, used when no structured answer was produced.

    Parameters
    ----------
    final_message : str
        Last text written by the agent.
    links : list[tuple[str, str]]
        Pairs of (query, url) collected during the turn.

    Returns
    -------
    str
        The text followed by the list of links.
    """
    return f"{final_message}\n\n{section('Fontes consultadas', format_links(links))}"
