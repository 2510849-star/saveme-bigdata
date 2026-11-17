# N3 — análises e visualizações do MongoDB

Atualização posterior: a N2 foi recuperada e auditada integralmente; ver
`AUDITORIA_FINAL_N2.md`. A referência à ausência do PDF abaixo descreve a
execução original. Os resultados anteriores foram preservados.

Executado em 17/11/2026 sobre **89.618 documentos reais** de
`saveme_analytics.jogos_analiticos`, em **50,680 segundos**. Sem leitura do CSV
original para análise, alteração de documentos/índices, commit ou push.

## Inspeção antes da implementação

O documento original da N2 não foi encontrado no repositório. Foram examinadas
as referências à N2 no README e nos relatórios de validação/tratamento/carga,
além do esquema implementado. As consultas foram confirmadas diretamente na coleção:

| Campo persistido | Tipo BSON e cobertura |
|---|---|
| `preco.valor` | double, 89.618 |
| `preco.desconto_percentual` | int, 89.618 |
| `avaliacoes.positivas`, `negativas`, `total` | int, 89.618 em cada campo |
| `avaliacoes.taxa_positivas_percentual` | double em 72.563; null em 17.055 |
| `catalogo.generos` | array, 89.618 |
| `catalogo.free_to_play_explicito` | bool, 89.618 |
| `popularidade.pico_jogadores_simultaneos` | int, 89.618 |

Não foram inventados atributos comerciais, moeda, vendas ou histórico de preços.

## Resultados reais

### Quantidade de avaliações

Ranking de 15 jogos por positivas + negativas. Primeiro: **Counter-Strike 2**,
appid 730, com **8.615.921 avaliações**: 7.480.813 positivas e 1.135.108 negativas.
Essas contagens não são vendas.

### Percentual positivo com mínimo de 100 avaliações

**20.162 jogos elegíveis**. Os 15 primeiros têm 100% de avaliações positivas;
o desempate considera total de avaliações decrescente e appid crescente.
Primeiro: **Desvelado**, appid 2878710, com 281 positivas e zero negativas.
Em seguida, Secret Sealing Travel (appid 1176050, 241 avaliações) e Meddl Dash
(appid 3147900, 194). O limite mínimo reduz distorções, mas não garante igual
confiabilidade estatística entre jogos com tamanhos de amostra diferentes.

### Gêneros mais frequentes

Agregação com `$setUnion`, `$unwind`, `$group`, ordenação e limite de 15.
Cada jogo é contado uma vez por gênero; pode pertencer a vários gêneros.

| Gênero | Jogos | Percentual do catálogo |
|---|---:|---:|
| Indie | 63.189 | 70,51% |
| Casual | 38.699 | 43,18% |
| Action | 36.842 | 41,11% |
| Adventure | 35.452 | 39,56% |
| Simulation | 18.570 | 20,72% |

Os outros dez gêneros do ranking estão no CSV. Os percentuais não são exclusivos
e podem somar mais de 100%. São as classificações da fonte, incluindo rótulos
como Utilities e Early Access; não foi inventada outra taxonomia.

### Preços e Free To Play

| Faixa na unidade da fonte | Jogos |
|---|---:|
| Preço zero | 14.160 |
| 0 < preço <= 10 | 58.501 |
| 10 < preço <= 20 | 12.723 |
| 20 < preço <= 50 | 3.654 |
| Preço > 50 | 580 |
| Indisponível | 0 |

Há **8.867 jogos explicitamente classificados Free To Play**. Dos preços zero,
8.795 têm essa categoria e **5.365 não a têm**. Também há **72** registros com
categoria explícita e preço positivo. Esses atributos foram mantidos separados;
não se inferiu o motivo comercial dessa combinação nem moeda.

### Descontos

**7.454 jogos com desconto**, equivalentes a **8,3175%** do catálogo; 82.164 sem
desconto. Desconto médio entre os descontados: **54,8075%**.

| Faixa percentual | Jogos | Percentual entre os descontados |
|---|---:|---:|
| 0 < desconto <= 10 | 178 | 2,39% |
| 10 < desconto <= 25 | 955 | 12,81% |
| 25 < desconto <= 50 | 2.412 | 32,36% |
| 50 < desconto <= 75 | 2.242 | 30,08% |
| 75 < desconto <= 100 | 1.667 | 22,36% |

O CSV inclui também o percentual sobre todo o catálogo e uma tabela adicional
com a distribuição por percentual exato. Não houve descontos nulos/inválidos.

### Relação preço e avaliação positiva

