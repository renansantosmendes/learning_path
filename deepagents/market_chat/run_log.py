"""Log file and link helpers of a chat session."""

from datetime import datetime
from pathlib import Path
from typing import TextIO

URL_PREFIX = "URL: "


def create_run_log_path(
    log_dir: Path,
) -> Path:
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
    return log_dir / f"analise_mercado_{timestamp}.log"


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


def extract_result_urls(
    search_output: str,
) -> list[str]:
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
        line[len(URL_PREFIX):].strip()
        for line in search_output.splitlines()
        if line.startswith(URL_PREFIX)
    ]


def add_unique_links(
    collected_links: list[tuple[str, str]],
    query: str,
    urls: list[str],
) -> None:
    """Adds (query, url) pairs to a list, skipping URLs already present.

    Parameters
    ----------
    collected_links : list[tuple[str, str]]
        List that receives the new pairs, in order.
    query : str
        Query that produced the URLs.
    urls : list[str]
        URLs returned by the query.

    Returns
    -------
    None
        The list is changed in place.
    """
    known_urls = {url for _, url in collected_links}
    for url in urls:
        if url not in known_urls:
            known_urls.add(url)
            collected_links.append((query, url))
