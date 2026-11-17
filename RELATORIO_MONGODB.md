# N3 — carga MongoDB: implementação e verificação

Atualização posterior: o servidor tornou-se acessível. A falha de comprovação
de idempotência e sua correção estão em `RELATORIO_IDEMPOTENCIA.md`.
As observações abaixo são mantidas como histórico da primeira verificação.

Verificação realizada em 17/11/2026. Não houve commit, push, instalação de
programas do sistema ou conexão ao PostgreSQL.

## Ambiente observado

| Item | Resultado real |
|---|---|
| Docker CLI | Instalado: 29.5.3, build d1c06ef |
| Docker Compose | Instalado: v5.1.4 |
| Docker Engine | Não acessível; `docker info` falhou ao abrir o pipe `docker_engine` |
| Serviço `com.docker.service` | Parado (`Stopped`) |
| MongoDB servidor local | Não encontrado no PATH nem no caminho padrão inspecionado; nenhum listener em 27017 foi identificado |
| mongosh | Instalado; sua presença não comprova servidor MongoDB |
| `MONGODB_URI` no processo | Não definida; nenhum segredo foi exibido |
| Ping em `127.0.0.1:27017` | Falhou por timeout de seleção de servidor |
| Compose preparado | `compose.yaml`, configuração sintaticamente validada |

O Docker emitiu aviso de acesso negado ao arquivo de configuração do usuário;
seu conteúdo não foi lido nem exposto. O serviço parado e a ausência do pipe
impediram confirmar um Engine funcional. Não foi iniciado container ou programa
do sistema. O README explica como iniciar o Docker Desktop e o serviço MongoDB.

A tentativa de carga com `--comprovar-idempotencia` falhou no ping inicial,
antes de ler ou escrever dados no banco, em **5,082 segundos**.
Uma consulta independente `--verificar`, fora da restrição de rede do sandbox,
também falhou no ping, em **5,113 segundos**.

**Quantidade gravada por essas tentativas: nenhum documento.** O total existente
na coleção é **desconhecido**, pois não houve conexão. Não foram criados banco,
coleção ou índice em servidor nesta sessão. A contagem, os três jogos de exemplo
e a segunda carga em MongoDB real permanecem pendentes; não se confundem com os
testes simulados descritos abaixo.

Os registros reais das tentativas estão em `outputs/mongodb/carga.json` e
`outputs/mongodb/verificacao.json`, ignorados pelo Git: `status: falhou`,
`conexao_confirmada: false` e `cargas: []`, sem contagens fabricadas.

## Implementação preparada

- `carga_mongodb.py`: usa PyMongo `MongoClient`, ping e timeouts; lê a conexão de
  `MONGODB_URI`, com padrão `mongodb://127.0.0.1:27017/`.
- Destino fixo: `saveme_analytics.jogos_analiticos`, separado da aplicação.
- Cria índice único completo em `appid` ou reutiliza um equivalente, inclusive
  com outro nome. Índice parcial/esparso não é aceito como prova global.
- Escreve lotes de até 1.000 `ReplaceOne(..., upsert=True)`, configuráveis, com
  `bulk_write(ordered=False)`. Não exclui jogos que já existam fora do CSV.
- `iterar_documentos()` em `pipeline_tratamento.py` centraliza a leitura,
  validação, tratamento, rejeições e verificação BSON já existentes. A API
  `processar_csv()` foi mantida. Nenhuma regra de tratamento foi duplicada.
- Não lê as três amostras para carregar: percorre o CSV completo incrementalmente.
- Relatórios registram inseridos, correspondentes, modificados de fato,
  inalterados, rejeitados, lotes confirmados e duração. Erros parciais de bulk
  preservam apenas as contagens retornadas, sem conteúdo de documentos.
- Falhas de conexão durante a escrita marcam resultado incerto do último lote.
  A carga não é transacional; reexecução por appid permite retomar sem duplicar.
- Verificação agrega appids distintos/duplicados, conta a coleção, consulta três
  exemplos e inspeciona o índice. A flag de idempotência executa duas cargas e
  exige origem idêntica, contagem estável e zero inserções/alterações na segunda.
