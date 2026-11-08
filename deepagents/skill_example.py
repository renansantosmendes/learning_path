"""
Exemplo de uso de Skills (formato Anthropic Agent Skills) com deepagents.

A skill "pesquisa-web" vive em deepagents/skills/pesquisa-web/SKILL.md e
ensina o agente a usar search_web e resumir o resultado em um unico
paragrafo. O agente descobre a skill sozinho via progressive disclosure:
primeiro ve apenas nome + descricao, e le o SKILL.md completo quando o
pedido do usuario combina com a descricao.
"""

import sys
from pathlib import Path

from deepagents.backends.filesystem import FilesystemBackend
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from tools import search_web

from deepagents import create_deep_agent

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

ROOT_DIR = Path(__file__).parent
backend = FilesystemBackend(root_dir=ROOT_DIR, virtual_mode=True)

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_deep_agent(
    tools=[search_web],
    model=model,
    backend=backend,
    skills=["skills"],
)

SKILL_PATH = ROOT_DIR / "skills" / "pesquisa-web" / "SKILL.md"


def _build_forced_skill_message(query: str) -> str:
    """Monta uma mensagem que forca o agente a seguir a skill pesquisa-web.

    Em vez de depender do modelo decidir (via progressive disclosure) se a
    skill se aplica, injeta as instrucoes completas do SKILL.md junto com o
    resultado real de search_web, garantindo que o comando /search_web
    sempre passe pelo fluxo da skill.
    """
    skill_instructions = SKILL_PATH.read_text(encoding="utf-8")
    raw_results = search_web(query)
    return (
        "Comando /search_web: siga estas instrucoes da skill 'pesquisa-web' a risca.\n\n"
        f"{skill_instructions}\n\n"
        f"Resultado bruto da busca para '{query}':\n\n{raw_results}\n\n"
        "Escreva a resposta final seguindo exatamente o formato pedido (um unico paragrafo)."
    )


def chat():
    """Chat interativo no terminal, transmitindo a resposta do agente em stream.

    Digite normalmente para conversar com o agente, ou use
    '/search_web <consulta>' para forcar o uso direto da skill pesquisa-web,
    sem depender do modelo decidir sozinho se deve pesquisar.
    """
    history: list[dict] = []
    print("Chat com o agente de pesquisa (digite 'sair' para encerrar).")
    print("Use /search_web <consulta> para forcar a skill de pesquisa.\n")

    while True:
        user_input = input("Voce: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"sair", "exit", "quit"}:
            break

        if user_input.startswith("/search_web"):
            query = user_input[len("/search_web"):].strip()
            if not query:
                print("Uso: /search_web <consulta>\n")
                continue
            message_content = _build_forced_skill_message(query)
        else:
            message_content = user_input

        history.append({"role": "user", "content": message_content})

        print("Agente: ", end="", flush=True)
        assistant_reply = ""
        for chunk, metadata in agent.stream(
            {"messages": history},
            stream_mode="messages",
        ):
            if metadata.get("langgraph_node") != "model" or not chunk.content:
                continue
            print(chunk.content, end="", flush=True)
            assistant_reply += chunk.content
        print("\n")

        history.append({"role": "assistant", "content": assistant_reply})


if __name__ == "__main__":
    chat()
