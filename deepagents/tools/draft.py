"""Local draft of the market analysis, kept in a JSON file.

The draft stores the investor's standing directives, the asset and indicators
analysed so far, partial conclusions, pending items and the history of
answered questions. The agent reads it with read_draft and changes it with
update_draft; the program records each answered question in the history.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.tools import BaseTool, tool

DRAFT_VERSION = 1
LIST_SECTIONS = (
    "diretivas",
    "ativos",
    "buscas",
    "conclusoes_parciais",
    "pendencias",
    "historico",
)
OBJECT_SECTIONS = ("indicadores",)
TEXT_SECTIONS = ("pedido_atual",)
DRAFT_SECTIONS = LIST_SECTIONS + OBJECT_SECTIONS + TEXT_SECTIONS
MODE_REPLACE = "replace"
MODE_APPEND = "append"


def build_empty_draft(
    session_id: str,
) -> dict[str, Any]:
    """Creates the structure of a new draft.

    Parameters
    ----------
    session_id : str
        Identifier of the session that created the draft.

    Returns
    -------
    dict[str, Any]
        Draft with every section empty.
    """
    return {
        "versao": DRAFT_VERSION,
        "sessao": session_id,
        "atualizado_em": _now(),
        "diretivas": [],
        "pedido_atual": "",
        "ativos": [],
        "indicadores": {},
        "buscas": [],
        "conclusoes_parciais": [],
        "pendencias": [],
        "historico": [],
    }


def _now() -> str:
    """Current local time in ISO format, to the second.

    Returns
    -------
    str
        Timestamp such as ``2026-11-08T12:00:00``.
    """
    return datetime.now().isoformat(timespec="seconds")


def load_draft(
    path: Path,
) -> dict[str, Any]:
    """Reads the draft file, or returns an empty draft when it does not exist.

    Parameters
    ----------
    path : Path
        Location of the draft JSON file.

    Returns
    -------
    dict[str, Any]
        The stored draft, or a new empty draft when the file is missing.
    """
    if not path.exists():
        return build_empty_draft("")
    return json.loads(path.read_text(encoding="utf-8"))


def save_draft(
    path: Path,
    draft: dict[str, Any],
) -> None:
    """Writes the draft atomically, so a crash never leaves a half file.

    Parameters
    ----------
    path : Path
        Location of the draft JSON file.
    draft : dict[str, Any]
        Draft to store. Its ``atualizado_em`` field is refreshed.

    Returns
    -------
    None
        The file is replaced on disk.
    """
    draft["atualizado_em"] = _now()
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(draft, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary_path, path)


def initialize_draft(
    path: Path,
    session_id: str,
) -> dict[str, Any]:
    """Creates the draft file when missing and records the current session.

    An existing draft is kept, so the analysis survives between runs.

    Parameters
    ----------
    path : Path
        Location of the draft JSON file.
    session_id : str
        Identifier of the session that is starting.

    Returns
    -------
    dict[str, Any]
        The draft that is now stored on disk.
    """
    draft = load_draft(path)
    if not path.exists():
        draft = build_empty_draft(session_id)
    draft["sessao"] = session_id
    save_draft(path, draft)
    return draft


def record_answered_question(
    path: Path,
    question: str,
    urls: list[str],
) -> None:
    """Appends an answered question and its sources to the draft history.

    Parameters
    ----------
    path : Path
        Location of the draft JSON file.
    question : str
        Question written by the investor.
    urls : list[str]
        Result URLs used to answer the question.

    Returns
    -------
    None
        The history is updated on disk.
    """
    draft = load_draft(path)
    draft["historico"].append(
        {
            "pedido": question,
            "respondido_em": _now(),
            "fontes": urls,
        }
    )
    save_draft(path, draft)


def apply_section_update(
    draft: dict[str, Any],
    section: str,
    value: Any,
    mode: str,
) -> None:
    """Changes one section of a draft in memory.

    Parameters
    ----------
    draft : dict[str, Any]
        Draft to change.
    section : str
        Section name, one of DRAFT_SECTIONS.
    value : Any
        New value. For list sections in append mode, a list is extended and
        any other value is added as one item.
    mode : str
        ``replace`` overwrites the section; ``append`` adds to a list section.

    Returns
    -------
    None
        The draft is changed in place.

    Raises
    ------
    ValueError
        If the section is unknown, the mode is invalid, or append is used on
        a section that is not a list.
    """
    if section not in DRAFT_SECTIONS:
        raise ValueError(
            f"Secao desconhecida '{section}'. Use uma de: {', '.join(DRAFT_SECTIONS)}."
        )
    if mode not in (MODE_REPLACE, MODE_APPEND):
        raise ValueError("Modo invalido. Use 'replace' ou 'append'.")
    if mode == MODE_REPLACE:
        draft[section] = value
        return
    if section not in LIST_SECTIONS:
        raise ValueError(f"A secao '{section}' nao aceita append; use replace.")
    if isinstance(value, list):
        draft[section].extend(value)
    else:
        draft[section].append(value)


def create_draft_tools(
    path: Path,
) -> list[BaseTool]:
    """Creates the tools that let the agent read and update the draft.

    Parameters
    ----------
    path : Path
        Location of the draft JSON file used by the tools.

    Returns
    -------
    list[BaseTool]
        Tools read_draft and update_draft bound to the given path.

    Example
    -------
    >>> read_draft, update_draft = create_draft_tools(Path("draft.json"))
    """

    @tool
    def read_draft() -> str:
        """Reads the local draft of the market analysis.

        The draft holds the standing directives, the assets and indicators
        analysed, partial conclusions, pending items and the history of
        answered questions.

        Call it at the start of every question, before any other tool, to
        reuse what was already analysed and follow the directives.

        Returns
        -------
        str
            The draft as JSON text.
        """
        return json.dumps(load_draft(path), ensure_ascii=False, indent=2)

    @tool
    def update_draft(
        section: str,
        value: str,
        mode: str = MODE_REPLACE,
    ) -> str:
        """Updates one section of the local draft.

        Sections: diretivas (investor's standing rules, list), pedido_atual
        (current question, text), ativos (tickers analysed, list),
        indicadores (key figures per ticker, object), buscas (searches made,
        list), conclusoes_parciais (partial conclusions, list), pendencias
        (open questions to check later, list). The history is written by the
        program and cannot be changed here.

        Parameters
        ----------
        section : str
            Name of the section to change.
        value : str
            New value. Send JSON for lists and objects, such as ["PETR4"] or
            {"PETR4": {"pl": 4.3}}; send plain text for pedido_atual.
        mode : str
            replace (default) overwrites the section; append adds items to a
            list section.

        Returns
        -------
        str
            Confirmation, or the reason the update was refused.
        """
        draft = load_draft(path)
        parsed_value = value
        if section not in TEXT_SECTIONS:
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                parsed_value = value
        if section == "historico":
            return "A secao historico e mantida pelo programa e nao pode ser alterada."
        try:
            apply_section_update(draft, section, parsed_value, mode)
        except ValueError as error:
            return f"Atualizacao recusada: {error}"
        save_draft(path, draft)
        return f"Secao '{section}' atualizada ({mode})."

    return [read_draft, update_draft]
