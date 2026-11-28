# 04 — Evidência histórica × executada agora

Regra: nada histórico foi promovido a teste atual. "Executado agora" = rodei neste ambiente em 2026-11-28 (UTC), Python 3.12.3, Node v22.23.5, contêiner Linux, **sem navegador e sem Android**. Artefatos: `logs/`, `tests_auditoria/`.

| Item | Resultado | Executado agora? | Evidência / observação |
|---|---|---|---|
| Integridade dos 3 ZIPs (CRC, `..`, caminhos absolutos, symlinks) | PASS | SIM | `unzip -tq` sem erros; nenhum caminho suspeito |
| ZIP Tool Hub: 94.977 bytes, 56 entradas, SHA-256 `f5415aab…253cee` | PASS | SIM | hash completo em `HASHES_SHA256.txt` |
| Git blob SHA do ZIP = `7bb74b7b…dc22` | PASS | SIM | calculado `sha1("blob N\0"+bytes)`: bate com o valor histórico. É Git blob SHA, **não** SHA-256 |
| `MANIFESTO.json` do pacote: 54 arquivos, bytes e SHA-256 | PASS | SIM | 0 divergentes; os 2 não listados são `MANIFESTO.json`/`MANIFESTO.md` |
| JavaScript (`node --test`) | PASS 27/27 | SIM | `logs/execucao_agora.log`, `logs/RELATORIO_EXECUCAO_AGORA.md` |
| Python (`unittest`) | PASS 30/30 | SIM | idem |
| Paridade da suíte do pacote | PASS 28/28 | SIM | só 28 casos; **não prova** paridade (ver `03_...`) |
| Caso IPv6 `http://[::1]:8080/x` | PASS | SIM | nos dois lados host `[::1]`, URL `http://[::1]:8080/x` (id 364 do corpus e testes unitários) |
| Simulação de navegador (DOM falso) | SIMULATION PASS 5/5 | SIM | **não é Chrome nem Android** |
| Sintaxe: `py_compile` (20 arquivos), `node --check` (15) | PASS | SIM | `logs/execucao_agora.log` |
| Imports Python / `require` Node | PASS | SIM | idem |
| Corpus adversarial, 516 casos Python × JS | **FAIL (paridade)**: 426 MATCH, 90 DIVERGE | SIM | `03_MATRIZ_PARIDADE.md` |
| Verificação de saída SVG/HTML (lista branca) | PASS (sem injeção); 6 saídas XML mal formadas | SIM | `tests_auditoria/resultado_seguranca_saida.json` |
| Python 26/26 | HISTÓRICO / NÃO REVALIDADO | NÃO | a suíte atual tem 30 testes; o log de 26 não foi fornecido |
| Python 68/68 | HISTÓRICO / NÃO REVALIDADO | NÃO | artefato primário não localizado; **não corresponde** a este pacote (30 testes) |
| JavaScript 27/27 (histórico) | confirmado em outro run | SIM (ver acima) | o número bate com o re-run atual; o log histórico em si não foi fornecido |
| Paridade 27/28 (divergência IPv6) | HISTÓRICO | NÃO | a causa/commit da correção não foi localizada (sem repositório); o estado atual (28/28, `[::1]` igual) foi verificado |
| 94 cenários de conformidade | HISTÓRICO / NÃO REVALIDADO | NÃO | artefato não localizado |
| 65 casos de validação SVG | HISTÓRICO / NÃO REVALIDADO | NÃO | artefato não localizado. O corpus novo tem 28 textos hostis + dezenas de casos de tipos/limites em `svg_chart`; **não são** os 65 |
| Chrome / Android / APK / dispositivo / runtime real / produção | NOT TESTED | NÃO | `smoke_test.html` existe e não foi executado |
| Python 3.9–3.11, Node < 22 | NOT TESTED | NÃO | |
| Hash esperado do contrato `AI_TOOL_BRIDGE.md` | BLOCKED | NÃO | não existe hash esperado |
| Repositório `vidift-max/ai-bridge-browser`, HEAD, branch, log, status | BLOCKED | NÃO | sem workspace original e sem rede; HEAD `5636e825…` vem do inventário histórico, não verificado |
| Commit / push | NÃO REALIZADO | NÃO | proibido nesta etapa |
