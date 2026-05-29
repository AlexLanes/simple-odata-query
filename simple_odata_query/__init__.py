"""Pacote para construções de `SQLs` a partir de Query Parameters estilo OData
- `QueryBuilder` classe principal para utilização
- `ResponseExecute` dataclasse com dados e metadatas
- `QueryParametersValidationException` exceção utilizada em erros"""

from .exception import QueryParametersValidationException
from .builder import QueryBuilder, ResponseExecute