# std
from typing import Self
# interno
from simple_odata_query.modelos import IClasseModelo

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

__all__ = ["IClasseModelo"]