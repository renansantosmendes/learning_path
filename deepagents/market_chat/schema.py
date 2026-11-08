"""Structured answer produced by the market analysis skill."""

from pydantic import BaseModel, Field


class RelatorioAnaliseMercado(BaseModel):
    """Structured answer of the market analysis skill.

    The links are not part of this model: they are collected from the
    search_web results by RunLogMiddleware and appended to the rendered
    report.
    """

    buscas_realizadas: list[str] = Field(
        description=(
            "One line per search_web call, in order, with the query, the "
            "decision (aceita or refinada) and the reason in one sentence."
        ),
    )
    panorama_de_noticias: list[str] = Field(
        description=(
            "From 3 to 5 facts found in the news, each with its context and "
            "numbers."
        ),
    )
    indicadores_do_ativo: list[str] = Field(
        description=(
            "Key figures of the asset from get_stock_quote and "
            "get_stock_fundamentals: price, returns, valuation, profitability "
            "and debt. Empty when the question is not about a specific asset."
        ),
    )
    analise_tecnica_e_risco: list[str] = Field(
        description=(
            "Signals from get_technical_indicators and metrics from "
            "get_risk_metrics, in plain language. Empty when not used."
        ),
    )
    contexto_macro: str | None = Field(
        default=None,
        description=(
            "Selic, CDI, IPCA and real rate from get_brazil_macro and how they "
            "affect the decision. None when not used."
        ),
    )
    riscos_e_pontos_de_atencao: list[str] = Field(
        description="From 2 to 4 risks or uncertainties from the news and the indicators.",
    )
    como_isso_pode_influenciar_a_decisao: str = Field(
        description=(
            "Educational reading: questions the investor should answer before "
            "deciding, and how the facts above connect to them. Never say buy "
            "or sell."
        ),
    )
    limitacoes_da_analise: str | None = Field(
        default=None,
        description=(
            "One or two sentences about gaps, delayed data, old news or weak "
            "sources. None when there are no limitations."
        ),
    )
