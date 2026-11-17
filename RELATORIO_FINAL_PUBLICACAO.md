# N3 — análises finais e prontidão para publicação

Atualização para apresentação: o código-base já foi publicado em `6300343` e
reproduzido em clone isolado; a fonte Kaggle foi identificada por verificação
externa. Ver `docs/RELATORIO_PREPARACAO_APRESENTACAO.md` e `docs/ORIGEM_DATASET.md`.
A seleção atual passou a 42 arquivos, com evidências pequenas. Os diagnósticos
abaixo preservam a situação histórica antes dessas atualizações, não a situação atual.

## Atualização documental de reprodução — 17/11/2026

README, preparação de publicação, manifesto e este relatório foram reinspecionados.
Nenhuma funcionalidade nova foi criada. O grupo **ainda precisa fornecer o link
exato do Kaggle, versão e instruções para obter o CSV**. A origem está identificada
apenas por título, plataforma, período e nome de arquivo; não foi inventada URL.

O README agora contém roteiro completo de ambiente limpo, com validação do hash
do CSV, dependências, Compose com projeto separado, testes, tratamento, duas cargas,
verificação e três scripts de análise. O roteiro não foi executado em um clone
independente nesta revisão. ObjectIds de um banco novo serão diferentes; hashes
BSON devem ser iguais entre as execuções desse banco, não aos hashes históricos.
Dependências transitivas e a imagem MongoDB não estão fixadas por lockfile/digest,
portanto não se promete reprodução bit a bit do ambiente.

Verificações não destrutivas desta atualização: 30 candidatos únicos e existentes,
nenhum ignorado na seleção, nenhum CSV/temporário/chave privada incluído e nenhum
segredo real identificado pelos padrões revistos (há somente a fixture fictícia
de URI autenticada em teste). Origin confirmado no GitHub, sem credencial embutida,
branch main e staging vazio. O PDF foi mantido e sua revisão prévia continua
registrada abaixo. `pip check` passou; Compose validou com código 0, embora o host
tenha emitido aviso de acesso à configuração Docker pessoal. SHA-256 do CSV
reconfirmado e inalterado. Nenhum serviço foi iniciado/parado, nenhum dado foi
gravado no MongoDB e nenhum staging/commit/push foi executado nesta revisão.

O manifesto permanece com os mesmos 30 nomes. A nova documentação não altera
os resultados históricos de 70 testes; a suíte não precisou ser repetida para
esta alteração exclusivamente documental. Bloqueios restantes: obtenção exata
do CSV pelo grupo, publicação autorizada e comprovação em clone limpo.

Revisão em 17/11/2026. **Código validado no ambiente atual, mas entrega/publicação
ainda pendente**: arquivos não foram adicionados ao índice, não houve commit/push,
a reprodução independente não foi testada e falta documentar a obtenção exata do CSV.

## 1. Análises efetivamente executadas

`analises_finais.py` leu exclusivamente os **89.618 documentos reais** de
`saveme_analytics.jogos_analiticos`. Execução concluída em **47,013 segundos**,
sem ler o CSV original como fonte de análise, sem alterar documentos/índices.

### Ranking de avaliações positivas

| Posição | Jogo | Positivas | Negativas | Total |
|---|---|---:|---:|---:|
| 1 | Counter-Strike 2 | 7.480.813 | 1.135.108 | 8.615.921 |
| 2 | Dota 2 | 1.998.462 | 451.338 | 2.449.800 |
| 3 | Grand Theft Auto V Legacy | 1.719.950 | 250.012 | 1.969.962 |

O CSV contém 15 jogos. Ordenação: positivas decrescente e appid crescente.
Total é coluna de contexto, não critério de ordenação. As contagens não são vendas.

### Proprietários estimados por faixa

**15 faixas distintas**, sem ausências/limites inválidos nesta execução:

| Faixa de proprietários estimados | Jogos | Percentual do catálogo |
|---|---:|---:|
| 0 - 20000 | 59.320 | 66,19% |
| 20000 - 50000 | 9.683 | 10,80% |
| 0 - 0 | 8.418 | 9,39% |
| 50000 - 100000 | 4.552 | 5,08% |

A tabela completa contém limites e contagem de jogos por intervalo. Não se
calculou ponto médio, soma de proprietários ou vendas. `0 - 0` foi preservado,
sem interpretá-lo como comprovação de nenhum proprietário.

O ranking descritivo de faixas começa com Dota 2 (200.000.000–500.000.000),
Counter-Strike 2 (100.000.000–200.000.000) e GTA V Legacy
(50.000.000–100.000.000). Ordenar pelos limites não fornece quantidades exatas;
intervalos sobrepostos não permitem classificação exata de proprietários.

### Comparação por gênero

