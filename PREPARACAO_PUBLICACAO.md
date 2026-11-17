# Publicação preparada — comandos não executados

A lista fechada de **42 arquivos** está em `ARQUIVOS_PUBLICACAO.txt`.
Inclui código, testes, configurações de exemplo, PDF da N2 e relatórios Markdown.
Inclui agora quatro PNGs pequenos e JSONs minimizados em docs/evidencias/.
Não inclui CSV original, documentos completos exportados, outputs, ambiente,
cache, logs ou arquivos com credenciais. Não usar `git add .` nesta entrega.

O remoto `origin` já está configurado para GitHub e a branch atual é `main`.
A URL está no README. O clone público de `main`/`6300343` foi testado;
permissões de escrita não foram verificadas por push nesta preparação.

## Revisar antes de publicar

1. Ler `RELATORIO_FINAL_PUBLICACAO.md` e as pendências da checklist.
2. Conferir `docs/ORIGEM_DATASET.md`: fonte Kaggle e versão 2 identificadas por
   metadados e comparação HTTP parcial. O download integral deve ser conferido
   pelo SHA-256; não foi repetido nesta preparação.
3. Conferir autoria acadêmica do PDF e a identidade Git que será usada no commit.
   Os nomes da equipe no PDF são autoria intencional, não dados de usuários da aplicação.
4. Consultar `docs/evidencias/execucao_validada.json`: reprodução em clone limpo
   já aprovada com ressalvas, usando cópia autorizada do CSV e MongoDB isolado.
   O CSV precisa ser obtido por fora do Git.

O roteiro integral, com dependências, verificação do hash, MongoDB separado,
testes, tratamento, duas cargas e todas as análises, está na seção
**Reprodução em ambiente limpo** do README. A execução do commit `6300343`
está resumida nas evidências. O ensaio isolado não exige apagar o banco original.

## Prévia sem adicionar arquivos

Na raiz do repositório, PowerShell:

```powershell
git status --short
git --literal-pathspecs add --dry-run --pathspec-from-file=ARQUIVOS_PUBLICACAO.txt
```

O modo literal trata corretamente o nome do PDF com espaços e parênteses.
O dry-run foi usado nesta preparação; não adiciona arquivos ao índice.

## Comandos para executar somente após autorizar a publicação

Os comandos abaixo foram **apenas preparados**, sem executar add real, commit ou push:

```powershell
git --literal-pathspecs add --pathspec-from-file=ARQUIVOS_PUBLICACAO.txt
git diff --cached --stat
git diff --cached --check
git diff --cached
git commit -m "Documenta fonte e prepara evidencias da apresentacao N3"
git push -u origin main
```

Revisar o diff antes do commit; se houver arquivo inesperado, parar e corrigir
a seleção. O push depende das permissões do remoto. Não usar force push.

## Depois da publicação

- Conferir no GitHub os 42 arquivos e a ausência dos diretórios ignorados.
- Confirmar acesso do professor e registrar a URL na entrega acadêmica.
- Reproduzir os comandos do README em clone limpo, obtendo o CSV documentado.
- Demonstrar testes, carga/idempotência e análises com os relatórios reais.

O núcleo de código já está publicado no commit `6300343`. Esta atualização de
documentação/evidências ainda não foi commitada nem enviada, por instrução do usuário.
Antes de apresentar, conferir que o remoto recebeu os arquivos realmente escolhidos.
