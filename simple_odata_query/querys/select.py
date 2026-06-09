# std
from dataclasses import dataclass
# interno
from simple_odata_query.coletor import ColetorModelo
from simple_odata_query import QueryParametersValidationException

def quote (t: str, char="\"") -> str:
    """Envolve com o `char` se a `str` tiver espaço"""
    return f"{char}{t}{char}" if " " in t else t

@dataclass
class CampoSelect:

    nome: str
    alias: str | None = None
    nome_sql: str | None = None

    def to_sql_alias (self) -> str:
        alias = quote(self.alias or self.nome)
        nome_sql = (
            quote(self.nome_sql)
            if self.nome_sql
            else quote(self.nome)
        )
        return (
            f"{nome_sql} AS {alias}"
            if nome_sql != alias else
            nome_sql
        )

    def to_sql_model (self) -> str:
        return quote(self.nome)

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

    campos: list[CampoSelect]

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
                self.campos.append(CampoSelect(nome))
                continue

            # Com alias
            self.campos.append(
                CampoSelect(
                    nome  = " ".join(partes[: index_as]).strip(),
                    alias = " ".join(partes[index_as + 1 :]).strip() or None
                )
            )

    def build (self, coletor: ColetorModelo) -> None:
        """Validar se os campos do `select` estão presentes no `coletor` e adicionar a `versão_sql` nos `self.campos`
        - `QueryParametersValidationException` caso algum campo incorreto"""
        if not self.campos:
            self.campos = [
                CampoSelect(nome_modelo, nome_sql=nome_sql)
                for nome_modelo, nome_sql in coletor.campos.items()
            ]
            return

        inesperados = list[str]()
        for campo in self.campos:
            if campo.nome in coletor.campos:
                campo.nome_sql = coletor.campos[campo.nome]
            else: inesperados.append(campo.nome)

        if inesperados: raise QueryParametersValidationException(
            mensagem = "Erro na validação do query parameter '$select'",
            detalhes = {
                "recebidos": [campo.nome for campo in self.campos],
                "inesperados": inesperados,
                "esperados": coletor.campos_modelo,
            }
        )

    def to_sql_alias (self) -> str:
        """Versão `SQL: SELECT` com os campos separados por `,` e renomeados da versão sql para modelo
        - Campos com espaço são envolvidos em aspas duplas"""
        campos = ", ".join(campo.to_sql_alias() for campo in self.campos)
        return f"SELECT {campos}"

    def to_sql_model (self) -> str:
        """Versão `SQL: SELECT` com os campos separados por `,` com nomes da versão do modelo
        - Campos com espaço são envolvidos em aspas duplas"""
        campos = ", ".join(campo.to_sql_model() for campo in self.campos)
        return f"SELECT {campos}"

    def to_metadata (self) -> str:
        """Versão `@metadata: $select` com os campos separados por `,`
        - Campos com espaço são envolvidos em aspas"""
        return ", ".join(campo.to_metadata() for campo in self.campos)

__all__ = ["Select", "quote"]