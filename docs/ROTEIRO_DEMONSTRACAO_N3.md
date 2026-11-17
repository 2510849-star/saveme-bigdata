# Demonstração N3 — SaveMe Games Big Data (8 a 12 minutos)

Disciplina: Desenvolvimento com Linguagens Disruptivas I. Apresentação: **17/11**.
Roteiro-base de **10 minutos**, com um minuto de margem em cada direção.
Objetivo: mostrar ingestão implementada, funcionamento real, saídas e reprodução;
não acrescentar funcionalidades nem prometer uma aplicação transacional pronta.

## Preparar antes da apresentação

1. Abrir PowerShell na raiz do repositório e ter a `.venv` já instalada.
2. Ter o CSV validado em `data/`, gráficos em `docs/evidencias/` e evidências JSON
   disponíveis localmente. Não depender de downloads durante os dez minutos.
3. Validar previamente o MongoDB. No ambiente ensaiado, usar a instância isolada
   de reprodução em **27018**, já carregada, sem apontar para o MongoDB principal.
   Mesmo banco/coleção lógicos, outro servidor/volume. Não criar nova instância
   concorrente na mesma porta nem limpar dados para simular uma primeira carga.
4. Fechar arquivos com credenciais, terminal com histórico privado e abas sem
   relação com a apresentação. URI com autenticação nunca deve aparecer na tela.
5. Deixar abertos README, N2 (páginas 3–8), código e quatro gráficos. Conferir os
   links das evidências antes da aula.

Pré-checagem, somente leitura:

```powershell
git rev-parse --short HEAD
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip check
$env:MONGODB_URI = 'mongodb://127.0.0.1:27018/'
.\.venv\Scripts\python.exe -X utf8 carga_mongodb.py --verificar --relatorio outputs/demonstracao/verificacao.json
```

Esperado: consulta concluída, 89.618 documentos, 89.618 appids distintos,
zero grupos duplicados e índice único. Esse comando **não carrega dados**.
Se 27018 não estiver disponível, preparar previamente um servidor isolado seguindo
o README. Não improvisar parada/remoção de volumes durante a aula. A porta 27017
do Compose padrão não deve ser confundida com o ambiente isolado do ensaio.

## 0:00–1:00 — Problema, escopo e aderência

Fala sugerida: “Implementamos o pipeline analítico proposto na N2 para um snapshot
Steam de março de 2025: CSV → leitura → validação → tratamento → transformação →
MongoDB → análises → tabelas e gráficos. São 89.618 jogos e 47 colunas de entrada.”

Mostrar o fluxo da N2 p.3 e explicar a distinção:

- **Aqui:** pipeline analítico, banco `saveme_analytics`, coleção `jogos_analiticos`.
- **Aplicação SaveMe:** usuários, listas de desejos, lojas, ofertas e histórico
  transacionais da p.5; não implementados neste repositório nem alimentados por
  dados inventados. MongoDB não substitui o PostgreSQL da aplicação.

Mostrar o link GitHub no README e as instruções. A revisão-base publicada é
`6300343`; as novas evidências/documentação ainda precisam ser publicadas após
autorização. Não afirmar que arquivos novos já estão no remoto antes de conferir.

## 1:00–2:15 — Fonte e etapas implementadas

Mostrar [ORIGEM_DATASET.md](ORIGEM_DATASET.md), a versão 2 identificada e o SHA-256.
Não chamar a fonte de dados ao vivo nem afirmar moeda/unidades não confirmadas.

Comandos curtos, sem modificar o CSV:

```powershell
Get-FileHash -LiteralPath data/games_march2025_cleaned.csv -Algorithm SHA256
.\.venv\Scripts\python.exe -X utf8 analise_dataset.py
Select-String -Path pipeline_tratamento.py -Pattern '^def validar_esquema','^def validar_appids','^def transformar_jogo','^def iterar_documentos'
```

Esperado: hash `04d8df2778aaa8f8b575934b7072d55224d37a2ded23e8261583f0fcf668dfab`,
shape `(89618, 47)`, zero duplicações por appid. O hash/leitura leva alguns segundos.
Explicar: não houve `dropna()` global; listas usam `ast.literal_eval`; sentinelas
mantêm bruto/tratado; taxa só é calculada com denominador positivo.

**Para a versão de oito minutos:** mostrar o hash/shape já registrados, identificando
claramente como evidência anterior, e avançar para a consulta real abaixo.

## 2:15–4:15 — MongoDB ao vivo: conexão, contagem, índice, documento e agregação

Executar o bloco abaixo exatamente como está, na raiz do projeto. As mensagens
da URI não incluem credenciais; o endereço consultado deve ser o isolado, 27018.

