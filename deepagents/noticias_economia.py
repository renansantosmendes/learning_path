"""
Entry point for the economy news skill for investors.

The instructions of the skill noticias-economia-investimento
(skills/noticias-economia-investimento/SKILL.md) are loaded once and passed
as the system prompt when the agent is created. The skill therefore applies
to every request, without changing the message written by the investor.

Each step of the run is printed to the console and saved to a timestamped
file in the logs/ directory: the text written by the model before each
action ([raciocinio]), the tool calls ([acao]) and the search results
returned by search_web ([busca] and [observacao]).
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO

from dotenv import load_dotenv
from langchain_core.tools import BaseTool, tool
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent

from tools import search_web

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

ROOT_DIR = Path(__file__).parent
SKILL_PATH = (
    ROOT_DIR / "skills" / "noticias-economia-investimento" / "SKILL.md"
)
LOG_DIR = ROOT_DIR / "logs"
FRONTMATTER_PATTERN = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)


def load_skill_body(skill_path: Path) -> str:
    """Reads a SKILL.md file and returns its instructions without frontmatter.

    Parameters
    ----------
    skill_path : Path
        Path to the SKILL.md file, which may start with a YAML frontmatter
        block delimited by ``---`` lines.

    Returns
    -------
    str
        Markdown body of the skill, with the frontmatter removed.

    Example
    -------
    >>> body = load_skill_body(SKILL_PATH)
    >>> body.startswith("# Noticias de Economia")
    True
    """
    content = skill_path.read_text(encoding="utf-8")
    return FRONTMATTER_PATTERN.sub("", content, count=1).strip()


def create_run_log_path(log_dir: Path) -> Path:
    """Creates the log directory and returns a timestamped log file path.

    Parameters
    ----------
    log_dir : Path
        Directory where the run logs are stored.

    Returns
    -------
    Path
        Path of a new log file named with the current date and time.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return log_dir / f"noticias_economia_{timestamp}.log"


