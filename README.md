# Pacote para construções de `SQLs` a partir de Query Parameters estilo OData

Agilizar a transformação de tabelas ou views em APIs com alta dinamicidade

### `ODataQueryBuilder` classe principal para utilização
### `QueryParametersValidationException` exceção utilizada em erros
- `IStatement[IClasseModelo]` interface com o método `execute` preparado para retornar um `ODataResponse`
- `ODataResponse` dataclasse com os dados e metadados retornados
- `IClasseModelo` interface modelo esperada com os nomes das propriedades anotadas e nome da `__tabela__`
- `Field` adicionar informações em um campo. Usar em conjunto ao `Annotated[T, Field()]`
    - `Field(nome_sql=)` Para indicar o nome do campo no banco de dados, caso seja diferente do modelo ou possua espaço
    - `Field().add_expand(...)` Adicionar uma relação de `$expand` no campo do modelo

> Devido a utilização de **SQLs dinâmicos**, não utilizar funções com banco de dados que aceitem script, o que permite executar mais de um comando por vez. Dessa forma, problemas de **injection maliciosos** são amenizados.

# Parâmetros

### QueryParameter `$select`
Utilizado para selecionar os campos desejados no retorno
- Cada campo pode ter apelido `campo AS alias` e estarem envoltos em aspas `'"`
- Formato `*` ou `campo [AS alias], "campo espaçado" [AS "alias"], ...`

### QueryParameters `$top` e `$skip`
Utilizado na realização de paginação do retorno
- `$skip` quantidade de itens a serem pulados
    - Não deve ser negativo
- `$top` quantidade máxima de itens retornados
    - Deve ser maior que `0`
    - Não deve ser maior que constante `QueryBuilder.MAX_TOP`
#### `TopSkip.SQL_FORMAT`
Formato `SQL` da paginação. Pode ser modificado caso sintaxe seja diferente de `LIMIT` e `OFFSET`

### QueryParameter `$orderby`
Utilizado para a ordenação do retorno
- O `campo` pode estar envolto em aspas `'"` caso possua espaço
- Formato `campo [ASC|DESC] [NULLS FIRST|LAST], ...`

### QueryParameter `$expand`
Utilizado para a criação de relação com outras tabelas
- Formato `*` ou `expand1, expand2, ...`

### QueryParameter `$filter`
Utilizado para filtrar o retorno
- Não é aplicado nenhuma validação e apenas adicionado na versão `SQL`
- Deve ser utilizada a mesma sintaxe do banco de dados

### QueryParameter `$count`
Indicação se deve ser feito o `COUNT(*) AS total` no metadata
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
    "$select": "campo1, 'campo2' as campo_apelido",
    "$expand": "expand1, expand2",
    "$filter": "campo1 < 10"
    "$orderby": "campo1, campo2 DESC NULLS FIRST",
    "$skip": "0",
    "$top": "100",
    "$count": "true",
})
```

### 2. Realizar o `build` da classe anotada para obter o `IStatement[IClasseModelo]`
- `Field(nome_sql=)` Indicar o nome do campo no banco de dados, caso seja diferente do modelo ou possua espaço
- `Field().add_expand(...)` Adicionar uma relação de `$expand` no campo do modelo
```python
from typing import Annotated
from simple_odata_query import Field, IStatement, QueryParametersValidationException

class AtoresFilme:
    __tabela__ = "film_actor"
    id:      Annotated[int, Field(nome_sql="actor_id")]
    film_id: int

class CategoriaFilme:
    __tabela__ = "film_category"
    id:      Annotated[int, Field(nome_sql="category_id")]
    film_id: int

class Filme:
    __tabela__ = "film"
    id:          Annotated[int, Field(nome_sql="film_id")
                                .add_expand("atores",    on=(AtoresFilme, "film_id"), include=False)
                                .add_expand("categoria", on=(CategoriaFilme, "film_id"), unique=True)]
    titulo:      Annotated[str, Field(nome_sql="title")]
    descricao:   Annotated[str, Field(nome_sql="description")]
    year:        int

try: statement: IStatement[Filme] = qb.build(Filme)
except QueryParametersValidationException as erro:
    print(erro)
    raise
```

### 3. Utilizar o método `execute()` para obter os dados formatados
Deve ser passado para o `execute()` uma função que aceita um `SQL` string e retorna os dados como uma lista das linhas
```python
from typing import Any
from simple_odata_query import ODataResponse

# não deve ser a execução de script, por questão de segurança,
# devido aceitar mais de 1 comando por vez
def sql_execute (sql: str) -> list[dict[str, Any]]:
    ...

response: ODataResponse = statement.execute(sql_execute)
response.to_dict()
```

## Exemplo **ODataResponse**
```json
{
	"@metadata": {
		"$select": "*",
		"$expand": "atores, categoria",
		"$filter": null,
		"$orderby": null,
		"$top": 1,
		"$skip": 0,
		"$count": true,
		"elapsed_ms": 9.14,
		"returned": 1,
		"total": 1000,
		"next": true
	},
	"dados": [
		{
			"id": 1,
			"titulo": "Alone Trip",
			"descricao": "A Fast-Paced Character Study of a Composer And a Dog who must Outgun a Boat in An Abandoned Fun House",
			"year": 2006,
			"atores": [
                { "id": 3  },
                { "id": 12 },
                { "id": 13 }
            ],
			"categoria": {
				"id": 12,
				"film_id": 17
			}
		}
	]
}
```