# std
from typing import Any, Callable
# interno
from simple_odata_query import IClasseModelo, ODataResponse

class IStatement[T: IClasseModelo]:
    """Interface `Statement[IClasseModelo]` com o método `execute` preparado para retornar um `ODataResponse`
    - Utilizar para anotações"""

    modelo: type[T]
    """`IClasseModelo` que o `Statement` foi preparado"""

    def execute (self, sql_execute: Callable[[str], list[dict[str, Any]]]) -> ODataResponse:
        """Executar o `Statement` e retornar o `ODataResponse`
        - Usar `.to_dict()` para transformar o retorno
        - `sql_execute` deve ser uma função que aceita um `SQL` string e retorna os dados como uma lista das linhas
        - `sql_execute` não deve ser a execução de script, por questão de segurança, devido aceitar mais de 1 comando por vez"""
        ...

__all__ = ["IStatement"]