from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent

from tools import search_web

load_dotenv()

INSTRUCTIONS = """
Voce e um agente de pesquisa. Use a ferramenta search_web para buscar
informacoes e depois escreva um resumo curto e claro para o usuario.
"""

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_deep_agent(
    tools=[search_web],
    system_prompt=INSTRUCTIONS,
    model=model,
)


def main():
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Pesquise o que sao deep agents e me de um resumo.",
                }
            ]
        }
    )

    for message in result["messages"]:
        message.pretty_print()


if __name__ == "__main__":
    main()
