---
name: noticias-economia-investimento
description: Busca noticias de economia e mercado financeiro com a ferramenta search_web, avalia se o conteudo recuperado e relevante e atual, refina as buscas quando ele nao faz sentido, e entrega um panorama para ajudar o investidor a entender o mercado e a tomar decisoes sobre acoes e outros ativos, com a lista de links consultados. Use quando o usuario pedir noticias de economia, mercado, bolsa, acoes, juros, inflacao, cambio, cripto, fundos, ou perguntar o que esta acontecendo no mercado para decidir investimentos. Nao use o formato de paragrafo unico da skill pesquisa-web.
license: MIT
allowed-tools: search_web
---

# Noticias de Economia para Investidor

## Objetivo

Entregar ao investidor um panorama atual do mercado baseado apenas em
noticias recuperadas com `search_web`, um registro das buscas feitas e a
lista de links consultados. A saida e analise educacional: nunca e
recomendacao de compra ou venda.

## Quando usar

Use esta skill quando o pedido envolver economia ou mercado financeiro
(ex: "noticias sobre a Petrobras para investir", "o que esta acontecendo
com os juros no Brasil", "como esta o mercado de criptomoedas", "vale
investir em tecnologia agora?"). Para pesquisas gerais que nao envolvem
economia ou investimento, use a skill `pesquisa-web`.

## Limite de buscas

Faca no maximo **3 chamadas** a `search_web` no total: a busca inicial e
no maximo 2 refinamentos. Nunca repita uma consulta ja feita.

## Passo a passo

1. **Entenda o pedido.** Identifique o ativo, setor, indicador ou tema
   (ex: acoes de um setor, Selic, dolar, Ibovespa, cripto) e o horizonte de
   interesse, se houver.
2. **Monte a consulta inicial, especifica ao pedido.** Se o pedido cita uma
   empresa, ativo ou setor, ele deve aparecer na consulta. Use termos de
   mercado em portugues, com nomes de empresas, tickers, instituicoes
   (Banco Central, B3, Ibovespa, FED) ou indicadores. Quando a atualidade
   importar, inclua "2026". Exemplo para "acoes da Petrobras":
   `"Petrobras acoes resultado trimestre 2026"`. Consulta generica como
   `"noticias economia Brasil"` so e aceitavel quando o pedido for
   generico.
3. **Chame `search_web`** com a consulta. A resposta tem as secoes
   `Resultados:` (com linhas `URL:`) e `Imagens:`. Copie as URLs da secao
   `Resultados:` para o registro de fontes. Ignore as imagens.
4. **Avalie o conteudo recuperado.** Escreva a avaliacao de cada criterio
   (sim ou nao), olhando os titulos, conteudos e datas dos resultados:
   - **Relevante:** trata do ativo ou tema pedido, e nao de assunto parecido.
   - **Economia ou mercado:** traz fatos de economia, empresas listadas,
     politica monetaria, indicadores ou desempenho de ativos.
   - **Atual:** o conteudo parece recente. Se nao ha data ou o conteudo for
     claramente antigo, considere-o fraco para decisoes de investimento.
   - **Substancial:** traz fatos, numeros ou contexto, e nao apenas titulos
     ou frases genericas.
   - **Diverso:** ha pelo menos 2 fontes de dominios diferentes.

   O conteudo "faz sentido" somente quando **Relevante** e **Substancial**
   sao sim e pelo menos 4 dos 5 criterios sao atendidos. Uma resposta
   genérica sobre o pais quando o pedido e sobre uma empresa e **nao** faz
   sentido, mesmo que seja bem escrita.
5. **Se nao fizer sentido, refine a busca.** Registre em uma frase o motivo
   (ex: "resultados falam de outra empresa"). Depois, monte uma consulta
   diferente e especifica, por exemplo:
   - trocar termos genericos por tickers ou nomes oficiais (ex: "PETR4");
   - usar sinonimos em portugues e ingles (ex: "juros" e "interest rate");
   - restringir por periodo ("ultimo mes", "2026") quando houver noticias
     antigas;
   - ampliar o tema quando a busca foi restrita demais e voltou vazia.

   Volte ao passo 3 com a nova consulta. Pare quando o conteudo fizer sentido
   ou quando as 3 buscas se esgotarem.
6. **Quando as buscas se esgotarem sem conteudo bom,** nao invente dados.
   Entregue o que foi encontrado, indique as limitacoes e diga que o
   investidor deve confirmar em fontes oficiais, como B3, CVM, Banco Central
   e demonstracoes financeiras das empresas.
7. **Monte a resposta final** no formato abaixo.

## Formato da resposta final

Use Markdown em portugues, com estas secoes nesta ordem. Nao escreva a
resposta em um unico paragrafo.

**Buscas realizadas**
Uma linha por chamada a `search_web`, na ordem em que foram feitas:
`n. "consulta" - decisao (aceita ou refinada) - motivo em uma frase`.

**Panorama do mercado**
De 3 a 5 pontos com os fatos mais relevantes encontrados, cada um com
o contexto e os numeros que aparecem nas fontes.

**Fatores de atencao e riscos**
De 2 a 4 pontos, com riscos ou incertezas citados nas noticias.

**Como isso pode influenciar a decisao de investir**
Uma leitura educacional: quais perguntas o investidor deve fazer antes de
decidir (ex: prazo, risco, diversificacao) e como os fatos acima se
conectam a elas. Nao diga "compre" nem "venda".

**Limitacoes da busca**
Uma ou duas frases, somente se houver lacunas, conteudo antigo ou fontes
fracas. Se nao houver, omita a secao.

**Fontes consultadas**
Liste, sem repeticao, todas as URLs que apareceram nas secoes `Resultados:`
das chamadas feitas, no formato:

- [Titulo do resultado](URL) - consulta: "texto da consulta"

Regras desta secao:
- Copie cada URL exatamente como aparece no campo `URL:`.
- Cite aqui as fontes usadas no texto. O programa que executa esta skill
  anexa automaticamente a lista completa de todos os links retornados pelas
  buscas, entao nao tente reproduzir essa lista inteira.
- Nunca use a pagina inicial de um site no lugar de uma URL de resultado.
- Nao inclua URLs de imagens nem URLs que nao estejam no retorno da busca.

**Aviso:** este conteudo e educacional e nao constitui recomendacao de
investimento. Decisoes devem considerar o perfil do investidor e, se
necessario, o apoio de um profissional habilitado.

## Regras

- Use apenas fatos presentes nos resultados de `search_web`. Nao complete com
  conhecimento proprio sobre cotacoes ou eventos recentes.
- Nao afirme que um ativo vai subir, cair ou que e um bom investimento.
- Cite numeros e datas somente se aparecerem no conteudo recuperado.
- Se duas fontes se contradizerem, mostre as duas versoes.
- Nao inclua imagens na resposta, apenas os links de fontes.

## Exemplo

Pedido do usuario: "Quero entender se vale a pena investir em acoes de
bancos agora."

Buscas realizadas:
1. "acoes bancos brasileiros resultado trimestre 2026" - refinada - resultados antigos e superficiais.
2. "Itau Bradesco Banco do Brasil resultado trimestre 2026 juros" - aceita - atende aos criterios.

Em seguida, o panorama, os riscos, a leitura educacional, o aviso e a lista
"Fontes consultadas" com os links de todos os resultados das duas buscas.
