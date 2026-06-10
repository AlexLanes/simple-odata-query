# std
from typing import Self, Mapping
from dataclasses import dataclass, field
from urllib.parse import parse_qs as parse_query_string
# interno
from . import *
from .querys import *
from .coletor import ColetorModelo

@dataclass
class ODataQueryBuilder:
    """Classe para construções de consultas `SQL` simplificadas com base em `QueryParameters` no estilo `OData`

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
    """

    select: Select = field(default_factory=Select)
    """`$select` selecionar os campos que devem ser retornados"""
    topskip: TopSkip = field(default_factory=TopSkip)
    """`$top` e `$skip` para a realização de paginação do retorno"""
    orderby: OrderBy = field(default_factory=OrderBy)
    """`$orderby` para a ordenação do retorno"""
    expand: Expand = field(default_factory=Expand)
    """`$expand` para a criação de relação com outras tabelas"""

    filter: str | None = None
    """`$filter` utilizado para filtrar o retorno
    - Não é aplicado nenhuma validação e apenas adicionado na versão `SQL`
    - Deve ser utilizada a mesma sintaxe do banco de dados"""
    count: bool = False
    """`$count` indicação se deve ser feito o `COUNT(*) AS total` no metadata"""

    MAX_TOP = 1000
    """Valor máximo do `$top`"""

    @classmethod
    def from_query (cls, query: str) -> Self:
        """Criar o `QueryBuilder` a partir da `query` string
        - Exceções de tipos inesperados são postergados para o método `.validar()`"""
        return cls.from_dict({
            key: value
            for key, (value, *_) in parse_query_string(query.lstrip("?")).items()
        })

    @classmethod
    def from_dict (cls, query: Mapping[str, str]) -> Self:
        """Criar o `QueryBuilder` a partir do mapa de parâmetros `query`
        - Exceções de tipos inesperados são postergados para o método `.build()`"""
        qb, erros = cls(), []
        query = {
            k.lower().strip().removeprefix("$"): v
            for k, v in query.items()
        }

        # $select
        if select := str(query.get("select", "")).strip():
            qb.select = Select(select)

        # $orderby
        if orderby := str(query.get("orderby", "")).strip():
            qb.orderby = OrderBy(orderby)

        # $expand
        if expand := str(query.get("expand", "")).strip():
            qb.expand = Expand(expand)

        # $filter
        if filter := str(query.get("filter", "")).strip():
            qb.filter = filter

        # $count
        count = str(query.get("count", "false")).lower().strip()
        if count in ("false", "true"): qb.count = count == "true"
        else: erros.append({
            "query": "$count",
            "mensagem": "Tipo inesperado para o query parameter",
            "esperado": "true|false",
            "recebido": count,
        })

        # $top | $skip
        ok = True
        top = str(query.get("top", "")).lower().strip() or None
        skip = str(query.get("skip", "")).lower().strip() or None
        for nome, valor in [("top", top), ("skip", skip)]:
            if valor is None or valor.isdigit():
                continue
            ok = False
            erros.append({
                "query": f"${nome}",
                "mensagem": "Tipo inesperado para o query parameter",
                "esperado": "integer",
                "recebido": valor,
            })
        if ok: qb.topskip = TopSkip(
            top  = int(top) if top is not None else None,
            skip = int(skip) if skip is not None else None,
            maxtop = ODataQueryBuilder.MAX_TOP
        )

        if erros: setattr(qb, "_erros", erros)
        return qb

    def build[T: IClasseModelo] (self, modelo: type[T]) -> IStatement[T]:
        """Realizar o build do `Statement` para a classe `modelo`
        - `QueryParametersValidationException` caso alguma falha de validação
        - `modelo` Classe modelo com os nomes das propriedades anotadas e nome da `__tabela__`"""
        if getattr(self, "_built", False):
            raise RuntimeError("Não reutilizar o ODataQueryBuilder.build()")
        if erros := getattr(self, "_erros", []):
            raise QueryParametersValidationException(
                mensagem = "Erro na validação de um ou mais Query Parameters",
                detalhes = {
                    "erros": erros
                }
            )

        coletor = ColetorModelo.from_modelo(modelo)
        self.topskip.build()
        self.select.build(coletor)
        self.expand.build(coletor)
        self.orderby.build(coletor)

        setattr(self, "_built", True)
        return (
            Statement(modelo, self)
            if not self.expand.expands else
            StatementComExpand(modelo, self)
        )

# Evitar `Circular Import`
from .statements.statement import Statement
from .statements.expand import StatementComExpand

__all__ = ["ODataQueryBuilder"]