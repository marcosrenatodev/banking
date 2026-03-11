from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ReconciliationStatus(str, Enum):
    OK = "OK"
    ERRO_QUANTIDADE = "ERRO_QUANTIDADE"
    ERRO_FINANCEIRO = "ERRO_FINANCEIRO"
    FALTANTE_NO_BANCO = "FALTANTE_NO_BANCO"
    NAO_CADASTRADO = "NAO_CADASTRADO"


@dataclass(frozen=True, slots=True)
class Position:
    ticker: str
    quantity: int
    financial: Decimal


@dataclass(frozen=True, slots=True)
class CustodianPosition:
    asset_name: str
    ticker: str
    quantity: int
    financial: Decimal


@dataclass(frozen=True, slots=True)
class ReconciliationRow:
    ticker: str
    status: ReconciliationStatus
    quantity_difference: int
    financial_difference: Decimal
