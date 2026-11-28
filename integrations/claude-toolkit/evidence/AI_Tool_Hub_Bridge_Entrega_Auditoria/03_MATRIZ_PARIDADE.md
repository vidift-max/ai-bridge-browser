# 03 — Matriz de paridade Python × JavaScript (corpus adversarial)

**Executado agora:** SIM (2026-11-28, Python 3.12.3, Node v22.23.5). Ambos os lados receberam exatamente o mesmo texto JSON (`cases.jsonl`, gerado por `gen_cases.py`).
Resultados brutos: `tests_auditoria/resultados_py.json`, `resultados_js.json`, `resultado_paridade.json`.

Critério: MATCH = mesmo desfecho (valor igual, ou mesmo código de erro). Inteiros e floats de valor inteiro são tratados como iguais (5 = 5.0), como já documentado pelo pacote. DIVERGE = valores diferentes, ou um lado aceita e o outro recusa, ou um lado lança exceção não controlada (CRASH).

## Resumo

| Ferramenta | Casos | MATCH | DIVERGE |
|---|---:|---:|---:|
| duration_timer | 71 | 61 | 10 |
| recipe_scaler | 85 | 78 | 7 |
| quiz_engine | 44 | 44 | 0 |
| svg_chart | 159 | 130 | 29 |
| link_card | 157 | 113 | 44 |
| **Total** | **516** | **426** | **90** |

**Leitura honesta:** o resultado histórico/atual `28/28` (suíte do pacote) continua verdadeiro para aqueles 28 casos, mas **não prova paridade**. Com 516 casos hostis/limite, há divergências reais. A paridade NÃO pode ser declarada.

Divergências por achado: F-01=11, F-03=5, F-04=3, F-05=1, F-06=14, F-08=8, F-09=44, F-10=4. Descrição de cada achado em `02_ACHADOS_E_RECOMENDACOES.md`.

Caso `link_card` com `http://[::1]:8080/x` (id 364): MATCH nos dois lados (host `[::1]`).

## Divergências (todas)

