from __future__ import annotations

from decimal import Decimal

from custody_reconciler.domain import (
    CustodianPosition,
    Position,
    ReconciliationRow,
    ReconciliationStatus,
)


FINANCIAL_TOLERANCE = Decimal("0.01")


def reconcile_positions(
    internal_positions: list[Position], custodian_positions: list[CustodianPosition]
) -> list[ReconciliationRow]:
    """Compara posicoes internas e do custodiante, gerando as divergencias por ticker."""
    internal_by_ticker = {position.ticker: position for position in internal_positions}
    custodian_by_ticker = {position.ticker: position for position in custodian_positions}

    rows: list[ReconciliationRow] = []
    for internal_position in internal_positions:
        custodian_position = custodian_by_ticker.pop(internal_position.ticker, None)
        if custodian_position is None:
            rows.append(
                ReconciliationRow(
                    ticker=internal_position.ticker,
                    status=ReconciliationStatus.FALTANTE_NO_BANCO,
                    quantity_difference=-internal_position.quantity,
                    financial_difference=-internal_position.financial,
                )
            )
            continue

        quantity_difference = custodian_position.quantity - internal_position.quantity
        financial_difference = custodian_position.financial - internal_position.financial

        if quantity_difference != 0:
            status = ReconciliationStatus.ERRO_QUANTIDADE
        elif abs(financial_difference) >= FINANCIAL_TOLERANCE:
            status = ReconciliationStatus.ERRO_FINANCEIRO
        else:
            status = ReconciliationStatus.OK

        rows.append(
            ReconciliationRow(
                ticker=internal_position.ticker,
                status=status,
                quantity_difference=quantity_difference,
                financial_difference=financial_difference,
            )
        )

    for custodian_position in custodian_positions:
        if custodian_position.ticker in internal_by_ticker:
            continue
        rows.append(
            ReconciliationRow(
                ticker=custodian_position.ticker,
                status=ReconciliationStatus.NAO_CADASTRADO,
                quantity_difference=custodian_position.quantity,
                financial_difference=custodian_position.financial,
            )
        )

    return rows
