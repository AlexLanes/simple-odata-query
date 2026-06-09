# interno
from simple_odata_query.coletor import ColetorModelo, ExpandData
from simple_odata_query import QueryParametersValidationException

class Expand:
    """Utilizado para criar relação com outras tabelas
    - Formato `nome1, nome2, ..."""

    todos: bool = False
    recebidos: list[str]
    expands: list[ExpandData]

    def __init__ (self, expand: str | None = None) -> None:
        self.expands = []
        self.recebidos = []

        if not expand: return
        if expand.strip() == "*":
            self.todos = True
            return

        for nome in map(str.strip, expand.split(",")):
            if not nome or nome in self.recebidos:
                continue
            self.recebidos.append(nome)

    def build (self, coletor: ColetorModelo) -> None:
        """Validar se os campos do `expand` estão presentes no `coletor` e construir o `self.expands`
        - `QueryParametersValidationException` caso algum campo incorreto"""
        if self.todos:
            return self.expands.extend(coletor.expands.values())

        inesperados = list[str]()
        esperados = coletor.nomes_expand
        for recebido in self.recebidos:
            inesperado = recebido not in esperados
            if inesperado: inesperados.append(recebido)
            else: self.expands.append(coletor.expands[recebido])

        if inesperados: raise QueryParametersValidationException(
            mensagem = "Erro na validação do query parameter '$expand'",
            detalhes = {
                "recebidos": self.recebidos,
                "inesperados": inesperados,
                "esperados": esperados,
            }
        )

    def to_metadata (self) -> str | None:
        """Versão `@metadata: $expand` com os campos separados por `,`"""
        return ", ".join(e.nome for e in self.expands) or None

__all__ = ["Expand"]