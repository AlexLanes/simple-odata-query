# std
from time import perf_counter
from typing import Any, Callable
from functools import cached_property
# interno
from simple_odata_query import *
from simple_odata_query.builder import ODataQueryBuilder

class Statement[T: IClasseModelo] (IStatement[T]):

    modelo: type[T]
    qb: ODataQueryBuilder

    TABELA_CTE = "cte_odata_builder"

    def __init__ (self, modelo: type[T], qb: ODataQueryBuilder) -> None:
        self.qb = qb
        self.modelo = modelo

    def __repr__ (self) -> str:
        nome = f"{self.modelo.__module__}.{self.modelo.__name__}"
        return f"<Statement tabela={self.tabela!r} modelo={nome!r}>"

    @property
    def tabela (self) -> str:
        return self.modelo.__tabela__

    def execute (self, sql_execute) -> ODataResponse:
        inicio = perf_counter()
        dados = sql_execute(self.to_sql())
        metadata = self.to_metadata(
            inicio   = inicio,
            returned = len(dados),
            total    = lambda: int(
                sql_execute(self.to_sql_count())
                [0]
                ["total"]
            )
        )

        return ODataResponse(
            metadata = metadata,
            results  = dados,
        )

    @cached_property
    def sql_tabela_cte (self) -> str:
        """Criar a `TABELA_CTE` com o `WITH`
        - Nomes dos campos devidamente traduzidos para o modelo"""
        return "\n".join((
            f"WITH {self.TABELA_CTE} AS (",
            f"    {self.qb.select.to_sql_alias()}",
            f"    FROM {self.tabela}",
            ")"
        ))

    def to_sql (self) -> str:
        """Realizar o build dos parâmetros para a versão `SQL: SELECT`
        - Utilizado `WITH` devido aos possíveis `ALIAS` nos campos"""
        return "\n".join(
            linha
            for linha in (
                self.sql_tabela_cte,
                "SELECT *",
                f"FROM {self.TABELA_CTE}",
                f"WHERE {self.qb.filter}" if self.qb.filter else "",
                self.qb.orderby.to_sql(),
                self.qb.topskip.to_sql(),
            )
            if linha
        )

    def to_sql_count (self) -> str:
        """Realizar o build dos parâmetros para a versão `SQL: COUNT(*) AS total`
        - Utilizado `WITH` devido aos possíveis `ALIAS` nos campos"""
        return "\n".join(
            linha
            for linha in (
                self.sql_tabela_cte,
                "SELECT COUNT(*) AS total",
                f"FROM {self.TABELA_CTE}",
                f"WHERE {self.qb.filter}" if self.qb.filter else "",
                self.qb.topskip.SQL_FORMAT.format(top=1, skip=0),
            )
            if linha
        )

    def to_metadata (self, returned: int, total: Callable[[], int], inicio: float) -> dict[str, Any]:
        """Construir um `dict` com campos de metadata
        - `returned` quantidade de itens retornados
        - `inicio` usado para gerar o tempo de execução
        - `total` é condicional do `$count` e obtém o total de itens existentes considerando o `$filter`"""
        qb = self.qb
        top, skip = qb.topskip.to_dict().values()
        metadata = {
            "$select": qb.select.to_metadata(),
            "$expand": qb.expand.to_metadata(),
            "$filter": qb.filter,
            "$orderby": qb.orderby.to_metadata(),
            "$top": top,
            "$skip": skip,
            "$count": qb.count,
            "elapsed_ms": round((perf_counter() - inicio) * 1000, 2),
            "returned": returned,
        }

        if qb.count:
            metadata["total"] = (t := total())
            metadata["next"] = (skip + top) < t

        return metadata

__all__ = ["Statement"]