**72.563 jogos incluídos**, com preço válido e pelo menos uma avaliação.
**17.055 excluídos**, por denominador zero. Taxa zero real foi preservada;
ausência de avaliações não foi convertida em 0%.

- Correlação de Pearson: **0,003998**.
- Correlação de Spearman: **0,047842**.

São associações fracas nesta amostra, sem evidência de uma associação linear
relevante. Isso não demonstra causalidade ou ausência de relações condicionadas
por gênero, popularidade ou tamanho da amostra. Não houve amostragem, ponderação
pelo número de avaliações ou remoção de outliers. A dispersão usa preço em escala
symlog, incluindo zero; a regra de 100 avaliações aplica-se apenas ao ranking.

### Pico de jogadores simultâneos

Campo presente e válido em todos os documentos. Primeiro do ranking de 15:
**Counter-Strike 2**, com **1.212.356** jogadores simultâneos de pico na fonte.
Não representa jogadores atuais, vendas ou proprietários exatos.

## Qualidade e preservação

- Totais recalculados divergentes dos persistidos: **0**.
- Taxas recalculadas divergentes das persistidas: **0**.
- Preços, descontos, positivas, negativas e picos nulos/inválidos: **0**.
- SHA-256 BSON antes/depois, incluindo `_id`, tipos e ordem dos campos:
  `482be064263186dcf3e2c311ce1f6c470e1e035304175da7c1a8d85a2584dac9`.
- Coleção e definições dos índices: **inalteradas**.
- O script não usa funções de carga nem acessa o arquivo CSV original.

## Arquivos e gráficos gerados

Em `outputs/analises/`, ignorado pelo Git:

- `ranking_avaliacoes.csv` e `.png`: barras de positivas/negativas empilhadas.
- `ranking_percentual_positivo.csv` e `.png`: taxas com mínimo de 100 avaliações.
- `generos_frequentes.csv` e `.png`: 15 gêneros.
- `distribuicao_precos.csv` e `.png`: faixas cruzadas com categoria F2P.
- `distribuicao_descontos.csv` e `.png`: faixas; gráfico apenas de descontos positivos.
- `descontos_percentuais.csv`: distribuição exata adicional.
- `relacao_preco_avaliacao.csv` e `.png`: 72.563 jogos e dispersão.
- `ranking_popularidade.csv` e `.png`: 15 maiores picos.
- `resumo.json`: indicadores, líderes, metodologia, hashes e duração.

Total: **8 CSVs, 7 PNGs e 1 resumo JSON**. Os sete gráficos foram inspecionados
visualmente; títulos, rótulos, acentos e caracteres dos nomes estão legíveis.
O cache de fontes do Matplotlib é um arquivo de suporte, também ignorado.

## Testes e execução

**52 testes aprovados**: 36 anteriores e 16 de análise. Cobrem limites das faixas,
empates e tamanho dos rankings, mínimo de 100, denominador zero, taxa zero real,
nulos/negativos/infinitos, descontos, preço zero independente de F2P, correlações,
dados insuficientes, popularidade, leitura com projeção e agregação multivalorada.

Além dos testes unitários, consultas independentes ao MongoDB confirmaram os três
rankings exportados; uma contagem independente com Pandas/explode sobre gêneros
lidos do banco confirmou os 15 gêneros. Contagens de descontos e de faixas de
preço também foram reconciliadas. Nenhuma dessas verificações usou o CSV original.

```powershell
.\.venv\Scripts\python.exe -X utf8 -W error::ResourceWarning -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 analises_mongodb.py
.\.venv\Scripts\python.exe -m pip check
git diff --check
git check-ignore outputs/analises/resumo.json outputs/analises/ranking_avaliacoes.csv outputs/analises/ranking_avaliacoes.png
```

Execução concluída com código 0. O Matplotlib informou apenas a construção inicial
do cache de fontes. Não houve erro no processamento, nos testes ou na geração.

## Arquivos do repositório e limitações

Criados: `analises_mongodb.py`, `tests/test_analises_mongodb.py` e este relatório.
Atualizado: `README.md`. As dependências existentes foram suficientes;
`requirements.txt` e `.gitignore` não precisaram de alteração nesta etapa.
CSV, coleção e relatórios anteriores foram preservados.

As análises representam o recorte do dataset Steam de março de 2025, não o estado
atual da loja. Documento original da N2 ausente; moeda não confirmada. Categorias
não são exclusivas e correlações são descritivas. Não execute ingestões simultâneas:
as auditorias de preservação não constituem snapshot transacional.
