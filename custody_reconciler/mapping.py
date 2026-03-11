from __future__ import annotations

import json
import re
from pathlib import Path

from custody_reconciler.errors import ReconciliationError


_SPACE_PATTERN = re.compile(r"\s+")
_TICKER_PATTERN = re.compile(r"^[A-Z]{4,6}\d{1,2}[A-Z]?$")


def normalize_name(name: str) -> str:
    return _SPACE_PATTERN.sub(" ", name.strip().upper())


def looks_like_ticker(value: str) -> bool:
    return bool(_TICKER_PATTERN.fullmatch(normalize_name(value).replace(" ", "")))


def load_name_mapping(path: Path) -> dict[str, str]:
    if not path.exists():
        raise ReconciliationError(f"Arquivo de mapping não encontrado: {path}")

    try:
        raw_mapping = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReconciliationError(
            f"Arquivo de mapping inválido em {path}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise ReconciliationError(f"Não foi possível ler o mapping {path}: {exc}") from exc

    if not isinstance(raw_mapping, dict):
        raise ReconciliationError("O arquivo de mapping deve conter um objeto JSON.")

    normalized_mapping: dict[str, str] = {}
    for raw_name, raw_ticker in raw_mapping.items():
        if not isinstance(raw_name, str) or not isinstance(raw_ticker, str):
            raise ReconciliationError(
                "O arquivo de mapping deve conter pares texto -> texto."
            )

        normalized_name = normalize_name(raw_name)
        ticker = raw_ticker.strip().upper()
        if not normalized_name or not ticker:
            raise ReconciliationError(
                "O arquivo de mapping não pode conter nome ou ticker vazio."
            )
        if normalized_name in normalized_mapping and normalized_mapping[normalized_name] != ticker:
            raise ReconciliationError(
                f"Conflito no mapping após normalização para {normalized_name!r}."
            )
        normalized_mapping[normalized_name] = ticker

    return normalized_mapping


def resolve_ticker(asset_name: str, name_mapping: dict[str, str]) -> str:
    normalized_name = normalize_name(asset_name)
    if normalized_name in name_mapping:
        return name_mapping[normalized_name]
    compact_value = normalized_name.replace(" ", "")
    if looks_like_ticker(compact_value):
        return compact_value
    return asset_name.strip()
