# std
from typing import Any

class QueryParametersValidationException (Exception):
    """`Exception` utilizada pelo pacote na validação dos parâmetros
    - `mensagem` descritiva sobre o erro
    - `detalhes` informações adicionais sobre o erro"""

    mensagem: str
    detalhes: dict[str, Any]

    def __init__ (self, mensagem: str, detalhes: dict[str, Any], *args: object) -> None:
        super().__init__(*args, mensagem)
        self.add_note(str(detalhes))
        self.mensagem = mensagem
        self.detalhes = detalhes
    
__all__ = ["QueryParametersValidationException"]