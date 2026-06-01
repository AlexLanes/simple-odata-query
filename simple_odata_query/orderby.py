# std
from typing import Literal
from dataclasses import dataclass
# interno
from .anotacoes import TVersaoCampoSQL
from . import QueryParametersValidationException

def quote (t: str, char="\"") -> str:
    """Envolve com o `char` se a `str` tiver espaço"""
    return f"{char}{t}{char}" if " " in t else t

@dataclass
class OrderValido:
    nome: str
    ordem: Literal["ASC", "DESC"] = "ASC"
    nulls: Literal["FIRST", "LAST"] | None = None

    def to_sql (self) -> str:
        return " ".join([
            quote(self.nome),
            self.ordem,
            f"NULLS {self.nulls}" if self.nulls else ""
        ]).rstrip()

    def to_metadata (self) -> str:
        return " ".join([
            quote(self.nome, char="'"),
            self.ordem,
            f"NULLS {self.nulls}" if self.nulls else ""
        ]).rstrip()

class OrderBy:
    """Utilizado para a ordenação do retorno
    - O `campo` pode estar envolto em aspas `'"` caso possua espaço
    - Formato `campo [ASC|DESC] [NULLS FIRST|LAST], ...`"""

    partes: list[str]
    """Partes do `orderby` separadas pela `,`"""
    validos: list[OrderValido]

    def __init__ (self, orderby: str | None = None) -> None:
        self.validos = []
        self.partes = [
            campo
            for campo in map(str.strip, (orderby or "").split(","))
            if campo
        ]

    def index_nome_campo (self, parte: str) -> int:
        """Encontrar o index do nome do campo na `parte`
        - Primeira palavra ou procurar entre `'"`"""
        index, aspas = 0, False

        while index < len(parte) - 1:
            char = parte[index]

            if char in "'\"":
                if aspas: return index + 1
                aspas = True
            if not aspas and char == " ":
                return index

            index += 1

        return len(parte) - 1

    def validar (self, esperados: TVersaoCampoSQL) -> None:
        """Validar se os campos do `orderby` estão presentes nos `esperados` e com o formato é o esperado
        - `QueryParametersValidationException` caso algum campo incorreto"""
        if self.validos or not self.partes:
            return

        erros = []
        for parte in self.partes:
            index_nome = self.index_nome_campo(parte)
            nome = parte[0 : index_nome + 1].strip()
            campo = OrderValido(nome.strip("'\""))

            if campo.nome not in esperados:
                erros.append({
                    "parte": parte,
                    "seção": nome,
                    "mensagem": f"O Campo({nome}) é inesperado",
                })
                continue

            ordem_nulls = [
                resto
                for resto in parte.removeprefix(nome)
                                  .strip().upper()
                                  .split()
                if resto
            ]
            match ordem_nulls:
                case []: pass
                case ["ASC" | "DESC" as order]:
                    campo.ordem = order
                case ["NULLS", "FIRST" | "LAST" as nulls]:
                    campo.nulls = nulls
                case ["ASC" | "DESC" as order, "NULLS", "FIRST" | "LAST" as nulls]:
                    campo.ordem = order
                    campo.nulls = nulls
                case _:
                    erros.append({
                        "parte": parte,
                        "seção": " ".join(ordem_nulls),
                        "mensagem": f"Formato inesperado para a ordem ou nulls",
                    })
                    continue

            self.validos.append(campo)

        if not erros: return
        raise QueryParametersValidationException(
            mensagem = "Erro na validação do query parameter '$orderby'",
            detalhes = {
                "erros": erros,
                "campos_esperados": list(esperados),
                "formato_esperado": "campo [ASC|DESC] [NULLS FIRST|LAST], ..."
            }
        )

    def to_sql (self) -> str | None:
        """Versão `SQL: ORDER BY` com os campos separados por `,`
        - Campos com espaço são envolvidos em aspas duplas
        - Retornado `None` caso o `ORDER BY` não tenha sido informado"""
        campos = ", ".join(order.to_sql() for order in self.validos)
        return f"ORDER BY {campos}" if campos else None

    def to_metadata (self) -> str | None:
        """Versão `@metadata: $orderby` com os campos separados por `,`
        - Campos com espaço são envolvidos em aspas
        - Retornado `None` caso o `ORDER BY` não tenha sido informado"""
        return ", ".join(order.to_metadata() for order in self.validos) or None

__all__ = ["OrderBy"]