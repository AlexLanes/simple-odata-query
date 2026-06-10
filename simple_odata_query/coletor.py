# std
from __future__ import annotations
from dataclasses import dataclass
from typing import (
    Annotated,
    get_type_hints, get_origin, get_args,
)
# interno
from simple_odata_query import IClasseModelo, Field

CACHE_COLETOR: dict[int, ColetorModelo] = {}
"""`{ hash_modelo: ColetorModelo }`"""

@dataclass(frozen=True)
class ExpandData:
    nome: str
    """Nome do `$expand`"""
    nome_modelo_fk: str
    """`nome_modelo` onde existe a relação"""
    identificador: str
    """`nome_modelo` do parente da relação"""
    unique: bool
    """Flag da relação `1:1`"""
    include: bool
    """Flag se o `nome_modelo_fk` deve ser incluído"""
    modelo: type[IClasseModelo]
    coletor: ColetorModelo

    @property
    def tabela (self) -> str:
        return self.coletor.nome_tabela

@dataclass(frozen=True)
class ColetorModelo:

    nome_tabela: str
    campos: dict[str, str]
    """`{ nome_modelo: nome_sql }`
    - Igual caso não haja `alias`"""
    expands: dict[str, ExpandData]
    """`{ nome_expand: ExpandData }`"""

    @property
    def campos_modelo (self) -> list[str]:
        return list(self.campos)

    @property
    def campos_sql (self) -> list[str]:
        return list(self.campos.values())

    @property
    def nomes_expand (self) -> list[str]:
        return list(self.expands)

    @property
    def campos_com_expand (self) -> list[str]:
        return list(expand.identificador for expand in self.expands.values())

    @classmethod
    def from_modelo (cls, modelo: type[IClasseModelo]) -> ColetorModelo:
        """Extrair do `modelo` os campos existentes e possíveis transformações"""
        hash_modelo = hash(modelo)
        if hit := CACHE_COLETOR.get(hash_modelo):
            return hit

        # __tabela__
        if not (nome_tabela := str(modelo.__dict__.get("__tabela__", ""))):
            raise ValueError(f"O modelo {modelo} não possui a propriedade '__tabela__' inicializada")

        # Obter dados das anotações da classe no `__annotations__`
        campos = dict[str, str]()
        expands = dict[str, ExpandData]()
        for nome_modelo, tipo in get_type_hints(modelo, include_extras=True).items():

            if get_origin(tipo) is not Annotated or not isinstance(field := get_args(tipo)[1], Field):
                campos[nome_modelo] = nome_modelo
                continue

            # Mapear `Field` do `Annotated[type, Field()]`
            nome_sql = field.nome_sql or nome_modelo
            for nome_expand, ((modelo_expand, nome_fk), unique, include) in field.expands.items():
                coletor = cls.from_modelo(modelo_expand)
                if nome_fk not in coletor.campos_modelo:
                    raise ValueError(
                        f"Erro na configuração do $expand={nome_expand!r} do modelo {modelo_expand}."
                        f" Nome do campo '{nome_fk}' não está presente nas anotações do modelo"
                    )
                expands[nome_expand] = ExpandData(
                    nome_expand,
                    nome_fk,
                    nome_modelo,
                    unique,
                    include,
                    modelo_expand,
                    coletor
                )

            campos[nome_modelo] = nome_sql

        # Obter dados de `= defaults`
        for nome_modelo in campos:
            # Obter `Alias` da propriedade `alias`
            if (default := modelo.__dict__.get(nome_modelo)) and (nome_sql := getattr(default, "alias", None)):
                campos[nome_modelo] = str(nome_sql)

        # Incluir CACHE e retornar
        coletor = ColetorModelo(nome_tabela, campos, expands)
        CACHE_COLETOR[hash_modelo] = coletor
        return coletor

__all__ = ["ColetorModelo"]