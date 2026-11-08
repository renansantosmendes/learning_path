from typing import Any

from dotenv import load_dotenv
from langchain_tavily import TavilySearch

load_dotenv()

_tavily_search = TavilySearch(
    max_results=10,
    timeout=30,
    verbose=True,
    search_depth="advanced",
    include_answer=True,
    include_images=True,
    include_image_descriptions=True,
    include_favicon=True,
)


def _format_results(results: list[dict[str, Any]]) -> str:
    """Formats the Tavily text results into a readable block.

    Parameters
    ----------
    results : list[dict[str, Any]]
        Result entries returned by Tavily, each with the keys ``title``,
        ``url``, ``content``, ``score`` and optionally ``favicon``.

    Returns
    -------
    str
        One block per result, separated by blank lines.
    """
    return "\n\n".join(
        f"Titulo: {result.get('title', '')}\n"
        f"URL: {result.get('url', '')}\n"
        f"Score: {result.get('score', '')}\n"
        f"Favicon: {result.get('favicon', '') or ''}\n"
        f"Conteudo: {result.get('content', '')}"
        for result in results
    )


def _format_images(images: list[Any]) -> str:
    """Formats the Tavily images into a bulleted list of URLs.

    Tavily returns either plain URL strings or dictionaries with ``url``
    and ``description`` keys, depending on ``include_image_descriptions``.

    Parameters
    ----------
    images : list[Any]
        Image entries returned by Tavily, as strings or dictionaries.

    Returns
    -------
    str
        One line per image, with its description when available.
    """
    lines = []
    for image in images:
        if isinstance(image, dict):
            url = image.get("url", "")
            description = image.get("description", "")
            suffix = f" ({description})" if description else ""
            lines.append(f"- {url}{suffix}")
        else:
            lines.append(f"- {image}")
    return "\n".join(lines)


def search_web(query: str) -> str:
    """Busca na web via Tavily e retorna resposta, resultados e imagens.

    Parameters
    ----------
    query : str
        Search query sent to Tavily.

    Returns
    -------
    str
        Text containing the Tavily short answer (if any), every text
        result with its score and favicon, and the list of related images.
    """
    response = _tavily_search.invoke({"query": query})

    if "error" in response:
        return f"Erro na busca por '{query}': {response['error']}"

    results = response.get("results", [])
    images = response.get("images", [])
    answer = response.get("answer")

    if not results and not images and not answer:
        return f"Nenhum resultado encontrado para '{query}'."

    sections = [f"Resultados da busca para '{query}':"]
    if answer:
        sections.append(f"Resposta resumida:\n{answer}")
    if results:
        sections.append(f"Resultados:\n\n{_format_results(results)}")
    if images:
        sections.append(f"Imagens:\n{_format_images(images)}")
    return "\n\n".join(sections)
