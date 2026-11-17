# Preparação da apresentação N3 — relatório de verificação

Data: **17/11/2026**. Escopo: documentação, fonte e evidências; **nenhuma alteração
do pipeline, arquitetura, dependências, CSV ou documentos MongoDB**. Sem commit/push.

## Aderência ao enunciado

| Exigência oficial | Material preparado |
|---|---|
| Implementar o pipeline da N2 | Código-base publicado em `main`, commit `6300343`; auditoria e reprodução real registradas |
| Mostrar funcionamento | Roteiro com leitura inicial, consulta real ao MongoDB, contagem, índice, documento e agregação; bloco de consulta ensaiado |
| Demonstrar saídas esperadas | Quatro gráficos pequenos, dois exemplos minimizados e resumo dos resultados reais |
| Apresentar em 17/11 | Roteiro-base de dez minutos, faixa de 8–12; a apresentação oral ainda deve ser ensaiada/realizada pelo grupo |
| Código no GitHub | Base publicada; estas novas evidências/documentação ainda não foram enviadas |
| Instruções de execução | README revisado, origem do CSV identificada, roteiro de reprodução e comandos de demonstração |

## 1. Investigação do dataset

A busca local examinou documentação, nome, tamanho e metadados de transferência
do CSV e arquivos locais com nome correspondente. Não havia um link Kaggle
recuperável nesses registros. Não foram acessadas conversas ou dados privados.

