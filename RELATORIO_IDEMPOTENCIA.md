# N3 — correção de idempotência

Diagnóstico em 17/11/2026, MongoDB **8.0.38**. Nenhuma exclusão de documentos,
coleção ou volumes, nenhum commit ou push.

## Falha original e causa real

O relatório `outputs/mongodb/carga.json` foi preservado. Ele registra a retomada
de 48.000 documentos para 89.618: 41.618 inseridos e 48.000 modificados, em
103,572 segundos. Na segunda carga, zero inseridos e 89.618 modificados,
em 96,891 segundos.

A condição original exigia contagem estável, zero inserções/modificações na
segunda carga e mesmo SHA-256 do CSV. Falhou no contador `modified_count`.
Uma contagem estável sozinha não prova igualdade de conteúdo.

Comparação somente leitura dos appids 730, 578080 e 570 com o CSV: nenhuma
diferença de valores, campos, tipos ou ordem de conteúdo, excluindo apenas `_id`.
Os BSONs de conteúdo eram idênticos. Datas são strings ISO determinísticas;
`executado_em_utc` fica apenas no relatório, não nos documentos. Os metadados
de origem Steam/2025-03 também são determinísticos.

Reprodução controlada no appid 730, enviando o mesmo conteúdo já persistido:

| Substituição | Correspondentes | Modified reportado | BSON persistido igual ao inicial |
|---|---:|---:|---|
| Sem `_id`, tentativa 1 | 1 | 1 | Sim |
| Sem `_id`, tentativa 2 | 1 | 1 | Sim |
| Com `_id` existente, tentativa 1 | 1 | 0 | Sim |
| Com `_id` existente, tentativa 2 | 1 | 0 | Sim |

Os bytes reais foram comparados com `RawBSONDocument`, não apenas por igualdade
de dicionários Python. Todas as quatro substituições preservaram o mesmo `_id`.

**Causa observada:** a omissão de `_id` no replacement faz esse servidor contar
modificação mesmo com BSON final idêntico. Incluí-lo explicitamente elimina o
efeito. Não foram encontradas diferenças de tipos, datas ou campos dinâmicos
como causa. Não se generaliza esse comportamento para outras versões nem se
afirma a implementação interna do servidor.

## Correção

Cada lote consulta pares appid/_id por `$in`. Documentos existentes são enviados
ao `ReplaceOne(..., upsert=True)` com seu `_id` preservado; novos jogos mantêm
a geração normal de `_id`. A transformação e o índice único não foram alterados.
Não há leitura de todos os documentos simultaneamente na memória.

A comprovação agora separa:

- `estado_final_identico`: contagem, SHA-256 do CSV e hash de todos os BSONs
  persistidos iguais entre as cargas. O hash inclui `_id`, tipos e ordem,
  com leitura incremental ordenada por appid.
- `segunda_carga_sem_modificacoes`: zero inserções/modificações segundo o
  servidor; os comandos de upsert continuam sendo enviados.
- `idempotencia_comprovada`: exige ambas, mantendo índice único e ausência de
  duplicados. A verificação ficou mais forte, não foi relaxada para forçar sucesso.

## Testes

**36 testes aprovados**, incluindo cinco novos casos: interrupção/retomada com
preservação de `_id` e duas cargas consecutivas; diferença BSON int64/int32
corrigida uma única vez; falha na leitura dos identificadores sem enviar lote;
contagem estável com hash diferente; e estado idêntico com modificações reportadas.

A coleção simulada agora usa BSON/ObjectId e reproduz o efeito de omitir `_id`.
A anterior comparava apenas dicionários Python, sem essa particularidade real.

## Comprovação real após a correção

As duas cargas foram efetivamente concluídas na coleção existente:

| Execução | Inseridos | Modificados | Inalterados | Rejeitados | Lotes | Duração da carga |
|---|---:|---:|---:|---:|---:|---:|
| Primeira corrigida | 0 | 0 | 89.618 | 0 | 90 | 98,735 s |
| Segunda corrigida | 0 | 0 | 89.618 | 0 | 90 | 90,534 s |

Não houve necessidade de reinserir ou alterar dados: a coleção já tinha o estado
correto. O objetivo foi corrigir a substituição e comprovar esse estado.

- Total final: **89.618 documentos** e **89.618 appids distintos**.
- Grupos duplicados: **0**; índice único: **true**.
- `estado_final_identico`: **true**.
- `segunda_carga_sem_modificacoes`: **true**.
- `idempotencia_comprovada`: **true**; status da execução: **concluido**.
- Duração total, incluindo consultas e hashes de auditoria: **235,874 segundos**.

Hash BSON de toda a coleção antes da correção e após cada uma das duas cargas,
incluindo todos os `_id`, conteúdo, tipos e ordem de campos:
`482be064263186dcf3e2c311ce1f6c470e1e035304175da7c1a8d85a2584dac9`.
As três assinaturas são iguais, comprovando preservação integral dos documentos.

O SHA-256 do CSV permaneceu
`04d8df2778aaa8f8b575934b7072d55224d37a2ded23e8261583f0fcf668dfab`.
Uma consulta posterior confirmou que todas as definições de índices são iguais
às anteriores: `_id_` e `appid_unico` (único), ambos versão 2.

Três exemplos consultados no servidor: appid 20, Team Fortress Classic; appid 240,
Counter-Strike: Source; appid 300, Day of Defeat: Source.

## Evidências e comandos

Saídas locais ignoradas pelo Git em `outputs/mongodb/`:

- `carga.json`: falha original preservada.
- `antes_correcao_idempotencia.json`: consulta anterior.
- `diagnostico_idempotencia.json`: comparação de três jogos com a origem.
- `reproducao_replaceone.json`: reprodução das quatro substituições idênticas.
- `estado_pre_correcao.json`: contagem, índices e hash da coleção antes das cargas.
- `idempotencia_corrigida.json`: relatório das duas cargas corrigidas.
- `indices_apos_correcao.json`: comparação exata dos índices com a captura anterior.

```powershell
.\.venv\Scripts\python.exe -X utf8 diagnostico_idempotencia.py
.\.venv\Scripts\python.exe -X utf8 -W error::ResourceWarning -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 carga_mongodb.py --comprovar-idempotencia --relatorio outputs/mongodb/idempotencia_corrigida.json
git diff --check
git status --short
```

Também foram executadas as consultas de auditoria e a reprodução controlada
descritas acima. Nenhuma credencial foi exposta.

## Arquivos e limites

Alterados: `carga_mongodb.py`, `tests/test_carga_mongodb.py`, `README.md` e
`RELATORIO_MONGODB.md` (referência para esta etapa). Criados:
`diagnostico_idempotencia.py` e este relatório. Nenhuma nova dependência.

A carga e as consultas de auditoria não são transacionais; escritas concorrentes
podem invalidar a comparação. A interrupção/retomada foi testada com simulação;
não se removeu parte da coleção real para recriar os 48.000 registros iniciais.
