# std
from typing import Literal
from dataclasses import dataclass
# interno
from simple_odata_query import QueryParametersValidationException

@dataclass
class TopSkip:
    """Utilizado na realização de paginação do retorno
    - `$skip` quantidade de itens a serem pulados
        - Não deve ser negativo
    - `$top` quantidade máxima de itens retornados
        - Deve ser maior que `0`
        - Não deve ser maior que `maxtop`
    ### `TopSkip.SQL_FORMAT`
    Formato `SQL` da paginação. Pode ser modificado caso sintaxe seja diferente de `LIMIT` e `OFFSET`
    """

    top: int | None = None
    """Quantidade máxima de itens retornados. `LIMIT`"""
    skip: int | None = None
    """Quantidade de itens a serem pulados. `OFFSET`"""
    maxtop: int = 1000
    """Quantidade máxima permitida para o `top`"""

    SQL_FORMAT = """LIMIT {top} OFFSET {skip}"""
    """Formato da versão SQL com os parâmetros `top` e `skip`
    - Pode ser modificado caso sintaxe seja diferente de `LIMIT` e `OFFSET`"""

    def build (self) -> None:
        """Validar se os campos estão no formato e range esperado
        - `QueryParametersValidationException` caso algum campo incorreto"""
        erros = []

        if self.top is not None and self.top <= 0:
            erros.append(f"Campo '$top' deve ser maior que 0")
        if (self.skip or 0) < 0:
            erros.append(f"Campo '$skip' não deve ser negativo")
        if (self.top or 0) > self.maxtop:
            erros.append(f"Campo '$top' não deve ser maior que o máximo '{self.maxtop}'")

        if erros:
            raise QueryParametersValidationException(
                mensagem = "Erro na validação dos query parameters '$top' ou '$skip'",
                detalhes = {
                    "erros": erros
                }
            )

    def to_dict (self) -> dict[Literal["top", "skip"], int]:
        return {
            "top": self.top or self.maxtop,
            "skip": self.skip or 0
        }

    def to_sql (self) -> str:
        """Versão SQL do `top` e `skip`"""
        return self.SQL_FORMAT.format(**self.to_dict())

__all__ = ["TopSkip"]