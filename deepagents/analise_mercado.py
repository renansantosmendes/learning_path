"""Entry point of the market analysis chat. The logic lives in market_chat/."""

import sys

from dotenv import load_dotenv
from market_chat.session import run_chat


def main() -> None:
    """Loads the environment and starts the interactive chat.

    Returns
    -------
    None
        The chat runs until the investor exits.
    """
    sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv()
    run_chat()


if __name__ == "__main__":
    main()
