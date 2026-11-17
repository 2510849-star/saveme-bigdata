# Checklist — entrega e demonstração N3

Preparada em 17/11/2026. Itens marcados refletem verificações já realizadas.
Não houve commit/push nesta etapa. Pendências semânticas e de cobertura estão em
`AUDITORIA_FINAL_N2.md`; não declarar conformidade integral sem tratá-las.

## Código, documentação e dados

- [x] Leitura, validação, tratamento, transformação e carga do CSV implementados.
- [x] 89.618 documentos persistidos em `saveme_analytics.jogos_analiticos`.
- [x] Índice único em appid e idempotência real comprovados em relatório anterior.
- [x] Análises principais e complementares executadas usando MongoDB real.
- [x] 70 testes automatizados aprovados na fase final.
- [x] CSV, coleção e índices preservados; hashes registrados.
- [x] README com ambiente, Compose, conexão, carga, testes e análises.
- [x] PDF N2 organizado em docs/, com leitura integral e auditoria por página.
- [x] `.env`, `.venv/`, dados e outputs ignorados; `.env.example` sem credenciais.
- [ ] Documentar URL exata de obtenção do CSV no Kaggle e condições de uso.
- [ ] Confirmar unidades, datas exatas dos períodos e semântica dos zeros/-1.
- [x] Completar e executar ranking de positivas, faixas de proprietários e
      comparação de características por gênero, com limites de interpretação.

## Antes da publicação no GitHub

Lista exata: `ARQUIVOS_PUBLICACAO.txt`. Comandos preparados:
`PREPARACAO_PUBLICACAO.md`. Revisão de segurança e resultados:
`RELATORIO_FINAL_PUBLICACAO.md`. Nada foi adicionado ao índice nesta preparação.

- [ ] Revisar todos os arquivos novos, incluindo PDF e relatórios. No estado auditado,
      apenas `.gitignore` e `analise_dataset.py` estavam rastreados pelo Git.
- [ ] Definir a seleção de arquivos da entrega: scripts, requirements, compose,
      `.env.example`, README, testes, PDF e relatórios Markdown.
- [ ] Incluir uma amostra pequena de resultados/evidências se exigida pelo professor;
      outputs completos estão ignorados e não serão publicados automaticamente.
- [ ] Revisar conteúdo para credenciais e dados desnecessários antes de adicionar.
- [ ] Após autorização, fazer commit e push e conferir o conteúdo efetivamente
      publicado. Estes passos estão pendentes por solicitação explícita do usuário.
- [ ] Verificar acesso do professor e copiar a URL correta do repositório.
- [ ] Em um clone limpo separado, seguir somente o README, obter o CSV documentado,
      criar ambiente e reproduzir testes, carga e análises. Isso ainda não foi testado
      num clone independente; executar no workspace atual não comprova esse item.

## Roteiro de demonstração

- [ ] Separar ambiente e tempo para a apresentação. A comprovação com duas cargas
      levou aproximadamente 236 segundos na execução registrada anteriormente.
- [ ] Mostrar PDF N2: fluxo na p.3, análises na p.4, modelo conceitual na p.5 e
      agregado nas pp.6–7. Explicar aplicação transacional versus pipeline analítico.
- [ ] Mostrar requisitos e os scripts sem abrir arquivos com segredos.
- [ ] Confirmar Engine/servidor e configuração de conexão:

```powershell
docker info
docker compose up -d --wait
docker compose ps
```

- [ ] Mostrar os testes e o tratamento, preservando relatórios anteriores com nova saída:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 pipeline_tratamento.py --saida outputs/demonstracao/tratamento
```

- [ ] Mostrar carga e comprovação real da segunda execução:

```powershell
.\.venv\Scripts\python.exe -X utf8 carga_mongodb.py --comprovar-idempotencia --relatorio outputs/demonstracao/idempotencia.json
.\.venv\Scripts\python.exe -X utf8 carga_mongodb.py --verificar --relatorio outputs/demonstracao/verificacao.json
```

- [ ] Conferir contagem, appids distintos, duplicados, índice, três exemplos e
      hashes de estado. Não confundir comandos de upsert enviados com modificações.
- [ ] Executar e abrir tabelas/gráficos/resumos das análises:

```powershell
.\.venv\Scripts\python.exe -X utf8 analises_mongodb.py --saida outputs/demonstracao/analises
.\.venv\Scripts\python.exe -X utf8 analises_complementares.py --saida outputs/demonstracao/complementares
```

- [ ] Explicar preço zero versus categoria Free To Play, avaliações versus vendas,
      proprietários estimados versus contagem exata, e snapshots versus histórico.
- [ ] Explicar média/mediana entre jogos, peso das avaliações e limitações de unidades
      e períodos. Não chamar unidades desconhecidas de horas ou minutos.
- [ ] Apresentar as diferenças e pendências da auditoria, sem afirmar que usuários,
      listas, ofertas multilojas, histórico ou integração com a aplicação existem aqui.
- [ ] Se o servidor não responder durante a apresentação, informar a falha e
      distinguir evidências de execuções anteriores de uma demonstração ao vivo.
- [ ] Se exigido, gravar vídeo/capturas e anexar evidências. O roteiro pronto não
      significa que a demonstração acadêmica já foi entregue.

Não remover a coleção nem os volumes para demonstrar idempotência. Rodar sem
cargas concorrentes. Não executar `docker compose down -v`.
