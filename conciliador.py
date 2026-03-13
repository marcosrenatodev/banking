from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from custody_reconciler.errors import ReconciliationError
from custody_reconciler.loaders import (
    load_custodian_positions,
    load_internal_positions,
    write_report,
)
from custody_reconciler.mapping import load_name_mapping
from custody_reconciler.reconciliation import reconcile_positions


LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    fixtures_dir = Path(__file__).resolve().parent / "fixtures"

    parser = argparse.ArgumentParser(
        description="Concilia posições entre sistema interno e custodiante."
    )
    parser.add_argument(
        "--internal",
        type=Path,
        default=fixtures_dir / "internal_system.json",
        help="Caminho para o arquivo internal_system.json.",
    )
    parser.add_argument(
        "--custodian",
        type=Path,
        default=fixtures_dir / "custodian_extract.csv",
        help="Caminho para o arquivo custodian_extract.csv.",
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        default=fixtures_dir / "custodian_mapping.json",
        help="Caminho para o arquivo JSON de de-para entre nome e ticker.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("relatorio_final.csv"),
        help="Caminho do CSV final gerado.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        internal_positions = load_internal_positions(args.internal)
        name_mapping = load_name_mapping(args.mapping)
        custodian_positions = load_custodian_positions(args.custodian, name_mapping)
        report_rows = reconcile_positions(internal_positions, custodian_positions)
        write_report(args.output, report_rows)
    except ReconciliationError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    except Exception as exc: 
        LOGGER.error("Falha inesperada: %s", exc)
        return 1

    LOGGER.info("Relatório gerado em %s", args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
