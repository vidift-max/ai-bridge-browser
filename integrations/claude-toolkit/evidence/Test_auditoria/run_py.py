#!/usr/bin/env python3
"""Executa cases.jsonl contra a implementação Python. Uso: run_py.py <dir_python_pkg> <saida.json>"""
import json, sys, traceback
sys.path.insert(0, sys.argv[1])
from ai_tool_hub import duration_timer, link_card, quiz_engine, recipe_scaler, svg_chart, ToolError
PY = {"durationTimer": duration_timer, "recipeScaler": recipe_scaler, "quizEngine": quiz_engine, "svgChart": svg_chart, "linkCard": link_card}
SN = {"parseDuration": "parse_duration", "formatDuration": "format_duration", "scaleRecipe": "scale_recipe", "formatAmount": "format_amount",
      "validateQuiz": "validate_quiz", "renderChart": "render_chart", "buildLinkCard": "build_link_card", "convert": "convert", "grade": "grade"}
res = []
for line in open("cases.jsonl", encoding="utf-8"):
    c = json.loads(line)
    try:
        args = json.loads(c["args_text"])
    except Exception as e:
        res.append({"id": c["id"], "outcome": "parse_error", "detail": type(e).__name__}); continue
    try:
        v = getattr(PY[c["tool"]], SN[c["fn"]])(*args)
        json.dumps(v, allow_nan=False)
        res.append({"id": c["id"], "outcome": "ok", "value": v})
    except ToolError as e:
        res.append({"id": c["id"], "outcome": "error", "code": e.code})
    except Exception as e:
        res.append({"id": c["id"], "outcome": "crash", "detail": type(e).__name__ + ": " + str(e)[:120]})
json.dump(res, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=True)
print("python:", len(res), "casos;", sum(r["outcome"] == "crash" for r in res), "crashes (exceção não-ToolError)")