```powershell
$env:MONGODB_URI = 'mongodb://127.0.0.1:27018/'
@'
import json
from carga_mongodb import conectar, BANCO, COLECAO
c = conectar()
try:
    assert c.address == ('127.0.0.1', 27018)
    k = c[BANCO][COLECAO]
    print('Endpoint confirmado:', c.address)
    print('Banco/colecao:', BANCO, COLECAO)
    print('Documentos:', k.count_documents({}))
    indices = {n: v for n, v in k.index_information().items()
               if list(v['key']) == [('appid', 1)]}
    print('Indice appid:', json.dumps(indices))
    doc = k.find_one({'appid': 730}, {'_id': 0, 'appid': 1, 'nome': 1,
                        'preco': 1, 'avaliacoes.positivas': 1,
                        'avaliacoes.negativas': 1, 'avaliacoes.total': 1,
                        'avaliacoes.taxa_positivas_percentual': 1})
    print('Documento real:', json.dumps(doc, ensure_ascii=False, indent=2))
    grupos = list(k.aggregate([
        {'$project': {'genero': {'$setUnion': ['$catalogo.generos', []]}}},
        {'$unwind': '$genero'},
        {'$group': {'_id': '$genero', 'jogos': {'$sum': 1}}},
        {'$sort': {'jogos': -1, '_id': 1}}, {'$limit': 5}
    ]))
    print('Agregacao real:', json.dumps(grupos, ensure_ascii=False, indent=2))
finally:
    c.close()
'@ | .\.venv\Scripts\python.exe -X utf8 -
```

Resultados esperados:

- 89.618 documentos; índice appid com `unique: true`.
- Counter-Strike 2: 7.480.813 positivas, 1.135.108 negativas, total 8.615.921 e
  taxa aproximada de 86,8255%. Não confundir positivas com total ou vendas.
- Indie 63.189; Casual 38.699; Action 36.842; Adventure 35.452; Simulation 18.570.
- Explicar `$setUnion` para evitar duplicação dentro do mesmo jogo, `$unwind`
  para gênero multivalorado e `$group` para contar. Percentuais podem somar >100%.

## 4:15–5:30 — Carga e idempotência sem esperar toda a carga

Explicar o código: `MongoClient` lê `MONGODB_URI`; upsert por appid em lotes,
índice único, preservação de `_id` e comparação de estado completo.

Mostrar os resultados realmente executados, não uma simulação ao vivo:

```powershell
$e = Get-Content docs/evidencias/execucao_validada.json -Raw -Encoding UTF8 | ConvertFrom-Json
$e.carga_inicial_e_idempotencia.cargas | Format-Table execucao,inseridos,atualizados,inalterados,rejeitados,duracao_segundos
$e.carga_inicial_e_idempotencia.idempotencia_comprovada
$e.verificacao_atual | Format-List
```

Esperado: primeira 89.618 inseridos; segunda zero inseridos/modificados e 89.618
inalterados; rejeitados zero; idempotência verdadeira. A evidência veio da reprodução
limpa: duas cargas e auditorias levaram cerca de 327 s. Não executá-las como
requisito dos dez minutos. Não apagar o banco para repetir o teste.

Se o professor pedir reprodução completa, este é o comando real para um momento
com tempo disponível, **não foi executado nesta preparação de evidências**:

```powershell
.\.venv\Scripts\python.exe -X utf8 carga_mongodb.py --comprovar-idempotencia --relatorio outputs/demonstracao/idempotencia.json
```

Não inferir sucesso apenas pela contagem: os relatórios também verificam hash
BSON estável e zero modificações na segunda passagem. Upserts ainda são enviados.

## 5:30–7:30 — Quatro saídas analíticas legíveis

```powershell
Invoke-Item docs/evidencias/ranking_avaliacoes.png
Invoke-Item docs/evidencias/distribuicao_precos.png
Invoke-Item docs/evidencias/generos_frequentes.png
Invoke-Item docs/evidencias/ranking_popularidade.png
```

Falas de 20–30 segundos por gráfico:

1. Avaliações: distinguir positivas, negativas e total; ranking não mede vendas.
2. Preços: 14.160 preços zero e 8.867 categorias Free To Play explícitas; os dois
   critérios são diferentes. Moeda não foi presumida.
3. Gêneros: Indie 63.189; os grupos se sobrepõem porque o catálogo é multivalorado.
4. Popularidade: pico de CS2 1.212.356 na fonte; não são usuários atuais.

Mencionar as demais análises, sem abrir 14 imagens: engajamento separa média/
mediana e total/duas semanas; proprietários são faixas; comparação por gênero
exclui jogos sem avaliações e oferece sensibilidade com mínimo de 100.
São 15 CSVs, 14 PNGs e três resumos no conjunto completo, gerados do MongoDB.

**Extensão opcional para até 12 minutos**, se o servidor estiver saudável:

```powershell
.\.venv\Scripts\python.exe -X utf8 analises_finais.py --saida outputs/demonstracao/finais
```

Leitura apenas; no ensaio levou cerca de 42 s. Mostrar o novo resumo/CSV sem
alterar a coleção. Não executar se isso comprometer o tempo ou a contingência.

