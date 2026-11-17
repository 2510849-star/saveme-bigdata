# N3 — execução de tratamento e transformação

Execução real em 17/11/2026, Python 3.12.14 e Pandas 3.1.1. Nenhuma conexão com
MongoDB, commit ou push. Scripts anteriores preservados. Regras detalhadas e
estrutura dos documentos estão no README.

## Resultados reais

| Verificação | Resultado |
|---|---:|
| Registros de entrada | 89.618 |
| Colunas de entrada | 47 |
| Colunas extras | 0 |
| appid distintos e válidos | 89.618 |
| Células nulas na entrada | 433.211 |
| Registros rejeitados | 0 |
| Documentos de saída | 89.618 |
| Documentos verificados como BSON e JSON sem NaN/Infinity | 89.618 |
| Amostras persistidas localmente | 3 |

Reconciliação: **89.618 = 0 rejeitados + 89.618 aceitos**. Todos os documentos
foram construídos e validados; apenas três foram retidos como amostra, sem
exportação dos 89 mil documentos completos e sem carga em banco.

SHA-256 antes e depois, idênticos:
`04d8df2778aaa8f8b575934b7072d55224d37a2ded23e8261583f0fcf668dfab`.

## Transformações contabilizadas

| Regra | Quantidade |
|---|---:|
| Datas de lançamento ISO validadas | 89.618 |
| Faixas de proprietários extraídas | 89.618 |
| Taxas positivas calculadas | 72.563 |
| Taxas ausentes por denominador zero | 17.055 |
| Idade negativa tratada como indisponível | 1 |
| `pct_pos_total`: -1 para None, mantendo bruto | 36.419 |
| `num_reviews_total`: -1 para None, mantendo bruto | 36.419 |
| `pct_pos_recent`: -1 para None, mantendo bruto | 82.931 |
| `num_reviews_recent`: -1 para None, mantendo bruto | 82.931 |
| Elementos vazios removidos de publishers | 6 |
| Espaços externos normalizados em itens de idiomas | 2 |
| Preços zero preservados | 14.160 |
| Categoria Free To Play explicitamente presente | 8.867 |

Cada uma das oito colunas de listas teve 89.618 conversões de representação
textual para lista Python. Listas vazias após tratamento:

| Campo de origem | Listas vazias na saída |
|---|---:|
| genres | 212 |
| developers | 221 |
| publishers | 553 |
| categories | 876 |
| supported_languages | 182 |
| full_audio_languages | 49.823 |
| screenshots | 106 |
| movies | 2.411 |

Publishers passa de 547 listas originalmente vazias para 553 após limpar as
seis ocorrências de `['']`. Não houve listas inválidas rejeitadas no CSV real.

Os 433.211 nulos originais foram preservados semanticamente como `None` nos
respectivos campos opcionais, sem remover linhas. Esse total é distinto dos
novos valores tratados indisponíveis de sentinelas/idade e da taxa sem denominador.
O relatório JSON inclui contagens por campo de entrada e por regra aplicada.
Os valores brutos de idade negativa e sentinelas permanecem nos documentos.

## Testes e comandos executados

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 pipeline_tratamento.py
git diff --check
git status --short
git check-ignore outputs/tratamento/qualidade.json outputs/tratamento/amostra_documentos.json
```

**16 testes aprovados**, incluindo múltiplos subcasos parametrizados com
`subTest`; nenhuma falha na execução dos testes ou do processamento real.

Cobertura: documento normal e codificação BSON/JSON, não mutação da entrada,
listas inválidas sem execução de código, nulos e listas vazias, publisher vazio,
idade negativa, sentinelas e nulos de métricas, denominador zero, preço zero sem
inferência de Free To Play, faixas válidas/inválidas, números inválidos, nome/data/
plataforma/percentuais inválidos, esquema incompleto/duplicado, appid duplicado
entre lotes e processamento integrado com rejeição, hash e repetibilidade.

`outputs/tratamento/qualidade.json` e `amostra_documentos.json` são locais e
ignorados pelo Git. É possível regenerá-los com o comando do pipeline.

## Arquivos desta etapa

- Criado `pipeline_tratamento.py`: validação, tratamento, transformação e relatório.
- Criado `tests/test_pipeline_tratamento.py`: testes automatizados com unittest.
- Criado `README.md`: execução, contrato de entrada, regras e estrutura documental.
- Criado este relatório com resultados da execução real.
- Alterado `.gitignore`: adicionado `outputs/` para não versionar saídas geradas.
- `requirements.txt`, código de análise/validação anterior e CSV não foram alterados
  nesta etapa. As dependências existentes foram suficientes.

## Limitações e próximo passo

- `-1` é interpretado como indisponibilidade **por hipótese de tratamento**,
  não por confirmação externa da semântica da fonte. O bruto foi mantido.
- O documento é uma projeção analítica: `packages` e `tags` permanecem no CSV,
  fora da versão 1 do documento. As oito colunas incluídas que representam listas
  de textos são convertidas; não se convertem pacotes de objetos em listas de textos.
- Moeda e unidades dos tempos de jogo não são inferidas. Não há histórico de preços.
- Descrições/HTML e possíveis títulos `none`/`Unknown` são preservados.
- `free_to_play_explicito: false` indica que a categoria não foi encontrada;
  não comprova que o jogo é pago. Preço zero não altera esse indicador.
- Compatibilidade BSON foi verificada localmente com PyMongo; isso não demonstra
  persistência ou consulta em servidor MongoDB, que estão fora desta etapa.
- Falhas globais de esquema/appid interrompem a execução; demais erros de conteúdo
  rejeitam linhas com motivo. Um CSV futuro deve ser avaliado pelo seu relatório,
  pois o sucesso desta execução não garante zero rejeições em outras entradas.

Próximo passo recomendado: revisar a hipótese das sentinelas e o contrato
documental; depois implementar a carga idempotente na coleção `jogos_analiticos`,
com índice único em `appid` e reconciliação das contagens.
