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

## Decisões técnicas

- O domínio usa `Decimal` para valores financeiros, evitando erros de arredondamento com `float` e permitindo aplicar a tolerância de `R$ 0,01` de forma previsível.
- O de-para entre nome do custodiante e ticker foi modelado em um JSON dedicado e versionável. Para este problema, essa abordagem é mais auditável e determinística do que inferências frágeis por similaridade de texto.
- A resolução automática foi limitada a um fallback seguro para casos em que o valor do custodiante já parece um ticker, como `KNIP11` ou `HGLG11`.
- O carregamento das entradas valida presença de campos obrigatórios, tipos numéricos e estrutura mínima dos arquivos, retornando erro amigável em vez de traceback bruto.

## Escopo e tradeoffs

- A entrega foi mantida como script de linha de comando porque o enunciado pede explicitamente um `script` que leia dois arquivos e gere `relatorio_final.csv`.
- Não foi adicionada interface em React para não deslocar o foco da avaliação, que aqui está na modelagem, robustez, legibilidade e regra de conciliação.
- Não foi usada API pública para descobrir ticker a partir do nome da empresa. Em cenário real, isso normalmente dependeria de uma fonte mestre de cadastro, provedor de market data ou serviço corporativo confiável. Para o teste, o mapping explícito é a alternativa mais controlada e reproduzível.

## Possíveis evoluções

- Integrar com uma fonte externa confiável de cadastro de ativos, mantendo cache local e trilha de auditoria para novos de-paras.
- Expor um resumo no terminal com contagem por status além do CSV final.
- Adicionar uma interface opcional apenas como camada de apresentação, reutilizando a regra de negócio Python sem duplicação.

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
