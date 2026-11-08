"""Paths, model name and prompts of the market analysis agent."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT_DIR / "logs"
DRAFT_PATH = ROOT_DIR / "draft.json"
MODEL_NAME = "gpt-5.4-nano"
SKILL_FILE_VIRTUAL_PATH = "/skills/analise-de-mercado/SKILL.md"
SYSTEM_PROMPT = (
    "Voce responde pedidos de investidores sobre acoes, economia e mercado. "
    "Antes de qualquer consulta, leia com read_file o arquivo "
    f"{SKILL_FILE_VIRTUAL_PATH} e siga as instrucoes dele em todas as "
    "etapas, inclusive no formato da resposta final. "
    "Antes de qualquer outra ferramenta, chame read_draft para recuperar o "
    "rascunho local: as diretivas do investidor, os ativos e indicadores ja "
    "analisados, as conclusoes parciais e as pendencias. Use essas "
    "informacoes quando forem relevantes e nao repita consultas ja feitas. "
    "Durante a analise, use update_draft para registrar: diretivas quando o "
    "investidor pedir uma regra fixa (mode append), pedido_atual, ativos, "
    "indicadores, buscas, conclusoes_parciais e pendencias. Nao altere o "
    "historico."
)
EXIT_COMMANDS = frozenset({"sair", "exit", "quit"})
