---
name: analise-de-mercado
description: Analisa acoes, indices e o mercado para ajudar o investidor a entender a situacao de um ativo antes de decidir investir. Combina noticias recentes (search_web) com cotacao e indicadores fundamentalistas (get_stock_quote, get_stock_fundamentals), indicadores tecnicos (get_technical_indicators), risco e retorno contra o Ibovespa (get_risk_metrics) e o contexto macroeconomico brasileiro (get_brazil_macro). Use quando o usuario pedir analise de uma acao (PETR4, VALE3, AAPL), de um setor, de juros, inflacao, cambio, cripto ou fundos, ou perguntar se vale a pena investir em algo. Nao use o formato de paragrafo unico da skill pesquisa-web.
license: MIT
allowed-tools: search_web get_stock_quote get_stock_fundamentals get_technical_indicators get_risk_metrics get_brazil_macro
---

# Analise de Mercado para Investidor

## Objetivo

Entregar ao investidor um panorama do ativo ou do mercado que cruze as
noticias com os numeros: preco, valuation, rentabilidade, endividamento,
sinais tecnicos, risco contra o Ibovespa e juros. O resultado e analise
educacional: nunca e recomendacao de compra ou venda.

## Quando usar

Use esta skill quando o pedido envolver economia, mercado financeiro ou um
ativo para investimento. Exemplos: "vale a pena investir na Petrobras?",
"como esta a VALE3 agora?", "o que os juros significam para os bancos?",
"compare o risco de PETR4 e ITUB4". Para pesquisas gerais sem relacao com
investimento, use a skill `pesquisa-web`.

## Ferramentas

- `search_web(query)`: noticias recentes. Use para entender o que esta
  acontecendo com o ativo ou o setor.
- `get_stock_quote(ticker)`: preco atual, variacao no dia, retornos de 1 mes,
  6 meses e do periodo de 12 meses, faixa de 52 semanas e perfil da empresa.
- `get_stock_fundamentals(ticker)`: P/L, P/VP, EV/EBITDA, dividend yield, ROE,
  ROA, margens, divida/patrimonio e liquidez corrente.
- `get_technical_indicators(ticker, period)`: medias moveis 9, 21 e 50, RSI,
  MACD, Bollinger, ATR, ADX e estocastico, com sinais em linguagem simples.
  Use periodo `6mo` ou maior.
- `get_risk_metrics(ticker, period, benchmark, risk_free_annual_percent)`:
  retorno e volatilidade anualizados, Sharpe, Sortino, drawdown maximo, VaR
  95%, beta e alfa contra o Ibovespa (`^BVSP`). Para a taxa livre de risco,
  use a taxa CDI obtida em `get_brazil_macro`.
- `get_brazil_macro()`: Selic, CDI anualizado, IPCA em 12 meses e juro real.

Tickers da B3 podem ser escritos sem o sufixo `.SA` (PETR4, VALE3). Ativos
americanos usam o ticker direto (AAPL). Indices usam o simbolo com `^`
(^BVSP).

## Limite de consultas

- No maximo **3 chamadas** a `search_web` por pergunta: a busca inicial e no
  maximo 2 refinamentos. Nunca repita uma consulta ja feita.
- Cada ferramenta de indicadores deve ser chamada **uma vez por ativo** por
  pergunta. Nao repita a mesma chamada com os mesmos argumentos.
- Chame `get_brazil_macro` quando o juro, a inflacao ou o cambio afetarem a
  tese (bancos, empresas endividadas, setores sensiveis a juros, decisoes de
  renda fixa contra renda variavel). Nao chame sem motivo.

## Rascunho local (draft.json)

- `read_draft()`: devolve o rascunho com as diretivas do investidor, os
  ativos e indicadores ja analisados, as conclusoes parciais, as pendencias e
  o historico das perguntas respondidas. Chame antes de qualquer outra
  ferramenta.
- `update_draft(section, value, mode)`: registra o andamento. Secoes:
  `diretivas` (regras fixas do investidor, use `mode="append"`), `pedido_atual`
  (texto), `ativos` (lista de tickers), `indicadores` (objeto por ticker),
  `buscas`, `conclusoes_parciais` e `pendencias` (listas). Valores de lista e
  objeto vao em JSON.
- O historico e mantido pelo programa e nao pode ser alterado.
- Se o rascunho ja tiver dados de um ativo analisado hoje, reutilize-os em
  vez de chamar as ferramentas de novo, a menos que o investidor peca dados
  atualizados.
- Se o investidor disser uma regra fixa (ex.: "sempre considere o juro real"),
  registre em `diretivas` e siga essa regra nas proximas analises.

## Passo a passo

1. **Recupere o rascunho.** Chame `read_draft` e aplique as diretivas
   registradas.
2. **Entenda o pedido.** Identifique o ativo (ticker), o setor ou o tema
   macro, e o horizonte de interesse, se houver. Se o pedido citar uma
   empresa sem o ticker, use o ticker mais conhecido da B3 e diga qual foi.
   Registre o pedido em `pedido_atual` com `update_draft`.
3. **Busque as noticias.** Chame `search_web` com uma consulta especifica,
   contendo o nome da empresa ou o ticker, e "2026" quando a atualidade
   importar. Exemplo: `"Petrobras PETR4 resultado trimestre 2026"`.
4. **Avalie as noticias.** Para cada resultado, verifique se ele e
   relevante para o ativo, se e de economia ou mercado, se parece atual, se
   traz fatos ou numeros e se ha pelo menos 2 fontes diferentes. Refine a
   busca se o conteudo nao fizer sentido, registrando o motivo.
