# Conciliadora de Custódia

Solução em Python para o teste técnico de conciliação de custódia. O projeto lê a posição do sistema interno, o extrato do custodiante e o de-para entre nome e ticker, compara quantidade e financeiro, ignora diferenças financeiras menores que `R$ 0,01` e gera o arquivo `relatorio_final.csv`.

## Desenvolvedor:
 Marcos Renato Rocha de Medeiros

## Requisitos

- Python `3.11+`
- Nenhuma dependência externa

Os exemplos abaixo assumem que o comando `python` aponta para uma versão compatível. Se no seu ambiente o interpretador disponível tiver outro nome, como `python3.11`, basta substituir nos comandos.

## Estrutura

- `conciliador.py`: ponto de entrada da aplicação
- `custody_reconciler/`: leitura e validação dos arquivos, regras de domínio, de-para e conciliação
- `fixtures/`: arquivos de exemplo usados na execução padrão
- `tests/`: suíte de testes com `unittest`

## Decisões técnicas

- Os valores financeiros usam `Decimal`, o que evita imprecisão com `float` e deixa a tolerância de `R$ 0,01` previsível.
- O de-para entre o nome do custodiante e o ticker foi mantido em um JSON dedicado, o que deixa a solução simples de auditar e reproduzir.
- Quando o valor vindo do custodiante já se parece com um ticker válido, o script reaproveita esse valor como fallback seguro.
- As entradas são validadas antes da conciliação, com mensagens de erro amigáveis em vez de traceback bruto.

## Escopo e tradeoffs

- A entrega foi mantida como script de linha de comando, que é exatamente o formato pedido no enunciado.
- O mapping entre nome e ticker faz parte da solução, em vez de depender de consulta externa. Para este desafio, isso deixa o comportamento mais controlado e determinístico.

## Possíveis evoluções

- Integrar o de-para com uma fonte confiável de cadastro de ativos, mantendo trilha de auditoria para novos mapeamentos.
- Exibir no terminal um resumo com contagem por status, além do CSV final.
- Separar a configuração dos caminhos de entrada em perfis ou ambientes para facilitar uso fora dos fixtures.

## Como executar

```bash
python conciliador.py
```

Esse comando usa os arquivos da pasta `fixtures/` e gera `relatorio_final.csv` no diretório atual.

### Parâmetros opcionais

```bash
python conciliador.py \
  --internal fixtures/internal_system.json \
  --custodian fixtures/custodian_extract.csv \
  --mapping fixtures/custodian_mapping.json \
  --output relatorio_final.csv
```

Parâmetros disponíveis:

- `--internal`: arquivo JSON com a posição do sistema interno
- `--custodian`: arquivo CSV com o extrato do custodiante
- `--mapping`: arquivo JSON com o de-para entre nome e ticker
- `--output`: caminho do CSV final gerado

## Como rodar os testes

```bash
python -m unittest discover -s tests
```

Assim como na execução do script, use um interpretador compatível com Python `3.11+`.
