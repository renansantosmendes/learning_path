"""Middleware that logs each agent step and collects search links."""

from typing import Any, TextIO

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage

from market_chat.run_log import add_unique_links, extract_result_urls, write_log_line

LOG_RESULT_PREVIEW_CHARS = 160
SEARCH_TOOL_NAME = "search_web"


class RunLogMiddleware(AgentMiddleware):
    """Logs the agent run and collects the links returned by search_web.

    After each model call, the model text is logged as ``[raciocinio]`` and
    each tool call as ``[acao]``. Every tool result is logged as
    ``[ferramenta]`` with its first characters. For search_web, the query is
    logged as ``[busca]`` and the URLs of the result are logged as
    ``[observacao]`` and stored in collected_links.

    Parameters
    ----------
    log_file : TextIO
        Open file where the run steps are appended.
    collected_links : list[tuple[str, str]]
        List that receives each new (query, url) pair, in order.

    Example
    -------
    >>> middleware = RunLogMiddleware(log_file, [])
    """

    def __init__(
        self,
        log_file: TextIO,
        collected_links: list[tuple[str, str]],
    ) -> None:
        """Stores the log file and the list that receives the links.

        Parameters
        ----------
        log_file : TextIO
            Open file where the run steps are appended.
        collected_links : list[tuple[str, str]]
            List that receives each new (query, url) pair.

        Returns
        -------
        None
            The attributes are stored on the instance.
        """
        super().__init__()
        self.log_file = log_file
        self.collected_links = collected_links

    def after_model(self, state: Any, runtime: Any) -> None:
        """Logs the text and the tool calls of the last model message.

        Parameters
        ----------
        state : Any
            Agent state, whose last message is the model response.
        runtime : Any
            Runtime provided by the agent graph. Not used.

        Returns
        -------
        None
            The agent state is not changed.
        """
        last_message = state["messages"][-1]
        text = last_message.content if isinstance(last_message.content, str) else ""
        if text.strip():
            write_log_line(f"[raciocinio] {text.strip()}", self.log_file)
        for call in getattr(last_message, "tool_calls", None) or []:
            write_log_line(f"[acao] {call['name']} {call['args']}", self.log_file)
        return None

    def wrap_tool_call(self, request: Any, handler: Any) -> Any:
        """Runs a tool call, logging its result and collecting search links.

        Parameters
        ----------
        request : ToolCallRequest
            Tool call requested by the model.
        handler : Callable
            Function that runs the tool call and returns its result.

        Returns
        -------
        ToolMessage or Command
            The result returned by handler, unchanged.
        """
        tool_name = request.tool_call["name"]
        arguments = request.tool_call["args"]
        query = arguments.get("query", "")
        if tool_name == SEARCH_TOOL_NAME:
            write_log_line(f"[busca] \"{query}\"", self.log_file)
        result = handler(request)
        if not isinstance(result, ToolMessage):
            return result
        output = str(result.content)
        if tool_name == SEARCH_TOOL_NAME:
            urls = extract_result_urls(output)
            write_log_line(f"[observacao] {len(urls)} links recebidos", self.log_file)
            add_unique_links(self.collected_links, query, urls)
        else:
            preview = output.splitlines()[0][:LOG_RESULT_PREVIEW_CHARS] if output else ""
            write_log_line(f"[ferramenta] {tool_name} {arguments} -> {preview}", self.log_file)
        return result