## 7:30–8:30 — Testes automatizados

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
$LASTEXITCODE
```

Esperado: `Ran 70 tests`, `OK`, código 0. Mostrar um teste de denominador zero
e um de retomada/idempotência. Explicar que mocks verificam regras e erros, mas
a comprovação real é a execução em banco independente, registrada separadamente.
Se o terminal destacar stderr em outra cor, avaliar `OK` e código de saída;
`unittest` usa stderr para o relatório, mesmo quando passa.

## 8:30–10:00 — Limitações, GitHub e encerramento

Apresentar o repositório, os comandos do README e a origem do CSV. Dizer que a
reprodução funcional passou com ressalvas: CSV fornecido por cópia, porta do
ensaio ajustada, mesmo host; não se validou outro sistema operacional nem se
repetiu download integral remoto nesta preparação. A URL Kaggle agora foi
identificada com metadados e comparações parciais, mantendo validação SHA-256.

Encerrar ligando cada requisito às evidências: pipeline implementado, consultas
ao vivo, saídas reais, testes, código GitHub e instruções. A N2 era proposta;
não usar seu texto futuro para afirmar que usuários/lojas/histórico foram feitos.
Não afirmar que a apresentação/entrega já aconteceu apenas porque o roteiro existe.

## Plano alternativo

| Problema | Como demonstrar com honestidade |
|---|---|
| Internet indisponível | Usar clone, venv, imagem e CSV preparados; abrir evidências locais. Não reinstalar pacotes ao vivo |
| Docker/MongoDB indisponível | Informar a falha. Mostrar JSON, documentos minimizados, hashes e quatro gráficos como execução anterior. Rodar os testes locais com mocks; não chamá-los de consulta real ao vivo |
| CSV indisponível | Não inventar entrada. Mostrar origem/hash e resultados anteriores; consultas ao banco já carregado podem continuar |
| Pouco tempo | Rota de oito minutos: pular leitura completa do CSV e reexecução opcional da análise; manter consulta real, evidências de carga, gráficos e testes |

Para a contingência, abrir sem internet:

```powershell
Get-Content docs/evidencias/README.md -Encoding UTF8
Get-Content docs/evidencias/documentos_reais.json -Encoding UTF8
```

Não instalar programas, trocar para o banco principal, apagar coleções ou remover
volumes como tentativa de recuperação durante a aula.

## Perguntas prováveis do professor

**Por que MongoDB se a aplicação usa PostgreSQL?** Responsabilidades distintas:
documentos analíticos agregados por jogo versus operações transacionais da aplicação.

**O que torna o caso Big Data?** A N2 propõe um pipeline para uma base de 89.618
registros e cerca de 469 MB, com atributos heterogêneos. A solução é local e não
distribuída; esse volume sozinho não demonstra escala massiva, streaming ou cluster.

**Por que Pandas e não só MongoDB?** MongoDB é fonte persistida e executa consultas/
agregações; Pandas tabula dados projetados e Matplotlib gera saídas. A carga lê
em lotes; as análises carregam projeções do catálogo, não todos os textos longos.

**O pipeline usa insert_many?** Usa PyMongo e `bulk_write` com `ReplaceOne(upsert=True)`
para permitir reexecução por appid sem duplicar. `insert_many` simples não resolveria
a retomada/idempotência demonstrada. As operações Pandas seguem a abordagem acadêmica.

**O CSV cleaned não dispensa tratamento?** Não: há 433.211 células nulas, listas
textuais, idade negativa e sentinelas; foram definidas regras por campo.

**Por que não remover todas as linhas com nulos?** Todas têm algum nulo; isso
apagaria a base analítica inteira. A ausência opcional não invalida todo jogo.

**Sem avaliações significa 0% positivo?** Não. Denominador zero produz null;
0% é válido quando há avaliações e nenhuma é positiva.

**Preço zero significa Free To Play?** Não necessariamente. O preço observado
e a categoria explícita são apresentados separadamente.

**Proprietários estimados equivalem a vendas?** Não. São intervalos da fonte;
não se calcula contagem exata ou receita com seus limites.

**Qual a unidade dos tempos?** Não foi confirmada; os valores são mantidos na
unidade original. Total e duas semanas são períodos distintos, não uma série histórica.

**Como sabe que a segunda carga não alterou dados?** Mesma origem, índice único,
89.618 appids, hashes BSON iguais e zero modificações; `_id` existente é preservado.

**E se uma carga falhar no meio?** Não é transacional. Há relatório de progresso/
incerteza e reexecução idempotente por appid; a retomada foi testada. Não se promete
rollback de todos os lotes nem ausência de escritas parciais.

**Os gráficos são de consultas reais?** Sim, produzidos do MongoDB e reproduzidos
em instância independente; as quatro cópias têm hashes de origem registrados.

**O que ainda falta?** Publicar estas novas evidências após revisão/autorização,
ensaiar a apresentação e conferir o arquivo obtido diretamente do Kaggle pelo
SHA-256. Unidades/moeda/sentinelas continuam limitações; não há multilojas nem histórico.
