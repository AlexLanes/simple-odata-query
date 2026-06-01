# std
from dataclasses import dataclass
# interno
from .anotacoes import TVersaoCampoSQL
from . import QueryParametersValidationException

def quote (t: str, char="\"") -> str:
    """Envolve com o `char` se a `str` tiver espaço"""
    return f"{char}{t}{char}" if " " in t else t

@dataclass
class Campo:
    nome: str
    alias: str | None = None
    versao_sql: str | None = None

    def to_sql (self) -> str:
        alias = quote(self.alias or self.nome)
        versao_sql = (
            quote(self.versao_sql)
            if self.versao_sql
            else quote(self.nome)
        )
        return (
            f"{versao_sql} AS {alias}"
            if versao_sql != alias
            else versao_sql
        )

    def to_metadata (self) -> str:
        nome = quote(self.nome, char="'")
        alias = quote(self.alias or "", char="'")
        return (
            f"{nome} AS {alias}"
            if alias and nome != alias
            else nome
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
                nome = " ".join(partes).strip()
                self.campos.append(Campo(nome))
                continue

            # Com alias
            self.campos.append(
                Campo(
                    nome  = " ".join(partes[: index_as]).strip(),
                    alias = " ".join(partes[index_as + 1 :]).strip() or None
                )
            )

    def validar (self, esperados: TVersaoCampoSQL) -> None:
        """Validar se os campos do `select` estão presentes nos `esperados`
        - Adicionar a `versão_sql` nos `campos`
        - `QueryParametersValidationException` caso algum campo incorreto"""
        if not self.campos:
            self.campos = [
                Campo(nome_modelo, versao_sql=versao_sql)
                for nome_modelo, versao_sql in esperados.items()
            ]
            return

        inesperados = list[str]()
        for campo in self.campos:
            if campo.nome in esperados:
                campo.versao_sql = esperados[campo.nome]
            else: inesperados.append(campo.nome)

        if inesperados: raise QueryParametersValidationException(
            mensagem = "Erro na validação do query parameter '$select'",
            detalhes = {
                "recebidos": [campo.nome for campo in self.campos],
                "inesperados": inesperados,
                "esperados": list(esperados),
            }
        )

    def to_sql (self) -> str:
        """Versão `SQL: SELECT` com os campos separados por `,`
        - Campos com espaço são envolvidos em aspas duplas"""
        campos = ", ".join(campo.to_sql() for campo in self.campos)
        return f"SELECT {campos}"

    def to_metadata (self) -> str:
        """Versão `@metadata: $select` com os campos separados por `,`
        - Campos com espaço são envolvidos em aspas"""
        return ", ".join(campo.to_metadata() for campo in self.campos)

__all__ = ["Select"]