A pesquisa externa encontrou o catálogo primário
[Steam Games Dataset 2025, versão 2](https://www.kaggle.com/datasets/artermiloff/steam-games-dataset/versions/2).
Metadados e lista de arquivos públicos confirmaram a referência
`artermiloff/steam-games-dataset`, responsável exibido Artemiy Ermilov,
atualização declarada em 13/03/2025 e licença declarada MIT no catálogo.

Correspondência verificada do arquivo:

- Nome exato `games_march2025_cleaned.csv` e **468.641.107 bytes** na API.
- Cabeçalho remoto com **47 colunas**, correspondente ao usado localmente.
- Dois trechos HTTP Range 206, de **65.536 bytes cada**, no início e no final,
  comparados com igualdade byte a byte ao CSV local.
- **89.618 registros** previamente processados no arquivo local e no MongoDB.
- SHA-256 local reconferido:
  `04d8df2778aaa8f8b575934b7072d55224d37a2ded23e8261583f0fcf668dfab`.

Não foi calculado SHA-256 integral de um novo download remoto nesta preparação.
Isso não foi ocultado: a identificação usa metadados, cabeçalho e amostras; a
confirmação integral de um arquivo obtido pelo grupo deve usar o hash conhecido.
A URL deixou de ser uma pendência de identificação. Data do download inicial pelo
grupo não foi inferida a partir da atualização do catálogo.

Fonte e obtenção: [ORIGEM_DATASET.md](ORIGEM_DATASET.md).
Registro compacto: [correspondencia_dataset.json](evidencias/correspondencia_dataset.json).
Respostas completas da API e auxiliares de coleta permanecem em outputs/, ignorados.

## 2. Evidências reais selecionadas

Em `docs/evidencias/`:

- **4 PNGs**: avaliações, distribuição de preços, gêneros e popularidade.
- `README.md`: resumo curto, leitura dos gráficos, testes e limites.
- `documentos_reais.json`: **duas projeções pequenas**, consultadas na instância
  MongoDB real isolada em 27018, appids 730 e 12370.
- `execucao_validada.json`: verificação atual, 70 testes reexecutados e resultados
  históricos de carga inicial/segunda carga da reprodução independente.
- `graficos_proveniencia.json`: caminhos relativos, tamanhos e hashes das cópias.
- `correspondencia_dataset.json`: fonte, versão e verificação parcial do CSV.

As quatro imagens foram copiadas sem edição do outputs/ original e têm os mesmos
hashes SHA-256 das origens. Foram verificadas visualmente como legíveis.
Não há CSV completo, dump MongoDB, descrição longa ou imagem volumosa na seleção.

Os exemplos preservam os nomes e appids públicos dos jogos, sem inventar dados.
Não contêm `_id` interno, contatos, URLs, textos livres ou informações de usuários.
O appid 12370 demonstra total zero e percentual positivo null. Não foram tratados
dados públicos de jogos como se fossem dados pessoais de jogadores.

## 3. Resultados apresentados

Consulta atual confirmou **89.618 documentos e appids distintos**, zero duplicados
e índice único. Agregação real: Indie 63.189, Casual 38.699, Action 36.842,
Adventure 35.452 e Simulation 18.570. Esses números conferem com as saídas originais.

CS2: 7.480.813 avaliações positivas, 1.135.108 negativas, 8.615.921 totais;
pico de 1.212.356 jogadores na fonte. Preços zero: 14.160; categoria F2P explícita:
8.867; jogos com desconto: 7.454 (8,32%). Avaliações não são vendas, gêneros são
multivalorados e preço zero não comprova classificação comercial.

Carga histórica da reprodução limpa, **não reexecutada nesta preparação**:

| Execução | Inseridos | Modificados | Inalterados | Rejeitados |
|---|---:|---:|---:|---:|
| Inicial, coleção vazia | 89.618 | 0 | 0 | 0 |
| Segunda | 0 | 0 | 89.618 | 0 |

Hash de estado igual entre as duas cargas e `idempotencia_comprovada: true`.
Os tempos de 123,793 s e 131,159 s pertencem àquela execução. O roteiro mostra
essa evidência sem exigir aguardar a carga completa durante a apresentação.

## 4. Testes e consultas ensaiadas nesta preparação

- Comando real: `.venv/Scripts/python.exe -X utf8 -W error::ResourceWarning -m unittest discover -s tests -v`.
- Resultado: **70 testes**, `OK`, código 0.
- O bloco Python extraído do roteiro foi executado contra 27018 com código 0:
  conexão, contagem, índice único, CS2 real e agregação dos cinco gêneros.
- Não houve carga ou escrita no banco. A captura diferencia dados atuais de
  resultados históricos, com datas UTC nos JSONs.
- Auxiliares e logs completos ficam em `outputs/preparacao_apresentacao/`, fora do Git.

SHA-256 BSON antes/depois da coleta:
`f81722cbcb107cfa3b8df2ff01ddce6a91d9feb4832f7ed7a67fe8931ea3df1b`.
Coleção e índices inalterados. É o hash da instância real de reprodução, com seus
ObjectIds próprios; não deve ser confundido com o hash do banco original.
O CSV foi apenas lido para conferência e manteve seu SHA-256.

## 5. Roteiro, contingência e publicação

[ROTEIRO_DEMONSTRACAO_N3.md](ROTEIRO_DEMONSTRACAO_N3.md) distribui dez minutos
entre problema, fonte, consulta real, idempotência, gráficos, testes e limitações.
Inclui rota curta, extensão até 12 minutos e respostas a perguntas do professor.
Os comandos PowerShell usam os scripts existentes. Em falha de Docker/internet,
apresentar as cópias locais como evidência anterior, sem simular consulta ao vivo.

README ganhou links relativos para os materiais. A seleção de publicação passou
de 30 para **42 arquivos**, incluindo estas 12 evidências/documentos adicionais.
`outputs/`, CSV, ambiente Python, caches, logs e auxiliares continuam ignorados.
Os comandos de publicação foram atualizados, mas nenhum staging/commit/push foi feito.

## 6. Parecer e pendências

Conferência final: os 42 candidatos existem, são únicos, não estão ignorados e
somam 1.267.228 bytes. Os JSONs são válidos, os links locais revisados resolvem
e os quatro PNGs são idênticos aos originais. A busca por padrões de segredos
encontrou somente a URI fictícia `usuario:senha@servidor` de um teste de erro;
não foram encontradas credenciais reais nessa revisão. `git diff --check`
passou, sem arquivos staged. Branch `main`, HEAD `6300343`. Código, testes,
dependências e configurações do pipeline não foram alterados.

**Material técnico/documental pronto para revisão e ensaio da apresentação**, com
pipeline-base já demonstrado e reproduzido. Isso não significa que a apresentação
acadêmica ou a atualização GitHub já tenham sido entregues.

Pendências:

1. Revisar e autorizar a publicação das novas evidências; conferir os links no
   GitHub depois do envio. O commit-base `6300343` não contém estes arquivos novos.
2. Ensaiar a fala no tempo previsto e verificar o servidor isolado antes da aula.
3. Ao obter uma cópia integral do Kaggle, conferir o SHA-256; download remoto
   integral não foi repetido nesta preparação.
4. Declarar os limites conhecidos: moeda/unidades e sentinelas não confirmadas,
   snapshot de março de 2025, sem multilojas/histórico nem sistema transacional.

Não há nova tecnologia, dependência, funcionalidade ou migração de dados nesta etapa.
