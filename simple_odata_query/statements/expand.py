# std
from time import perf_counter
from itertools import groupby
from functools import cached_property
from typing import Any, Callable, override
# interno
from .statement import Statement
from simple_odata_query import *
from simple_odata_query.querys.select import CampoSelect, quote
from simple_odata_query.coletor import ColetorModelo, ExpandData

class StatementComExpand[T: IClasseModelo] (Statement[T]):

    coletor: ColetorModelo
    campos_expand_faltando_select: set[str]
    """Campos que são de relações do `$expand` que não foram inclusos no `$select`"""

    TABELA_CTE_EXPAND = "cte_odata_builder_expand"

    @override
    def __init__ (self, modelo, qb) -> None:
        super().__init__(modelo, qb)

        self.coletor = ColetorModelo.from_modelo(modelo)
        campos_select = {c.nome for c in self.qb.select.campos}
        self.campos_expand_faltando_select = {
            campo
            for campo in self.coletor.campos_com_expand
            if campo not in campos_select
        }

    @override
    def __repr__ (self) -> str:
        expands = ", ".join(self.coletor.nomes_expand)
        nome = f"{self.modelo.__module__}.{self.modelo.__name__}"
        return f"<Statement tabela={self.tabela!r} modelo={nome!r} expands={expands!r}>"

    @override
    def execute (self, sql_execute) -> ODataResponse:
        inicio = perf_counter()

        dados = sql_execute(self.to_sql())
        self.update_expands(sql_execute, dados)

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
    @override
    def sql_tabela_cte (self) -> str:
        # Adicionado campos que sejam `Coletor.expands` mesmo que não tenham sido requisitados no `$select`
        return "\n".join((
            f"WITH {self.TABELA_CTE} AS (",
            f"    {self.select_com_campos_de_expand}",
            f"    FROM {self.tabela}",
            ")"
        ))

    @property
    def expands (self) -> list[ExpandData]:
        """Expands ordenados pelo identificador primário"""
        return sorted(
            self.qb.expand.expands,
            key = lambda e: e.identificador
        )

    @cached_property
    def select_com_campos_de_expand (self) -> str:
        # Todos os campos de expand já presentes no `$select`
        sql = self.qb.select.to_sql_alias()
        if not self.campos_expand_faltando_select:
            return sql

        # Necessário incluir os campos do `$expand`
        partes = [sql]
        partes.extend(
            CampoSelect(nome=campo, nome_sql=self.coletor.campos[campo])
            .to_sql_alias()
            for campo in self.campos_expand_faltando_select
        )
        return ", ".join(partes)

    def expand_to_sql_model (self, expand: ExpandData) -> str:
        campo_identificador = expand.identificador
        campo_fk = quote(expand.coletor.campos[expand.nome_modelo_fk])
        campos_expand = ", ".join(
            f"t1.{quote(nome_sql)} AS {nome_modelo}"
            if nome_sql != nome_modelo else
            f"t1.{quote(nome_sql)}"

            for nome_modelo, nome_sql in expand.coletor.campos.items()
        )

        return "\n".join(
            linha
            for linha in (
                self.sql_tabela_cte + ",",

                f"{self.TABELA_CTE_EXPAND} AS (",
                f"    SELECT {campo_identificador}",
                f"    FROM {self.TABELA_CTE}",
                f"    WHERE {self.qb.filter}" if self.qb.filter else "",
                f"    {self.qb.orderby.to_sql() or ""}",
                f"    {self.qb.topskip.to_sql()}",
                ")",

                f"SELECT {campos_expand}",
                f"FROM {expand.tabela} t1",
                f"JOIN {self.TABELA_CTE_EXPAND} t2",
                f"    ON t1.{campo_fk} = t2.{campo_identificador}",
                f"ORDER BY t1.{campo_fk} ASC"
            )
            if linha and not linha.isspace()
        )

    def update_expands (self, sql_execute: Callable[[str], list[dict[str, Any]]],
                              dados: list[dict[str, Any]]) -> None:
        """Adicionar os expands em `dados` e remover as chaves do `campos_expand_faltando_select`"""
        for nome_identificador, expands in groupby(self.expands, lambda e: e.identificador):
            expands = list(expands)
            ultimo_expand = expands[-1]
            necessario_remover = nome_identificador in self.campos_expand_faltando_select

            for expand in expands:
                groupby_fk = {
                    fk: list(grupo)
                    for fk, grupo in groupby(
                        iterable = sql_execute(self.expand_to_sql_model(expand)),
                        key      = lambda item: item[expand.nome_modelo_fk]
                    )
                }

                for item in dados:
                    itens_expand = groupby_fk.get(item[nome_identificador])
                    item[expand.nome] = (
                        (itens_expand[0] if itens_expand else {})
                        if expand.unique else
                        (itens_expand if itens_expand is not None else [])
                    )

                    # Remover a chave identificadora, não requisitada no `$select`, mas incluída por causa do `$expand` 
                    if necessario_remover and expand is ultimo_expand:
                        item.pop(nome_identificador)
                    # Remover a chave fk caso requisitado pelo `expand.include`
                    if itens_expand and not expand.include:
                        for ie in itens_expand:
                            if expand.nome_modelo_fk in ie:
                                ie.pop(expand.nome_modelo_fk)
                            else: break

__all__ = ["StatementComExpand"]