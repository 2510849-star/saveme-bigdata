# SaveMe Games — preparação e validação inicial da N3

Inspeção realizada em 17/11/2026, somente para diagnóstico. Não houve limpeza,
transformação persistida, conexão com MongoDB, commit ou push.

## Ambiente e reprodução

- Python 3.12.14, ambiente `.venv` isolado, sem pacotes globais habilitados.
- Dependências diretas testadas: pandas 3.1.1, pymongo 4.20.0 e matplotlib 3.11.2.
- `requirements.txt` fixa essas versões. Dependências transitivas são instaladas
  automaticamente pelo pip; nenhuma outra dependência direta foi adicionada.
- `python -m pip check`: `No broken requirements found.`
- O script original `analise_dataset.py` foi preservado e executado com sucesso.
- Executar os comandos abaixo na raiz do repositório. Não é necessário ativar
  o ambiente nem alterar a política de execução do PowerShell.

Comandos principais executados com sucesso (caminho pessoal do Python anonimizado
para publicação; use a instalação completa de Python 3.12 disponível no seu computador):

```powershell
Test-Path -LiteralPath data/games_march2025_cleaned.csv -PathType Leaf
& '<caminho-do-python-3.12>' -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 analise_dataset.py
.\.venv\Scripts\python.exe -X utf8 validacao_inicial.py
.\.venv\Scripts\python.exe -X utf8 validacao_inicial.py | Tee-Object -FilePath validacao_inicial.log
.\.venv\Scripts\python.exe -m pip check
git check-ignore data/games_march2025_cleaned.csv .venv/pyvenv.cfg .env .env.local exemplo.tmp
git diff -- analise_dataset.py
git diff --check
git status --short
```

Em outro computador com Python completo instalado, criar o ambiente com
`python -m venv .venv` e executar os comandos com `.venv\Scripts\python.exe`.
O caminho do interpretador foi omitido por ser específico do computador. A `.venv` é local
e deve ser recriada em outras máquinas, não copiada ou versionada.

Erros encontrados e resolvidos:

1. `python --version`: o atalho em WindowsApps não pôde ser executado.
2. `py --version`: launcher não encontrado.
3. O Python 3.13.5 do pgAdmin respondeu a `--version`, mas
   `-m venv .venv` falhou com `No module named venv`. Essa instalação não foi alterada.
4. A primeira instalação via pip falhou por restrição de rede (`WinError 10013`),
   terminando com erro de resolução de pacotes. A repetição com acesso de rede
   autorizado instalou as três bibliotecas e suas dependências com sucesso.
5. A importação de Matplotlib funcionou, mas avisou que o diretório padrão de
   cache não era gravável. Uma nova verificação das três importações, sem aviso,
   usou cache dentro do ambiente ignorado pelo Git:

   ```powershell
   $env:MPLCONFIGDIR = Join-Path (Get-Location) '.venv\matplotlib-cache'
   .\.venv\Scripts\python.exe -c "import pandas, pymongo, matplotlib; print('Importações OK:', pandas.__version__, pymongo.version, matplotlib.__version__)"
   ```

## Fonte e integridade

- Arquivo: `data/games_march2025_cleaned.csv`, 468.641.107 bytes.
- Leitura: `pd.read_csv(..., low_memory=False)`.
- Dimensões reais: **89.618 linhas × 47 colunas**, iguais à referência da N2.
- SHA-256 antes e depois do diagnóstico:
  `04d8df2778aaa8f8b575934b7072d55224d37a2ded23e8261583f0fcf668dfab`.
- O CSV não foi regravado e seu conteúdo permaneceu idêntico.
- `data/` permanece ignorado pelo Git.

## Esquema e valores ausentes

Tipos inferidos por `info()` no Pandas 3.1.1: 19 colunas `int64`, duas `float64`,
três `bool` e 23 `str`. `release_date` permanece textual: não foi convertida
nem validada semanticamente como data nesta etapa.

| Coluna | Tipo Pandas | Nulos |
|---|---|---:|
| appid | int64 | 0 |
| name | str | 0 |
| release_date | str | 0 |
| required_age | int64 | 0 |
| price | float64 | 0 |
| dlc_count | int64 | 0 |
| detailed_description | str | 197 |
| about_the_game | str | 220 |
| short_description | str | 120 |
| reviews | str | 79.217 |
| header_image | str | 0 |
| website | str | 48.504 |
| support_url | str | 45.508 |
| support_email | str | 10.820 |
| windows | bool | 0 |
| mac | bool | 0 |
| linux | bool | 0 |
| metacritic_score | int64 | 0 |
| metacritic_url | str | 86.071 |
| achievements | int64 | 0 |
| recommendations | int64 | 0 |
| notes | str | 72.975 |
| supported_languages | str | 0 |
| full_audio_languages | str | 0 |
| packages | str | 0 |
| developers | str | 0 |
| publishers | str | 0 |
| categories | str | 0 |
| genres | str | 0 |
| screenshots | str | 0 |
| movies | str | 0 |
| user_score | int64 | 0 |
| score_rank | float64 | 89.579 |
| positive | int64 | 0 |
| negative | int64 | 0 |
| estimated_owners | str | 0 |
| average_playtime_forever | int64 | 0 |
| average_playtime_2weeks | int64 | 0 |
| median_playtime_forever | int64 | 0 |
| median_playtime_2weeks | int64 | 0 |
| discount | int64 | 0 |
| peak_ccu | int64 | 0 |
| tags | str | 0 |
| pct_pos_total | int64 | 0 |
| num_reviews_total | int64 | 0 |
| pct_pos_recent | int64 | 0 |
| num_reviews_recent | int64 | 0 |

