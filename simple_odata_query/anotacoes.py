# std
from dataclasses import dataclass
from typing import (
    Any, Annotated,
    get_type_hints, get_origin, get_args
)

type TVersaoCampoSQL = dict[str, str]
"""`{ nome_modelo: versao_sql }`"""
CACHE_ANOTACOES: dict[int, TVersaoCampoSQL] = {}
"""`{ hash_classe: TAliasCampoSQL }`"""

def coletar_campos_classe (cls: type) -> TVersaoCampoSQL:
    """Extrair da `cls` os campos existentes e possíveis transformações"""
    hash_cls = hash(cls)
    if hit := CACHE_ANOTACOES.get(hash_cls):
        return hit

    campos: TVersaoCampoSQL = {}

    # Mapear os campos e obter `Alias` do `Annotated`
    for campo, tipo in get_type_hints(cls, include_extras=True).items():
        alias = campo
        if get_origin(tipo) is Annotated:
            match get_args(tipo)[1]:
                case str() as a: alias = a
                case { "alias": str() as a }: alias = a
        campos[campo] = alias

    # Obter `Alias` da propriedade `alias` em uma classe default
    for campo in campos:
        if (default := cls.__dict__.get(campo)) and hasattr(default, "alias"):
            campos[campo] = str(default.alias)

    CACHE_ANOTACOES[hash_cls] = campos
    return campos

@dataclass
class ResponseExecute:
    """Response do `QueryBuilder.execute` com os dados e metadatas
    - Usar `to_dict()` para transformar"""

    metadata: dict[str, Any]
    dados: list[dict[str, Any]]

    def to_dict (self, nome_dados="dados") -> dict[str, Any]:
        """Transformar o `Response` para a versão `dict`
        - `nome_dados` para renomear o campo `dados`"""
        return {
            "@metadata": self.metadata,
            nome_dados: self.dados
        }

__all__ = [
    "TVersaoCampoSQL",
    "ResponseExecute",
    "coletar_campos_classe",
]