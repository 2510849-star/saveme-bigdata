# Auditoria final N2 × N3 — SaveMe Games Big Data

Atualização da fase final: as lacunas de ranking por positivas, análise das
faixas de proprietários e comparação de características por gênero foram
implementadas e executadas. Ver `RELATORIO_FINAL_PUBLICACAO.md`. As matrizes
abaixo preservam o diagnóstico anterior a essa implementação.

Data: 17/11/2026. Conclusão: **pipeline funcional e aderente ao núcleo analítico
da N2, com cobertura parcial de algumas consultas propostas e pendências de
semântica, disponibilização e entrega**. Não se declara conformidade integral.

## 1. Documento efetivamente lido

Foram lidas integralmente as **oito páginas**, extraído o texto e inspecionadas
visualmente todas as páginas, sobretudo o diagrama da p.5 e o modelo das pp.6–7.

O caminho informado `docs/N2 Flaris - SaveMe Games (1)(1).pdf` não existia no
workspace, inclusive fora do sandbox. Foi localizada a cópia
`N2 Flaris - SaveMe Games (1).pdf`, de 669.844 bytes, na Área de Trabalho do
computador usado na auditoria (caminho pessoal omitido para publicação).
Ela foi lida e copiada sem alteração de conteúdo para o caminho solicitado em
`docs/`. As duas cópias têm SHA-256 idêntico:
`8b4e683b2f63bc24789f30495ae29e4d1eaa95da25bb5c9f0e693fcdf5c8599f`.
Não se afirma ter comparado com outra versão que não estava acessível.

Texto extraído e renderizações das oito páginas estão em `outputs/auditoria_n2/`,
ignorados pelo Git. O PDF em `docs/` permite reproduzir a auditoria.

## 2. Conferência por seção do PDF

| N2 | Proposta e implementação observada | Situação |
|---|---|---|
| 1.1–1.2, p.1 | Captura, organização e análise Steam: `pipeline_tratamento.py`, `carga_mongodb.py`, scripts de análise e resultados reais | Núcleo implementado; apoio à aplicação ainda indireto |
| 1.3, p.1 | Fonte, processo e MongoDB existem; usuário acessa arquivos/terminal, não uma interface integrada ao SaveMe | Parcial na disponibilização |
| 1.4, p.2 | Mesmo CSV Steam/março de 2025, 89.618 × 47; origem Kaggle identificada no PDF | Implementado; URL exata e condições de obtenção do dataset ainda precisam ser documentadas |
| 1.4, p.2 | Validar unidades, períodos e nulos | Tipos/nulos tratados; unidade dos tempos, janela exata, moeda e significado de sentinelas não confirmados externamente |
| 1.4, p.3 | Outras lojas/APIs são evolução futura e exigem acesso autorizado | Não implementadas; não são fonte comprovada nem requisito de ingestão atual |
| 1.5, p.3 | Exemplos de CS2, PUBG e Dota 2 no dataset | Valores históricos já conferidos; exemplo CS2 da p.7 novamente validado no MongoDB nesta auditoria |
| 1.6, p.3 | Oito etapas do fluxo | Ver matriz abaixo |
| 1.7, p.4 | Sete famílias de análises | Ver matriz de consultas; algumas coberturas são parciais |
| 1.8, p.4 | Python, CSV, MongoDB e agregações; PostgreSQL separado | Atendido; Pandas/Matplotlib complementam as tecnologias sem substituir o MongoDB |
| 1.9, p.4 | Informações organizadas e estrutura extensível | Atendido para Steam; multilojas não demonstrado nem inventado |
| 2, p.5 | Modelo conceitual transacional | Não implementado neste repositório analítico; ver delimitação abaixo |
| 3.1, p.6 | Um documento por jogo, dados relacionados agregados | Atendido |
| 3.2, p.6 | Coleção `jogos_analiticos`, appid e seis grupos de informações | Atendido semanticamente; nomes físicos e tipos detalhados abaixo |
| 3.3, p.7 | Exemplo de Counter-Strike 2 | Compatível com o documento real |
| 3.4, p.8 | Consultas por positivas, gêneros, preços, descontos, popularidade e comparação de avaliações | Cobertura parcial, ampliada nesta etapa |
| 3.5, p.8 | MongoDB analítico separado, appid único e indexado | Atendido; índice único preservado, sem conexão ao PostgreSQL |
| 3.6, p.8 | Estrutura documental preparada para consultas futuras | Implementada e executada na N3; a N2 era uma proposta, não evidência de implementação |

