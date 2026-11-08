"""Interactive chat session of the market analysis agent."""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from tools.draft import initialize_draft, record_answered_question

from market_chat.agent import create_investment_agent
from market_chat.config import DRAFT_PATH, EXIT_COMMANDS, LOG_DIR
from market_chat.report import format_fallback_report, format_report_markdown
from market_chat.run_log import create_run_log_path, write_log_line
from market_chat.schema import RelatorioAnaliseMercado


def run_investor_turn(
    agent: Any,
    investor_request: str,
    thread_config: dict[str, Any],
    collected_links: list[tuple[str, str]],
) -> str:
    """Runs one question of the investor in the conversation thread.

    Parameters
    ----------
    agent : CompiledStateGraph
        Agent created by create_investment_agent.
    investor_request : str
        Question written by the investor, sent unchanged.
    thread_config : dict[str, Any]
        Config with the thread_id that keeps the conversation history.
    collected_links : list[tuple[str, str]]
        Links collected by the middleware; cleared before the turn.

    Returns
    -------
    str
        Markdown answer with the links of the turn.
    """
    collected_links.clear()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": investor_request}]},
        config=thread_config,
    )
    report = result.get("structured_response")
    if isinstance(report, RelatorioAnaliseMercado):
        return format_report_markdown(report, collected_links)
    return format_fallback_report(result["messages"][-1].content, collected_links)


def run_chat(
    log_dir: Path = LOG_DIR,
    draft_path: Path = DRAFT_PATH,
    read_input: Callable[[str], str] = input,
) -> Path:
    """Runs the interactive session until the investor types an exit command.

    Parameters
    ----------
    log_dir : Path
        Directory where the session log is saved.
    draft_path : Path
        JSON file of the local draft; created when missing.
    read_input : Callable[[str], str]
        Function that reads each question. Defaults to ``input``.

    Returns
    -------
    Path
        Path of the session log file.
    """
    log_path = create_run_log_path(log_dir)
    session_id = datetime.now().strftime("sessao-%Y%m%d_%H%M%S")
    thread_config = {"configurable": {"thread_id": session_id}}
    collected_links: list[tuple[str, str]] = []
    initialize_draft(draft_path, session_id)

    with log_path.open("w", encoding="utf-8") as log_file:
        agent = create_investment_agent(log_file, collected_links, draft_path)
        print("Chat do agente de analise de mercado (digite 'sair' para encerrar).")
        print(f"Rascunho local: {draft_path}")
        while True:
            investor_request = read_input("\nPedido do investidor: ").strip()
            if not investor_request:
                continue
            if investor_request.lower() in EXIT_COMMANDS:
                break
            write_log_line(f"[pedido] {investor_request}", log_file)
            answer = run_investor_turn(agent, investor_request, thread_config, collected_links)
            record_answered_question(
                draft_path,
                investor_request,
                [url for _, url in collected_links],
            )
            write_log_line("[resposta] final gerada", log_file)
            print(f"\n{answer}")

    print(f"\nLog salvo em: {log_path}")
    return log_path
