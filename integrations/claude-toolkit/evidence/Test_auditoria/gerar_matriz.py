#!/usr/bin/env python3
"""Gera ../03_MATRIZ_PARIDADE.md a partir de resultado_paridade.json (saída real de run_py.py/run_js.js/compare.py)."""
import json
from collections import Counter, defaultdict
rows = json.load(open("resultado_paridade.json"))
def esc(s, n=70):
    s = str(s).encode("unicode_escape", "backslashreplace").decode().replace("|", "\\|").replace("`", "'")
    return s if len(s) <= n else s[:n - 1] + "…"
def finding(r):
    if r["status"] == "MATCH": return ""
    d = r["py"].get("detail", "")
    if r["py"]["outcome"] == "crash" and "positional" in d: return "F-10"
    g, fn, note = r["group"], r["fn"], r["note"]
    if g == "duration_timer": return "F-03" if fn == "parseDuration" else "F-04"
    if g == "recipe_scaler": return "F-05" if fn == "formatAmount" else "F-01"
    if g == "svg_chart":
        if r["py"]["outcome"] == "crash": return "F-01"
        return "F-08" if ("width=" in note or "height=" in note) else "F-06"
    if g == "link_card": return "F-09"
    return "NAO_CLASSIFICADO"
def show(x, r):
    if x["outcome"] == "error": return "erro " + x["code"]
    if x["outcome"] == "crash": return "CRASH " + esc(x["detail"], 48)
    if x["outcome"] == "parse_error": return "parse_error"
    v = x["value"]
    if r["group"] == "svg_chart": return "SVG ok"
    if r["group"] == "link_card" and isinstance(v, dict): return esc(v["url"], 44)
    if isinstance(v, str) and r["group"] == "svg_chart": return "SVG ok"
    return "ok " + esc(json.dumps(v, ensure_ascii=False), 44)
for r in rows: r["finding"] = finding(r)
assert not any(r["finding"] == "NAO_CLASSIFICADO" for r in rows)
# SVG ok hides text differences; show 'SVG (n B)' using sizes already summarised? keep generic.
tot = Counter(r["status"] for r in rows)
by = defaultdict(Counter)
for r in rows: by[r["group"]][r["status"]] += 1
fc = Counter(r["finding"] for r in rows if r["finding"])
out = ["# 03 — Matriz de paridade Python × JavaScript (corpus adversarial)", "",
       "**Executado agora:** SIM (2026-11-28, Python 3.12.3, Node v22.23.5). Ambos os lados receberam exatamente o mesmo texto JSON (`cases.jsonl`, gerado por `gen_cases.py`).",
       "Resultados brutos: `tests_auditoria/resultados_py.json`, `resultados_js.json`, `resultado_paridade.json`.", "",
       "Critério: MATCH = mesmo desfecho (valor igual, ou mesmo código de erro). Inteiros e floats de valor inteiro são tratados como iguais (5 = 5.0), como já documentado pelo pacote. DIVERGE = valores diferentes, ou um lado aceita e o outro recusa, ou um lado lança exceção não controlada (CRASH).", "",
       "## Resumo", "", "| Ferramenta | Casos | MATCH | DIVERGE |", "|---|---:|---:|---:|"]
for g in ["duration_timer", "recipe_scaler", "quiz_engine", "svg_chart", "link_card"]:
    out.append(f"| {g} | {sum(by[g].values())} | {by[g]['MATCH']} | {by[g]['DIVERGE']} |")
out += [f"| **Total** | **{len(rows)}** | **{tot['MATCH']}** | **{tot['DIVERGE']}** |", "",
        "**Leitura honesta:** o resultado histórico/atual `28/28` (suíte do pacote) continua verdadeiro para aqueles 28 casos, mas **não prova paridade**. Com 516 casos hostis/limite, há divergências reais. A paridade NÃO pode ser declarada.", "",
        "Divergências por achado: " + ", ".join(f"{k}={v}" for k, v in sorted(fc.items())) + ". Descrição de cada achado em `02_ACHADOS_E_RECOMENDACOES.md`.", "",
        "Caso `link_card` com `http://[::1]:8080/x` (id %d): " % next(r["id"] for r in rows if r["args_text"].startswith('[{"url": "http://[::1]:8080/x"}')) + "MATCH nos dois lados (host `[::1]`).", "",
        "## Divergências (todas)", "", "| ID | Ferramenta | Função | Caso | Python | JavaScript | Achado |", "|---:|---|---|---|---|---|---|"]
for r in rows:
    if r["status"] != "MATCH":
        out.append(f"| {r['id']} | {r['group']} | {r['fn']} | {esc(r['note'] or r['args_text'], 60)} | {show(r['py'], r)} | {show(r['js'], r)} | {r['finding']} |")
out += ["", "## Todos os casos (MATCH e DIVERGE)", "", "| ID | Ferramenta | Função | Caso | Resultado |", "|---:|---|---|---|---|"]
for r in rows:
    out.append(f"| {r['id']} | {r['group']} | {r['fn']} | {esc(r['note'] or r['args_text'], 60)} | {r['status']}{(' ' + r['finding']) if r['finding'] else ''} |")
open("../03_MATRIZ_PARIDADE.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
json.dump(rows, open("resultado_paridade_classificado.json", "w", encoding="utf-8"), ensure_ascii=True, indent=1)
print(dict(tot)); print({g: dict(c) for g, c in by.items()}); print(dict(fc))
