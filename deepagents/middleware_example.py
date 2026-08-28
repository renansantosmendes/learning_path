"""
Exemplo simples de AgentMiddleware.

O middleware "envolve" cada chamada ao modelo: registra um log antes e
depois, e conta quantas vezes o modelo foi chamado durante a execucao
do agente.
"""

from dotenv import load_dotenv
from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelResponse
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent

from tools import search_web

load_dotenv()


class LoggingMiddleware(AgentMiddleware):
    """Loga cada chamada ao modelo e conta quantas chamadas foram feitas."""

    def __init__(self) -> None:
        super().__init__()
        self.call_count = 0

    def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        self.call_count += 1
        print(f"[LoggingMiddleware] Chamada #{self.call_count} ao modelo -> iniciando")

        response = handler(request)

        print(f"[LoggingMiddleware] Chamada #{self.call_count} ao modelo -> concluida")
        return response


logging_middleware = LoggingMiddleware()

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_deep_agent(
    tools=[search_web],
    system_prompt="Voce e um agente de pesquisa. Use search_web e resuma o resultado.",
    model=model,
    middleware=[logging_middleware],
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

    print(f"\nTotal de chamadas ao modelo registradas pelo middleware: {logging_middleware.call_count}")


if __name__ == "__main__":
    main()
