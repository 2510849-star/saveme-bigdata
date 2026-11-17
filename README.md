# SaveMe Games — pipeline analítico Steam (N3)

Projeto acadêmico de Desenvolvimento com Linguagens de Programação Disruptivas I.
O projeto implementa leitura, validação, tratamento, transformação e carga em
MongoDB do CSV da N2. O banco analítico `saveme_analytics` é separado do PostgreSQL
da aplicação, com coleção `jogos_analiticos` identificada por `appid`.
A carga, a idempotência e as análises já foram demonstradas em MongoDB real.
Para reproduzir, é necessário um servidor MongoDB acessível.

Código publicado: [GitHub — saveme-bigdata](https://github.com/2510849-star/saveme-bigdata),
branch `main`, revisão validada `6300343`. As evidências/documentação desta
preparação ainda não foram enviadas ao remoto.

## Origem do CSV — identificação verificada

Fonte identificada: [Steam Games Dataset 2025, versão 2 no Kaggle](https://www.kaggle.com/datasets/artermiloff/steam-games-dataset/versions/2),
referência `artermiloff/steam-games-dataset`. O catálogo exibe Artemiy Ermilov,
atualização de 13/03/2025 e licença declarada MIT para o dataset. O arquivo é
`games_march2025_cleaned.csv`, referente a março de 2025; não escolher o `full`
nem o snapshot de maio de 2024.

A investigação confirmou nome, tamanho exato, cabeçalho de 47 colunas e igualdade
dos primeiros/últimos 64 KiB remotos com o arquivo local. Não foi repetido download
remoto integral nesta preparação; conferir sempre o SHA-256 após obter o arquivo.
[Origem, fontes primárias e instruções](docs/ORIGEM_DATASET.md) e
[registro da correspondência](docs/evidencias/correspondencia_dataset.json).

Referência do arquivo efetivamente validado:

- Caminho local: `data/games_march2025_cleaned.csv`, fora do Git.
- Tamanho: **468.641.107 bytes**, **89.618 registros e 47 colunas**.
- SHA-256: `04d8df2778aaa8f8b575934b7072d55224d37a2ded23e8261583f0fcf668dfab`.

Um clone do repositório **não contém o CSV**. Obter o arquivo da versão identificada,
extrair se necessário e colocá-lo em `data/`, sem sobrescrever a cópia original
validada. A lacuna de URL foi resolvida pela pesquisa; a confirmação integral de
um novo download continua sendo o hash acima. A data do download inicial pelo
grupo não foi reconstruída nem inventada.

## Reprodução em ambiente limpo — executada com ressalvas

O commit `6300343` foi clonado e executado com nova venv e MongoDB independente
em 27018: 70 testes, carga inicial de 89.618 documentos, segunda carga sem
modificações e 15 CSVs iguais aos originais. Foram gerados 14 PNGs e três resumos.
[Evidência compacta da execução](docs/evidencias/execucao_validada.json).
O CSV desse ensaio foi fornecido por cópia autorizada; a obtenção integral do
Kaggle não foi repetida. Os passos abaixo são o procedimento para uma nova reprodução.

Roteiro para **Windows/PowerShell**, em outra máquina/VM ou ambiente independente.
Requer Git, instalação completa de **Python 3.12**, Docker com Compose e Engine
Linux em funcionamento, acesso à internet para dependências/imagem e espaço para
o CSV, a imagem MongoDB e o volume de dados. As instalações de sistema são feitas
pelo responsável pelo ambiente; os scripts do projeto não as executam.
`requirements.txt` fixa as três dependências diretas; dependências transitivas e
a tag `mongo:8.0` não estão congeladas por lockfile/digest. Isso é uma limitação
de reprodução bit a bit, distinta da reprodução funcional esperada.

### 1. Obter o código publicado e instalar as dependências

Após a publicação da atualização de evidências (42 arquivos selecionados), executar
em uma pasta nova, fora do workspace
original. O primeiro comando pede a URL real, sem presumir o endereço do grupo:

```powershell
$urlRepositorio = Read-Host 'Cole a URL do repositorio GitHub publicado pelo grupo'
git clone $urlRepositorio saveme-bigdata-reproducao
if ($LASTEXITCODE -ne 0) { throw 'Falha no clone; conferir URL e acesso' }
Set-Location saveme-bigdata-reproducao
python --version
python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel criar a venv; usar Python 3.12 completo' }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependencias' }
.\.venv\Scripts\python.exe -m pip check
```

Conferir Python 3.12 antes de criar o ambiente. Se `python` for um atalho
indisponível do Windows, usar o caminho de uma instalação completa. Não é
necessário ativar a `.venv` nem alterar a política de execução do PowerShell.
O commit publicado `6300343` contém os scripts do pipeline e análises. As novas
evidências e a documentação desta apresentação ainda não foram commitadas/enviadas;
conferir o conteúdo efetivamente publicado ao repetir o clone.

### 2. Obter o CSV e conferir integridade

Obter o arquivo específico da versão 2 seguindo [estas instruções](docs/ORIGEM_DATASET.md).
Não usar outro arquivo para contornar uma divergência de hash. Depois, conferir:

```powershell
New-Item -ItemType Directory -Path data -Force | Out-Null
if (-not (Test-Path -LiteralPath 'data/games_march2025_cleaned.csv' -PathType Leaf)) {
    throw 'CSV ausente; obter o arquivo da versao 2 indicada em docs/ORIGEM_DATASET.md'
}
$hashCsvEsperado = '04d8df2778aaa8f8b575934b7072d55224d37a2ded23e8261583f0fcf668dfab'
$hashCsvObtido = (Get-FileHash -LiteralPath 'data/games_march2025_cleaned.csv' -Algorithm SHA256).Hash
if ($hashCsvObtido -ne $hashCsvEsperado) { throw 'CSV diferente do validado; conferir versao com o grupo' }
.\.venv\Scripts\python.exe -X utf8 analise_dataset.py
.\.venv\Scripts\python.exe -X utf8 validacao_inicial.py
```

Esperado: `(89618, 47)`, 89.618 appids distintos, zero duplicações em appid e
433.211 células nulas. Não modificar o CSV para fazer esses números coincidirem.

### 3. Iniciar MongoDB isolado do ambiente original

No ambiente limpo, usar um nome de projeto Compose próprio para separar seu
volume do projeto habitual. A porta local continua sendo 27017. Se já houver
um MongoDB usando essa porta, **não parar nem apagar o existente**: usar outra
máquina/VM de reprodução ou um servidor separado e configurar a URI adequada.
Os comandos abaixo pressupõem que a porta esteja disponível no ambiente limpo.

```powershell
docker --version
docker compose version
docker info
docker compose -p saveme-n3-reproducao config --quiet
docker compose -p saveme-n3-reproducao up -d --wait
if ($LASTEXITCODE -ne 0) { throw 'MongoDB nao iniciou; conferir Engine, imagem e porta' }
docker compose -p saveme-n3-reproducao ps
docker compose -p saveme-n3-reproducao exec mongodb mongosh --quiet --eval "db.adminCommand('ping').ok"
$env:MONGODB_URI = 'mongodb://127.0.0.1:27017/'
```

Esperado: serviço saudável e ping `1`. `.env.example` é somente documentação;
o Python lê a variável de ambiente do processo, não carrega `.env` automaticamente.
Não executar o ensaio apontando para o banco original se a intenção é comprovar
uma primeira carga em banco vazio. Não apagar coleções/volumes para criar esse vazio.

### 4. Testar, tratar, carregar duas vezes e analisar

Na raiz do clone, sem outras cargas concorrentes:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 pipeline_tratamento.py --saida outputs/reproducao/tratamento
.\.venv\Scripts\python.exe -X utf8 carga_mongodb.py --comprovar-idempotencia --relatorio outputs/reproducao/idempotencia.json
.\.venv\Scripts\python.exe -X utf8 carga_mongodb.py --verificar --relatorio outputs/reproducao/verificacao.json
.\.venv\Scripts\python.exe -X utf8 analises_mongodb.py --saida outputs/reproducao/analises
.\.venv\Scripts\python.exe -X utf8 analises_complementares.py --saida outputs/reproducao/complementares
.\.venv\Scripts\python.exe -X utf8 analises_finais.py --saida outputs/reproducao/finais
```

Executar cada linha somente após a anterior terminar com código 0. Critérios:

- **70 testes aprovados** e tratamento com 89.618 aceitos/zero rejeições.
- Em banco inicialmente vazio: primeira carga com 89.618 inseridos. Em retomada,
  as contagens iniciais podem variar; isso não comprova um ensaio de banco vazio.
- Segunda carga com zero inseridos/modificados, total 89.618, appids únicos,
  `estado_final_identico`, `segunda_carga_sem_modificacoes` e
  `idempotencia_comprovada` verdadeiros.
- Análises concluídas: 15 CSVs, 14 PNGs e três resumos JSON, além dos relatórios
  de tratamento/carga. Hashes da coleção antes/depois de cada análise iguais.
- Em outro banco os ObjectIds serão diferentes: comparar hashes de estado
  **dentro da mesma reprodução**, não exigir o hash BSON do banco original.
- Registrar ambiente, comandos, duração, erros e resultados. A reprodução funcional
  já passou com as ressalvas acima; isso não comprova outro sistema operacional,
  obtenção integral do Kaggle ou desempenho igual em qualquer máquina.

Para apenas parar o serviço do ensaio, preservando dados, usar
`docker compose -p saveme-n3-reproducao stop`. A reprodução não exige remoção de
volumes nem exclusão da coleção. As saídas ficam separadas das evidências anteriores.

O pipeline lê lotes de 2.000 linhas com `pd.read_csv()`, verifica cada documento
com BSON localmente e usa SHA-256 para conferir a preservação do CSV. Não grava
o dataset tratado completo. A saída padrão é:

- `outputs/tratamento/qualidade.json`: contagens de entrada, nulos por campo,
  rejeições, motivos, transformações, documentos válidos e hashes.
- `outputs/tratamento/amostra_documentos.json`: no máximo três documentos.

`outputs/` está ignorado pelo Git. É possível escolher caminhos com
`--csv CAMINHO --saida DIRETORIO`. Falhas de esquema ou identificadores encerram
o comando com código 1; erros de conteúdo rejeitam a linha e aparecem no relatório.
O relatório e as amostras são escritos somente após concluir o processamento.
Se houver falha, arquivos de uma execução anterior podem continuar no diretório;
eles não constituem evidência da execução que falhou.

## Regras implementadas

- **Esquema:** exige as 47 colunas da N2; colunas extras são informadas e não entram
  no documento. `appid` deve ser inteiro positivo não nulo e único em todo o CSV,
  inclusive entre lotes. Uma violação interrompe o processamento, sem selecionar
  arbitrariamente um registro duplicado.
- **Campos obrigatórios:** nome não vazio; preço finito não negativo; desconto
  inteiro entre 0 e 100; avaliações positivas e negativas inteiras não negativas.
  Ausências ou valores inválidos rejeitam a linha. Não há `dropna()` global.
- **Textos opcionais:** ausências e textos em branco viram `None`. Textos presentes
  são preservados, inclusive HTML e títulos como `Unknown` e `none`.
- **Listas:** `genres`, `developers`, `publishers`, `categories`,
  `supported_languages`, `full_audio_languages`, `screenshots` e `movies` são
  lidos por `ast.literal_eval()`. Ausências viram `[]`; itens `None`, vazios ou só
  espaços são removidos; textos têm espaços externos removidos. Lista malformada,
  estrutura diferente de lista ou elemento de outro tipo rejeita a linha, com
  indicação do campo. Não se usa `eval()`.
- **Sentinelas:** `pct_pos_total`, `num_reviews_total`, `pct_pos_recent` e
  `num_reviews_recent` mantêm `bruto` e `tratado`. **Hipótese:** `-1` representa
  indisponibilidade e seu tratado vira `None`; ausência também vira `None`.
  Outros negativos, percentuais acima de 100 e fracionários rejeitam a linha.
  A interpretação da sentinela ainda precisa ser confirmada na fonte.
- **Idade:** mantém `bruto`; qualquer idade negativa ou ausente produz
  `tratado: None`, sem inferir uma idade.
- **Proprietários:** preserva a faixa original e extrai inteiros inferior/superior.
  Ausência produz limites `None`; formato inválido, limites negativos/invertidos
  ou fora de int64 rejeitam a linha. Não se calcula uma quantidade exata fictícia.
- **Taxa positiva:** `positive / (positive + negative) * 100`. Sem avaliações,
  `None`; uma taxa real de 0% continua sendo zero. A taxa não é arredondada.
- **Preço:** mantém o valor, inclusive zero; sem moeda inferida ou histórico.
  `free_to_play_explicito` é verdadeiro somente quando `genres` contém a categoria
  `Free To Play` (comparação sem diferença de caixa). Falso significa ausência
  dessa evidência, não prova que o jogo seja pago.
- **Data:** preserva o texto bruto e valida data ISO `AAAA-MM-DD`. Ausência vira
  `None`; data presente inválida rejeita a linha. Não há inferência regional.
- **Outros números opcionais:** DLCs, conquistas, scores e popularidade ausentes
  viram `None`; contagens negativas ou não inteiras são rejeitadas. Scores de
  Metacritic/usuário devem estar entre 0 e 100. Zeros desses scores são preservados,
  pois sua semântica de indisponibilidade não foi confirmada.
- **Plataformas:** booleanos nativos ou `None` para ausência; texto arbitrário
  não é convertido silenciosamente em verdadeiro.
- **Saída:** apenas tipos Python nativos, sem NaN/Infinity e com limite de 16 MiB
  por documento verificado via BSON. Não há normalização destrutiva do CSV.

## Estrutura documental (versão 1)

| Grupo | Conteúdo |
|---|---|
| `appid`, `nome` | Identificação Steam |
| `lancamento` | Texto bruto e data ISO validada |
| `catalogo` | Gêneros, empresas, categorias, idiomas, mídia, plataformas, idade, DLCs e conquistas |
| `preco` | Valor original e desconto percentual |
| `avaliacoes` | Positivas, negativas, total, taxa calculada, quatro métricas brutas/tratadas e scores |
| `popularidade` | Faixa de proprietários, limites, pico simultâneo, recomendações e tempos de jogo |
| `informacoes` | Descrições, notas, resenhas, imagens e contatos/links opcionais |
| `origem` | Steam, mês de referência `2025-03` e nome do arquivo |
| `versao_documento` | `1` |

O mês é a referência do dataset, não uma data observada de coleta de cada jogo.
`packages` (lista de objetos) e `tags` (dicionário) ficam fora desta projeção;
permanecem preservados no CSV. O diagnóstico de nulos continua cobrindo todas as
47 colunas. Não há dados de outras lojas, histórico de preços nem conversão de moeda.
As unidades dos tempos de jogo não são inferidas; são mantidos os valores da fonte.

## Qualidade e testes

Os contadores de transformação se referem apenas a documentos aceitos. Contadores
podem se sobrepor (uma lista convertida também pode ter elementos removidos),
portanto não representam quantidades de linhas mutuamente exclusivas. Rejeições
de conteúdo registram o primeiro motivo de cada linha e até dez exemplos.
O total deve reconciliar `entrada = rejeitados + saída` em execução concluída.

Testes com `unittest` (biblioteca padrão) cobrem regras normais, limites, formatos
BSON/JSON, duplicidade entre lotes, rejeições, repetibilidade e preservação de bytes.
Não há dependências adicionais de teste nem serviço de banco necessário.

Ver `RELATORIO_TRATAMENTO.md` para o resultado da execução real desta etapa e
`RELATORIO_VALIDACAO_INICIAL.md` para o diagnóstico anterior.

## MongoDB: ambiente e inicialização

Instale as dependências Python com o comando já apresentado. PyMongo já consta
em `requirements.txt`; não foram adicionadas dependências. Para servidor, escolha
um MongoDB existente ou Docker com Compose. A instalação de Docker/MongoDB no
sistema não é feita por estes scripts.

Verifique as ferramentas e o Engine:

```powershell
docker --version
docker compose version
docker info
```

Docker Desktop precisa estar iniciado, com o Engine de containers Linux funcional.
Se aparecer erro de pipe/daemon, abra o Docker Desktop e aguarde sua inicialização.
Não basta o comando `docker --version` responder.

Com o Engine disponível, na raiz do repositório:

```powershell
docker compose config --quiet
docker compose up -d --wait
docker compose ps
docker compose exec mongodb mongosh --quiet --eval "db.adminCommand('ping').ok"
```

`compose.yaml` usa `mongo:8.0`, volume nomeado persistente e publica a porta apenas
em `127.0.0.1:27017`. Essa configuração sem autenticação destina-se à demonstração
local. Não é uma configuração para exposição em rede. Se a porta estiver ocupada
por MongoDB local, reutilize esse servidor ou ajuste o mapeamento e a URI.

Para parar preservando dados: `docker compose down`. Não remova o volume se quiser
manter a coleção entre demonstrações. Baixar a imagem requer internet; a
disponibilidade do container só estará comprovada após iniciar e verificar o ping.

## Carga e comprovação de idempotência

Sem variável definida, a conexão usa `mongodb://127.0.0.1:27017/`. Para configurar
outra conexão em PowerShell:

```powershell
$env:MONGODB_URI = 'mongodb://127.0.0.1:27017/'
```

`.env.example` documenta o nome da variável. O script lê o ambiente do processo;
não carrega arquivos `.env` automaticamente. Não coloque URI com credenciais no
código, nos relatórios ou em arquivos versionados. Os erros do driver são
sanitizados antes de serem apresentados.

```powershell
# Duas cargas completas, verificando estabilidade e ausência de alterações na segunda
.\.venv\Scripts\python.exe -X utf8 carga_mongodb.py --comprovar-idempotencia

# Consulta independente, sem escrever ou criar índices
.\.venv\Scripts\python.exe -X utf8 carga_mongodb.py --verificar --relatorio outputs/mongodb/verificacao.json
```

Uma carga simples: `carga_mongodb.py` sem a flag de idempotência. Opções adicionais:
`--tamanho-lote 1000`, `--csv CAMINHO` e `--relatorio CAMINHO_JSON`.
Os comandos Python devem usar o executável `.venv\Scripts\python.exe` como acima.

O script executa `ping` antes de ler/escrever, acessa somente
`saveme_analytics.jogos_analiticos` e cria índice único completo de `appid`, ou
reutiliza um índice equivalente existente. Não remove índices nem coleções. Se
houver duplicados antigos ou índice incompatível, a carga falha e deve ser revisada.
Banco e coleção são materializados pelo MongoDB na criação do índice/primeira carga.

O iterador `iterar_documentos()` de `pipeline_tratamento.py` é compartilhado pela
análise e pela carga: não existe uma segunda implementação das regras. O leitor
mantém um lote do CSV e até 1.000 operações de escrita em memória, além do conjunto
de identificadores para detecção de duplicados entre lotes. Não acumula os 89 mil
documentos. Não utiliza as três amostras como fonte da carga.

Cada lote consulta os `_id` existentes com um filtro `$in` de appids. Cada operação
é `ReplaceOne({"appid": appid}, documento, upsert=True)` por meio de
`bulk_write(..., ordered=False)`, incluindo explicitamente o `_id` já existente
no documento de substituição. Novos appids são inseridos; existentes são
substituídos pelo documento canônico atual, mantendo o `_id` do MongoDB. Campos
obsoletos no documento anterior são removidos. Appids ausentes de um CSV posterior
não são excluídos da coleção. A contagem pode, portanto, ser maior que a entrada
se o banco já contiver outros jogos.

O relatório padrão, `outputs/mongodb/carga.json`, registra:

- Status, conexão confirmada, duração e contagens de inseridos, correspondentes,
  atualizados de fato e inalterados por execução.
- Rejeições e relatório de tratamento, com SHA-256 do CSV antes/depois.
- Contagem total, quantidade de appids distintos, grupos duplicados e índice único.
- Três jogos consultados diretamente da coleção, ordenados por `appid`.
- `estado_final_identico`: mesmo SHA-256 de todos os BSONs persistidos (incluindo
  `_id`, ordem e tipos), ordenados por appid, mesma contagem e mesmo SHA-256 do CSV.
- `segunda_carga_sem_modificacoes`: zero inserções e zero modificações reportadas
  pelo servidor na segunda carga. Os upserts ainda são enviados; isso não significa
  ausência de comandos de escrita.
- `idempotencia_comprovada`: exige as duas condições acima, além das verificações
  de índice único e ausência de duplicados em cada carga. Os hashes de estado
  acrescentam duas leituras completas, sem acumular os documentos na memória.

Em MongoDB indisponível, sai com código 1 e registra falha, sem fabricar contagens.
Quando não há conexão confirmada, o relatório não informa total da coleção nem
insere resultados de testes simulados. Relatórios anteriores de outras etapas
são preservados; para manter várias tentativas de carga, use `--relatorio` diferente.

A carga não é transacional: falhas após alguns lotes podem deixar progresso
parcial. Falhas de bulk registram somente contagens retornadas pelo servidor;
falhas de rede indicam que o resultado do último lote pode ser incerto. Nesse
caso a conclusão/rejeições finais não são afirmadas. Reexecutar os mesmos dados
converge por appid sem duplicar. Uma falha de esquema/identificadores ou mudança
do CSV durante a leitura também pode interromper após lotes já aplicados.

## Testar a persistência sem servidor

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
```

Os testes usam mocks e uma coleção em memória para lotes, upsert, segunda carga,
substituição, índice único, rejeições, verificações e falhas de conexão/escrita,
incluindo a garantia de não expor mensagens com credenciais. Esses testes não
substituem a comprovação de persistência em servidor real.
Ver `RELATORIO_MONGODB.md` para o estado observado do ambiente e da execução.

## Correção de idempotência no MongoDB 8.0.38

No servidor inspecionado, `ReplaceOne` sem `_id` reportou uma modificação mesmo
quando o BSON final persistido permaneceu idêntico. A reprodução com `_id`
explícito reportou zero modificações. Por isso o carregador preserva `_id` no
documento enviado, sem removê-lo, regenerá-lo ou recriar a coleção.

O estado final idempotente e a ausência de modificações são propriedades distintas.
Não se relaxou a verificação para aceitar apenas contagem estável. A implementação
agora também compara hashes do conteúdo persistido. Não execute cargas concorrentes
durante a demonstração; as consultas de auditoria não formam um snapshot transacional.

Diagnóstico somente leitura (compara tipos, campos e BSON de três jogos com o CSV):

```powershell
.\.venv\Scripts\python.exe -X utf8 diagnostico_idempotencia.py
.\.venv\Scripts\python.exe -X utf8 carga_mongodb.py --comprovar-idempotencia --relatorio outputs/mongodb/idempotencia_corrigida.json
```

O relatório anterior da carga falha é preservado usando um novo caminho de saída.
Resultados da correção e da nova execução estão em `RELATORIO_IDEMPOTENCIA.md`.

## Análises e visualizações a partir do MongoDB

Com MongoDB acessível e a ingestão concluída, execute:

```powershell
.\.venv\Scripts\python.exe -X utf8 analises_mongodb.py
```

Usa `MONGODB_URI` e o mesmo padrão local da carga. A fonte exclusiva é
`saveme_analytics.jogos_analiticos`: consultas com projeção de campos por PyMongo,
agregação de gêneros no MongoDB, tabulação em Pandas e gráficos em Matplotlib
com backend sem janela. O script não relê o CSV original nem escreve na coleção.
O hash BSON de todos os documentos e a definição dos índices são comparados antes
e depois. Execute sem cargas concorrentes: a auditoria não é um snapshot transacional.

Saídas em `outputs/analises/`, ignoradas pelo Git:

| Arquivo CSV | Conteúdo | Gráfico PNG |
|---|---|---|
| `ranking_avaliacoes.csv` | 15 maiores totais, positivas e negativas | Barras empilhadas |
| `ranking_percentual_positivo.csv` | 15 maiores taxas, mínimo de 100 avaliações | Barras |
| `generos_frequentes.csv` | 15 gêneros mais frequentes e percentual do catálogo | Barras |
| `distribuicao_precos.csv` | Faixas de preço cruzadas com categoria F2P explícita | Barras empilhadas |
| `distribuicao_descontos.csv` | Faixas de desconto e percentuais | Barras dos jogos com desconto |
| `descontos_percentuais.csv` | Distribuição por percentual exato de desconto | Sem gráfico adicional |
| `relacao_preco_avaliacao.csv` | Todos os jogos com preço válido e alguma avaliação | Dispersão |
| `ranking_popularidade.csv` | 15 maiores picos de jogadores simultâneos | Barras |

Os PNGs usam o mesmo nome-base dos CSVs correspondentes. `resumo.json` registra
indicadores, líderes, metodologia, exclusões, divergências em campos derivados,
hashes de preservação e tempo de execução. `--saida DIRETORIO` permite guardar
execuções separadas. Saídas existentes com os mesmos nomes são substituídas;
uma execução interrompida pode deixar arquivos parciais ou antigos, portanto
considere válidos apenas resultados de execução concluída e seu resumo correspondente.

Regras e interpretação:

- Total e taxa positiva são recalculados de `avaliacoes.positivas` e `negativas`
  armazenadas, com conferência dos derivados persistidos. Denominador zero gera
  ausência, não 0%. Ranking de percentual exige total >= 100, desempata por maior
  total e depois appid crescente. Ranking de quantidade desempata por appid.
- Gêneros são multivalorados; a agregação usa `$setUnion`, `$unwind` e `$group`.
  O mesmo jogo conta uma vez em cada gênero, e a soma dos percentuais pode superar
  100%. O denominador é o total de jogos da coleção.
- Faixas de preço: zero, `(0,10]`, `(10,20]`, `(20,50]`, acima de 50 e indisponível.
  Não se infere moeda. `catalogo.free_to_play_explicito` é uma dimensão separada;
  preço zero não comprova gratuidade comercial nem classificação Free To Play.
- Desconto positivo significa percentual > 0 e <= 100. O CSV apresenta proporções
  sobre o catálogo e sobre os jogos com desconto; o gráfico mostra apenas faixas
  positivas. Valores ausentes não viram desconto zero.
- A relação preço/avaliação inclui todos os jogos com preço válido e denominador
  positivo, sem exigir 100 avaliações (esse filtro vale apenas para o ranking).
  O eixo de preço usa `symlog` para incluir zero e reduzir a compressão por preços
  altos. Pearson e Spearman descrevem associação, não causalidade; a amostra,
  os gêneros e o número desigual de avaliações podem influenciar os resultados.
- Avaliações não são vendas. Proprietários estimados não são contagens exatas
  e não entram como vendas nestas análises. Pico de jogadores é o valor registrado
  no dataset, não uma medição atual.
- Ausências, infinitos, negativos e valores fora do domínio são excluídos apenas
  das análises afetadas, sem modificar documentos. Uma análise sem dados suficientes
  gera tabela vazia/gráfico informativo; correlações indefinidas ficam `null`.

Na primeira execução das análises, o documento original da N2 ainda não estava
no repositório. A auditoria posterior leu suas oito páginas, incluindo o diagrama
conceitual e o modelo agregado, agora disponíveis em
`docs/N2 Flaris - SaveMe Games (1)(1).pdf`. As consultas usam campos reais persistidos.
Resultados reais desta execução: `RELATORIO_ANALISES.md`.

Testes, incluindo regras de análise:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
```

## Análises complementares e auditoria da N2

```powershell
.\.venv\Scripts\python.exe -X utf8 analises_complementares.py
```

Fonte exclusiva: MongoDB. Saída separada em `outputs/analises/complementares/`,
preservando as análises anteriores. São gerados três CSVs, quatro PNGs e um resumo:

- `engajamento_resumo.csv`: quatro indicadores, separando média/mediana por jogo
  e período total/duas semanas. Informa quantidade de zeros, positivos, ausentes,
  estatísticas com zeros e estatísticas apenas dos valores positivos.
- `engajamento_ranking.csv`: até 15 jogos por indicador, sem misturar períodos.
- `comparacao_precos.csv`: grupos de preço zero e preço positivo; quantidades,
  avaliações somadas, médias/medianas de contagens e taxas, e taxa ponderada.
- `engajamento_cobertura.png`, `engajamento_valores_positivos.png`,
  `comparacao_preco_avaliacoes.png`, `comparacao_preco_percentuais.png`.
- `resumo.json`: metodologia, resultados e hashes de preservação da coleção.

A N2 p.2 exige validar unidades/períodos, mas não define a unidade dos tempos.
Por isso, os valores são mantidos na **unidade original não confirmada**, sem
conversão para horas/minutos. A janela de duas semanas é a da fonte de março de
2025, não as duas semanas anteriores à execução. Os zeros não são interpretados
automaticamente como ausência de jogadores ou de atividade.

Uma média das médias por jogo não é a média entre todos os jogadores; não há
tamanho da amostra por jogo para essa ponderação. O mesmo cuidado vale para
medianas. Total e duas semanas não são somados nem usados como série histórica.

Preço zero não significa classificação comercial Free To Play. Na comparação,
contagens de avaliações incluem zeros válidos; médias/medianas percentuais
excluem denominadores zero. A taxa ponderada é `100 * soma(positivas)/soma(total)`;
a média das taxas dá peso igual a cada jogo com alguma avaliação. Os dois
indicadores são apresentados separados, sem confundir avaliações com vendas.

O documento da N2 foi recuperado de uma cópia local na Área de Trabalho e copiado
sem alteração de bytes para `docs/`, pois o caminho informado não estava presente
no workspace. Origem, hash e comparação por página constam em `AUDITORIA_FINAL_N2.md`.
Relatórios anteriores que registram a ausência da N2 descrevem o momento daquela
execução; não devem ser interpretados como situação atual.

Auditoria de conformidade, diferenças e resultados: `AUDITORIA_FINAL_N2.md`.
Roteiro de entrega e demonstração: `CHECKLIST_ENTREGA_N3.md`.

## Análises finais: positivas, proprietários estimados e gêneros

```powershell
.\.venv\Scripts\python.exe -X utf8 analises_finais.py
```

Usa exclusivamente os documentos do MongoDB e grava uma saída separada em
`outputs/analises/finais/`, preservando os resultados anteriores:

- `ranking_positivas.csv` e `.png`: 15 jogos ordenados por positivas, não por
  positivas + negativas. Empate por appid; o CSV mostra também negativas e total.
- `proprietarios_faixas.csv` e `.png`: quantidade de jogos por intervalo de
  proprietários estimados, com limites e percentuais. Não usa ponto médio nem
  soma os limites como se fossem proprietários/vendas exatos.
- `ranking_faixas_proprietarios.csv`: 15 jogos ordenados pelo limite inferior,
  depois superior e appid. Trata-se de ordenação descritiva de intervalos;
  faixas sobrepostas não permitem uma classificação exata de proprietários.
  `0 - 0` é preservado, sem afirmar que comprova ausência de proprietários.
- `comparacao_generos.csv`: todos os gêneros, quantidade de jogos, preços médios/
  medianos, contagens de elegíveis, média/mediana de taxas e taxa ponderada.
- `comparacao_generos.png`: os 15 gêneros mais frequentes, preço mediano e média
  de taxas entre jogos com pelo menos 100 avaliações. O CSV também inclui a
  população com qualquer denominador positivo para comparar sensibilidade.
- `resumo.json`: resultados reais, metodologia, duração e hashes de preservação.

Jogos podem pertencer a vários gêneros, mas só contam uma vez dentro do mesmo
gênero. Jogos sem avaliações entram na quantidade do catálogo e no preço, mas
não nas médias das taxas. Uma taxa real de 0% continua válida. A média dá o mesmo
peso a cada jogo; a ponderada usa soma de positivas/soma do total. Moeda não
confirmada, gêneros multivalorados e amostras diferentes limitam a interpretação.

Última execução: 89.618 jogos, 15 faixas válidas e 33 gêneros; 70 testes aprovados.
Ver `RELATORIO_FINAL_PUBLICACAO.md` para números e revisão de publicação.
`ARQUIVOS_PUBLICACAO.txt` contém a lista fechada de arquivos; os comandos
preparados, ainda não executados, estão em `PREPARACAO_PUBLICACAO.md`.

## Apresentação N3 — evidências e roteiro

- [Roteiro de 8 a 12 minutos, comandos e perguntas do professor](docs/ROTEIRO_DEMONSTRACAO_N3.md).
- [Resumo curto, resultados reais e 70 testes](docs/evidencias/README.md).
- [Carga inicial, segunda execução idempotente e verificação atual](docs/evidencias/execucao_validada.json).
- [Dois documentos reais minimizados, sem dados privados](docs/evidencias/documentos_reais.json).
- Gráficos selecionados: [avaliações](docs/evidencias/ranking_avaliacoes.png),
  [preços](docs/evidencias/distribuicao_precos.png),
  [gêneros](docs/evidencias/generos_frequentes.png),
  [popularidade](docs/evidencias/ranking_popularidade.png).
- [Origem e obtenção do dataset](docs/ORIGEM_DATASET.md).
- [Relatório desta preparação](docs/RELATORIO_PREPARACAO_APRESENTACAO.md).

As quatro imagens são cópias pequenas das saídas reais de `outputs/`, com hashes
de proveniência. Outputs completos continuam ignorados. A apresentação deve
distinguir consulta ao vivo de evidência de execução anterior, especialmente
se Docker ou internet falharem. Não é necessário repetir toda a carga no palco.