| ID | Ferramenta | Função | Caso | Python | JavaScript | Achado |
|---:|---|---|---|---|---|---|
| 22 | duration_timer | parseDuration | ["\u0661\u0662"] | ok 12.0 | erro INVALID_FORMAT | F-03 |
| 23 | duration_timer | parseDuration | ["\uff11\uff12"] | ok 12.0 | erro INVALID_FORMAT | F-03 |
| 24 | duration_timer | parseDuration | ["\u0661\u0662m"] | ok 720.0 | erro INVALID_FORMAT | F-03 |
| 26 | duration_timer | parseDuration | ["\\u001f5\\u001f"] | ok 5.0 | erro INVALID_FORMAT | F-03 |
| 27 | duration_timer | parseDuration | ["\\ufeff5"] | erro INVALID_FORMAT | ok 5 | F-03 |
| 61 | duration_timer | formatDuration | [3600,null] | erro INVALID_FORMAT | ok "01:00:00" | F-04 |
| 65 | duration_timer | formatDuration | [1e300,"clock"] | ok "277777777777777792362433404223450069084574… | ok "2.777777777777778e+296:36:00" | F-04 |
| 66 | duration_timer | formatDuration | [1e300,"words"] | ok "115740740740740746817680585093104195451906… | ok "1.1574074074074075e+295d 36m" | F-04 |
| 70 | duration_timer | formatDuration | [3600,"words",1] | CRASH TypeError: format_duration() takes from 1 to 2 … | ok "1h" | F-10 |
| 71 | duration_timer | formatDuration | [] | CRASH TypeError: format_duration() missing 1 required… | erro INVALID_FORMAT | F-10 |
| 75 | recipe_scaler | convert | [1e308,"lb","g"] | CRASH OverflowError: cannot convert float infinity to… | ok null | F-01 |
| 100 | recipe_scaler | convert | [1] | CRASH TypeError: convert() missing 2 required positio… | erro UNKNOWN_UNIT | F-10 |
| 101 | recipe_scaler | convert | [] | CRASH TypeError: convert() missing 3 required positio… | erro INVALID_AMOUNT | F-10 |
| 105 | recipe_scaler | scaleRecipe | [{"title": "R", "base_servings": 4, "ingredients": [{"name"… | CRASH OverflowError: cannot convert float infinity to… | ok {"title": "R", "base_servings": 1e+308, "sc… | F-01 |
| 119 | recipe_scaler | scaleRecipe | base_servings=1e-320 | CRASH OverflowError: cannot convert float infinity to… | ok {"title": "R", "base_servings": 2, "scale_f… | F-01 |
| 137 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":"A","amount":1e3… | CRASH OverflowError: cannot convert float infinity to… | ok {"title": "", "base_servings": 2, "scale_fa… | F-01 |
| 147 | recipe_scaler | formatAmount | [1e21] | ok "1000000000000000000000" | ok "1e+21" | F-05 |
| 219 | svg_chart | renderChart | hostil: a\\x85b | SVG ok | SVG ok | F-06 |
| 220 | svg_chart | renderChart | hostil: a\\ufeffb | SVG ok | SVG ok | F-06 |
| 224 | svg_chart | renderChart | hostil: \\U0001f600\\U0001f600\\U0001f600\\U0001f600\\U0001… | SVG ok | SVG ok | F-06 |
| 255 | svg_chart | renderChart | labels=[3.14159,2] | SVG ok | SVG ok | F-06 |
| 256 | svg_chart | renderChart | labels=[1e21,2] | SVG ok | SVG ok | F-06 |
| 257 | svg_chart | renderChart | labels=[1e-7,2] | SVG ok | SVG ok | F-06 |
| 260 | svg_chart | renderChart | labels=[0.30000000000000004,2] | SVG ok | SVG ok | F-06 |
| 261 | svg_chart | renderChart | labels=[1.005,2.675] | SVG ok | SVG ok | F-06 |
| 262 | svg_chart | renderChart | labels=[5e-324,2] | SVG ok | SVG ok | F-06 |
| 263 | svg_chart | renderChart | labels=[1e309,2] | CRASH OverflowError: cannot convert float infinity to… | SVG ok | F-01 |
| 267 | svg_chart | renderChart | labels=[1.5e300,2] | SVG ok | SVG ok | F-06 |
| 297 | svg_chart | renderChart | valor=1e308 | CRASH OverflowError: cannot convert float infinity to… | SVG ok | F-01 |
| 298 | svg_chart | renderChart | linha valor=1e308 | CRASH OverflowError: cannot convert float infinity to… | SVG ok | F-01 |
| 299 | svg_chart | renderChart | valor=1.7976931348623157e308 | CRASH OverflowError: int too large to convert to float | SVG ok | F-01 |
| 300 | svg_chart | renderChart | linha valor=1.7976931348623157e308 | CRASH OverflowError: int too large to convert to float | SVG ok | F-01 |
| 311 | svg_chart | renderChart | valor=1000000000000000000000000000000000000000 | CRASH OverflowError: int too large to convert to float | erro INVALID_VALUE | F-01 |
| 312 | svg_chart | renderChart | linha valor=1000000000000000000000000000000000000000 | CRASH OverflowError: int too large to convert to float | erro INVALID_VALUE | F-01 |
| 313 | svg_chart | renderChart | valor=123456789012345678901234567890 | SVG ok | SVG ok | F-06 |
| 314 | svg_chart | renderChart | linha valor=123456789012345678901234567890 | SVG ok | SVG ok | F-06 |
| 324 | svg_chart | renderChart | width=640.0 | erro INVALID_SIZE | SVG ok | F-08 |
| 325 | svg_chart | renderChart | height=640.0 | erro INVALID_SIZE | SVG ok | F-08 |
| 342 | svg_chart | renderChart | width=1e3 | erro INVALID_SIZE | SVG ok | F-08 |
| 343 | svg_chart | renderChart | height=1e3 | erro INVALID_SIZE | SVG ok | F-08 |
| 352 | svg_chart | renderChart | width=2000.0 | erro INVALID_SIZE | SVG ok | F-08 |
| 353 | svg_chart | renderChart | height=2000.0 | erro INVALID_SIZE | SVG ok | F-08 |
| 354 | svg_chart | renderChart | width=200.0 | erro INVALID_SIZE | SVG ok | F-08 |
| 355 | svg_chart | renderChart | height=200.0 | erro INVALID_SIZE | SVG ok | F-08 |
| 358 | svg_chart | renderChart | truncamento: 119 'a' + emoji + bcd | SVG ok | SVG ok | F-06 |
| 359 | svg_chart | renderChart | truncamento emoji em title/label/name | SVG ok | SVG ok | F-06 |
| 368 | link_card | buildLinkCard | url=http://[0:0:0:0:0:0:0:1]/ | http://[0:0:0:0:0:0:0:1]/ | http://[::1]/ | F-09 |
| 369 | link_card | buildLinkCard | url=http://[::FFFF:1.2.3.4]/ | http://[::ffff:1.2.3.4]/ | http://[::ffff:102:304]/ | F-09 |
| 371 | link_card | buildLinkCard | url=http://[fe80::1%25eth0]/ | http://[fe80::1%25eth0]/ | erro INVALID_URL | F-09 |
| 378 | link_card | buildLinkCard | url=http://127.1/ | http://127.1/ | http://127.0.0.1/ | F-09 |
| 379 | link_card | buildLinkCard | url=http://0x7f.1/ | http://0x7f.1/ | http://127.0.0.1/ | F-09 |
| 380 | link_card | buildLinkCard | url=http://2130706433/ | http://2130706433/ | http://127.0.0.1/ | F-09 |
| 381 | link_card | buildLinkCard | url=http://0177.0.0.1/ | http://0177.0.0.1/ | http://127.0.0.1/ | F-09 |
| 384 | link_card | buildLinkCard | url=http://256.256.256.256/ | http://256.256.256.256/ | erro INVALID_URL | F-09 |
| 385 | link_card | buildLinkCard | url=http://1.2.3/ | http://1.2.3/ | http://1.2.0.3/ | F-09 |
| 386 | link_card | buildLinkCard | url=http://1.2.3.4.5/ | http://1.2.3.4.5/ | erro INVALID_URL | F-09 |
| 392 | link_card | buildLinkCard | url=http://exa%6Dple.com/ | http://exa%6Dple.com/ | http://example.com/ | F-09 |
| 393 | link_card | buildLinkCard | url=http://b\\xfccher.de/ | http://b\xfccher.de/ | http://xn--bcher-kva.de/ | F-09 |
| 395 | link_card | buildLinkCard | url=http://\\u4f8b\\u3048.jp/ | http://\u4f8b\u3048.jp/ | http://xn--r8jz45g.jp/ | F-09 |
| 396 | link_card | buildLinkCard | url=http://EXAMPLE.com/\\xc4 | http://example.com/\xc4 | http://example.com/%C3%84 | F-09 |
| 397 | link_card | buildLinkCard | url=http://example.com/\\xe9?\\xe9#\\xe9 | http://example.com/\xe9?\xe9#\xe9 | http://example.com/%C3%A9?%C3%A9#%C3%A9 | F-09 |
| 398 | link_card | buildLinkCard | url=http://example.com/a/../b | http://example.com/a/../b | http://example.com/b | F-09 |
| 399 | link_card | buildLinkCard | url=http://example.com/./a//b | http://example.com/./a//b | http://example.com/a//b | F-09 |
| 400 | link_card | buildLinkCard | url=http://example.com/%2e%2e/x | http://example.com/%2e%2e/x | http://example.com/x | F-09 |
| 404 | link_card | buildLinkCard | url=http://example.com/? | http://example.com/ | http://example.com/? | F-09 |
| 405 | link_card | buildLinkCard | url=http://example.com/# | http://example.com/ | http://example.com/# | F-09 |
| 406 | link_card | buildLinkCard | url=http://example.com/path? | http://example.com/path | http://example.com/path? | F-09 |
| 407 | link_card | buildLinkCard | url=http://example.com/p?a="<>' | http://example.com/p?a="<>' | http://example.com/p?a=%22%3C%3E%27 | F-09 |
| 408 | link_card | buildLinkCard | url=http://example.com/"<>'{}\|^ | http://example.com/"<>'{}\|^ | http://example.com/%22%3C%3E%60%7B%7D\|^ | F-09 |
| 437 | link_card | buildLinkCard | url=http://evil.com\\\\@good.com | erro CREDENTIALS_IN_URL | http://evil.com/@good.com | F-09 |
| 438 | link_card | buildLinkCard | url=http://evil.com\\\\x | http://evil.com\\x/ | http://evil.com/x | F-09 |
| 439 | link_card | buildLinkCard | url=http://evil.com\\\\ | http://evil.com\\/ | http://evil.com/ | F-09 |
| 441 | link_card | buildLinkCard | url=http://evil.com/\\\\x | http://evil.com/\\x | http://evil.com//x | F-09 |
| 457 | link_card | buildLinkCard | url=https://example.com/\\xa0x | https://example.com/\xa0x | https://example.com/%C2%A0x | F-09 |
| 458 | link_card | buildLinkCard | url=https://example.com/\\u3000x | https://example.com/\u3000x | https://example.com/%E3%80%80x | F-09 |
| 459 | link_card | buildLinkCard | url=https://exam\\xa0ple.com | https://exam\xa0ple.com/ | erro INVALID_URL | F-09 |
| 460 | link_card | buildLinkCard | url=https://exam\\u200bple.com | https://exam\u200bple.com/ | https://example.com/ | F-09 |
| 461 | link_card | buildLinkCard | url=https://example.com/\\u202e | https://example.com/\u202e | https://example.com/%E2%80%AE | F-09 |
| 462 | link_card | buildLinkCard | url=https://\\uff25\\uff38\\uff21\\uff2d\\uff30\\uff2c\\uff… | ok "<483 bytes>" | https://example.com/ | F-09 |
| 463 | link_card | buildLinkCard | url=https://example.com\\u3002 | https://example.com\u3002/ | https://example.com./ | F-09 |
| 464 | link_card | buildLinkCard | url=https://example.com\\uff0e | https://example.com\uff0e/ | https://example.com./ | F-09 |
| 475 | link_card | buildLinkCard | url=https://example.com/\\ud800 | https://example.com/\ud800 | https://example.com/%EF%BF%BD | F-09 |
| 476 | link_card | buildLinkCard | url=https://example.com/<script>alert(1)</script> | https://example.com/<script>alert(1)</scrip… | https://example.com/%3Cscript%3Ealert(1)%3C… | F-09 |
| 477 | link_card | buildLinkCard | url=https://example.com/"><script>alert(1)</script> | https://example.com/"><script>alert(1)</scr… | https://example.com/%22%3E%3Cscript%3Ealert… | F-09 |
| 485 | link_card | buildLinkCard | url=http://[v1.fe]/ | http://v1.fe/ | erro INVALID_URL | F-09 |
| 509 | link_card | buildLinkCard | title/description="\U0001f600\U0001f600\U0001f600\U0001f600… | ok "<3618 bytes>" | ok "<3378 bytes>" | F-09 |
| 510 | link_card | buildLinkCard | title/description="ttttttttttttttttttttttttttttttttttttttt | ok "<806 bytes>" | ok "<794 bytes>" | F-09 |
| 511 | link_card | buildLinkCard | title/description="a\\u0085b" | https://example.com/ | https://example.com/ | F-09 |
| 512 | link_card | buildLinkCard | title/description="a\\ufeffb" | https://example.com/ | https://example.com/ | F-09 |
| 515 | link_card | buildLinkCard | descri\xe7\xe3o emoji no corte | ok "<882 bytes>" | ok "<870 bytes>" | F-09 |

## Todos os casos (MATCH e DIVERGE)

| ID | Ferramenta | Função | Caso | Resultado |
|---:|---|---|---|---|
| 1 | duration_timer | parseDuration | [""] | MATCH |
| 2 | duration_timer | parseDuration | ["   "] | MATCH |
| 3 | duration_timer | parseDuration | ["0"] | MATCH |
| 4 | duration_timer | parseDuration | ["-1"] | MATCH |
| 5 | duration_timer | parseDuration | ["1e3"] | MATCH |
| 6 | duration_timer | parseDuration | ["1e400"] | MATCH |
| 7 | duration_timer | parseDuration | ["1h30m"] | MATCH |
| 8 | duration_timer | parseDuration | ["1H"] | MATCH |
| 9 | duration_timer | parseDuration | ["1.5.5h"] | MATCH |
| 10 | duration_timer | parseDuration | ["99999999999999999999"] | MATCH |
| 11 | duration_timer | parseDuration | ["7d"] | MATCH |
| 12 | duration_timer | parseDuration | ["7d1s"] | MATCH |
| 13 | duration_timer | parseDuration | ["604800"] | MATCH |
| 14 | duration_timer | parseDuration | ["604801"] | MATCH |
| 15 | duration_timer | parseDuration | ["0:00"] | MATCH |
| 16 | duration_timer | parseDuration | ["1:60"] | MATCH |
| 17 | duration_timer | parseDuration | ["1:2:3:4"] | MATCH |
| 18 | duration_timer | parseDuration | ["1 h"] | MATCH |
| 19 | duration_timer | parseDuration | ["1h  30m"] | MATCH |
| 20 | duration_timer | parseDuration | ["1m1m"] | MATCH |
| 21 | duration_timer | parseDuration | ["m"] | MATCH |
| 22 | duration_timer | parseDuration | ["\u0661\u0662"] | DIVERGE F-03 |
| 23 | duration_timer | parseDuration | ["\uff11\uff12"] | DIVERGE F-03 |
| 24 | duration_timer | parseDuration | ["\u0661\u0662m"] | DIVERGE F-03 |
| 25 | duration_timer | parseDuration | ["1\\u00a0m"] | MATCH |
| 26 | duration_timer | parseDuration | ["\\u001f5\\u001f"] | DIVERGE F-03 |
| 27 | duration_timer | parseDuration | ["\\ufeff5"] | DIVERGE F-03 |
| 28 | duration_timer | parseDuration | ["5\\u2003"] | MATCH |
| 29 | duration_timer | parseDuration | ["\u0130"] | MATCH |
| 30 | duration_timer | parseDuration | ["1h30m\\n"] | MATCH |
| 31 | duration_timer | parseDuration | [null] | MATCH |
| 32 | duration_timer | parseDuration | [true] | MATCH |
| 33 | duration_timer | parseDuration | [[]] | MATCH |
| 34 | duration_timer | parseDuration | [{}] | MATCH |
| 35 | duration_timer | parseDuration | [5] | MATCH |
| 36 | duration_timer | parseDuration | [-5] | MATCH |
| 37 | duration_timer | parseDuration | [0] | MATCH |
| 38 | duration_timer | parseDuration | [0.0001] | MATCH |
| 39 | duration_timer | parseDuration | [1e-9] | MATCH |
| 40 | duration_timer | parseDuration | [1e309] | MATCH |
| 41 | duration_timer | parseDuration | [604800] | MATCH |
| 42 | duration_timer | parseDuration | [604800.0005] | MATCH |
| 43 | duration_timer | parseDuration | [1e21] | MATCH |
| 44 | duration_timer | parseDuration | ["999999999999999999999999999999999999999999999999999999999… | MATCH |
| 45 | duration_timer | parseDuration | ["1" ] | MATCH |
| 46 | duration_timer | parseDuration | ["0.5s"] | MATCH |
| 47 | duration_timer | parseDuration | ["1,5h"] | MATCH |
| 48 | duration_timer | parseDuration | ["1h-1m"] | MATCH |
| 49 | duration_timer | parseDuration | ["+5m"] | MATCH |
| 50 | duration_timer | parseDuration | ["5M"] | MATCH |
| 51 | duration_timer | parseDuration | ["5\uff4d"] | MATCH |
| 52 | duration_timer | formatDuration | [0] | MATCH |
| 53 | duration_timer | formatDuration | [-1] | MATCH |
| 54 | duration_timer | formatDuration | [1e9] | MATCH |
| 55 | duration_timer | formatDuration | [1e309] | MATCH |
| 56 | duration_timer | formatDuration | ["5"] | MATCH |
| 57 | duration_timer | formatDuration | [null] | MATCH |
| 58 | duration_timer | formatDuration | [true] | MATCH |
| 59 | duration_timer | formatDuration | [59.9999] | MATCH |
| 60 | duration_timer | formatDuration | [3600,"x"] | MATCH |
| 61 | duration_timer | formatDuration | [3600,null] | DIVERGE F-04 |
| 62 | duration_timer | formatDuration | [604801,"words"] | MATCH |
| 63 | duration_timer | formatDuration | [86399.999,"words"] | MATCH |
| 64 | duration_timer | formatDuration | [0,"words"] | MATCH |
| 65 | duration_timer | formatDuration | [1e300,"clock"] | DIVERGE F-04 |
| 66 | duration_timer | formatDuration | [1e300,"words"] | DIVERGE F-04 |
| 67 | duration_timer | formatDuration | [3723.9,"clock"] | MATCH |
| 68 | duration_timer | formatDuration | [5e-324] | MATCH |
| 69 | duration_timer | formatDuration | [3600,"CLOCK"] | MATCH |
| 70 | duration_timer | formatDuration | [3600,"words",1] | DIVERGE F-10 |
| 71 | duration_timer | formatDuration | [] | DIVERGE F-10 |
| 72 | recipe_scaler | convert | [1,"cup","ml"] | MATCH |
| 73 | recipe_scaler | convert | [-1,"cup","ml"] | MATCH |
| 74 | recipe_scaler | convert | [0,"cup","ml"] | MATCH |
| 75 | recipe_scaler | convert | [1e308,"lb","g"] | DIVERGE F-01 |
| 76 | recipe_scaler | convert | [1e309,"lb","g"] | MATCH |
| 77 | recipe_scaler | convert | ["1","cup","ml"] | MATCH |
| 78 | recipe_scaler | convert | [null,"cup","ml"] | MATCH |
| 79 | recipe_scaler | convert | [true,"cup","ml"] | MATCH |
| 80 | recipe_scaler | convert | [1,"CUP","ML"] | MATCH |
| 81 | recipe_scaler | convert | [1,"cup","cup"] | MATCH |
| 82 | recipe_scaler | convert | [1,"fl oz","ml"] | MATCH |
| 83 | recipe_scaler | convert | [1,"fl_oz","ml"] | MATCH |
| 84 | recipe_scaler | convert | [1,"__proto__","ml"] | MATCH |
| 85 | recipe_scaler | convert | [1,"constructor","ml"] | MATCH |
| 86 | recipe_scaler | convert | [1,"toString","g"] | MATCH |
| 87 | recipe_scaler | convert | [1,"hasOwnProperty","g"] | MATCH |
| 88 | recipe_scaler | convert | [1,"cup","g"] | MATCH |
| 89 | recipe_scaler | convert | [1,"g","cup"] | MATCH |
| 90 | recipe_scaler | convert | [1,null,"g"] | MATCH |
| 91 | recipe_scaler | convert | [1,5,"g"] | MATCH |
| 92 | recipe_scaler | convert | [1,["g"],"g"] | MATCH |
| 93 | recipe_scaler | convert | [1e-12,"g","kg"] | MATCH |
| 94 | recipe_scaler | convert | [2.675,"cup","ml"] | MATCH |
| 95 | recipe_scaler | convert | [0.0000005,"ml","ml"] | MATCH |
| 96 | recipe_scaler | convert | [123456789012345678,"g","kg"] | MATCH |
| 97 | recipe_scaler | convert | [1,"  Cups  ","ML"] | MATCH |
| 98 | recipe_scaler | convert | [1,"\uff47","g"] | MATCH |
| 99 | recipe_scaler | convert | [1,"G","g"] | MATCH |
| 100 | recipe_scaler | convert | [1] | DIVERGE F-10 |
| 101 | recipe_scaler | convert | [] | DIVERGE F-10 |
| 102 | recipe_scaler | scaleRecipe | [{"title": "R", "base_servings": 4, "ingredients": [{"name"… | MATCH |
| 103 | recipe_scaler | scaleRecipe | [{"title": "R", "base_servings": 4, "ingredients": [{"name"… | MATCH |
| 104 | recipe_scaler | scaleRecipe | [{"title": "R", "base_servings": 4, "ingredients": [{"name"… | MATCH |
| 105 | recipe_scaler | scaleRecipe | [{"title": "R", "base_servings": 4, "ingredients": [{"name"… | DIVERGE F-01 |
| 106 | recipe_scaler | scaleRecipe | [{"title": "R", "base_servings": 4, "ingredients": [{"name"… | MATCH |
| 107 | recipe_scaler | scaleRecipe | [{"title": "R", "base_servings": 4, "ingredients": [{"name"… | MATCH |
| 108 | recipe_scaler | scaleRecipe | [{"title": "R", "base_servings": 4, "ingredients": [{"name"… | MATCH |
| 109 | recipe_scaler | scaleRecipe | [{"title": "R", "base_servings": 4, "ingredients": [{"name"… | MATCH |
| 110 | recipe_scaler | scaleRecipe | [{"title": "R", "base_servings": 4, "ingredients": [{"name"… | MATCH |
| 111 | recipe_scaler | scaleRecipe | [{"title": "R", "base_servings": 4, "ingredients": [{"name"… | MATCH |
| 112 | recipe_scaler | scaleRecipe | [{"title": "R", "base_servings": 4, "ingredients": [{"name"… | MATCH |
| 113 | recipe_scaler | scaleRecipe | [{"title": "R", "base_servings": 4, "ingredients": [{"name"… | MATCH |
| 114 | recipe_scaler | scaleRecipe | base_servings=0 | MATCH |
| 115 | recipe_scaler | scaleRecipe | base_servings=-1 | MATCH |
| 116 | recipe_scaler | scaleRecipe | base_servings="4" | MATCH |
| 117 | recipe_scaler | scaleRecipe | base_servings=null | MATCH |
| 118 | recipe_scaler | scaleRecipe | base_servings=1e309 | MATCH |
| 119 | recipe_scaler | scaleRecipe | base_servings=1e-320 | DIVERGE F-01 |
| 120 | recipe_scaler | scaleRecipe | base_servings=true | MATCH |
| 121 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[]},2] | MATCH |
| 122 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":"x"},2] | MATCH |
| 123 | recipe_scaler | scaleRecipe | [{"base_servings":4},2] | MATCH |
| 124 | recipe_scaler | scaleRecipe | [[],2] | MATCH |
| 125 | recipe_scaler | scaleRecipe | [null,2] | MATCH |
| 126 | recipe_scaler | scaleRecipe | ["x",2] | MATCH |
| 127 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":"","amount":1}]}… | MATCH |
| 128 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":"  ","amount":1}… | MATCH |
| 129 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":5,"amount":1}]},… | MATCH |
| 130 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":"A"}]},2] | MATCH |
| 131 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":"A","amount":"1"… | MATCH |
| 132 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":"A","amount":-1}… | MATCH |
| 133 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":"A","amount":1,"… | MATCH |
| 134 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":"A","amount":1,"… | MATCH |
| 135 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":"A","amount":1,"… | MATCH |
| 136 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":"A","amount":1,"… | MATCH |
| 137 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":"A","amount":1e3… | DIVERGE F-01 |
| 138 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":"A","amount":1,"… | MATCH |
| 139 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":["just a string"]},2] | MATCH |
| 140 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[null]},2] | MATCH |
| 141 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[[]]},2] | MATCH |
| 142 | recipe_scaler | scaleRecipe | [{"base_servings":4,"ingredients":[{"name":"<script>x</scri… | MATCH |
| 143 | recipe_scaler | scaleRecipe | 5000 ingredientes (sem limite documentado) | MATCH |
| 144 | recipe_scaler | formatAmount | [2.345] | MATCH |
| 145 | recipe_scaler | formatAmount | [12] | MATCH |
| 146 | recipe_scaler | formatAmount | [-0.001] | MATCH |
| 147 | recipe_scaler | formatAmount | [1e21] | DIVERGE F-05 |
| 148 | recipe_scaler | formatAmount | [1e-7] | MATCH |
| 149 | recipe_scaler | formatAmount | [0] | MATCH |
| 150 | recipe_scaler | formatAmount | [-0] | MATCH |
| 151 | recipe_scaler | formatAmount | [2.675] | MATCH |
| 152 | recipe_scaler | formatAmount | [1.005] | MATCH |
| 153 | recipe_scaler | formatAmount | ["x"] | MATCH |
| 154 | recipe_scaler | formatAmount | [null] | MATCH |
| 155 | recipe_scaler | formatAmount | [1e309] | MATCH |
| 156 | recipe_scaler | formatAmount | [123456789012345680000] | MATCH |
| 157 | quiz_engine | validateQuiz | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 158 | quiz_engine | validateQuiz | [null] | MATCH |
| 159 | quiz_engine | validateQuiz | [[]] | MATCH |
| 160 | quiz_engine | validateQuiz | ["x"] | MATCH |
| 161 | quiz_engine | validateQuiz | [5] | MATCH |
| 162 | quiz_engine | validateQuiz | [{}] | MATCH |
| 163 | quiz_engine | validateQuiz | [{"title": "", "questions": []}] | MATCH |
| 164 | quiz_engine | validateQuiz | [{"title": 5, "questions": [{"id": "q1", "prompt": "p", "op… | MATCH |
| 165 | quiz_engine | validateQuiz | [{"title": "T", "questions": []}] | MATCH |
| 166 | quiz_engine | validateQuiz | [{"title": "T", "questions": "x"}] | MATCH |
| 167 | quiz_engine | validateQuiz | [{"title": "T", "questions": [null]}] | MATCH |
| 168 | quiz_engine | validateQuiz | [{"title": "T", "questions": [[]]}] | MATCH |
| 169 | quiz_engine | validateQuiz | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 170 | quiz_engine | validateQuiz | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 171 | quiz_engine | validateQuiz | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 172 | quiz_engine | validateQuiz | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 173 | quiz_engine | validateQuiz | [{"title": "T", "questions": [{"id": 1, "prompt": "p", "opt… | MATCH |
| 174 | quiz_engine | validateQuiz | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 175 | quiz_engine | validateQuiz | 5000 perguntas (sem limite documentado) | MATCH |
| 176 | quiz_engine | validateQuiz | 5000 op\xe7\xf5es | MATCH |
| 177 | quiz_engine | validateQuiz | t\xedtulo de 200 KB | MATCH |
| 178 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 179 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 180 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 181 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 182 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 183 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 184 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 185 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 186 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 187 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 188 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 189 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 190 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 191 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 192 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 193 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 194 | quiz_engine | grade | [{"title": "T", "questions": [{"id": "q1", "prompt": "p", "… | MATCH |
| 195 | quiz_engine | grade | id de pergunta __proto__ | MATCH |
| 196 | quiz_engine | grade | id de pergunta constructor | MATCH |
| 197 | quiz_engine | grade | id toString e explica\xe7\xe3o com HTML (retorno bruto, n\x… | MATCH |
| 198 | quiz_engine | grade | 3 perguntas, 0 acertos | MATCH |
| 199 | quiz_engine | grade | arredondamento 33.3 | MATCH |
| 200 | quiz_engine | grade | arredondamento 66.7 | MATCH |
| 201 | svg_chart | renderChart | baseline | MATCH |
| 202 | svg_chart | renderChart | baseline linha | MATCH |
| 203 | svg_chart | renderChart | hostil: <script>alert(1)</script> | MATCH |
| 204 | svg_chart | renderChart | hostil: "/><script>alert(1)</script> | MATCH |
| 205 | svg_chart | renderChart | hostil: </text><script>x</script><text | MATCH |
| 206 | svg_chart | renderChart | hostil: ]]> | MATCH |
| 207 | svg_chart | renderChart | hostil: <!ENTITY x SYSTEM 'file:///etc | MATCH |
| 208 | svg_chart | renderChart | hostil: &xxe; | MATCH |
| 209 | svg_chart | renderChart | hostil: <?xml version='1.0'?> | MATCH |
| 210 | svg_chart | renderChart | hostil: javascript:alert(1) | MATCH |
| 211 | svg_chart | renderChart | hostil: <svg onload=alert(1)> | MATCH |
| 212 | svg_chart | renderChart | hostil: <foreignObject><iframe src=//e | MATCH |
| 213 | svg_chart | renderChart | hostil: <a xlink:href="javascript:aler | MATCH |
| 214 | svg_chart | renderChart | hostil: <image href="http://evil/x.png | MATCH |
| 215 | svg_chart | renderChart | hostil: <style>*{background:url(http:/ | MATCH |
| 216 | svg_chart | renderChart | hostil: ' onmouseover='alert(1) | MATCH |
| 217 | svg_chart | renderChart | hostil: \\x00\\x01\\x02\\x1f | MATCH |
| 218 | svg_chart | renderChart | hostil: a\\u2028b\\u2029c | MATCH |
| 219 | svg_chart | renderChart | hostil: a\\x85b | DIVERGE F-06 |
| 220 | svg_chart | renderChart | hostil: a\\ufeffb | DIVERGE F-06 |
| 221 | svg_chart | renderChart | hostil: a\\ufffe\\uffffb | MATCH |
| 222 | svg_chart | renderChart | hostil: a\\ud800b | MATCH |
| 223 | svg_chart | renderChart | hostil: \\u202eRTL | MATCH |
| 224 | svg_chart | renderChart | hostil: \\U0001f600\\U0001f600\\U0001f600\\U0001f600\\U0001… | DIVERGE F-06 |
| 225 | svg_chart | renderChart | hostil: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA | MATCH |
| 226 | svg_chart | renderChart | hostil: \\x7f\\x80\\x9f | MATCH |
| 227 | svg_chart | renderChart | hostil: &#x3C;script&#x3E; | MATCH |
| 228 | svg_chart | renderChart | hostil: %3Cscript%3E | MATCH |
| 229 | svg_chart | renderChart | hostil: ${7*7}{{7*7}} | MATCH |
| 230 | svg_chart | renderChart | hostil: \\\\u003cscript\\\\u003e | MATCH |
| 231 | svg_chart | renderChart | hostil linha | MATCH |
| 232 | svg_chart | renderChart | hostil linha | MATCH |
| 233 | svg_chart | renderChart | hostil linha | MATCH |
| 234 | svg_chart | renderChart | hostil linha | MATCH |
| 235 | svg_chart | renderChart | hostil linha | MATCH |
| 236 | svg_chart | renderChart | hostil linha | MATCH |
| 237 | svg_chart | renderChart | [null] | MATCH |
| 238 | svg_chart | renderChart | [[]] | MATCH |
| 239 | svg_chart | renderChart | ["x"] | MATCH |
| 240 | svg_chart | renderChart | [5] | MATCH |
| 241 | svg_chart | renderChart | [true] | MATCH |
| 242 | svg_chart | renderChart | [{}] | MATCH |
| 243 | svg_chart | renderChart | [{"type":"pie"}] | MATCH |
| 244 | svg_chart | renderChart | [{"type":"BAR"}] | MATCH |
| 245 | svg_chart | renderChart | [{"type":"bar "}] | MATCH |
| 246 | svg_chart | renderChart | [{"type":["bar"]}] | MATCH |
| 247 | svg_chart | renderChart | labels="x" | MATCH |
| 248 | svg_chart | renderChart | labels=[] | MATCH |
| 249 | svg_chart | renderChart | labels=null | MATCH |
| 250 | svg_chart | renderChart | labels=[null] | MATCH |
| 251 | svg_chart | renderChart | labels=[true] | MATCH |
| 252 | svg_chart | renderChart | labels=[[1]] | MATCH |
| 253 | svg_chart | renderChart | labels=[{"a":1}] | MATCH |
| 254 | svg_chart | renderChart | labels=[1,"a"] | MATCH |
| 255 | svg_chart | renderChart | labels=[3.14159,2] | DIVERGE F-06 |
| 256 | svg_chart | renderChart | labels=[1e21,2] | DIVERGE F-06 |
| 257 | svg_chart | renderChart | labels=[1e-7,2] | DIVERGE F-06 |
| 258 | svg_chart | renderChart | labels=[123456789012,2] | MATCH |
| 259 | svg_chart | renderChart | labels=[-5,2] | MATCH |
| 260 | svg_chart | renderChart | labels=[0.30000000000000004,2] | DIVERGE F-06 |
| 261 | svg_chart | renderChart | labels=[1.005,2.675] | DIVERGE F-06 |
| 262 | svg_chart | renderChart | labels=[5e-324,2] | DIVERGE F-06 |
| 263 | svg_chart | renderChart | labels=[1e309,2] | DIVERGE F-01 |
| 264 | svg_chart | renderChart | labels=[0.1,2] | MATCH |
| 265 | svg_chart | renderChart | labels=[100.0,2] | MATCH |
| 266 | svg_chart | renderChart | labels=[1e5,2] | MATCH |
| 267 | svg_chart | renderChart | labels=[1.5e300,2] | DIVERGE F-06 |
| 268 | svg_chart | renderChart | 50 labels (limite) | MATCH |
| 269 | svg_chart | renderChart | 51 labels | MATCH |
| 270 | svg_chart | renderChart | 6 series (limite) | MATCH |
| 271 | svg_chart | renderChart | 7 series | MATCH |
| 272 | svg_chart | renderChart | series=[] | MATCH |
| 273 | svg_chart | renderChart | series="x" | MATCH |
| 274 | svg_chart | renderChart | series=null | MATCH |
| 275 | svg_chart | renderChart | series=[null] | MATCH |
| 276 | svg_chart | renderChart | series=["x"] | MATCH |
| 277 | svg_chart | renderChart | series=[{}] | MATCH |
| 278 | svg_chart | renderChart | series=[{"values":"x"}] | MATCH |
| 279 | svg_chart | renderChart | series=[{"values":[]}] | MATCH |
| 280 | svg_chart | renderChart | series=[{"values":[1,2,3]}] | MATCH |
| 281 | svg_chart | renderChart | valor="1" | MATCH |
| 282 | svg_chart | renderChart | linha valor="1" | MATCH |
| 283 | svg_chart | renderChart | valor=null | MATCH |
| 284 | svg_chart | renderChart | linha valor=null | MATCH |
| 285 | svg_chart | renderChart | valor=true | MATCH |
| 286 | svg_chart | renderChart | linha valor=true | MATCH |
| 287 | svg_chart | renderChart | valor=[] | MATCH |
| 288 | svg_chart | renderChart | linha valor=[] | MATCH |
| 289 | svg_chart | renderChart | valor={} | MATCH |
| 290 | svg_chart | renderChart | linha valor={} | MATCH |
| 291 | svg_chart | renderChart | valor=-1 | MATCH |
| 292 | svg_chart | renderChart | linha valor=-1 | MATCH |
| 293 | svg_chart | renderChart | valor=-0.0 | MATCH |
| 294 | svg_chart | renderChart | linha valor=-0.0 | MATCH |
| 295 | svg_chart | renderChart | valor=0 | MATCH |
| 296 | svg_chart | renderChart | linha valor=0 | MATCH |
| 297 | svg_chart | renderChart | valor=1e308 | DIVERGE F-01 |
| 298 | svg_chart | renderChart | linha valor=1e308 | DIVERGE F-01 |
| 299 | svg_chart | renderChart | valor=1.7976931348623157e308 | DIVERGE F-01 |
| 300 | svg_chart | renderChart | linha valor=1.7976931348623157e308 | DIVERGE F-01 |
| 301 | svg_chart | renderChart | valor=1e309 | MATCH |
| 302 | svg_chart | renderChart | linha valor=1e309 | MATCH |
| 303 | svg_chart | renderChart | valor=-1e309 | MATCH |
| 304 | svg_chart | renderChart | linha valor=-1e309 | MATCH |
| 305 | svg_chart | renderChart | valor=5e-324 | MATCH |
| 306 | svg_chart | renderChart | linha valor=5e-324 | MATCH |
| 307 | svg_chart | renderChart | valor=1e-320 | MATCH |
| 308 | svg_chart | renderChart | linha valor=1e-320 | MATCH |
| 309 | svg_chart | renderChart | valor=1e21 | MATCH |
| 310 | svg_chart | renderChart | linha valor=1e21 | MATCH |
| 311 | svg_chart | renderChart | valor=1000000000000000000000000000000000000000 | DIVERGE F-01 |
| 312 | svg_chart | renderChart | linha valor=1000000000000000000000000000000000000000 | DIVERGE F-01 |
| 313 | svg_chart | renderChart | valor=123456789012345678901234567890 | DIVERGE F-06 |
| 314 | svg_chart | renderChart | linha valor=123456789012345678901234567890 | DIVERGE F-06 |
| 315 | svg_chart | renderChart | valor=0.1 | MATCH |
| 316 | svg_chart | renderChart | linha valor=0.1 | MATCH |
| 317 | svg_chart | renderChart | valor=1e15 | MATCH |
| 318 | svg_chart | renderChart | linha valor=1e15 | MATCH |
| 319 | svg_chart | renderChart | valor=2.5e-7 | MATCH |
| 320 | svg_chart | renderChart | linha valor=2.5e-7 | MATCH |
| 321 | svg_chart | renderChart | tudo zero | MATCH |
| 322 | svg_chart | renderChart | width="640" | MATCH |
| 323 | svg_chart | renderChart | height="640" | MATCH |
| 324 | svg_chart | renderChart | width=640.0 | DIVERGE F-08 |
| 325 | svg_chart | renderChart | height=640.0 | DIVERGE F-08 |
| 326 | svg_chart | renderChart | width=640.5 | MATCH |
| 327 | svg_chart | renderChart | height=640.5 | MATCH |
| 328 | svg_chart | renderChart | width=199 | MATCH |
| 329 | svg_chart | renderChart | height=199 | MATCH |
| 330 | svg_chart | renderChart | width=200 | MATCH |
| 331 | svg_chart | renderChart | height=200 | MATCH |
| 332 | svg_chart | renderChart | width=2000 | MATCH |
| 333 | svg_chart | renderChart | height=2000 | MATCH |
| 334 | svg_chart | renderChart | width=2001 | MATCH |
| 335 | svg_chart | renderChart | height=2001 | MATCH |
| 336 | svg_chart | renderChart | width=true | MATCH |
| 337 | svg_chart | renderChart | height=true | MATCH |
| 338 | svg_chart | renderChart | width=null | MATCH |
| 339 | svg_chart | renderChart | height=null | MATCH |
| 340 | svg_chart | renderChart | width=-1 | MATCH |
| 341 | svg_chart | renderChart | height=-1 | MATCH |
| 342 | svg_chart | renderChart | width=1e3 | DIVERGE F-08 |
| 343 | svg_chart | renderChart | height=1e3 | DIVERGE F-08 |
| 344 | svg_chart | renderChart | width="__proto__" | MATCH |
| 345 | svg_chart | renderChart | height="__proto__" | MATCH |
| 346 | svg_chart | renderChart | width=[] | MATCH |
| 347 | svg_chart | renderChart | height=[] | MATCH |
| 348 | svg_chart | renderChart | width={} | MATCH |
| 349 | svg_chart | renderChart | height={} | MATCH |
| 350 | svg_chart | renderChart | width=1e309 | MATCH |
| 351 | svg_chart | renderChart | height=1e309 | MATCH |
| 352 | svg_chart | renderChart | width=2000.0 | DIVERGE F-08 |
| 353 | svg_chart | renderChart | height=2000.0 | DIVERGE F-08 |
| 354 | svg_chart | renderChart | width=200.0 | DIVERGE F-08 |
| 355 | svg_chart | renderChart | height=200.0 | DIVERGE F-08 |
| 356 | svg_chart | renderChart | campos extras/desconhecidos | MATCH |
| 357 | svg_chart | renderChart | title/name n\xe3o-string | MATCH |
| 358 | svg_chart | renderChart | truncamento: 119 'a' + emoji + bcd | DIVERGE F-06 |
| 359 | svg_chart | renderChart | truncamento emoji em title/label/name | DIVERGE F-06 |
| 360 | link_card | buildLinkCard | url=https://example.com | MATCH |
| 361 | link_card | buildLinkCard | url=https://Example.COM:443/a | MATCH |
| 362 | link_card | buildLinkCard | url=http://example.com:80 | MATCH |
| 363 | link_card | buildLinkCard | url=http://example.com:8080/x | MATCH |
| 364 | link_card | buildLinkCard | url=http://[::1]:8080/x | MATCH |
| 365 | link_card | buildLinkCard | url=http://[::1]/ | MATCH |
| 366 | link_card | buildLinkCard | url=http://[::1]:80/ | MATCH |
| 367 | link_card | buildLinkCard | url=https://[::1]:443 | MATCH |
| 368 | link_card | buildLinkCard | url=http://[0:0:0:0:0:0:0:1]/ | DIVERGE F-09 |
| 369 | link_card | buildLinkCard | url=http://[::FFFF:1.2.3.4]/ | DIVERGE F-09 |
| 370 | link_card | buildLinkCard | url=http://[2001:DB8::1]:9/p?q=1#f | MATCH |
| 371 | link_card | buildLinkCard | url=http://[fe80::1%25eth0]/ | DIVERGE F-09 |
| 372 | link_card | buildLinkCard | url=http://[::1 | MATCH |
| 373 | link_card | buildLinkCard | url=http://::1/ | MATCH |
| 374 | link_card | buildLinkCard | url=http://[::1]x/ | MATCH |
| 375 | link_card | buildLinkCard | url=http://[::g]/ | MATCH |
| 376 | link_card | buildLinkCard | url=http://[]/ | MATCH |
| 377 | link_card | buildLinkCard | url=http://127.0.0.1:3000/ | MATCH |
| 378 | link_card | buildLinkCard | url=http://127.1/ | DIVERGE F-09 |
| 379 | link_card | buildLinkCard | url=http://0x7f.1/ | DIVERGE F-09 |
| 380 | link_card | buildLinkCard | url=http://2130706433/ | DIVERGE F-09 |
| 381 | link_card | buildLinkCard | url=http://0177.0.0.1/ | DIVERGE F-09 |
| 382 | link_card | buildLinkCard | url=http://192.168.0.1/ | MATCH |
| 383 | link_card | buildLinkCard | url=http://169.254.169.254/latest/meta-data/ | MATCH |
| 384 | link_card | buildLinkCard | url=http://256.256.256.256/ | DIVERGE F-09 |
| 385 | link_card | buildLinkCard | url=http://1.2.3/ | DIVERGE F-09 |
| 386 | link_card | buildLinkCard | url=http://1.2.3.4.5/ | DIVERGE F-09 |
| 387 | link_card | buildLinkCard | url=http://localhost/ | MATCH |
| 388 | link_card | buildLinkCard | url=http://LOCALHOST:8080 | MATCH |
| 389 | link_card | buildLinkCard | url=http://example.com./ | MATCH |
| 390 | link_card | buildLinkCard | url=http://-bad-.com/ | MATCH |
| 391 | link_card | buildLinkCard | url=http://a_b.com/ | MATCH |
| 392 | link_card | buildLinkCard | url=http://exa%6Dple.com/ | DIVERGE F-09 |
| 393 | link_card | buildLinkCard | url=http://b\\xfccher.de/ | DIVERGE F-09 |
| 394 | link_card | buildLinkCard | url=http://xn--bcher-kva.de/ | MATCH |
| 395 | link_card | buildLinkCard | url=http://\\u4f8b\\u3048.jp/ | DIVERGE F-09 |
| 396 | link_card | buildLinkCard | url=http://EXAMPLE.com/\\xc4 | DIVERGE F-09 |
| 397 | link_card | buildLinkCard | url=http://example.com/\\xe9?\\xe9#\\xe9 | DIVERGE F-09 |
| 398 | link_card | buildLinkCard | url=http://example.com/a/../b | DIVERGE F-09 |
| 399 | link_card | buildLinkCard | url=http://example.com/./a//b | DIVERGE F-09 |
| 400 | link_card | buildLinkCard | url=http://example.com/%2e%2e/x | DIVERGE F-09 |
| 401 | link_card | buildLinkCard | url=http://example.com/a%2Fb | MATCH |
| 402 | link_card | buildLinkCard | url=http://example.com?q=1 | MATCH |
| 403 | link_card | buildLinkCard | url=http://example.com#f | MATCH |
| 404 | link_card | buildLinkCard | url=http://example.com/? | DIVERGE F-09 |
| 405 | link_card | buildLinkCard | url=http://example.com/# | DIVERGE F-09 |
| 406 | link_card | buildLinkCard | url=http://example.com/path? | DIVERGE F-09 |
| 407 | link_card | buildLinkCard | url=http://example.com/p?a="<>' | DIVERGE F-09 |
| 408 | link_card | buildLinkCard | url=http://example.com/"<>'{}\|^ | DIVERGE F-09 |
| 409 | link_card | buildLinkCard | url=http://example.com: | MATCH |
| 410 | link_card | buildLinkCard | url=http://example.com:/ | MATCH |
| 411 | link_card | buildLinkCard | url=http://example.com:0/ | MATCH |
| 412 | link_card | buildLinkCard | url=http://example.com:65535/ | MATCH |
| 413 | link_card | buildLinkCard | url=http://example.com:65536/ | MATCH |
| 414 | link_card | buildLinkCard | url=http://example.com:99999999999/ | MATCH |
| 415 | link_card | buildLinkCard | url=http://example.com:-1/ | MATCH |
| 416 | link_card | buildLinkCard | url=http://example.com:abc/ | MATCH |
| 417 | link_card | buildLinkCard | url=http://example.com:080/ | MATCH |
| 418 | link_card | buildLinkCard | url=http://example.com:+80/ | MATCH |
| 419 | link_card | buildLinkCard | url=HTTP://EXAMPLE.COM | MATCH |
| 420 | link_card | buildLinkCard | url=hTtPs://example.com | MATCH |
| 421 | link_card | buildLinkCard | url=http:/example.com | MATCH |
| 422 | link_card | buildLinkCard | url=http:example.com | MATCH |
| 423 | link_card | buildLinkCard | url=http:///x | MATCH |
| 424 | link_card | buildLinkCard | url=http:// | MATCH |
| 425 | link_card | buildLinkCard | url=http://:80 | MATCH |
| 426 | link_card | buildLinkCard | url=http://?x | MATCH |
| 427 | link_card | buildLinkCard | url=http://#x | MATCH |
| 428 | link_card | buildLinkCard | url=http://. | MATCH |
| 429 | link_card | buildLinkCard | url=http://.. | MATCH |
| 430 | link_card | buildLinkCard | url=http://a b.com | MATCH |
| 431 | link_card | buildLinkCard | url=http://a.com/ b | MATCH |
| 432 | link_card | buildLinkCard | url=http://u:p@x.com | MATCH |
| 433 | link_card | buildLinkCard | url=http://u@x.com | MATCH |
| 434 | link_card | buildLinkCard | url=http://:p@x.com | MATCH |
| 435 | link_card | buildLinkCard | url=http://@x.com | MATCH |
| 436 | link_card | buildLinkCard | url=http://x.com@evil.com | MATCH |
| 437 | link_card | buildLinkCard | url=http://evil.com\\\\@good.com | DIVERGE F-09 |
| 438 | link_card | buildLinkCard | url=http://evil.com\\\\x | DIVERGE F-09 |
| 439 | link_card | buildLinkCard | url=http://evil.com\\\\ | DIVERGE F-09 |
| 440 | link_card | buildLinkCard | url=http:\\\\\\\\evil.com | MATCH |
| 441 | link_card | buildLinkCard | url=http://evil.com/\\\\x | DIVERGE F-09 |
| 442 | link_card | buildLinkCard | url=javascript:alert(1) | MATCH |
| 443 | link_card | buildLinkCard | url=JaVaScRiPt:alert(1) | MATCH |
| 444 | link_card | buildLinkCard | url=data:text/html,<script>x</script> | MATCH |
| 445 | link_card | buildLinkCard | url=file:///etc/passwd | MATCH |
| 446 | link_card | buildLinkCard | url=ftp://x.com | MATCH |
| 447 | link_card | buildLinkCard | url=mailto:a@b.c | MATCH |
| 448 | link_card | buildLinkCard | url=vbscript:x | MATCH |
| 449 | link_card | buildLinkCard | url=blob:http://x/y | MATCH |
| 450 | link_card | buildLinkCard | url=about:blank | MATCH |
| 451 | link_card | buildLinkCard | url=//example.com | MATCH |
| 452 | link_card | buildLinkCard | url=example.com | MATCH |
| 453 | link_card | buildLinkCard | url=/path | MATCH |
| 454 | link_card | buildLinkCard | url= | MATCH |
| 455 | link_card | buildLinkCard | url=    | MATCH |
| 456 | link_card | buildLinkCard | url=  https://example.com   | MATCH |
| 457 | link_card | buildLinkCard | url=https://example.com/\\xa0x | DIVERGE F-09 |
| 458 | link_card | buildLinkCard | url=https://example.com/\\u3000x | DIVERGE F-09 |
| 459 | link_card | buildLinkCard | url=https://exam\\xa0ple.com | DIVERGE F-09 |
| 460 | link_card | buildLinkCard | url=https://exam\\u200bple.com | DIVERGE F-09 |
| 461 | link_card | buildLinkCard | url=https://example.com/\\u202e | DIVERGE F-09 |
| 462 | link_card | buildLinkCard | url=https://\\uff25\\uff38\\uff21\\uff2d\\uff30\\uff2c\\uff… | DIVERGE F-09 |
| 463 | link_card | buildLinkCard | url=https://example.com\\u3002 | DIVERGE F-09 |
| 464 | link_card | buildLinkCard | url=https://example.com\\uff0e | DIVERGE F-09 |
| 465 | link_card | buildLinkCard | url=https://example.com/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa… | MATCH |
| 466 | link_card | buildLinkCard | url=https://example.com/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa… | MATCH |
| 467 | link_card | buildLinkCard | url=https://example.com/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa… | MATCH |
| 468 | link_card | buildLinkCard | url=http://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa… | MATCH |
| 469 | link_card | buildLinkCard | url=https://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa… | MATCH |
| 470 | link_card | buildLinkCard | url=https://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa… | MATCH |
| 471 | link_card | buildLinkCard | url=https://example.com/% | MATCH |
| 472 | link_card | buildLinkCard | url=https://example.com/%zz | MATCH |
| 473 | link_card | buildLinkCard | url=https://example.com/%00 | MATCH |
| 474 | link_card | buildLinkCard | url=https://example.com/\\x00 | MATCH |
| 475 | link_card | buildLinkCard | url=https://example.com/\\ud800 | DIVERGE F-09 |
| 476 | link_card | buildLinkCard | url=https://example.com/<script>alert(1)</script> | DIVERGE F-09 |
| 477 | link_card | buildLinkCard | url=https://example.com/"><script>alert(1)</script> | DIVERGE F-09 |
| 478 | link_card | buildLinkCard | url=https://example.com/?a=1&b=2&amp;c=3 | MATCH |
| 479 | link_card | buildLinkCard | url=https://example.com/'onmouseover='alert(1) | MATCH |
| 480 | link_card | buildLinkCard | url=https://example.com:443@evil.com/ | MATCH |
| 481 | link_card | buildLinkCard | url=https://evil.com:443:80/ | MATCH |
| 482 | link_card | buildLinkCard | url=http://1e3.com/ | MATCH |
| 483 | link_card | buildLinkCard | url=http://[::1]:8080:90/ | MATCH |
| 484 | link_card | buildLinkCard | url=http://[::1]:/ | MATCH |
| 485 | link_card | buildLinkCard | url=http://[v1.fe]/ | DIVERGE F-09 |
| 486 | link_card | buildLinkCard | tipo errado url=null | MATCH |
| 487 | link_card | buildLinkCard | tipo errado url=5 | MATCH |
| 488 | link_card | buildLinkCard | tipo errado url=[] | MATCH |
| 489 | link_card | buildLinkCard | tipo errado url={} | MATCH |
| 490 | link_card | buildLinkCard | tipo errado url=true | MATCH |
| 491 | link_card | buildLinkCard | entrada=null | MATCH |
| 492 | link_card | buildLinkCard | entrada=[] | MATCH |
| 493 | link_card | buildLinkCard | entrada="https://example.com" | MATCH |
| 494 | link_card | buildLinkCard | entrada=5 | MATCH |
| 495 | link_card | buildLinkCard | entrada={} | MATCH |
| 496 | link_card | buildLinkCard | entrada={"u":"https://example.com"} | MATCH |
| 497 | link_card | buildLinkCard | entrada=[{"url":"https://example.com"}] | MATCH |
| 498 | link_card | buildLinkCard | entrada=[] | MATCH |
| 499 | link_card | buildLinkCard | title/description=null | MATCH |
| 500 | link_card | buildLinkCard | title/description=5 | MATCH |
| 501 | link_card | buildLinkCard | title/description=[] | MATCH |
| 502 | link_card | buildLinkCard | title/description={} | MATCH |
| 503 | link_card | buildLinkCard | title/description="" | MATCH |
| 504 | link_card | buildLinkCard | title/description="  " | MATCH |
| 505 | link_card | buildLinkCard | title/description="x" | MATCH |
| 506 | link_card | buildLinkCard | title/description="<script>alert(1)</script>" | MATCH |
| 507 | link_card | buildLinkCard | title/description="\\u0000a\\u001fb" | MATCH |
| 508 | link_card | buildLinkCard | title/description="ttttttttttttttttttttttttttttttttttttttt | MATCH |
| 509 | link_card | buildLinkCard | title/description="\U0001f600\U0001f600\U0001f600\U0001f600… | DIVERGE F-09 |
| 510 | link_card | buildLinkCard | title/description="ttttttttttttttttttttttttttttttttttttttt | DIVERGE F-09 |
| 511 | link_card | buildLinkCard | title/description="a\\u0085b" | DIVERGE F-09 |
| 512 | link_card | buildLinkCard | title/description="a\\ufeffb" | DIVERGE F-09 |
| 513 | link_card | buildLinkCard | title/description="\\u2028" | MATCH |
| 514 | link_card | buildLinkCard | descri\xe7\xe3o 301 | MATCH |
| 515 | link_card | buildLinkCard | descri\xe7\xe3o emoji no corte | DIVERGE F-09 |
| 516 | link_card | buildLinkCard | campos extras | MATCH |
