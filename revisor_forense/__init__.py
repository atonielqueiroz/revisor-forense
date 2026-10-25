"""Revisor forense: aponta marcas de escrita automatizada em peças jurídicas em português."""
__version__ = "0.1.0"

from .leitura import ler, ler_texto  # noqa: E402,F401
from .motor import revisar  # noqa: E402,F401