def write_log_line(
    line: str,
    log_file: TextIO,
) -> None:
    """Prints a log line to the console and appends it to the log file.

    Parameters
    ----------
    line : str
        Text to be logged. A timestamp is added in front of it.
    log_file : TextIO
        Open file where the line is appended.

    Returns
    -------
    None
        The line is printed and written to the file.
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    indented_line = line.replace("\n", "\n         ")
    formatted_line = f"{timestamp} {indented_line}"
    print(formatted_line)
    log_file.write(formatted_line + "\n")
    log_file.flush()


def extract_result_urls(search_output: str) -> list[str]:
    """Extracts the result URLs from the text returned by search_web.

    Parameters
    ----------
    search_output : str
        Text returned by search_web, with one ``URL: `` line per result.

    Returns
    -------
    list[str]
        URLs in order of appearance, without the ``URL: `` prefix.
    """
    return [
        line[len("URL: "):].strip()
        for line in search_output.splitlines()
        if line.startswith("URL: ")
    ]


def create_logged_search_tool(
    log_file: TextIO,
    collected_links: list[tuple[str, str]],
) -> BaseTool:
    """Creates the search_web tool that logs each search and its results.

    The tool keeps the behavior of tools.search_web and also records every
    (query, url) pair found, so the final answer can list all the links.

    Parameters
    ----------
    log_file : TextIO
        Open file where each search and its result count are appended.
    collected_links : list[tuple[str, str]]
        List that receives each new (query, url) pair, in order.

    Returns
    -------
    BaseTool
        Tool named search_web, ready to be given to the agent.
    """

    @tool("search_web")
    def search_web_logged(query: str) -> str:
        """Busca na web via Tavily e retorna resposta, resultados e imagens."""
        write_log_line(f"[busca] \"{query}\"", log_file)
        output = search_web(query)
        urls = extract_result_urls(output)
        write_log_line(f"[observacao] {len(urls)} links recebidos", log_file)
        for url in urls:
            if all(saved_url != url for _, saved_url in collected_links):
                collected_links.append((query, url))
        return output

    return search_web_logged


def create_investment_agent(search_tool: BaseTool):
    """Creates the deep agent with the economy news skill as system prompt.

    Parameters
    ----------
    search_tool : BaseTool
        Search tool given to the agent, normally created by
        create_logged_search_tool.

    Returns
    -------
    CompiledStateGraph
        Agent ready to be run with a list of messages.
    """
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return create_deep_agent(
        tools=[search_tool],
        model=model,
        system_prompt=load_skill_body(SKILL_PATH),
    )


def describe_model_message(message) -> list[str]:
    """Describes a model message as readable log lines.

    Parameters
    ----------
    message : AIMessage
        Message emitted by the model during the run.

    Returns
    -------
    list[str]
        ``[raciocinio]`` with the text written by the model, and one
        ``[acao]`` line per tool call. Empty when there is nothing to log.
    """
    lines = []
    text = message.content if isinstance(message.content, str) else ""
    if text.strip():
        lines.append(f"[raciocinio] {text.strip()}")
    for call in getattr(message, "tool_calls", None) or []:
        lines.append(f"[acao] {call['name']} {call['args']}")
    return lines


def run_agent_with_log(
    agent,
    investor_request: str,
    log_file: TextIO,
) -> str:
    """Runs the agent step by step, logging the model messages as they come.

    Parameters
    ----------
    agent : CompiledStateGraph
        Agent created by create_investment_agent.
    investor_request : str
        Question or request written by the investor, sent unchanged.
    log_file : TextIO
        Open file where the run steps are appended.

    Returns
    -------
    str
        Text of the last message produced by the model, which is the
        final answer.
    """
    final_answer = ""
    stream = agent.stream(
        {"messages": [{"role": "user", "content": investor_request}]},
        stream_mode="updates",
    )
    for update in stream:
        for node_name, node_update in update.items():
            if not isinstance(node_update, dict):
                continue
            for message in node_update.get("messages", []):
                if getattr(message, "type", "") != "ai":
                    continue
                for line in describe_model_message(message):
                    write_log_line(f"[{node_name}] {line}", log_file)
                if isinstance(message.content, str) and message.content.strip():
                    final_answer = message.content
    return final_answer


def format_result_links(links: list[tuple[str, str]]) -> str:
    """Formats the collected links as a Markdown list.

    Parameters
    ----------
    links : list[tuple[str, str]]
        Pairs of (query, url) collected during the run.

    Returns
    -------
    str
        Markdown section with one line per link and the query that found it.
    """
    lines = ["**Todos os links retornados pelas buscas**"]
    lines.extend(f"- {url} - consulta: \"{query}\"" for query, url in links)
    return "\n".join(lines)


def ask_investment_news(
    investor_request: str,
    log_file: TextIO,
) -> str:
    """Runs the agent on the investor request and returns the final answer.

    Parameters
    ----------
    investor_request : str
        Question or request written by the investor, sent unchanged.
    log_file : TextIO
        Open file where the run steps are appended.

    Returns
    -------
    str
        Final answer produced by the agent, followed by the complete list
        of links returned by every search.
    """
    collected_links: list[tuple[str, str]] = []
    search_tool = create_logged_search_tool(log_file, collected_links)
    agent = create_investment_agent(search_tool)
    final_answer = run_agent_with_log(agent, investor_request, log_file)
    return f"{final_answer}\n\n{format_result_links(collected_links)}"


def main() -> None:
    """Reads the investor request, runs the agent and prints the answer.

    The run steps are saved to a new file in the logs/ directory, and the
    path of that file is printed at the end.

    Returns
    -------
    None
        The answer is printed to the console.
    """
    investor_request = input("Pedido do investidor: ").strip()
    if not investor_request:
        print("Nenhum pedido informado.")
        return

    log_path = create_run_log_path(LOG_DIR)
    with log_path.open("w", encoding="utf-8") as log_file:
        write_log_line(f"[pedido] {investor_request}", log_file)
        answer = ask_investment_news(investor_request, log_file)
        write_log_line("[resposta] final gerada", log_file)

    print(f"\n{answer}")
    print(f"\nLog salvo em: {log_path}")


if __name__ == "__main__":
    main()