- Credenciais/URI e mensagens brutas do driver não entram nos relatórios/logs.

## Testes executados

**31 testes aprovados**: os 16 anteriores e 15 novos testes de persistência.
Os novos testes usam mocks e uma coleção simulada, sem servidor ou dependências
adicionais. A execução final também habilitou avisos de recursos como erros.

Verificações de persistência simulada:

- Cinco documentos divididos em lotes `[2, 2, 1]` na primeira carga.
- Primeira carga simulada: 5 inseridos, 0 modificados.
- Segunda carga simulada: 0 inseridos, 0 modificados, 5 inalterados e total 5.
- Documento com nome alterado: uma modificação, sem duplicar appid; campo obsoleto
  é removido pela substituição.
- Rejeição de lista inválida reutiliza o tratamento existente.
- Índices, consulta de três exemplos, modo somente leitura, conexão por ambiente,
  fechamento do cliente e sanitização de erros foram testados.
- Falhas de índice, bulk parcial e rede foram simuladas e contabilizadas.

Na primeira execução da nova suíte houve avisos de arquivo aberto quando uma
escrita falhava durante a iteração. Foram corrigidos com fechamento explícito do
iterador/leitor CSV; a suíte final passou sem esses avisos. Uma sondagem inicial
inline do MongoDB também teve erro de aspas no PowerShell; foi corrigida e as
sondagens posteriores efetivamente alcançaram a tentativa de ping.

## Regressão com o CSV real

Após introduzir o iterador compartilhado, foi executado novamente o tratamento
com saída separada em `outputs/regressao_mongodb/`, preservando os relatórios
originais:

- Entrada: **89.618**, 47 colunas, 89.618 appids distintos.
- Rejeições: **0**; documentos transformados e verificados como BSON: **89.618**.
- SHA-256 antes/depois:
  `04d8df2778aaa8f8b575934b7072d55224d37a2ded23e8261583f0fcf668dfab`.
- Comparação programática: relatório JSON e três amostras iguais aos produzidos
  anteriormente em `outputs/tratamento/`.

Esses resultados comprovam a regressão de tratamento, **não persistência real**.

## Comandos principais executados

```powershell
docker --version
docker compose version
docker info --format '{{.ServerVersion}}'
Get-Service -Name com.docker.service
Get-Command docker,mongod,mongosh -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 27017 -State Listen -ErrorAction SilentlyContinue
docker compose config --quiet
.\.venv\Scripts\python.exe -X utf8 carga_mongodb.py --comprovar-idempotencia
.\.venv\Scripts\python.exe -X utf8 carga_mongodb.py --verificar --relatorio outputs/mongodb/verificacao.json
.\.venv\Scripts\python.exe -X utf8 -W error::ResourceWarning -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 pipeline_tratamento.py --saida outputs/regressao_mongodb
git diff --check
git status --short
```

Também foram executados um ping PyMongo direto com timeout de 3 segundos e a
comparação programática dos relatórios/amostras de tratamento.

## Arquivos desta etapa

Criados: `carga_mongodb.py`, `compose.yaml`, `.env.example`,
`tests/test_carga_mongodb.py`, `tests/__init__.py` e este relatório.

Alterados: `pipeline_tratamento.py` (extração do iterador e fechamento do leitor)
e `README.md` (MongoDB, inicialização, carga, verificação e limitações).

Preservados nesta etapa: CSV, scripts de análise/validação, testes anteriores,
relatórios anteriores, `.gitignore` e `requirements.txt`. As dependências já
existentes foram suficientes. `outputs/` já era ignorado pelo Git.

## Próximo passo para comprovação real

1. Abrir o Docker Desktop e aguardar Engine funcional (`docker info`).
2. Executar `docker compose up -d --wait` e conferir `docker compose ps`.
3. Executar `carga_mongodb.py --comprovar-idempotencia` pelo Python da `.venv`.
4. Executar `--verificar` e revisar os relatórios de contagem, unicidade, exemplos
   e segunda carga. Só então registrar a quantidade efetivamente persistida.

Não há necessidade de instalar pacotes Python adicionais para essas ações.