## 3. As oito etapas do fluxo (N2 p.3)

| Etapa | Evidência | Avaliação |
|---|---|---|
| Entrada | `data/games_march2025_cleaned.csv` local, ignorado pelo Git | Atendida para CSV; aquisição manual |
| Leitura/identificação | `pd.read_csv`, esquema de 47 colunas e lotes em `iterar_documentos()` | Atendida |
| Validação | `validar_esquema`, `validar_appids`, nome e números obrigatórios, duplicidade entre lotes | Atendida para o contrato definido |
| Tratamento | Listas com literal_eval; nulos por campo; idade/sentinelas com bruto preservado; datas ISO | Atendida com hipóteses semânticas explícitas; não equivale a validação externa da fonte |
| Transformação | Taxa positiva, total, limites de proprietários e documento agregado | Atendida |
| Armazenamento | MongoClient, índice único, upserts em lotes; idempotência real já comprovada | Atendida; carga não transacional e retomável |
| Análise | `analises_mongodb.py` e `analises_complementares.py`, somente MongoDB | Implementada; cobertura de consultas não integral |
| Disponibilização | CSV/PNG/JSON, README e terminal | Atendida como artefatos acadêmicos; sem API/tela integrada ao SaveMe |

## 4. Modelo conceitual da página 5

O diagrama contém **USUARIO**, **LISTA_DESEJOS**, **ITEM_LISTA**, **JOGO**, **LOJA**,
**OFERTA** e **HISTORICO_PRECO**. Mostra usuário possuindo listas, listas contendo
itens, itens apontando para jogos, jogos com ofertas/histórico e lojas
disponibilizando ofertas. Inclui PKs/FKs, dados do usuário, datas e preço/desconto
de oferta, além de preço/data de registro do histórico.

O repositório atual **não implementa** usuários, autenticação, listas de desejos,
itens de lista, entidades de outras lojas, ofertas por loja nem histórico de preços.
Isso deve ser declarado na apresentação. Não se criou histórico a partir de um
snapshot nem ofertas de lojas ausentes da fonte.

Essas entidades representam a aplicação, não os documentos analíticos exigidos
nas pp.6–8. A própria N2 pp.4 e 8 separa MongoDB de PostgreSQL. Portanto, sua
ausência aqui não prova falha da ingestão Steam, mas impede afirmar que todo o
modelo conceitual da aplicação foi implementado neste repositório.

## 5. Modelo agregado das páginas 6 e 7

| Grupo lógico da N2 | Campo real | Observação |
|---|---|---|
| Identificação | `appid`, `nome`, `lancamento.bruto`, `lancamento.data_iso` | Data é string ISO validada, não BSON Date; diferença de representação que limita operadores temporais nativos |
| Catálogo | `catalogo.generos`, `desenvolvedores`, `publicadoras` | Arrays nativos, não strings de listas |
| Preço | `preco.valor`, `preco.desconto_percentual` | Double e inteiro; moeda não inferida; não é histórico/oferta multilojas |
| Avaliações | `avaliacoes.positivas`, `negativas`, `total`, `taxa_positivas_percentual` | Derivados extras consistentes; sem denominador, taxa null |
| Popularidade | `popularidade.proprietarios_estimados`, `pico_jogadores_simultaneos`, quatro tempos | Faixa bruta e limites preservados; não são vendas exatas |
| Origem | `origem.plataforma`, `mes_referencia`, `arquivo` | Steam, 2025-03, nome do arquivo identificando o dataset; não há campo literal com o título amigável do exemplo |

