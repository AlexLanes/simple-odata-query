# std
from typing import Any, Protocol

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

__all__ = ["IClasseModelo"]