**33 gêneros** encontrados; **212 jogos sem gênero**. Cada jogo conta uma vez
em cada gênero, podendo pertencer a vários. Taxas excluem denominadores zero;
preço e quantidade do catálogo continuam incluindo jogos sem avaliações.

| Gênero | Jogos | Preço mediano na unidade da fonte | Taxa média, jogos com >=100 avaliações | Elegíveis >=100 |
|---|---:|---:|---:|---:|
| Indie | 63.189 | 3,99 | 79,86% | 13.659 |
| Casual | 38.699 | 2,99 | 80,64% | 6.300 |
| Action | 36.842 | 4,99 | 77,73% | 8.573 |
| Adventure | 35.452 | 4,99 | 80,01% | 8.759 |
| Simulation | 18.570 | 4,99 | 77,23% | 4.969 |

O CSV inclui preço médio/mediano, elegíveis, jogos sem avaliações, taxa média/
mediana entre jogos com alguma avaliação, taxa ponderada e análise de sensibilidade
com mínimo de 100 avaliações. O gráfico usa os 15 gêneros mais frequentes e essa
última população para a taxa. Uma taxa de 0% real continua válida.

Moeda não confirmada; não há inferência causal nem comparação de vendas.
Gêneros não são exclusivos e seus totais não devem ser somados como jogos distintos.

## 2. Saídas e preservação

Nova pasta `outputs/analises/finais/`, ignorada pelo Git, preservando as anteriores:

- `ranking_positivas.csv` e `.png`.
- `proprietarios_faixas.csv` e `.png`.
- `ranking_faixas_proprietarios.csv`.
- `comparacao_generos.csv` e `.png`.
- `resumo.json`, com indicadores, metodologia e hashes.

Total: **4 CSVs, 3 PNGs e 1 JSON**. Os três PNGs foram inspecionados visualmente.
Consultas independentes no MongoDB conferiram os 15 appids do ranking, todas as
faixas e as contagens/preços médios/taxas com mínimo de 100 de todos os gêneros.

Hash BSON antes/depois, incluindo `_id`, tipos e ordem de todos os documentos:
`482be064263186dcf3e2c311ce1f6c470e1e035304175da7c1a8d85a2584dac9`.
**Coleção e índices inalterados**. O CSV não foi modificado; sua integridade é
reconferida na preparação final, com SHA-256
`04d8df2778aaa8f8b575934b7072d55224d37a2ded23e8261583f0fcf668dfab`.
Nenhuma exclusão de MongoDB ou volume.

## 3. Testes

**70 testes aprovados**: 60 anteriores e dez novos para positivas versus total,
limite/empates, intervalos válidos/inválidos, zeros, multigênero sem duplicação,
denominador zero, taxas simples/ponderadas, mínimo de 100, preços nulos/zero,
grupos vazios e preservação da entrada. Avisos de recursos tratados como erros.
`pip check`: nenhuma dependência quebrada. `git diff --check`: sem erros.

## 4. Revisão de arquivos de configuração

| Arquivo | Revisão |
|---|---|
| README.md | Comandos das três fases de análise, metodologias, limitações e instruções para publicação |
| .gitignore | Mantém data/outputs/env/cache fora do Git; ampliado para chaves, credenciais de serviço e temporários comuns |
| requirements.txt | Mantido: pandas 3.1.1, pymongo 4.20.0 e matplotlib 3.11.2; nenhuma dependência nova necessária |
| compose.yaml | Validado com `docker compose config --quiet`; MongoDB 8.0, volume persistente, healthcheck, porta apenas no loopback |
| .env.example | Somente URI local sem autenticação; script lê variável do processo, não carrega .env automaticamente |

O Compose sem autenticação é destinado à demonstração local e não à exposição
em rede. A validação sintática exibiu aviso de permissão do arquivo de configuração
Docker do host, sem invalidar o Compose ou afetar a execução real das análises.

## 5. Segredos, privacidade e portabilidade

- Revisão textual dos arquivos candidatos, com padrões de URIs autenticadas,
  tokens de serviços conhecidos, chaves privadas e caminhos locais.
- Nenhum segredo real identificado. O único URI autenticado encontrado é uma
  mensagem **fictícia** em `tests/test_carga_mongodb.py`, usada para provar que
  erros de conexão não expõem credenciais; o teste usa mocks, não essa conexão.
- Caminhos pessoais do interpretador e da Área de Trabalho foram anonimizados em
  `RELATORIO_VALIDACAO_INICIAL.md` e `AUDITORIA_FINAL_N2.md`. Resultados históricos
  não foram alterados; o caminho do Python virou um marcador explícito.
