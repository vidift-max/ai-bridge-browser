#!/usr/bin/env python3
"""Compara resultados Python x JS e verifica segurança de SVG/HTML. Uso: compare.py res_py.json res_js.json cases.jsonl saida_prefixo"""
import json, sys, re, xml.etree.ElementTree as ET
from html.parser import HTMLParser
py = {r["id"]: r for r in json.load(open(sys.argv[1]))}
js = {r["id"]: r for r in json.load(open(sys.argv[2]))}
cases = {}
for l in open(sys.argv[3], encoding="utf-8"):
    c = json.loads(l); cases[c["id"]] = c
def norm(v):
    if isinstance(v, float) and v == int(v) and abs(v) < 1e15: return int(v)
    if isinstance(v, list): return [norm(x) for x in v]
    if isinstance(v, dict): return {k: norm(x) for k, x in v.items()}
    return v
def classify(a, b):
    if a["outcome"] != b["outcome"]: return "DIVERGE", f'py={a["outcome"]} js={b["outcome"]}'
    if a["outcome"] == "ok":
        return ("MATCH", "") if norm(a["value"]) == norm(b["value"]) else ("DIVERGE", "valores diferentes")
    if a["outcome"] == "error":
        return ("MATCH", "") if a["code"] == b["code"] else ("DIVERGE", f'py={a["code"]} js={b["code"]}')
    if a["outcome"] == "crash": return "BOTH_CRASH", f'py={a["detail"][:50]} | js={b["detail"][:50]}'
    return "BOTH_PARSE_ERROR", ""
ALLOWED_EL = {"svg", "title", "rect", "text", "line", "polyline", "circle"}
ALLOWED_AT = {"svg": {"xmlns", "viewBox", "width", "height", "role", "font-family", "font-size"}, "title": set(), "rect": {"width", "height", "fill", "x", "y"},
              "text": {"x", "y", "text-anchor", "fill", "font-size", "font-weight"}, "line": {"x1", "y1", "x2", "y2", "stroke"},
              "polyline": {"points", "fill", "stroke", "stroke-width"}, "circle": {"cx", "cy", "r", "fill"}}
def svg_check(s):
    try: root = ET.fromstring(s)
    except Exception as e: return "NOT_WELLFORMED_XML: " + str(e)[:60]
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag not in ALLOWED_EL: return "ELEMENTO_NAO_PERMITIDO: " + tag
        extra = set(el.attrib) - ALLOWED_AT[tag]
        if extra: return f"ATRIBUTO_NAO_PERMITIDO em {tag}: {sorted(extra)}"
        for k, v in el.attrib.items():
            if re.search(r"(?i)javascript:|https?:|data:", v): return "URL_EM_ATRIBUTO"
    return "OK"
class H(HTMLParser):
    def __init__(s): super().__init__(); s.tags = []; s.attrs = []
    def handle_starttag(s, t, a): s.tags.append(t); s.attrs.append((t, dict(a)))
def html_check(s):
    p = H(); p.feed(s)
    if p.tags[0] != "a" or p.tags.count("a") != 1: return "ESTRUTURA_A"
    if set(p.tags) - {"a", "strong", "span", "p"}: return "TAG_NAO_PERMITIDA: " + str(set(p.tags) - {"a", "strong", "span", "p"})
    a = p.attrs[0][1]
    if set(a) != {"class", "href", "rel", "target"}: return "ATRIBUTOS_A: " + str(sorted(a))
    if not re.match(r"(?i)^https?://", a["href"]): return "HREF_ESQUEMA"
    if a["rel"] != "noopener noreferrer nofollow" or a["target"] != "_blank": return "REL_TARGET"
    for t, at in p.attrs[1:]:
        if at: return "ATRIBUTO_EM_FILHO"
    return "OK"
rows = []; sec = []
for i in sorted(cases):
    c = cases[i]; st, why = classify(py[i], js[i])
    rows.append({"id": i, "group": c["group"], "fn": c["fn"], "note": c["note"], "args_text": c["args_text"][:200], "status": st, "why": why,
                 "py": {k: (v if k != "value" else (v if len(json.dumps(v)) < 400 else "<%d bytes>" % len(json.dumps(v)))) for k, v in py[i].items() if k != "id"},
                 "js": {k: (v if k != "value" else (v if len(json.dumps(v)) < 400 else "<%d bytes>" % len(json.dumps(v)))) for k, v in js[i].items() if k != "id"}})
    for lang, r in (("py", py[i]), ("js", js[i])):
        if r["outcome"] != "ok": continue
        if c["tool"] == "svgChart": sec.append({"id": i, "lang": lang, "kind": "svg", "result": svg_check(r["value"]), "note": c["note"]})
        if c["tool"] == "linkCard": sec.append({"id": i, "lang": lang, "kind": "link_html", "result": html_check(r["value"]["html"]), "note": c["note"], "url": r["value"]["url"]})
pre = sys.argv[4]
json.dump(rows, open(pre + "_paridade.json", "w", encoding="utf-8"), ensure_ascii=True, indent=1)
json.dump(sec, open(pre + "_seguranca_saida.json", "w", encoding="utf-8"), ensure_ascii=True, indent=1)
from collections import Counter
print("paridade por status:", dict(Counter(r["status"] for r in rows)))
print("paridade por ferramenta/status:", dict(Counter((r["group"], r["status"]) for r in rows)))
print("segurança de saída:", dict(Counter((s["kind"], s["lang"], s["result"].split(":")[0]) for s in sec)))
