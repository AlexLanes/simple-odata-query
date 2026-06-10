# std
from dataclasses import dataclass
from typing import Any, Protocol, Self

class IClasseModelo (Protocol):
    """Interface modelo esperada com os nomes das propriedades anotadas e nome da `__tabela__`
    - `Field(nome_sql=)` Indicar o nome do campo no banco de dados, caso seja diferente do modelo ou possua espaço
    - `Field().add_expand(...)` Adicionar uma relação de `$expand` no campo do modelo

    # Exemplo
    ```python
    from typing import Annotated
    from simple_odata_query import Field

    class AtoresFilme:
        __tabela__ = "film_actor"
        id:      Annotated[int, Field(nome_sql="actor_id")]
        film_id: int

    class CategoriaFilme:
        __tabela__ = "film_category"
        id:      Annotated[int, Field(nome_sql="category_id")]
        film_id: int

    class Filme:
        __tabela__ = "film"
        id:          Annotated[int, Field(nome_sql="film_id")
                                    .add_expand("atores",    on=(AtoresFilme, "film_id"), include=False)
                                    .add_expand("categoria", on=(CategoriaFilme, "film_id"), unique=True)]
        titulo:      Annotated[str, Field(nome_sql="title")]
        descricao:   Annotated[str, Field(nome_sql="description")]
        year:        int
    ```
    """

    __tabela__: str
    """Nome da tabela"""
    __annotations__: dict[str, Any]

class Field:
    """Adicionar informações em um campo. Usar em conjunto ao `Annotated[T, Field()]`
    - `Field(nome_sql=)` Indicar o nome do campo no banco de dados, caso seja diferente do modelo ou possua espaço
    - `Field().add_expand(...)` Adicionar uma relação de `$expand` no campo do modelo"""

    nome_sql: str | None = None
    expands: dict[str, tuple[tuple[type[IClasseModelo], str], bool, bool]]
    """`{ nome_expand: ((IClasseModelo, nome_campo), unique, include) }`"""

    def __init__ (self, *, nome_sql: str | None = None) -> None:
        self.expands = {}
        self.nome_sql = nome_sql

    def add_expand (self, nome: str, *,
                          on: tuple[type[IClasseModelo], str],
                          unique: bool = False,
                          include: bool = True) -> Self:
        """Adicionar uma relação de `$expand` no campo do modelo
        - `nome` Nome utilizado no `$expand`
        - `on` Relacionamento existente `(IClasseModelo, nome_campo)` para ser feito o `$expand`
        - `unique` Indicação se a relação é de `1:1` entre os modelos
            - `True` retorna como um `dict`
            - `False` retorna uma `list[dict]`
        - `include` Indicação se o campo da relação deve ser incluído"""
        self.expands[nome] = (on, unique, include)
        return self

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

__all__ = [
    "Field",
    "IClasseModelo",
    "ODataResponse",
]