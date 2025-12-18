"""
Models para Gestão de Contratos Públicos
DEPRECADO: Os modelos foram unificados em models.py

Este arquivo mantém apenas imports para compatibilidade retroativa.
Use os modelos de contracts.models diretamente.
"""

# Imports para compatibilidade retroativa
from .models import (
    RegimeLegal,
    TipoTermoAditivo,
    Contrato,
    TermoAditivo,
)

# Aliases para compatibilidade
ContratoPublico = Contrato
ProjetoPublico = None  # Removido - usar Projeto de models.py

__all__ = [
    'RegimeLegal',
    'TipoTermoAditivo',
    'Contrato',
    'ContratoPublico',
    'TermoAditivo',
]
