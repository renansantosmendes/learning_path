from pathlib import Path

from market_chat.run_log import (
    add_unique_links,
    create_run_log_path,
    extract_result_urls,
)


def test_create_run_log_path_creates_directory(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_path = create_run_log_path(log_dir)
    assert log_dir.is_dir()
    assert log_path.parent == log_dir
    assert log_path.name.startswith("analise_mercado_")
    assert log_path.suffix == ".log"


def test_extract_result_urls_reads_only_url_lines() -> None:
    output = "Titulo: A\nURL: https://a.com\nConteudo: x\nURL: https://b.com"
    assert extract_result_urls(output) == ["https://a.com", "https://b.com"]


def test_add_unique_links_skips_repeated_urls() -> None:
    links: list[tuple[str, str]] = [("q1", "https://a.com")]
    add_unique_links(links, "q2", ["https://a.com", "https://b.com"])
    assert links == [("q1", "https://a.com"), ("q2", "https://b.com")]