Existem **433.211 células nulas**. Todas as 89.618 linhas têm pelo menos um nulo.
Portanto, remover toda linha com algum nulo eliminaria o dataset inteiro.
As contagens usam o reconhecimento padrão de ausências de `read_csv()`.
Listas vazias e sentinelas numéricas não são contabilizadas por `isna()`.

## Identificação e campos numéricos prioritários

- `appid`: 89.618 identificadores distintos, nenhum ausente, zero, negativo,
  fracionário ou repetido. Intervalo: 20 a 3.542.350.
- Linhas integralmente duplicadas: **0**.
- `appid`, `discount`, `positive` e `negative` contêm valores Python `int`;
  `price` contém valores Python `float`, em todas as linhas.
- Nos cinco campos não há valores presentes não numéricos, infinitos ou negativos.
- `discount`: intervalo 0 a 100; nenhum valor fora dessa faixa ou fracionário.
- `positive` e `negative`: contagens inteiras, máximos de 7.480.813 e 1.135.108.
- 17.055 jogos têm `positive == 0` e `negative == 0`: uma futura taxa de aprovação
  precisará tratar denominador zero sem atribuir aprovação zero artificialmente.
- `price`: mínimo 0, mediana 4,99, média aproximada 7,309623 e máximo 999,98.
  Há 14.160 preços zero. Preço zero e preço alto não comprovam erro ou gratuidade.
  Moeda e significado comercial devem ser confirmados na documentação da fonte.
- Os maiores preços incluem appids 2504210 e 2499620 (999,98), 1200520 (999,00),
  3013840 (500,00) e 253670 (299,90). Não foram removidos como outliers.

## Listas textuais e proprietários estimados

`genres`, `developers`, `publishers` e `estimated_owners` são `str`, não listas
ou quantidades numéricas nativas. As três primeiras foram inspecionadas com
`ast.literal_eval`, sem executar o conteúdo e sem substituir as colunas.

| Campo | Listas com textos não vazios | Listas vazias `[]` | Listas com item vazio |
|---|---:|---:|---:|
| genres | 89.406 | 212 | 0 |
| developers | 89.397 | 221 | 0 |
| publishers | 89.065 | 547 | 6 |

Nenhuma dessas três colunas contém texto que falhe na leitura como lista.
Os seis publishers problemáticos são `['']`, nos appids 385770, 270010,
2314430, 889530, 938660 e 759830.

Todas as 89.618 faixas de `estimated_owners` seguem o formato
`inteiro não negativo - inteiro não negativo`; nenhuma está invertida.
A faixa `0 - 20000` ocorre 59.320 vezes, e `0 - 0`, 8.418 vezes.
São estimativas por intervalo: não representam uma contagem exata de proprietários.

## Outras inconsistências e pontos de atenção

- `required_age = -1` em uma linha: appid 2731870, `Ys X: Nordics`.
- `pct_pos_total` e `num_reviews_total` têm **36.419 valores -1 em cada coluna**.
- `pct_pos_recent` e `num_reviews_recent` têm **82.931 valores -1 em cada coluna**.
  Esses valores sugerem sentinelas de indisponibilidade; seu significado precisa
  ser confirmado na fonte. Não devem entrar como valores negativos reais em médias.
- Nenhuma outra coluna numérica tem negativos. Não há valores acima de 100 em
  `pct_pos_total`, `pct_pos_recent`, `metacritic_score` ou `user_score`.
- Há espaços externos em `detailed_description` (41.566), `about_the_game`
  (41.518), `short_description` (6), `reviews` (10.163) e `notes` (1.942).
- Cinco nomes coincidem com marcadores textuais: `none` nos appids 385020,
  398970 e 339860; `Unknown` nos appids 996730 e 1968520. Podem ser títulos
  legítimos e exigem revisão, não substituição automática por nulo.
- Também há marcadores textuais a revisar em `detailed_description` (1),
  `about_the_game` (1), `short_description` (1), `support_url` (10) e
  `support_email` (2). Isso não prova que sejam dados ausentes.

## Recomendações para a próxima etapa

1. Definir regras explícitas de esquema e integridade de `appid`, preservando-o
   como identificador inteiro obrigatório e único.
2. Confirmar o significado de `-1`, zeros de scores e preços na fonte antes de
   converter sentinelas para ausentes. Tratar a idade negativa como pendência.
3. Planejar a conversão segura das listas textuais, distinguindo `[]` de `['']`.
   Preservar os valores brutos para rastreabilidade.
4. Manter `estimated_owners` original e, posteriormente, derivar limites inferior
   e superior, sem inventar uma contagem exata.
5. Definir tratamento de nulos por coluna. Usar `fillna()` apenas onde houver
   regra justificada; não preencher todas as ausências com zero nem descartar
   todas as linhas incompletas.
6. Definir regras para datas, conteúdo textual/HTML, moeda e indicadores derivados.
   A validação atual não atesta toda a semântica das 47 colunas.

Nenhuma dessas transformações foi aplicada nesta etapa. O próximo passo é
documentar essas regras de tratamento antes de implementá-las.

## Arquivos e verificação final

- Alterado: `.gitignore`, preservando `data/` e adicionando proteção de `.env`,
  variantes `.env.*` (com exceção de `.env.example`), `.venv/` e temporários.
- Criados: `requirements.txt`, `validacao_inicial.py` e este relatório.
- Criados localmente e ignorados: `.venv/` e `validacao_inicial.log`.
- Preservados: `analise_dataset.py` e o CSV original.
- `git check-ignore` confirmou a exclusão do CSV, ambiente, segredos e temporários.
- `git diff -- analise_dataset.py` não apresentou alterações.
- Não foi implementada nem executada carga no MongoDB.
