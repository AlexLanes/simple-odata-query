# std
from typing import Iterable
from dataclasses import dataclass
# interno
from . import QueryParametersValidationException

@dataclass
class Campo:

    nome: str
    alias: str | None = None

    def to_sql (self) -> str:
        return (
            f'"{self.nome}"'
            if not self.alias else
            f'"{self.nome}" AS "{self.alias}"'
        )

class Select:
    """Utilizado para selecionar os campos desejados no retorno
    - Cada campo pode ter apelido `campo AS alias` e estarem envoltos em aspas `'"`
    - Formato `campo [AS alias], "campo espaçado" [AS "alias"], ...`"""

    campos: list[Campo]

    def __init__ (self, select: str | None = None) -> None:
        self.campos = []
        if not select or select.strip() == "*":
            return

        for parte in map(str.strip, select.split(",")):
            if not parte or parte.isspace():
                continue

            partes = [p.strip("'\"") for p in parte.split()]
            *_, index_as = [
                index
                for index, p in enumerate(partes)
                if p.lower() == "as"
            ] or [0]

            # Sem alias "campo AS alias"
            if index_as == 0:
                nome = " ".join(partes)
                self.campos.append(Campo(nome))
                continue

            # Com alias
            self.campos.append(
                Campo(
                    nome  = " ".join(partes[: index_as]),
                    alias = " ".join(partes[index_as + 1 :]) or None
                )
            )

    def validar (self, campos_esperados: Iterable[str]) -> None:
        """Validar se os campos do `select` estão presentes nos `campos_esperados`
        - `QueryParametersValidationException` caso algum campo incorreto"""
        if not self.campos: return

        campos = [campo.nome for campo in self.campos]
        inesperados = [
            campo
            for campo in campos
            if campo not in campos_esperados
        ]

        if not inesperados: return
        raise QueryParametersValidationException(
            mensagem = "Erro na validação do query parameter '$select'",
            detalhes = {
                "recebidos": campos,
                "inesperados": inesperados,
                "esperados": campos_esperados,
            }
        )

    def to_sql (self) -> str:
        """Versão SQL `SELECT` com os campos e alias envolvidos em `"`
        - `SELECT *` Caso nenhum campo informado"""
        campos = (
            "*"
            if not self.campos else
            ", ".join(campo.to_sql() for campo in self.campos)
        )
        return f"SELECT {campos}"

__all__ = ["Select"]