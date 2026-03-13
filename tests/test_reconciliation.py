from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from decimal import Decimal
from pathlib import Path

from conciliador import main
from custody_reconciler.domain import (
    CustodianPosition,
    Position,
    ReconciliationStatus,
)
from custody_reconciler.loaders import (
    load_custodian_positions,
    load_internal_positions,
    write_report,
)
from custody_reconciler.mapping import load_name_mapping, resolve_ticker
from custody_reconciler.reconciliation import reconcile_positions


class ReconciliationFlowTests(unittest.TestCase):
    """Agrupa cenarios que validam o fluxo principal de conciliacao."""
    def test_end_to_end_fixture_generates_expected_csv(self) -> None:
        """Valida o fluxo completo com fixtures e confere o CSV final esperado."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "relatorio_final.csv"

            result = main(["--output", str(output_path)])

            self.assertEqual(result, 0)
            with output_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(
            rows,
            [
                {
                    "Ticker": "PETR4",
                    "Status": "OK",
                    "Divergencia_Qtde": "0",
                    "Divergencia_Financ": "0.00",
                },
                {
                    "Ticker": "VALE3",
                    "Status": "ERRO_QUANTIDADE",
                    "Divergencia_Qtde": "-10",
                    "Divergencia_Financ": "-650.00",
                },
                {
                    "Ticker": "ITUB4",
                    "Status": "ERRO_FINANCEIRO",
                    "Divergencia_Qtde": "0",
                    "Divergencia_Financ": "0.05",
                },
                {
                    "Ticker": "BBDC4",
                    "Status": "FALTANTE_NO_BANCO",
                    "Divergencia_Qtde": "-300",
                    "Divergencia_Financ": "-4200.00",
                },
                {
                    "Ticker": "MGLU3",
                    "Status": "OK",
                    "Divergencia_Qtde": "0",
                    "Divergencia_Financ": "0.00",
                },
                {
                    "Ticker": "WEGE3",
                    "Status": "ERRO_QUANTIDADE",
                    "Divergencia_Qtde": "20",
                    "Divergencia_Financ": "1100.00",
                },
                {
                    "Ticker": "KNIP11",
                    "Status": "NAO_CADASTRADO",
                    "Divergencia_Qtde": "100",
                    "Divergencia_Financ": "10500.00",
                },
                {
                    "Ticker": "HGLG11",
                    "Status": "NAO_CADASTRADO",
                    "Divergencia_Qtde": "50",
                    "Divergencia_Financ": "7500.00",
                },
            ],
        )

    def test_reconcile_all_statuses(self) -> None:
        """Confere se a conciliacao consegue produzir todos os status possiveis."""
        internal_positions = [
            Position("OKAY3", 10, Decimal("100.00")),
            Position("QTDX3", 10, Decimal("100.00")),
            Position("FINC3", 10, Decimal("100.00")),
            Position("MISS3", 10, Decimal("100.00")),
        ]
        custodian_positions = [
            CustodianPosition("Okay Corp", "OKAY3", 10, Decimal("100.00")),
            CustodianPosition("Qty Corp", "QTDX3", 8, Decimal("80.00")),
            CustodianPosition("Fin Corp", "FINC3", 10, Decimal("100.01")),
            CustodianPosition("New Corp", "NEWC3", 5, Decimal("50.00")),
        ]

        rows = reconcile_positions(internal_positions, custodian_positions)

        statuses = {row.ticker: row.status for row in rows}
        self.assertEqual(statuses["OKAY3"], ReconciliationStatus.OK)
        self.assertEqual(statuses["QTDX3"], ReconciliationStatus.ERRO_QUANTIDADE)
        self.assertEqual(statuses["FINC3"], ReconciliationStatus.ERRO_FINANCEIRO)
        self.assertEqual(statuses["MISS3"], ReconciliationStatus.FALTANTE_NO_BANCO)
        self.assertEqual(statuses["NEWC3"], ReconciliationStatus.NAO_CADASTRADO)

    def test_financial_tolerance_boundary(self) -> None:
        """Testa o limite da tolerancia financeira entre OK e erro financeiro."""
        internal_positions = [Position("ABCD3", 1, Decimal("10.000"))]
        custodian_positions = [
            CustodianPosition("ABCD3", "ABCD3", 1, Decimal("10.009")),
        ]

        rows = reconcile_positions(internal_positions, custodian_positions)
        self.assertEqual(rows[0].status, ReconciliationStatus.OK)

        custodian_positions = [
            CustodianPosition("ABCD3", "ABCD3", 1, Decimal("10.01")),
        ]
        rows = reconcile_positions(internal_positions, custodian_positions)
        self.assertEqual(rows[0].status, ReconciliationStatus.ERRO_FINANCEIRO)

    def test_mapping_normalization_and_identity_fallback(self) -> None:
        """Verifica normalizacao de nomes, reconhecimento de ticker e fallback sem cadastro."""
        mapping = load_name_mapping(Path("fixtures/custodian_mapping.json"))

        self.assertEqual(resolve_ticker("  vale   s.a.  ", mapping), "VALE3")
        self.assertEqual(resolve_ticker("knip11", mapping), "KNIP11")
        self.assertEqual(resolve_ticker("Ativo sem cadastro", mapping), "Ativo sem cadastro")

    def test_invalid_input_returns_friendly_error(self) -> None:
        """Garante que entradas invalidas retornem erro amigavel pela interface de linha de comando."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            internal_path = temp_path / "internal_system.json"
            custodian_path = temp_path / "custodian_extract.csv"
            mapping_path = temp_path / "custodian_mapping.json"

            internal_path.write_text(
                json.dumps([{"ticker": "PETR4", "quantidade": 10.5, "financeiro": 1}]),
                encoding="utf-8",
            )
            custodian_path.write_text(
                "Ativo,Quantidade,Saldo_Financeiro\nPETROLEO BRASILEIRO S.A.,10,1.00\n",
                encoding="utf-8",
            )
            mapping_path.write_text(
                json.dumps({"PETROLEO BRASILEIRO S.A.": "PETR4"}),
                encoding="utf-8",
            )

            stderr_buffer = io.StringIO()
            with redirect_stderr(stderr_buffer):
                result = main(
                    [
                        "--internal",
                        str(internal_path),
                        "--custodian",
                        str(custodian_path),
                        "--mapping",
                        str(mapping_path),
                        "--output",
                        str(temp_path / "relatorio_final.csv"),
                    ]
                )

        self.assertEqual(result, 1)
        self.assertIn("Quantidade deve ser inteira", stderr_buffer.getvalue())

    def test_duplicate_rows_are_aggregated_by_ticker(self) -> None:
        """Confirma que linhas duplicadas sao agregadas por ticker antes da conciliacao."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            internal_path = temp_path / "internal_system.json"
            custodian_path = temp_path / "custodian_extract.csv"
            mapping_path = temp_path / "custodian_mapping.json"
            output_path = temp_path / "relatorio_final.csv"

            internal_path.write_text(
                json.dumps(
                    [
                        {"ticker": "PETR4", "quantidade": 10, "financeiro": 100.0},
                        {"ticker": "PETR4", "quantidade": 5, "financeiro": 50.0},
                    ]
                ),
                encoding="utf-8",
            )
            custodian_path.write_text(
                (
                    "Ativo,Quantidade,Saldo_Financeiro\n"
                    "PETROLEO BRASILEIRO S.A.,8,80.00\n"
                    "PETROLEO BRASILEIRO S.A.,7,70.00\n"
                ),
                encoding="utf-8",
            )
            mapping_path.write_text(
                json.dumps({"PETROLEO BRASILEIRO S.A.": "PETR4"}),
                encoding="utf-8",
            )

            internal_positions = load_internal_positions(internal_path)
            mapping = load_name_mapping(mapping_path)
            custodian_positions = load_custodian_positions(custodian_path, mapping)
            rows = reconcile_positions(internal_positions, custodian_positions)
            write_report(output_path, rows)

            with output_path.open("r", encoding="utf-8", newline="") as handle:
                report_rows = list(csv.DictReader(handle))

        self.assertEqual(len(internal_positions), 1)
        self.assertEqual(len(custodian_positions), 1)
        self.assertEqual(report_rows[0]["Status"], "OK")


if __name__ == "__main__":
    unittest.main()
