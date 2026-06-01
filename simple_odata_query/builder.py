# std
from dataclasses import dataclass, field
from typing import Any, Self, Mapping, Callable
from urllib.parse import parse_qs as parse_query_string
# interno
from .anotacoes import *
from .select import Select
from .orderby import OrderBy
from .top_skip import TopSkip
from . import QueryParametersValidationException

@dataclass
class QueryBuilder:
    """Classe para construções de consultas `SQL` simplificadas com base em `QueryParameters` no estilo `OData`

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
    ### `TopSkip.SQL_FORMAT`
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
    ```
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
    Possível de se aplicar `Alias` para o nome do campo no banco de dados
    ```
    from typing import Annotated
    from simple_odata_query import QueryParametersValidationException

    class Usuarios:
        id: int
        nome: str
        sobrenome: str
        idade: Annotated[int, "Idade"]
        nome_sobrenome: Annotated[str, {"alias": "nome e sobrenome"}]
        criado_em: str = Field(alias="Criado Em") # Default com propriedade "alias"

    try: qb.validar(Usuarios)
    except QueryParametersValidationException: ...
    ```

    ### 3. Utilizar o método `execute()` para obter e formatar os dados
    Deve ser passado para o `execute()` uma função que aceita um `SQL` string e retorna os dados como uma lista das linhas.  
    ```
    from typing import Any
    from simple_odata_query import ResponseExecute

    # não deve ser a execução de script, por questão de segurança,
    # devido aceitar mais de 1 comando por vez
    def sql_execute (sql: str) -> list[dict[str, Any]]:
        ...

    response: ResponseExecute = qb.execute("nome_tabela", sql_execute)
    response.to_dict()
    ```
    """

    select: Select = field(default_factory=Select)
    """`$select` selecionar os campos que devem ser retornados"""
    topskip: TopSkip = field(default_factory=TopSkip)
    """`$top` e `$skip` para a realização de paginação do retorno"""
    orderby: OrderBy = field(default_factory=OrderBy)
    """`$orderby` para a ordenação do retorno"""

    filter: str | None = None
    """`$filter` utilizado para filtrar o retorno
    - Não é aplicado nenhuma validação e apenas adicionado na versão `SQL`
    - Deve ser utilizada a mesma sintaxe do banco de dados"""
    count: bool = False
    """`$count` indicação se deve ser feito o `COUNT(*)` como `total` no metadata"""

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
        - Exceções de tipos inesperados são postergados para o método `.validar()`"""
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
            maxtop = QueryBuilder.MAX_TOP
        )

        if erros: setattr(qb, "_erros", erros)
        return qb

    def validar (self, classe_anotada: type) -> Self:
        """Invocar os métodos de validação de cada propriedade
        - `classe_anotada` utilizada para validar os campos existentes
        - `QueryParametersValidationException` caso alguma falha de validação"""
        if erros := getattr(self, "_erros", []):
            raise QueryParametersValidationException(
                mensagem = "Erro na validação de um ou mais Query Parameters",
                detalhes = {
                    "erros": erros
                }
            )

        campos = coletar_campos_classe(classe_anotada)
        self.topskip.validar()
        self.select.validar(campos)
        self.orderby.validar(campos)

        return self

    def execute (self, tabela: str, sql_execute: Callable[[str], list[dict[str, Any]]]) -> ResponseExecute:
        """Executar a consulta na `tabela`
        - Retornado classe `ResponseExecute` com os dados desejados. Usar `.to_dict()` para transformar
        - `sql_execute` deve ser uma função que aceita um `SQL` string e retorna os dados como uma lista das linhas
        - `sql_execute` não deve ser a execução de script, por questão de segurança, devido aceitar mais de 1 comando por vez"""
        dados = sql_execute(self.to_sql(tabela))
        metadata = self.to_metadata(
            returned = len(dados),
            total = lambda: int(
                sql_execute(self.to_sql_count(tabela))
                [0]
                ["total"]
            )
        )
        return ResponseExecute(
            metadata = metadata,
            dados = dados
        )

    def to_sql (self, tabela: str) -> str:
        """Realizar o build dos parâmetros para a versão `SQL` para o `SELECT`"""
        return f"""
            {self.select.to_sql()}
            FROM {tabela}
            {f"WHERE {self.filter}" if self.filter else ""}
            {self.orderby.to_sql()}
            {self.topskip.to_sql()}
        """

    def to_sql_count (self, tabela: str) -> str:
        """Realizar o build dos parâmetros para a versão `SQL` para o `count(*) as total`"""
        return f"""
            SELECT count(*) as total
            FROM {tabela}
            {f"WHERE {self.filter}" if self.filter else ""}
            {self.topskip.SQL_FORMAT.format(top=1, skip=0)}
        """

    def to_metadata (self, returned: int, total: Callable[[], int]) -> dict[str, Any]:
        """Construir um `dict` com campos de metadata
        - `returned` quantidade de itens retornados
        - `total` obtém o total de itens existentes considerando o `$filter`. Dependente do `$count`"""
        top, skip = self.topskip.to_dict().values()
        metadata = {
            "$select": self.select.to_metadata(),
            "$filter": self.filter,
            "$orderby": self.orderby.to_metadata(),
            "$top": top,
            "$skip": skip,
            "$count": self.count,
            "returned": returned,
        }

        if self.count:
            metadata["total"] = (t := total())
            metadata["next"] = (skip + top) < t

        return metadata

__all__ = ["QueryBuilder"]