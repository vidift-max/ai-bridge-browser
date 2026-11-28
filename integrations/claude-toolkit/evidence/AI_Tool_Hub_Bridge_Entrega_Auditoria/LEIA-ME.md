# AI_Tool_Hub_Bridge_Entrega_Auditoria

Entrega da auditoria somente leitura do AI Tool Hub (2026-11-28). **Status: BLOCKED** (ver `01_RELATORIO_AUDITORIA.md`).

## Índice
| Arquivo / pasta | Conteúdo |
|---|---|
| `01_RELATORIO_AUDITORIA.md` | Relatório final: status, implementação, testes, segurança, pendências |
| `02_ACHADOS_E_RECOMENDACOES.md` | 17 achados (F-01…F-17) com reprodução e recomendação |
| `03_MATRIZ_PARIDADE.md` | Matriz Python × JS dos 516 casos (426 MATCH, 90 DIVERGE) |
| `04_EVIDENCIAS_HISTORICAS_vs_EXECUTADAS.md` | O que é histórico e o que foi executado agora |
| `05_AUTENTICACAO_PERMISSOES_LIMITES_LICENCA_CONTRATO.md` | Auth, permissões, limites, logs, licença, SHA-256 do contrato |
| `tests_auditoria/` | Corpus, scripts e resultados brutos (reproduzíveis) |
| `logs/` | Saída bruta da suíte do pacote, sintaxe, imports, MANIFESTO.json |
| `entradas_originais/` | Os 3 ZIPs recebidos, byte a byte, com SHA-256 |
| `HASHES_SHA256.txt` | SHA-256 de todos os arquivos deste ZIP (exceto ele mesmo) |

## Reproduzir (testado com Python 3.12.3 e Node v22.23.5; sem rede)
A partir da raiz deste ZIP descompactado:
```bash
unzip entradas_originais/AI_Tool_Hub_Pacote_Independente.zip -d pkg
B=$(pwd)/pkg/AI_Tool_Hub_Package/01_Ferramentas_Exportaveis
cd tests_auditoria
python3 gen_cases.py                                  # gera cases.jsonl (516 casos)
python3 run_py.py $B/python resultados_py.json
node run_js.js $B/js resultados_js.json
python3 compare.py resultados_py.json resultados_js.json cases.jsonl resultado
python3 gerar_matriz.py                               # regrava ../03_MATRIZ_PARIDADE.md
```

(`timing_py.py` e `timing_js.js` medem o achado F-02; use `timeout`, a entrada de 32 mil caracteres leva ~32 s em Python.)

## Limites desta entrega
Sem workspace original, sem rede, sem navegador, sem Android. Nada foi alterado no pacote; nada foi enviado ao GitHub. Evidências históricas sem artefato continuam históricas.