Não existe no PDF um JSON Schema rígido que obrigue esses nomes físicos. A
organização semântica é compatível, com grupos e campos adicionais (`informacoes`,
scores, idade bruta/tratada e versão do documento). Não há motivo para migrar
89.618 documentos apenas para imitar rótulos conceituais do PDF.

O exemplo CS2 foi consultado no banco: appid 730, nome Counter-Strike 2, data
2012-08-21, Valve como desenvolvedor/publicadora, preço/desconto zero,
7.480.813 positivas e 1.135.108 negativas, coerentes com a p.7.

Diferença de projeção: o CSV tem 47 colunas, mas `tags` e `packages` não entram
no documento atual. `tags` aparece explicitamente na lista de atributos da N2 p.2;
`packages` não é exigido nos seis grupos da p.6. Permanecem no CSV original.
Essa omissão limita análises de tags, sem invalidar as análises existentes.

## 6. Cobertura das análises previstas

| N2 | Estado atual |
|---|---|
| Preços e descontos (pp.4/8) | Distribuições por faixa, percentuais exatos e jogos com desconto implementados |
| Proporção positiva e comparação positivas/negativas (pp.4/8) | Implementadas; ranking por total e taxa, com mínimo de 100 apenas para taxa |
| Maior quantidade de positivas (p.8) | **Não existe ranking específico ordenado só por positivas**; total não é equivalente |
| Popularidade por pico (p.4) | Implementada |
| Popularidade por proprietários estimados (p.4) | **Faixas armazenadas, mas sem análise/ranking próprio**; qualquer ordenação futura deve explicitar limites e empates, não inventar contagem exata |
| Gêneros e suas características (p.4) | Frequência multivalorada implementada; comparação de preço/avaliação por gênero ainda não |
| Engajamento médio/mediano e períodos (p.4) | **Implementado nesta etapa**, mantendo unidades originais e períodos separados |
| Relações preço/avaliação/desconto/popularidade (p.4) | Preço × taxa implementado; relações envolvendo simultaneamente desconto e popularidade não exploradas |
| Gratuitos × pagos (p.8) | **Comparação preço zero × positivo implementada nesta etapa**; não rotulada como comprovação de gratuidade/pagamento comercial |

A N2 chama essas análises de possibilidades, não uma lista fechada de gráficos
obrigatórios. As diferenças acima são lacunas de cobertura a declarar e priorizar,
sem afirmar que toda possibilidade futura já foi realizada.

## 7. Novos resultados reais

Execução de `analises_complementares.py`: **84,022 segundos**, 89.618 documentos,
zero preços ausentes/inválidos. Fonte exclusiva: MongoDB.

### Engajamento

| Campo | Positivos | Zeros | Ausentes/inválidos | Média entre jogos positivos | Mediana entre jogos positivos |
|---|---:|---:|---:|---:|---:|
| tempo_medio_total | 8.010 | 81.608 | 0 | 1.285,66 | 218 |
| tempo_mediano_total | 8.010 | 81.608 | 0 | 1.283,92 | 213 |
| tempo_medio_duas_semanas | 717 | 88.901 | 0 | 629,04 | 137 |
| tempo_mediano_duas_semanas | 717 | 88.901 | 0 | 662,68 | 137 |

Todos os valores temporais estão na **unidade original não confirmada**. A N2
p.2 exige validação, mas não informa minutos/horas. Não houve conversão nem
suposição de datas exatas da janela. Não se conclui que zeros são inatividade.
As medianas entre todos os jogos, incluindo zeros, são zero nos quatro campos.
O máximo total de 1.462.997 unidades revela valores extremos a investigar na fonte;
não foi removido nem interpretado como horas/minutos. Estatísticas de indicadores
por jogo não representam a média/mediana de todos os jogadores da Steam.

### Comparação por preço

| Indicador | Preço zero | Preço positivo |
|---|---:|---:|
| Jogos | 14.160 | 75.458 |
| Jogos com alguma avaliação | 6.810 | 65.753 |
| Jogos sem avaliações | 7.350 | 9.705 |
| Avaliações totais somadas | 34.426.316 | 98.181.307 |
| Média de avaliações por jogo, incluindo zeros válidos | 2.431,24 | 1.301,14 |
| Mediana de avaliações por jogo | 0 | 15 |
| Média das taxas positivas por jogo com avaliações | 74,95% | 75,44% |
| Mediana das taxas positivas por jogo com avaliações | 77,78% | 81,82% |
| Taxa positiva ponderada pelas avaliações | 80,46% | 87,70% |
| Categoria Free To Play explícita | 8.795 | 72 |

