---
name: pesquisa-web
description: Pesquisa um topico na web usando a ferramenta search_web e resume o resultado para o usuario em um unico paragrafo, direto e sem topicos. Use quando o usuario pedir para pesquisar, buscar ou descobrir informacoes sobre algum assunto.
license: MIT
allowed-tools: search_web
---

# Pesquisa Web

## Quando usar

Use esta skill sempre que o usuario pedir para pesquisar, buscar ou descobrir
informacoes sobre um assunto na web (ex: "pesquise sobre X", "o que e Y",
"busque informacoes sobre Z").

## Passo a passo

1. Identifique a consulta principal a partir do pedido do usuario. Se o pedido
   for vago, escolha a formulacao de busca mais direta e especifica possivel.
2. Chame a ferramenta `search_web` passando essa consulta.
3. Leia o resultado retornado e escreva um resumo para o usuario que:
   - Tenha exatamente **um paragrafo** (sem listas, sem topicos, sem quebras
     de linha extras).
   - Seja curto e direto (poucas frases, apenas o essencial).
   - Use linguagem clara, sem jargao desnecessario.
   - Nao inclua links, citacoes ou meta-comentarios sobre a busca em si
     (ex: nao diga "de acordo com a busca").
4. Entregue apenas o paragrafo final como resposta. Nao repita a pergunta do
   usuario nem adicione introducoes como "aqui esta o resumo:".

## Exemplo

Pedido do usuario: "Pesquise o que sao deep agents e me de um resumo."

Acao: chamar `search_web("o que sao deep agents")`.

Resposta esperada (um paragrafo apenas):

"Deep agents sao agentes construidos sobre o LangGraph que combinam
planejamento por meio de listas de tarefas, suporte a sub-agentes
especializados e um sistema de arquivos virtual, permitindo executar tarefas
complexas de forma estruturada e com contexto persistente."
