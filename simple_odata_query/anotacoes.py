# std
from functools import cache
from typing import Any, Protocol
from dataclasses import dataclass

class ClasseAnotada (Protocol):
    """Classe com os nomes e tipos anotados"""
    __annotations__: dict[str, Any]

class ClasseAnotadaComAlias (ClasseAnotada):
    """Classe com os nomes e tipos anotados com propriedade `__alias__` para apelidos"""
    __alias__: dict[str, str]
    """{ "Apelido do Campo": "nome_campo_classe" }"""

@cache
def coletar_campos_existentes (cls: type[ClasseAnotada | ClasseAnotadaComAlias]) -> list[str]:
    """Coletar os campos da `cls` levando em conta hierarquia
    - Utilizado `@cache`"""
    return [
        str(campo)
        for pai in reversed(cls.__mro__)
            if pai is not object
        for objetos in (getattr(pai, "__annotations__", {}), getattr(pai, "__alias__", {}))
        for campo in objetos
    ]

@dataclass
class ResponseExecute:
    """Response do `QueryBuilder.execute` com os dados e metadatas
    - Usar `to_dict()` para transformar"""

    metadata: dict[str, Any]
    dados: list[dict[str, Any]]

    def to_dict (self, nome_dados="dados") -> dict[str, Any]:
        """Transformar o `Response` para a versão `dict`
        - `nome_dados` para renomear o campo `dados`"""
        return {
            "@metadata": self.metadata,
            nome_dados: self.dados
        }

__all__ = [
    "ClasseAnotada",
    "ClasseAnotadaComAlias",
    "coletar_campos_existentes",
    "ResponseExecute",
]