A média de taxas dá peso igual a jogos; a taxa ponderada usa soma de positivas /
soma de avaliações. Nenhuma delas mede vendas ou efeito causal do preço.
Preço zero e categoria Free To Play são dimensões distintas, inclusive nos dados.

## 8. Testes, artefatos e preservação

**60 testes aprovados**: 52 anteriores e oito complementares, cobrindo períodos,
média/mediana, zeros/nulos/negativos/infinitos, rankings, ponderação, grupos por
preço independentes de F2P, grupos vazios e não mutação da entrada.

Agregações independentes no MongoDB conferiram zeros/positivos e médias de tempo,
contagens/somas/taxas ponderadas por preço e o exemplo da p.7. Os quatro gráficos
foram inspecionados visualmente; o espaçamento de legenda foi ajustado e eles
foram regenerados das tabelas exportadas do MongoDB, sem ler o CSV original.
Uma primeira sondagem independente falhou ao comparar rótulos acentuados enviados
pelo pipe do PowerShell; a conferência foi corrigida para agrupar por condição
booleana de preço zero e concluída com código 0. Não houve alteração nos resultados.

Saídas em `outputs/analises/complementares/`:

- `engajamento_resumo.csv`, `engajamento_ranking.csv`, `comparacao_precos.csv`.
- `engajamento_cobertura.png`, `engajamento_valores_positivos.png`,
  `comparacao_preco_avaliacoes.png`, `comparacao_preco_percentuais.png`.
- `resumo.json`, com indicadores, metodologia, duração e hashes.

SHA-256 BSON antes/depois:
`482be064263186dcf3e2c311ce1f6c470e1e035304175da7c1a8d85a2584dac9`.
**Coleção e índices inalterados.** CSV preservado, hash reconferido:
`04d8df2778aaa8f8b575934b7072d55224d37a2ded23e8261583f0fcf668dfab`.
Os relatórios de tratamento, carga/idempotência e análises anteriores permanecem.

## 9. Entrega e próximos passos

1. Documentar a aquisição exata do dataset e confirmar moeda, unidades, janela
   temporal e semântica dos zeros/-1 na fonte. Por enquanto são limitações/hipóteses.
2. Se a avaliação exigir todas as consultas da N2, completar ranking por positivas,
   análise por faixas de proprietários e comparações de características por gênero.
3. Declarar que a disponibilização atual é CSV/PNG/JSON/terminal; integração com
   a aplicação e o modelo transacional não foram implementados aqui.
4. Preparar a publicação GitHub e a demonstração conforme `CHECKLIST_ENTREGA_N3.md`.
   No Git local, somente `.gitignore` e `analise_dataset.py` estão rastreados;
   o restante ainda está sem commit. Isso é uma pendência real de entrega,
   mantida porque o usuário proibiu commit/push nesta etapa.

O PDF não contém as exigências N3 de GitHub/demonstração: elas vêm do enunciado
informado pelo usuário. A N2 pp.3 e 8 ressalva que era especificação; a N3 já
implementa esse núcleo. Não há falha por não implementar APIs futuras/outras lojas.

## 10. Reprodução e arquivos desta etapa

```powershell
.\.venv\Scripts\python.exe -X utf8 -W error::ResourceWarning -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 analises_complementares.py
.\.venv\Scripts\python.exe -m pip check
git diff --check
git status --short
```

Criados: `analises_complementares.py`, seus testes, este relatório, checklist e
cópia auditada do PDF em `docs/`. Atualizados: `analises_mongodb.py` (projeção
reutilizável e referência à N2), README e anotação histórica em
`RELATORIO_ANALISES.md`. Nenhuma nova dependência, alteração de dados, commit ou push.
