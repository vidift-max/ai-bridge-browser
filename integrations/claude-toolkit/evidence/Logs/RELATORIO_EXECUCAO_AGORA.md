# Relatório de testes — execução real

- Data: 2026-11-28 06:19 UTC
- Sistema: Linux-6.18.44-fc-v880-x86_64-with-glibc2.39
- Python: 3.12.3
- Node.js: v22.23.5
- Ambiente: contêiner Linux sem navegador e sem aparelho Android

## Resumo

| Etapa | Resultado | Detalhe |
|---|---|---|
| Testes JavaScript (node --test) | APROVADA | 27 aprovados, 0 falhas, de 27 |
| Testes Python (unittest) | APROVADA | 30 executados, todos aprovados |
| Paridade JS x Python | APROVADA | 28 de 28 casos idênticos |
| Simulação de navegador (DOM falso) | APROVADA | 5 verificações OK |

## O que NÃO foi testado

- Navegador real e Android (Chrome, Firefox, WebView): **não executado**. `smoke_test.html` existe para você rodar.
- Python 3.9–3.11 e Node.js anterior à v22.
- Acessibilidade, desempenho e segurança por terceiros.

## Saídas brutas

### Testes JavaScript (node --test)

Comando: `/usr/bin/node --test duration_timer.test.js ...` — código de saída: 0

```text
TAP version 13
# Subtest: parseDuration: formatos válidos
ok 1 - parseDuration: formatos válidos
  ---
  duration_ms: 3.316097
  type: 'test'
  ...
# Subtest: parseDuration: erros com código estável
ok 2 - parseDuration: erros com código estável
  ---
  duration_ms: 0.72785
  type: 'test'
  ...
# Subtest: formatDuration
ok 3 - formatDuration
  ---
  duration_ms: 0.310439
  type: 'test'
  ...
# Subtest: createTimer: ciclo completo com relógio falso
ok 4 - createTimer: ciclo completo com relógio falso
  ---
  duration_ms: 0.530314
  type: 'test'
  ...
# Subtest: createTimer: estados inválidos e duração inválida
ok 5 - createTimer: estados inválidos e duração inválida
  ---
  duration_ms: 0.32365
  type: 'test'
  ...
# Subtest: normaliza URL válida
ok 6 - normaliza URL válida
  ---
  duration_ms: 3.130084
  type: 'test'
  ...
# Subtest: monta HTML escapado com rel seguro
ok 7 - monta HTML escapado com rel seguro
  ---
  duration_ms: 0.415002
  type: 'test'
  ...
# Subtest: recusa esquemas perigosos
ok 8 - recusa esquemas perigosos
  ---
  duration_ms: 0.551865
  type: 'test'
  ...
# Subtest: outros erros
ok 9 - outros erros
  ---
  duration_ms: 0.341164
  type: 'test'
  ...
# Subtest: host IPv6 mantém colchetes (regressão de paridade)
ok 10 - host IPv6 mantém colchetes (regressão de paridade)
  ---
  duration_ms: 0.202313
  type: 'test'
  ...
# Subtest: validateQuiz: válido
ok 11 - validateQuiz: válido
  ---
  duration_ms: 2.745661
  type: 'test'
  ...
# Subtest: validateQuiz: detecta problemas
ok 12 - validateQuiz: detecta problemas
  ---
  duration_ms: 0.44908
  type: 'test'
  ...
# Subtest: grade: acertos, erros e não respondidas
ok 13 - grade: acertos, erros e não respondidas
  ---
  duration_ms: 0.307845
  type: 'test'
  ...
# Subtest: grade: opção inválida e ids desconhecidos
ok 14 - grade: opção inválida e ids desconhecidos
  ---
  duration_ms: 0.198293
  type: 'test'
  ...
# Subtest: grade: erros e arredondamento
ok 15 - grade: erros e arredondamento
  ---
  duration_ms: 0.621256
  type: 'test'
  ...
# Subtest: convert: volume e massa
ok 16 - convert: volume e massa
  ---
  duration_ms: 2.121154
  type: 'test'
  ...
# Subtest: convert: erros
ok 17 - convert: erros
  ---
  duration_ms: 0.614133
  type: 'test'
  ...
# Subtest: scaleRecipe: dobra e não altera a entrada
ok 18 - scaleRecipe: dobra e não altera a entrada
  ---
  duration_ms: 0.998352
  type: 'test'
  ...
# Subtest: scaleRecipe: fração
ok 19 - scaleRecipe: fração
  ---
  duration_ms: 0.177182
  type: 'test'
  ...
# Subtest: scaleRecipe: erros
ok 20 - scaleRecipe: erros
  ---
  duration_ms: 0.437907
  type: 'test'
  ...
# Subtest: formatAmount
ok 21 - formatAmount
  ---
  duration_ms: 0.320618
  type: 'test'
  ...
# Subtest: niceMax
ok 22 - niceMax
  ---
  duration_ms: 2.132412
  type: 'test'
  ...
# Subtest: barras: estrutura do SVG
ok 23 - barras: estrutura do SVG
  ---
  duration_ms: 0.988111
  type: 'test'
  ...
# Subtest: linhas com duas séries e legenda
ok 24 - linhas com duas séries e legenda
  ---
  duration_ms: 0.330583
  type: 'test'
  ...
# Subtest: escapa texto (anti-injeção)
ok 25 - escapa texto (anti-injeção)
  ---
  duration_ms: 0.284531
  type: 'test'
  ...
# Subtest: todos os valores zero não quebra
ok 26 - todos os valores zero não quebra
  ---
  duration_ms: 0.277073
  type: 'test'
  ...
# Subtest: erros de validação
ok 27 - erros de validação
  ---
  duration_ms: 0.719646
  type: 'test'
  ...
1..27
# tests 27
# suites 0
# pass 27
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 371.398146
```

