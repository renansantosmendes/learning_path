from dotenv import load_dotenv
from langchain_tavily import TavilySearch

load_dotenv()

_tavily_search = TavilySearch(max_results=5)


def search_web(query: str) -> str:
    """Busca na web via Tavily e retorna os resultados encontrados para a query."""
    response = _tavily_search.invoke({"query": query})
    results = response.get("results", [])
    if not results:
        return f"Nenhum resultado encontrado para '{query}'."

    formatted = "\n\n".join(
        f"Titulo: {r.get('title', '')}\nURL: {r.get('url', '')}\nConteudo: {r.get('content', '')}"
        for r in results
    )
    return f"Resultados da busca para '{query}':\n\n{formatted}"
