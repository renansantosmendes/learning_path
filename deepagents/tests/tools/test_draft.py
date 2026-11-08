import json
from pathlib import Path

import pytest
from tools.draft import (
    apply_section_update,
    build_empty_draft,
    create_draft_tools,
    initialize_draft,
    load_draft,
    record_answered_question,
    save_draft,
)


def test_initialize_draft_creates_file_with_session(tmp_path: Path) -> None:
    path = tmp_path / "draft.json"
    draft = initialize_draft(path, "sessao-1")
    assert path.exists()
    assert draft["sessao"] == "sessao-1"
    assert json.loads(path.read_text(encoding="utf-8"))["historico"] == []


def test_initialize_draft_keeps_existing_content(tmp_path: Path) -> None:
    path = tmp_path / "draft.json"
    draft = build_empty_draft("antiga")
    draft["diretivas"] = ["sempre considerar o juro real"]
    save_draft(path, draft)
    reloaded = initialize_draft(path, "nova")
    assert reloaded["diretivas"] == ["sempre considerar o juro real"]
    assert reloaded["sessao"] == "nova"


def test_apply_section_update_replaces_and_appends() -> None:
    draft = build_empty_draft("s")
    apply_section_update(draft, "ativos", ["PETR4"], "replace")
    apply_section_update(draft, "ativos", "VALE3", "append")
    assert draft["ativos"] == ["PETR4", "VALE3"]
    apply_section_update(draft, "diretivas", ["regra A"], "append")
    apply_section_update(draft, "diretivas", "regra B", "append")
    assert draft["diretivas"] == ["regra A", "regra B"]


def test_apply_section_update_rejects_unknown_section_and_bad_append() -> None:
    draft = build_empty_draft("s")
    with pytest.raises(ValueError, match="Secao desconhecida"):
        apply_section_update(draft, "inexistente", [], "replace")
    with pytest.raises(ValueError, match="nao aceita append"):
        apply_section_update(draft, "indicadores", {}, "append")


def test_read_and_update_tools_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "draft.json"
    initialize_draft(path, "s")
    read_draft, update_draft = create_draft_tools(path)
    result = update_draft.invoke(
        {"section": "indicadores", "value": '{"PETR4": {"pl": 4.3}}'}
    )
    assert "atualizada" in result
    stored = json.loads(read_draft.invoke({}))
    assert stored["indicadores"] == {"PETR4": {"pl": 4.3}}


def test_update_tool_keeps_plain_text_for_pedido_atual(tmp_path: Path) -> None:
    path = tmp_path / "draft.json"
    initialize_draft(path, "s")
    _, update_draft = create_draft_tools(path)
    update_draft.invoke({"section": "pedido_atual", "value": "2026"})
    assert load_draft(path)["pedido_atual"] == "2026"


def test_update_tool_refuses_to_change_history(tmp_path: Path) -> None:
    path = tmp_path / "draft.json"
    initialize_draft(path, "s")
    _, update_draft = create_draft_tools(path)
    result = update_draft.invoke(
        {"section": "historico", "value": "[]", "mode": "replace"}
    )
    assert "mantida pelo programa" in result


def test_record_answered_question_appends_history(tmp_path: Path) -> None:
    path = tmp_path / "draft.json"
    initialize_draft(path, "s")
    record_answered_question(path, "Vale PETR4?", ["https://a.com/1"])
    history = load_draft(path)["historico"]
    assert len(history) == 1
    assert history[0]["pedido"] == "Vale PETR4?"
    assert history[0]["fontes"] == ["https://a.com/1"]


def test_save_draft_leaves_no_temporary_file(tmp_path: Path) -> None:
    path = tmp_path / "draft.json"
    save_draft(path, build_empty_draft("s"))
    assert not (tmp_path / "draft.json.tmp").exists()