- PDF N2 revisado: oito páginas; metadados apenas título/produtor, sem caminhos
  pessoais; nenhum email/URI autenticado no texto extraído. O diagrama não contém
  registros de usuários, apenas nomes de entidades/campos. Os nomes da equipe são
  autoria acadêmica intencional, a confirmar na revisão final dos autores.
- `data/`, outputs, cache de fontes, .venv, logs e credenciais não integram a lista
  de publicação. Nenhum dump/documento completo do MongoDB será adicionado.
- Há uma cópia redundante da N2 em data/, já ignorada; a publicação usa somente
  a cópia organizada em docs/. Nenhuma dessas cópias foi apagada.
- O remoto origin aponta ao GitHub sem credencial embutida detectada. A URL e
  informações pessoais da identidade Git não são copiadas para a documentação.

A busca por padrões e a revisão manual não garantem ausência de todo segredo
possível. Revisar o diff exato antes do commit continua necessário. Relatórios
locais da revisão, sem conteúdo de segredos, estão em `outputs/revisao_publicacao/`.

## 6. Git e seleção exata

A lista fechada em `ARQUIVOS_PUBLICACAO.txt` contém **30 arquivos**. No estado
auditado, somente `.gitignore` e `analise_dataset.py` estão rastreados; os outros
28 candidatos estão não rastreados. `.gitignore` está modificado. O índice de
staging permanece vazio; nenhum add real, commit ou push foi feito.

Os arquivos ignorados incluem o CSV, ambiente Python, outputs e caches/logs.
O dry-run da seleção e os inventários verificam existência, ausência de ignorados
na lista e exclusão dos artefatos locais. Não foi usado `git add .`.
Inventário final: 2 candidatos rastreados e 28 não rastreados; nenhum arquivo
não ignorado fora da lista fechada. O dry-run mostrou 29 adições/atualizações,
pois `analise_dataset.py` já está rastreado e inalterado. Índice confirmado vazio
após a prévia. O lock temporário do dry-run exigiu execução fora do sandbox;
isso não adicionou arquivos ao staging. A conferência de ignore usou entrada
em bytes LF para evitar que CR de pipes Windows fosse interpretado como parte
de um nome de arquivo.

Inventário de ignorados por raiz: .venv (8.624 arquivos), outputs (58), data (2),
cache Python da raiz (5), caches em tests (6) e um log de validação. Contagens
podem crescer com execuções locais; nenhum desses arquivos integra o manifesto.

`PREPARACAO_PUBLICACAO.md` contém os comandos exatos de add seletivo, revisão,
commit e push, todos preparados para execução futura pelo usuário. O origin e
a branch main existem; acesso/permissões remotos não foram testados por push.

## 7. Parecer de prontidão

**Implementação pronta para revisão de publicação no ambiente validado, mas a
entrega não está pronta/publicada.** Pendências reais:

1. **Reprodutibilidade externa:** documentar URL/versão exatas para obter o CSV
   e testar instalação/execução em ambiente ou clone limpo separado. O CSV está
   corretamente fora do Git; sem essa obtenção documentada um clone não basta.
2. **Entrega GitHub:** revisar os 30 candidatos e o diff final; fazer commit/push
   apenas quando autorizado; conferir acesso do professor e conteúdo publicado.
3. **Demonstração acadêmica:** executar/registrar o roteiro conforme solicitado
   pelo professor. Evidências locais anteriores não são uma entrega da apresentação.

Limitações a declarar: unidade dos tempos, moeda e semântica de sentinelas não
confirmadas externamente; tags fora da projeção; dados são snapshot Steam de
março de 2025; sem histórico de preços, multilojas ou interface transacional.
Essas limitações não foram ocultadas nem substituídas por dados inventados.

As três lacunas analíticas desta solicitação foram preenchidas. Relações
multivariadas adicionais são possibilidades da N2, não resultados já demonstrados.

## 8. Arquivos e comandos desta etapa

Criados: `analises_finais.py`, `tests/test_analises_finais.py`, este relatório,
`ARQUIVOS_PUBLICACAO.txt` e `PREPARACAO_PUBLICACAO.md`.
Atualizados: README, .gitignore, checklist, anotação da auditoria e anonimização
dos dois relatórios citados. requirements, Compose e .env.example foram revisados
e mantidos. Sem reestruturação do pipeline.

```powershell
.\.venv\Scripts\python.exe -X utf8 -W error::ResourceWarning -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 analises_finais.py
.\.venv\Scripts\python.exe -m pip check
docker compose config --quiet
git diff --check
git status --short
git ls-files
git --literal-pathspecs add --dry-run --pathspec-from-file=ARQUIVOS_PUBLICACAO.txt
```

Os últimos inventários/dry-run são verificações locais de preparação; não equivalem
a commit/push. Comandos futuros de publicação estão no documento específico.