5. **Levante os indicadores.** Chame, nesta ordem e conforme o pedido:
   `get_brazil_macro` (antes de `get_risk_metrics`, para obter a taxa CDI que
   sera usada como taxa livre de risco), `get_stock_quote`,
   `get_stock_fundamentals`, `get_technical_indicators` e
   `get_risk_metrics` com `risk_free_annual_percent` igual ao CDI. Para uma
   comparacao entre ativos, faca as chamadas de cada um.
6. **Cruze noticias e numeros.** Procure coerencia entre eles. Exemplos:
   noticia de lucro forte com P/L alto ou tendencia de baixa; noticia de
   queda com RSI em sobrevenda; juro alto com empresa muito endividada.
   Quando houver contradicao, mostre as duas leituras.
7. **Monte a resposta final** no formato abaixo.

## Interpretacao dos indicadores

- **P/L e P/VP**: quanto o mercado paga pelo lucro e pelo patrimonio. Valores
  altos pedem crescimento para se justificar; valores baixos podem indicar
  barato ou problema, e a diferenca depende do setor.
- **ROE e margens**: rentabilidade do negocio. Compare com o proprio historico
  quando houver dados, nao so com outros setores.
- **Divida / patrimonio e liquidez corrente**: capacidade de pagar as contas.
  Empresas com muita divida sofrem mais quando os juros sobem.
- **Dividend yield**: quanto o ativo paga em proventos em relacao ao preco.
  Um yield muito alto pode refletir queda do preco.
- **Sinais tecnicos**: descrevem o grafico, nao o valor da empresa. RSI acima
  de 70 ou abaixo de 30, cruzamento do MACD e a posicao em relacao a media de
  50 dias sao sinais de momento, nao de qualidade.
- **Sharpe e Sortino**: retorno obtido por unidade de risco. Valores acima de
  1 sao considerados bons. Compare ativos com o mesmo periodo.
- **Beta e alfa**: beta acima de 1 oscila mais que o Ibovespa; abaixo de 1,
  oscila menos. Alfa positivo indica retorno acima do esperado para o risco
  assumido.
- **Selic, CDI e juro real**: o juro real (CDI descontado do IPCA) e a
  referencia de custo de oportunidade. Quando ele e alto, renda fixa compete
  com acoes.

## Formato da resposta final

Use Markdown em portugues, com estas secoes nesta ordem. Nao escreva a
resposta em um unico paragrafo.

**Buscas realizadas**
Uma linha por chamada a `search_web`: `n. "consulta" - decisao - motivo`.

**Panorama de noticias**
De 3 a 5 pontos com os fatos mais relevantes, com contexto e numeros que
aparecem nas fontes.

**Indicadores do ativo**
Preco, retornos, valuation, rentabilidade e endividamento, com os valores
das ferramentas. Omita a secao se a pergunta nao for sobre um ativo.

**Analise tecnica e risco**
Sinais tecnicos e metricas de risco em linguagem simples. Omita a secao se
nao usou essas ferramentas.

**Contexto macroeconomico**
Selic, CDI, IPCA e juro real, e como eles afetam a decisao. Omita a secao se
nao usou `get_brazil_macro`.

**Riscos e pontos de atencao**
De 2 a 4 pontos, combinando noticias e indicadores.

**Como isso pode influenciar a decisao de investir**
Leitura educacional: perguntas que o investidor deve responder antes de
decidir (prazo, tolerancia a risco, diversificacao, perfil) e como os fatos
acima se conectam a elas. Nao diga "compre" nem "venda".

**Limitacoes da analise**
Uma ou duas frases sobre dados defasados, noticias antigas, indicadores
inconsistentes entre si ou fontes fracas. Omita se nao houver.

**Fontes consultadas**
Cite as fontes usadas no texto. O programa anexa automaticamente a lista
completa dos links retornados pelas buscas.

**Aviso:** este conteudo e educacional e nao constitui recomendacao de
investimento. Decisoes devem considerar o perfil do investidor e, se
necessario, o apoio de um profissional habilitado.

## Regras

- Use apenas dados retornados pelas ferramentas e noticias encontradas. Nao
  complete com conhecimento proprio sobre cotacoes, resultados ou eventos
  recentes.
- Se uma ferramenta retornar erro ou "n/d", diga isso na resposta e nao
  invente o valor.
- Nao afirme que um ativo vai subir, cair ou que e um bom investimento.
- Cite numeros e datas somente se aparecerem nos resultados das ferramentas.
- Se duas fontes ou indicadores se contradizerem, mostre as duas leituras.
- Nao inclua imagens nem URLs de imagens na resposta.

## Exemplo

Pedido: "Vale a pena investir na Petrobras agora?"

1. Ticker: PETR4. Busca: `"Petrobras PETR4 resultado trimestre 2026"`. A
   primeira busca traz resultados sobre o balanco do trimestre: aceita.
2. Chama `get_stock_quote`, `get_stock_fundamentals`,
   `get_technical_indicators` (6mo), `get_risk_metrics` com a taxa CDI e
   `get_brazil_macro`.
3. Cruza: lucro forte nas noticias, P/L baixo nos fundamentos, RSI em
   sobrevenda e juro real alto. Mostra que o ativo parece barato, mas o
   momento tecnico e o juro alto pesam contra. Nao conclui compra ou venda.
4. Responde com as secoes acima e o aviso.
