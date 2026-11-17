# Publicação preparada — comandos não executados

A lista fechada de **30 arquivos** está em `ARQUIVOS_PUBLICACAO.txt`.
Inclui código, testes, configurações de exemplo, PDF da N2 e relatórios Markdown.
Não inclui CSV original, documentos completos exportados, outputs, ambiente,
cache, logs ou arquivos com credenciais. Não usar `git add .` nesta entrega.

O remoto `origin` já está configurado para GitHub e a branch atual é `main`.
A URL não é reproduzida neste documento. Não houve consulta remota para
confirmar permissões/acesso; será necessário verificá-los na publicação.

## Revisar antes de publicar

1. Ler `RELATORIO_FINAL_PUBLICACAO.md` e as pendências da checklist.
2. **O grupo precisa fornecer o link exato do Kaggle, versão e instruções para
   obter `games_march2025_cleaned.csv`. A URL ainda não está documentada; não foi
   inventada. Sem isso, outra pessoa sem o arquivo não consegue reproduzir.**
3. Conferir autoria acadêmica do PDF e a identidade Git que será usada no commit.
   Os nomes da equipe no PDF são autoria intencional, não dados de usuários da aplicação.
4. Ensaiar a instalação num ambiente/clone limpo separado. Essa verificação ainda
   não foi feita, e o CSV precisa ser obtido por fora do Git.

O roteiro integral, com dependências, verificação do hash, MongoDB separado,
testes, tratamento, duas cargas e todas as análises, está na seção
**Reprodução em ambiente limpo** do README. Ele é um procedimento preparado,
não evidência de que um clone independente já foi executado. Não aponta o ensaio
para o banco original nem exige apagar coleções/volumes.

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
git commit -m "Implementa pipeline Steam e analises N3 do SaveMe Games"
git push -u origin main
```

Revisar o diff antes do commit; se houver arquivo inesperado, parar e corrigir
a seleção. O push depende das permissões do remoto. Não usar force push.

## Depois da publicação

- Conferir no GitHub os 30 arquivos e a ausência dos diretórios ignorados.
- Confirmar acesso do professor e registrar a URL na entrega acadêmica.
- Reproduzir os comandos do README em clone limpo, obtendo o CSV documentado.
- Demonstrar testes, carga/idempotência e análises com os relatórios reais.

O estado atual não é uma entrega publicada: o commit/push estão pendentes por
instrução do usuário, e a reprodução independente ainda precisa ser comprovada.
