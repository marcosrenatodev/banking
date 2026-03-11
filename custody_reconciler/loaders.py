from __future__ import annotations

import csv
import json
from collections import OrderedDict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

from custody_reconciler.domain import CustodianPosition, Position, ReconciliationRow
from custody_reconciler.errors import ReconciliationError
from custody_reconciler.mapping import resolve_ticker


TWO_PLACES = Decimal("0.01")


def load_internal_positions(path: Path) -> list[Position]:
    if not path.exists():
        raise ReconciliationError(f"Arquivo do sistema interno não encontrado: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReconciliationError(
            f"JSON inválido em {path}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise ReconciliationError(
            f"Não foi possível ler o arquivo do sistema interno {path}: {exc}"
        ) from exc

    if not isinstance(payload, list):
        raise ReconciliationError("O arquivo do sistema interno deve conter uma lista.")

    aggregated: OrderedDict[str, Position] = OrderedDict()
    for index, raw_item in enumerate(payload, start=1):
        if not isinstance(raw_item, dict):
            raise ReconciliationError(
                f"Registro {index} do sistema interno deve ser um objeto JSON."
            )
        ticker = _read_required_string(raw_item, "ticker", "sistema interno", index)
        quantity = _parse_quantity(
            raw_item.get("quantidade"), f"sistema interno, registro {index}"
        )
        financial = _parse_decimal(
            raw_item.get("financeiro"), f"sistema interno, registro {index}"
        )
        _accumulate_internal(aggregated, Position(ticker=ticker, quantity=quantity, financial=financial))

    return list(aggregated.values())


def load_custodian_positions(
    path: Path, name_mapping: dict[str, str]
) -> list[CustodianPosition]:
    if not path.exists():
        raise ReconciliationError(f"Arquivo do custodiante não encontrado: {path}")

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            expected_columns = {"Ativo", "Quantidade", "Saldo_Financeiro"}
            if reader.fieldnames is None:
                raise ReconciliationError("O CSV do custodiante está vazio.")
            if set(reader.fieldnames) != expected_columns:
                raise ReconciliationError(
                    "O CSV do custodiante deve conter exatamente as colunas "
                    "Ativo, Quantidade, Saldo_Financeiro."
                )

            aggregated: OrderedDict[str, CustodianPosition] = OrderedDict()
            for index, row in enumerate(reader, start=2):
                asset_name = _read_required_string(row, "Ativo", "custodiante", index)
                quantity = _parse_quantity(row.get("Quantidade"), f"custodiante, linha {index}")
                financial = _parse_decimal(
                    row.get("Saldo_Financeiro"), f"custodiante, linha {index}"
                )
                ticker = resolve_ticker(asset_name, name_mapping)
                _accumulate_custodian(
                    aggregated,
                    CustodianPosition(
                        asset_name=asset_name,
                        ticker=ticker,
                        quantity=quantity,
                        financial=financial,
                    ),
                )
    except ReconciliationError:
        raise
    except OSError as exc:
        raise ReconciliationError(
            f"Não foi possível ler o arquivo do custodiante {path}: {exc}"
        ) from exc

    return list(aggregated.values())


def write_report(path: Path, rows: Iterable[ReconciliationRow]) -> None:
    try:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "Ticker",
                    "Status",
                    "Divergencia_Qtde",
                    "Divergencia_Financ",
                ],
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "Ticker": row.ticker,
                        "Status": row.status.value,
                        "Divergencia_Qtde": row.quantity_difference,
                        "Divergencia_Financ": _format_decimal(row.financial_difference),
                    }
                )
    except OSError as exc:
        raise ReconciliationError(
            f"Não foi possível escrever o relatório em {path}: {exc}"
        ) from exc


def _read_required_string(
    payload: dict[str, object], field_name: str, source_name: str, index: int
) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ReconciliationError(
            f"Campo obrigatório {field_name!r} ausente ou inválido em {source_name}, registro {index}."
        )
    return value.strip().upper() if field_name == "ticker" else value.strip()


def _parse_quantity(value: object, context: str) -> int:
    if isinstance(value, bool) or value is None:
        raise ReconciliationError(f"Quantidade inválida em {context}.")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ReconciliationError(f"Quantidade inválida em {context}.")
        if not stripped.lstrip("+-").isdigit():
            raise ReconciliationError(
                f"Quantidade deve ser inteira em {context}, valor recebido: {value!r}."
            )
        return int(stripped)
    raise ReconciliationError(
        f"Quantidade deve ser inteira em {context}, valor recebido: {value!r}."
    )


def _parse_decimal(value: object, context: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ReconciliationError(f"Valor financeiro inválido em {context}.")
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ReconciliationError(
            f"Valor financeiro inválido em {context}, valor recebido: {value!r}."
        ) from exc
    return parsed


def _format_decimal(value: Decimal) -> str:
    return f"{value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP):f}"


def _accumulate_internal(
    aggregated: OrderedDict[str, Position], position: Position
) -> None:
    existing = aggregated.get(position.ticker)
    if existing is None:
        aggregated[position.ticker] = position
        return
    aggregated[position.ticker] = Position(
        ticker=existing.ticker,
        quantity=existing.quantity + position.quantity,
        financial=existing.financial + position.financial,
    )


def _accumulate_custodian(
    aggregated: OrderedDict[str, CustodianPosition], position: CustodianPosition
) -> None:
    existing = aggregated.get(position.ticker)
    if existing is None:
        aggregated[position.ticker] = position
        return
    aggregated[position.ticker] = CustodianPosition(
        asset_name=existing.asset_name,
        ticker=existing.ticker,
        quantity=existing.quantity + position.quantity,
        financial=existing.financial + position.financial,
    )
