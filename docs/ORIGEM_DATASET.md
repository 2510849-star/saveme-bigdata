# Origem e obtenção do dataset

Verificação realizada em **17/11/2026**. A pesquisa identificou uma correspondência
verificável para o arquivo usado no projeto:

- **Título:** Steam Games Dataset 2025.
- **Referência Kaggle:** `artermiloff/steam-games-dataset`.
- **Responsável exibido pelo catálogo:** Artemiy Ermilov.
- **Versão:** 2, atualização declarada em 13/03/2025, referência março de 2025.
- **Arquivo específico:** `games_march2025_cleaned.csv`.
- **Licença declarada no catálogo do dataset:** MIT. Isso não define a licença
  do código deste projeto nem deve ser atribuído a outra versão sem conferência.

Fontes primárias:

- [Página da versão 2 no Kaggle](https://www.kaggle.com/datasets/artermiloff/steam-games-dataset/versions/2).
- [Identificador persistente da versão](https://www.kaggle.com/dsv/11017460).
- [Metadados públicos](https://www.kaggle.com/api/v1/datasets/view/artermiloff/steam-games-dataset).
- [Lista de arquivos da versão 2](https://www.kaggle.com/api/v1/datasets/list/artermiloff/steam-games-dataset?datasetVersionNumber=2).

## Como a correspondência foi verificada

Não se usou apenas semelhança de título. A API lista o mesmo nome de arquivo e
**468.641.107 bytes**, exatamente o tamanho local. Uma leitura HTTP parcial do
arquivo da versão 2 confirmou o cabeçalho com **47 colunas**. Os primeiros e os
últimos **65.536 bytes** remotos foram comparados byte a byte com o arquivo local,
com igualdade nos dois trechos. O processamento local já validou **89.618 registros**.

O registro publicável dessa verificação está em
[evidencias/correspondencia_dataset.json](evidencias/correspondencia_dataset.json).
Nenhum CSV completo está sendo publicado. Os metadados de transferência locais
não continham um link de download Kaggle; por isso, não se afirma quem fez o
download inicial nem a data em que o grupo o obteve.

**Limite:** não foi repetido um download integral remoto nesta preparação, portanto
não se afirma ter calculado o SHA-256 de todos os bytes remotos. A identificação
é sustentada pelos metadados e pelas amostras HTTP; a confirmação integral do
arquivo obtido por outra pessoa deve usar o SHA-256 abaixo.

## Obter e colocar em data/

1. Abrir a página da **versão 2** indicada acima.
2. Selecionar `games_march2025_cleaned.csv`, não o arquivo `full`, os arquivos de
   maio de 2024 nem outra versão. Seguir as opções de download exibidas pelo Kaggle.
3. Se receber um arquivo compactado, extrair somente o CSV necessário.
4. Colocá-lo em `data/games_march2025_cleaned.csv`, na raiz do clone. Não sobrescrever
   a cópia original já validada para fazer uma nova tentativa.
5. Conferir tamanho, hash e dimensões antes de executar a carga.

O endpoint público que respondeu às leituras parciais foi:

[Arquivo da versão 2](https://www.kaggle.com/api/v1/datasets/download/artermiloff/steam-games-dataset/games_march2025_cleaned.csv?datasetVersionNumber=2).
O acesso ao serviço pode mudar; não há dependência desse endpoint durante a
apresentação quando o CSV e o ambiente já estão preparados.

Na raiz do repositório, em PowerShell:

```powershell
New-Item -ItemType Directory -Path data -Force | Out-Null
if (-not (Test-Path -LiteralPath 'data/games_march2025_cleaned.csv' -PathType Leaf)) {
    throw 'Baixar o arquivo especifico da versao 2 e coloca-lo em data/'
}
$hashEsperado = '04d8df2778aaa8f8b575934b7072d55224d37a2ded23e8261583f0fcf668dfab'
$hashObtido = (Get-FileHash -LiteralPath 'data/games_march2025_cleaned.csv' -Algorithm SHA256).Hash
if ($hashObtido -ne $hashEsperado) { throw 'Arquivo diferente do validado; conferir versao sem alterar o original' }
.\.venv\Scripts\python.exe -X utf8 analise_dataset.py
```

Esperado: `(89618, 47)` e zero duplicações em `appid`. Um download de arquivo
distinto deve ser investigado, não ajustado artificialmente. `data/` permanece
ignorado pelo Git. A antiga pendência de descobrir a URL foi resolvida por esta
investigação; a obtenção integral a partir do Kaggle ainda deve ser ensaiada pelo grupo.
