# Conciliadora de Custódia

Mini-projeto em Python para conciliar posições entre um sistema interno e o extrato do custodiante, gerando um relatório CSV de exceções.

## Requisitos

- Python `3.11+`
- Nenhuma dependência externa

## Estrutura

- `conciliador.py`: ponto de entrada da aplicação
- `custody_reconciler/`: regras de domínio, leitura/validação, de-para e conciliação
- `fixtures/`: arquivos do enunciado para execução imediata
- `tests/`: suíte `unittest`

## Como executar

```bash
python conciliador.py
```

O comando acima usa os fixtures incluídos no projeto e gera `relatorio_final.csv` no diretório atual. Se o seu ambiente expõe apenas `python3`, use `python3 conciliador.py`.

### Parâmetros opcionais

```bash
python conciliador.py \
  --internal fixtures/internal_system.json \
  --custodian fixtures/custodian_extract.csv \
  --mapping fixtures/custodian_mapping.json \
  --output relatorio_final.csv
```

## Como rodar os testes

```bash
python -m unittest discover -s tests
```
