# Pacote para construções de `SQLs` a partir de Query Parameters estilo OData

Agilizar a transformação de tabelas ou views em APIs com alta dinamicidade

> Pacote para construções de `SQLs` a partir de Query Parameters estilo OData
- `QueryBuilder` classe principal para utilização
- `ResponseExecute` dataclasse com dados e metadatas
- `QueryParametersValidationException` exceção utilizada em erros

> Devido a utilização de **SQLs** dinâmicos, não utilizar funções com banco de dados que aceitem script, o que permite executar mais de um comando por vez. Dessa forma,
problemas de **injection maliciosos** são amenizados.

# Parâmetros

### Select
#### QueryParameter `$select`
Utilizado para selecionar os campos desejados no retorno
- Cada campo pode ter apelido `campo AS alias` e estarem envoltos em aspas `'"`
- Formato `*` ou `campo [AS alias], "campo espaçado" [AS "alias"], ...`

### TopSkip
#### QueryParameters `$top` e `$skip`
Utilizado na realização de paginação do retorno
- `$skip` quantidade de itens a serem pulados
    - Não deve ser negativo
- `$top` quantidade máxima de itens retornados
    - Deve ser maior que `0`
    - Não deve ser maior que constante `QueryBuilder.MAX_TOP`
#### `TopSkip.SQL_FORMAT`
Formato `SQL` da paginação. Pode ser modificado caso sintaxe seja diferente de `LIMIT` e `OFFSET`

### OrderBy
#### QueryParameter `$orderby`
Utilizado para a ordenação do retorno
- O `campo` pode estar envolto em aspas `'"` caso possua espaço
- Formato `campo [ASC|DESC] [NULLS FIRST|LAST], ...`

### Filter
#### QueryParameter `$filter`
Utilizado para filtrar o retorno
- Não é aplicado nenhuma validação e apenas adicionado na versão `SQL`
- Deve ser utilizada a mesma sintaxe do banco de dados

### Count
#### QueryParameter `$count`
Indicação se deve ser feito o `COUNT(*)` como `total` no metadata
- Formato `true|false`

<br>

---

<br>

# Utilização

### 1. Criar o `QueryBuilder` a partir dos query parameters
```python
from simple_odata_query import QueryBuilder

qb = QueryBuilder.from_query("?$count=true&$skip=0&$top=100&$select=campo1%2C%20%27campo2%27%20as%20campo_apelido&$orderby=campo1%2C%20campo2%20DESC%20NULLS%20FIRST&$filter=campo1%20%3C%2010")
qb = QueryBuilder.from_dict({
    '$count': 'true',
    '$skip': '0',
    '$top': '100',
    '$select': "campo1, 'campo2' as campo_apelido",
    '$orderby': 'campo1, campo2 DESC NULLS FIRST',
    '$filter': 'campo1 < 10'
})
```

### 2. Validar o `QueryBuilder` com uma classe anotada com os campos existentes
```python
from simple_odata_query import QueryParametersValidationException

class DadosExemplo:
    campo1: str
    campo2: int

try: qb.validar(DadosExemplo)
except QueryParametersValidationException: ...
```

### 3. Utilizar o método `execute()` para obter e formatar os dados
Deve ser passado para o `execute()` uma função que aceita um `SQL` string e retorna os dados como uma lista das linhas.  
```python
from typing import Any
from simple_odata_query import ResponseExecute

# não deve ser a execução de script, por questão de segurança,
# devido aceitar mais de 1 comando por vez
def sql_execute (sql: str) -> list[dict[str, Any]]:
    ...

response: ResponseExecute = qb.execute("nome_tabela", sql_execute)
response.to_dict()
```

## Exemplo **ResponseExecute**
```json
{
  "@metadata": {
    "$select": "\"id_linha\"",
    "$filter": "id_linha < 10",
    "$orderby": "\"id_linha\" ASC",
    "$top": 3,
    "$skip": 0,
    "$count": true,
    "returned": 3,
    "total": 5,
    "next": true
  },
  "dados": [
    {
      "id_linha": 5
    },
    {
      "id_linha": 6
    },
    {
      "id_linha": 7
    }
  ]
}
```