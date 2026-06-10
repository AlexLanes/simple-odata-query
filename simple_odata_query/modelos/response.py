# std
from typing import Any
from dataclasses import dataclass

@dataclass
class ODataResponse:
    """Response do `IStatement.execute` com os dados e metadados
    - Usar `to_dict()` para transformar"""

    metadata: dict[str, Any]
    results: list[dict[str, Any]]

    def __repr__ (self) -> str:
        return f"<ODataResponse returned={len(self.results)}>"

    def to_dict (self, nome_results="results") -> dict[str, Any]:
        """Transformar o para a versão `dict`
        - `nome_results` para renomear o campo `results`"""
        return {
            "@metadata": self.metadata,
            nome_results: self.results
        }

__all__ = ["ODataResponse"]