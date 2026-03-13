from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ReconciliationStatus(str, Enum):
    """Enumera os status possiveis gerados pela conciliacao."""

    OK = "OK"
    ERRO_QUANTIDADE = "ERRO_QUANTIDADE"
    ERRO_FINANCEIRO = "ERRO_FINANCEIRO"
    FALTANTE_NO_BANCO = "FALTANTE_NO_BANCO"
    NAO_CADASTRADO = "NAO_CADASTRADO"


@dataclass(frozen=True, slots=True)
class Position:
    """Representa uma posicao consolidada do sistema interno."""

    ticker: str
    quantity: int
    financial: Decimal


@dataclass(frozen=True, slots=True)
class CustodianPosition:
    """Representa uma posicao vinda do custodiante com nome original e ticker resolvido."""

    asset_name: str
    ticker: str
    quantity: int
    financial: Decimal


@dataclass(frozen=True, slots=True)
class ReconciliationRow:
    """Representa uma linha do relatorio final de conciliacao."""

    ticker: str
    status: ReconciliationStatus
    quantity_difference: int
    financial_difference: Decimal