### Testes Python (unittest)

Comando: `/usr/bin/python3 -m unittest ...` — código de saída: 0

```text
test_arquivos_json (test_cli.TestCli.test_arquivos_json) ... ok
test_erro_retorna_2_com_codigo (test_cli.TestCli.test_erro_retorna_2_com_codigo) ... ok
test_parse_e_convert (test_cli.TestCli.test_parse_e_convert) ... ok
test_format (test_duration_timer.TestFormat.test_format) ... ok
test_erros (test_duration_timer.TestParse.test_erros) ... ok
test_formatos_validos (test_duration_timer.TestParse.test_formatos_validos) ... ok
test_ciclo_completo (test_duration_timer.TestTimer.test_ciclo_completo) ... ok
test_estados_invalidos (test_duration_timer.TestTimer.test_estados_invalidos) ... ok
test_esquemas_perigosos (test_link_card.TestLinkCard.test_esquemas_perigosos) ... ok
test_html_escapado (test_link_card.TestLinkCard.test_html_escapado) ... ok
test_ipv6_host_com_colchetes (test_link_card.TestLinkCard.test_ipv6_host_com_colchetes) ... ok
test_normaliza (test_link_card.TestLinkCard.test_normaliza) ... ok
test_outros_erros (test_link_card.TestLinkCard.test_outros_erros) ... ok
test_acertos_erros_nao_respondidas (test_quiz_engine.TestGrade.test_acertos_erros_nao_respondidas) ... ok
test_erros_e_arredondamento (test_quiz_engine.TestGrade.test_erros_e_arredondamento) ... ok
test_opcao_invalida_e_ids_desconhecidos (test_quiz_engine.TestGrade.test_opcao_invalida_e_ids_desconhecidos) ... ok
test_problemas (test_quiz_engine.TestValidate.test_problemas) ... ok
test_valido (test_quiz_engine.TestValidate.test_valido) ... ok
test_erros (test_recipe_scaler.TestConvert.test_erros) ... ok
test_validas (test_recipe_scaler.TestConvert.test_validas) ... ok
test_dobra_sem_alterar_entrada (test_recipe_scaler.TestScale.test_dobra_sem_alterar_entrada) ... ok
test_erros (test_recipe_scaler.TestScale.test_erros) ... ok
test_format_amount (test_recipe_scaler.TestScale.test_format_amount) ... ok
test_fracao (test_recipe_scaler.TestScale.test_fracao) ... ok
test_barras (test_svg_chart.TestChart.test_barras) ... ok
test_erros (test_svg_chart.TestChart.test_erros) ... ok
test_escapa_texto (test_svg_chart.TestChart.test_escapa_texto) ... ok
test_linhas_duas_series (test_svg_chart.TestChart.test_linhas_duas_series) ... ok
test_nice_max (test_svg_chart.TestChart.test_nice_max) ... ok
test_zeros (test_svg_chart.TestChart.test_zeros) ... ok

----------------------------------------------------------------------
Ran 30 tests in 0.010s

OK
```

### Paridade JS x Python

Comando: `/usr/bin/python3 paridade_js_python.py ...` — código de saída: 0

```text
Paridade JS x Python: 28/28 casos idênticos.
```

### Simulação de navegador (DOM falso)

Comando: `/usr/bin/node simulacao_navegador.js ...` — código de saída: 0

```text
OK  UMD (ramo de navegador): 6 módulos registrados em window.AIToolHub
OK  smoke_test.html: 13 de 13 verificações passaram.
OK  app.js: 5 ferramentas respondem aos cliques (DOM falso)
OK  index_standalone.html: arquivo único funciona (DOM falso)
OK  smoke_test_standalone.html: 13 de 13 verificações passaram.

ATENÇÃO: simulação em Node. Falta validar em navegador real (Chrome/Android).
```
