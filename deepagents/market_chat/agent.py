"""Creation of the market analysis deep agent."""

from pathlib import Path
from typing import Any, TextIO

from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemPermission
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from tools import MARKET_ANALYSIS_TOOLS, create_draft_tools, search_web

from deepagents import create_deep_agent
from market_chat.config import DRAFT_PATH, MODEL_NAME, ROOT_DIR, SYSTEM_PROMPT
from market_chat.middleware import RunLogMiddleware
from market_chat.schema import RelatorioAnaliseMercado


def build_read_only_permissions() -> list[FilesystemPermission]:
    """Permissions that deny every write through the filesystem tools.

    Returns
    -------
    list[FilesystemPermission]
        A single rule denying writes to every path.
    """
    return [
        FilesystemPermission(
            operations=["write"],
            paths=["/**"],
            mode="deny",
        ),
    ]


def create_investment_agent(
    log_file: TextIO,
    collected_links: list[tuple[str, str]],
    draft_path: Path = DRAFT_PATH,
) -> Any:
    """Creates the deep agent with the skill, the tools and the middleware.

    Parameters
    ----------
    log_file : TextIO
        Open file where the run steps are appended.
    collected_links : list[tuple[str, str]]
        List that receives each (query, url) pair found by search_web.
    draft_path : Path
        JSON file used by the draft tools.

    Returns
    -------
    CompiledStateGraph
        Agent ready to be run with a thread_id in its config.

    Example
    -------
    >>> agent = create_investment_agent(log_file, [])
    """
    set_llm_cache(InMemoryCache())
    return create_deep_agent(
        tools=[search_web, *MARKET_ANALYSIS_TOOLS, *create_draft_tools(draft_path)],
        model=ChatOpenAI(model=MODEL_NAME),
        system_prompt=SYSTEM_PROMPT,
        backend=FilesystemBackend(root_dir=ROOT_DIR, virtual_mode=True),
        skills=["skills"],
        permissions=build_read_only_permissions(),
        response_format=RelatorioAnaliseMercado,
        middleware=[RunLogMiddleware(log_file, collected_links)],
        checkpointer=InMemorySaver(),
    )
