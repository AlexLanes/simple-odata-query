"""Pacote para construções de `SQLs` a partir de Query Parameters estilo OData
### `ODataQueryBuilder` classe principal para utilização
### `QueryParametersValidationException` exceção utilizada em erros
- `IStatement[IClasseModelo]` interface com o método `execute` preparado para retornar um `ODataResponse`
- `ODataResponse` dataclasse com os dados e metadados retornados
- `IClasseModelo` interface modelo esperada com os nomes das propriedades anotadas e nome da `__tabela__`
- `Field` adicionar informações em um campo. Usar em conjunto ao `Annotated[T, Field()]`
    - `Field(nome_sql=)` Para indicar o nome do campo no banco de dados, caso seja diferente do modelo ou possua espaço
    - `Field().add_expand(...)` Adicionar uma relação de `$expand` no campo do modelo"""

from simple_odata_query.exception import QueryParametersValidationException
from simple_odata_query.modelos import Field, IClasseModelo, IStatement, ODataResponse

from simple_odata_query.builder import ODataQueryBuilder