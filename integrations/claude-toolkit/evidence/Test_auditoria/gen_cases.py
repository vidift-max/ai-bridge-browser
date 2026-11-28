#!/usr/bin/env python3
"""Gera cases.jsonl: entradas (texto JSON bruto) hostis/limite para as 5 ferramentas.
args_text é TEXTO JSON, lido por json.loads (Python) e JSON.parse (Node) — assim ambos recebem exatamente os mesmos bytes."""
import json, sys
J = json.dumps
cases = []
def add(group, tool, fn, args_text, note=""):
    cases.append({"id": len(cases) + 1, "group": group, "tool": tool, "fn": fn, "args_text": args_text, "note": note})

# ---------- duration_timer ----------
for v in ['""', '"   "', '"0"', '"-1"', '"1e3"', '"1e400"', '"1h30m"', '"1H"', '"1.5.5h"', '"99999999999999999999"',
          '"7d"', '"7d1s"', '"604800"', '"604801"', '"0:00"', '"1:60"', '"1:2:3:4"', '"1 h"', '"1h  30m"', '"1m1m"', '"m"',
          '"١٢"', '"１２"', '"١٢m"', '"1\\u00a0m"', '"\\u001f5\\u001f"', '"\\ufeff5"', '"5\\u2003"', '"İ"', '"1h30m\\n"',
          'null', 'true', '[]', '{}', '5', '-5', '0', '0.0001', '1e-9', '1e309', '604800', '604800.0005', '1e21',
          '"%s"' % ("9" * 5000), '"1" ', '"0.5s"', '"1,5h"', '"1h-1m"', '"+5m"', '"5M"', '"5ｍ"']:
    add("duration_timer", "durationTimer", "parseDuration", "[%s]" % v)
for a in ['[0]', '[-1]', '[1e9]', '[1e309]', '["5"]', '[null]', '[true]', '[59.9999]', '[3600,"x"]', '[3600,null]', '[604801,"words"]',
          '[86399.999,"words"]', '[0,"words"]', '[1e300,"clock"]', '[1e300,"words"]', '[3723.9,"clock"]', '[5e-324]', '[3600,"CLOCK"]',
          '[3600,"words",1]', '[]']:
    add("duration_timer", "durationTimer", "formatDuration", a)

# ---------- recipe_scaler ----------
for a in ['[1,"cup","ml"]', '[-1,"cup","ml"]', '[0,"cup","ml"]', '[1e308,"lb","g"]', '[1e309,"lb","g"]', '["1","cup","ml"]',
          '[null,"cup","ml"]', '[true,"cup","ml"]', '[1,"CUP","ML"]', '[1,"cup","cup"]', '[1,"fl oz","ml"]', '[1,"fl_oz","ml"]',
          '[1,"__proto__","ml"]', '[1,"constructor","ml"]', '[1,"toString","g"]', '[1,"hasOwnProperty","g"]', '[1,"cup","g"]',
          '[1,"g","cup"]', '[1,null,"g"]', '[1,5,"g"]', '[1,["g"],"g"]', '[1e-12,"g","kg"]', '[2.675,"cup","ml"]', '[0.0000005,"ml","ml"]',
          '[123456789012345678,"g","kg"]', '[1,"  Cups  ","ML"]', '[1,"ｇ","g"]', '[1,"G","g"]', '[1]', '[]']:
    add("recipe_scaler", "recipeScaler", "convert", a)
R = lambda **k: J(dict({"title": "R", "base_servings": 4, "ingredients": [{"name": "A", "amount": 1.5, "unit": "cup"}, {"name": "B", "amount": 2, "unit": None}]}, **k))
add("recipe_scaler", "recipeScaler", "scaleRecipe", "[%s,8]" % R())
for s in ['0', '-1', '1e308', '1e309', '"2"', 'null', 'true', '[]', '{}', '0.0001', '1e-320']:
    add("recipe_scaler", "recipeScaler", "scaleRecipe", "[%s,%s]" % (R(), s))
for b in ['0', '-1', '"4"', 'null', '1e309', '1e-320', 'true']:
    txt = R(base_servings=0).replace('"base_servings": 0', '"base_servings": ' + b)
    add("recipe_scaler", "recipeScaler", "scaleRecipe", "[%s,2]" % txt, "base_servings=" + b)
add("recipe_scaler", "recipeScaler", "scaleRecipe", '[{"base_servings":4,"ingredients":[]},2]')
add("recipe_scaler", "recipeScaler", "scaleRecipe", '[{"base_servings":4,"ingredients":"x"},2]')
add("recipe_scaler", "recipeScaler", "scaleRecipe", '[{"base_servings":4},2]')
add("recipe_scaler", "recipeScaler", "scaleRecipe", '[[],2]')
add("recipe_scaler", "recipeScaler", "scaleRecipe", '[null,2]')
add("recipe_scaler", "recipeScaler", "scaleRecipe", '["x",2]')
for ing in ['{"name":"","amount":1}', '{"name":"  ","amount":1}', '{"name":5,"amount":1}', '{"name":"A"}', '{"name":"A","amount":"1"}',
            '{"name":"A","amount":-1}', '{"name":"A","amount":1,"unit":"zzz"}', '{"name":"A","amount":1,"unit":"__proto__"}',
            '{"name":"A","amount":1,"unit":5}', '{"name":"A","amount":1,"unit":""}', '{"name":"A","amount":1e308,"unit":"g"}',
            '{"name":"A","amount":1,"unit":"g","extra":{"x":1},"__proto__":{"admin":true}}', '"just a string"', 'null', '[]',
            '{"name":"<script>x</script>","amount":1,"unit":"g"}']:
    add("recipe_scaler", "recipeScaler", "scaleRecipe", '[{"base_servings":4,"ingredients":[%s]},2]' % ing)
add("recipe_scaler", "recipeScaler", "scaleRecipe", '[{"base_servings":4,"title":"T","ingredients":[%s]},2]' % ",".join(['{"name":"i","amount":1,"unit":"g"}'] * 5000), "5000 ingredientes (sem limite documentado)")
for v in ['2.345', '12', '-0.001', '1e21', '1e-7', '0', '-0', '2.675', '1.005', '"x"', 'null', '1e309', '123456789012345680000']:
    add("recipe_scaler", "recipeScaler", "formatAmount", "[%s]" % v)

# ---------- quiz_engine ----------
def Q(**k):
    q = {"title": "T", "questions": [{"id": "q1", "prompt": "p", "options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}], "correct_option_id": "a"}]}
    q.update(k); return q
add("quiz_engine", "quizEngine", "validateQuiz", "[%s]" % J(Q()))
for bad in [None, [], "x", 5, {}, {"title": "", "questions": []}, Q(title=5), Q(questions=[]), Q(questions="x"), Q(questions=[None]), Q(questions=[[]]),
            Q(questions=[{"id": "q1", "prompt": "p", "options": [{"id": "a", "text": "x"}], "correct_option_id": "a"}]),
            Q(questions=[{"id": "q1", "prompt": "p", "options": [{"id": "a", "text": "x"}, {"id": "a", "text": "y"}], "correct_option_id": "a"}]),
            Q(questions=[{"id": "q1", "prompt": "p", "options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}], "correct_option_id": "z"}]),
            Q(questions=[{"id": "q1", "prompt": "p", "options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}], "correct_option_id": 5}]),
            Q(questions=[{"id": 1, "prompt": "p", "options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}], "correct_option_id": "a"}]),
            Q(questions=[{"id": "q1", "prompt": "p", "options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}], "correct_option_id": "a"}] * 2)]:
    add("quiz_engine", "quizEngine", "validateQuiz", "[%s]" % J(bad))
big = {"title": "T", "questions": [{"id": "q%d" % i, "prompt": "p", "options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}], "correct_option_id": "a"} for i in range(5000)]}
add("quiz_engine", "quizEngine", "validateQuiz", "[%s]" % J(big), "5000 perguntas (sem limite documentado)")
manyopt = Q(questions=[{"id": "q1", "prompt": "p", "options": [{"id": "o%d" % i, "text": "x"} for i in range(5000)], "correct_option_id": "o0"}])
add("quiz_engine", "quizEngine", "validateQuiz", "[%s]" % J(manyopt), "5000 opções")
add("quiz_engine", "quizEngine", "validateQuiz", "[%s]" % J(Q(title="A" * 200000)), "título de 200 KB")
for ans in ['{}', '{"q1":"a"}', '{"q1":"b"}', '{"q1":"zz"}', '{"q1":null}', '{"q1":5}', '{"q1":["a"]}', '{"q1":true}', '[]', 'null', '"a"', '5',
            '{"q1":"a","zz":"a","__proto__":"a"}', '{"__proto__":{"q1":"a"}}', '{"constructor":"a"}', '{"q1":"A"}', '{"q1":" a"}']:
    add("quiz_engine", "quizEngine", "grade", "[%s,%s]" % (J(Q()), ans))
add("quiz_engine", "quizEngine", "grade", '[%s,{"q1":"a"}]' % J(Q(questions=[{"id": "__proto__", "prompt": "p", "options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}], "correct_option_id": "a"}])), "id de pergunta __proto__")
add("quiz_engine", "quizEngine", "grade", '[%s,{"q1":"a"}]' % J(Q(questions=[{"id": "constructor", "prompt": "p", "options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}], "correct_option_id": "a"}])), "id de pergunta constructor")
add("quiz_engine", "quizEngine", "grade", '[%s,{}]' % J(Q(questions=[{"id": "toString", "prompt": "p", "options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}], "correct_option_id": "a", "explanation": "<img src=x onerror=alert(1)>"}])), "id toString e explicação com HTML (retorno bruto, não escapado)")
add("quiz_engine", "quizEngine", "grade", '[%s,{}]' % J(Q(questions=[{"id": "q%d" % i, "prompt": "p", "options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}], "correct_option_id": "a"} for i in range(3)])), "3 perguntas, 0 acertos")
add("quiz_engine", "quizEngine", "grade", '[%s,{"q0":"a"}]' % J(Q(questions=[{"id": "q%d" % i, "prompt": "p", "options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}], "correct_option_id": "a"} for i in range(3)])), "arredondamento 33.3")
add("quiz_engine", "quizEngine", "grade", '[%s,{"q0":"a","q1":"a"}]' % J(Q(questions=[{"id": "q%d" % i, "prompt": "p", "options": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}], "correct_option_id": "a"} for i in range(3)])), "arredondamento 66.7")

# ---------- svg_chart ----------
def S(**k):
    s = {"type": "bar", "labels": ["a", "b"], "series": [{"name": "S", "values": [1, 2]}]}
    s.update(k); return s
add("svg_chart", "svgChart", "renderChart", "[%s]" % J(S()), "baseline")
add("svg_chart", "svgChart", "renderChart", "[%s]" % J(S(type="line")), "baseline linha")
HOSTILE = ["<script>alert(1)</script>", '"/><script>alert(1)</script>', "</text><script>x</script><text>", "]]>", "<!ENTITY x SYSTEM 'file:///etc/passwd'>",
           "&xxe;", "<?xml version='1.0'?>", "javascript:alert(1)", "<svg onload=alert(1)>", "<foreignObject><iframe src=//evil></iframe></foreignObject>",
           '<a xlink:href="javascript:alert(1)">x</a>', '<image href="http://evil/x.png"/>', "<style>*{background:url(http://evil)}</style>", "' onmouseover='alert(1)",
           "\x00\x01\x02\x1f", "a\u2028b\u2029c", "a\x85b", "a\ufeffb", "a\ufffe\uffffb", "a\ud800b", "\u202eRTL", "😀" * 30, "A" * 10000, "\x7f\x80\x9f", "&#x3C;script&#x3E;", "%3Cscript%3E", "${7*7}{{7*7}}", "\\u003cscript\\u003e"]
for h in HOSTILE:
    add("svg_chart", "svgChart", "renderChart", "[%s]" % J(S(title=h, labels=[h, "b"], series=[{"name": h, "values": [1, 2]}, {"name": "o", "values": [3, 4]}])), "hostil: " + h[:30].encode("unicode_escape").decode())
for h in HOSTILE[:6]:
    add("svg_chart", "svgChart", "renderChart", "[%s]" % J(S(type="line", title=h, labels=[h, "b"], series=[{"name": h, "values": [1, 2]}])), "hostil linha")
# tipos errados / limites
for sp in ['null', '[]', '"x"', '5', 'true', '{}', '{"type":"pie"}', '{"type":"BAR"}', '{"type":"bar "}', '{"type":["bar"]}']:
    add("svg_chart", "svgChart", "renderChart", "[%s]" % sp)
for lab in ['"x"', '[]', 'null', '[null]', '[true]', '[[1]]', '[{"a":1}]', '[1,"a"]', '[3.14159,2]', '[1e21,2]', '[1e-7,2]', '[123456789012,2]', '[-5,2]', '[0.30000000000000004,2]',
            '[1.005,2.675]', '[5e-324,2]', '[1e309,2]', '[0.1,2]', '[100.0,2]', '[1e5,2]', '[1.5e300,2]']:
    add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","labels":%s,"series":[{"values":[1,2]}]}]' % lab, "labels=" + lab)
add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","labels":%s,"series":[{"values":%s}]}]' % (J(list("x" * 50)), J([1] * 50)), "50 labels (limite)")
add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","labels":%s,"series":[{"values":%s}]}]' % (J(list("x" * 51)), J([1] * 51)), "51 labels")
add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","labels":["a"],"series":%s}]' % J([{"values": [1]}] * 6), "6 series (limite)")
add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","labels":["a"],"series":%s}]' % J([{"values": [1]}] * 7), "7 series")
for ser in ['[]', '"x"', 'null', '[null]', '["x"]', '[{}]', '[{"values":"x"}]', '[{"values":[]}]', '[{"values":[1,2,3]}]']:
    add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","labels":["a","b"],"series":%s}]' % ser, "series=" + ser)
for v in ['"1"', 'null', 'true', '[]', '{}', '-1', '-0.0', '0', '1e308', '1.7976931348623157e308', '1e309', '-1e309', '5e-324', '1e-320', '1e21',
          '1' + '0' * 400, '123456789012345678901234567890', '0.1', '1e15', '2.5e-7']:
    add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","labels":["a","b"],"series":[{"values":[%s,1]}]}]' % v, "valor=" + v[:40])
    add("svg_chart", "svgChart", "renderChart", '[{"type":"line","labels":["a","b"],"series":[{"values":[%s,1]}]}]' % v, "linha valor=" + v[:40])
add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","labels":["a","b"],"series":[{"values":[0,0]}]}]', "tudo zero")
for wh in ['"640"', '640.0', '640.5', '199', '200', '2000', '2001', 'true', 'null', '-1', '1e3', '"__proto__"', '[]', '{}', '1e309', '2000.0', '200.0']:
    add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","labels":["a"],"series":[{"values":[1]}],"width":%s}]' % wh, "width=" + wh)
    add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","labels":["a"],"series":[{"values":[1]}],"height":%s}]' % wh, "height=" + wh)
add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","labels":["a"],"series":[{"values":[1],"color":"red;}</style><script>","href":"javascript:1","onclick":"x"}],"href":"javascript:1","style":"x","onload":"x","__proto__":{"type":"line"}}]', "campos extras/desconhecidos")
add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","title":5,"labels":["a"],"series":[{"name":5,"values":[1]},{"name":null,"values":[1]},{"name":"  ","values":[1]}]}]', "title/name não-string")
add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","title":"%s","labels":["a"],"series":[{"values":[1]}]}]' % ("a" * 119 + "😀" + "bcd"), "truncamento: 119 'a' + emoji + bcd")
add("svg_chart", "svgChart", "renderChart", '[{"type":"bar","title":"%s","labels":["%s"],"series":[{"name":"%s","values":[1]},{"values":[2]}]}]' % ("t" * 119 + "😀😀", "l" * 19 + "😀😀", "n" * 13 + "😀😀"), "truncamento emoji em title/label/name")

# ---------- link_card ----------
U = lambda u, **k: "[%s]" % J(dict({"url": u}, **k))
urls = ["https://example.com", "https://Example.COM:443/a", "http://example.com:80", "http://example.com:8080/x", "http://[::1]:8080/x", "http://[::1]/", "http://[::1]:80/",
        "https://[::1]:443", "http://[0:0:0:0:0:0:0:1]/", "http://[::FFFF:1.2.3.4]/", "http://[2001:DB8::1]:9/p?q=1#f", "http://[fe80::1%25eth0]/", "http://[::1", "http://::1/", "http://[::1]x/",
        "http://[::g]/", "http://[]/", "http://127.0.0.1:3000/", "http://127.1/", "http://0x7f.1/", "http://2130706433/", "http://0177.0.0.1/", "http://192.168.0.1/", "http://169.254.169.254/latest/meta-data/",
        "http://256.256.256.256/", "http://1.2.3/", "http://1.2.3.4.5/", "http://localhost/", "http://LOCALHOST:8080", "http://example.com./", "http://-bad-.com/", "http://a_b.com/", "http://exa%6Dple.com/",
        "http://bücher.de/", "http://xn--bcher-kva.de/", "http://例え.jp/", "http://EXAMPLE.com/Ä", "http://example.com/é?é#é", "http://example.com/a/../b", "http://example.com/./a//b", "http://example.com/%2e%2e/x", "http://example.com/a%2Fb",
        "http://example.com?q=1", "http://example.com#f", "http://example.com/?", "http://example.com/#", "http://example.com/path?", "http://example.com/p?a=\"<>'", "http://example.com/\"<>`{}|^",
        "http://example.com:", "http://example.com:/", "http://example.com:0/", "http://example.com:65535/", "http://example.com:65536/", "http://example.com:99999999999/", "http://example.com:-1/", "http://example.com:abc/", "http://example.com:080/", "http://example.com:+80/",
        "HTTP://EXAMPLE.COM", "hTtPs://example.com", "http:/example.com", "http:example.com", "http:///x", "http://", "http://:80", "http://?x", "http://#x", "http://.", "http://..", "http://a b.com", "http://a.com/ b",
        "http://u:p@x.com", "http://u@x.com", "http://:p@x.com", "http://@x.com", "http://x.com@evil.com", "http://evil.com\\@good.com", "http://evil.com\\x", "http://evil.com\\", "http:\\\\evil.com", "http://evil.com/\\x",
        "javascript:alert(1)", "JaVaScRiPt:alert(1)", "data:text/html,<script>x</script>", "file:///etc/passwd", "ftp://x.com", "mailto:a@b.c", "vbscript:x", "blob:http://x/y", "about:blank", "//example.com", "example.com", "/path", "", "   ", "  https://example.com  ",
        "https://example.com/\u00a0x", "https://example.com/\u3000x", "https://exam\u00a0ple.com", "https://exam\u200bple.com", "https://example.com/\u202e", "https://ＥＸＡＭＰＬＥ.com", "https://example.com\u3002", "https://example.com\uff0e",
        "https://example.com/" + "a" * 2020, "https://example.com/" + "a" * 2028, "https://example.com/" + "a" * 2029, "http://" + "a" * 2040 + ".com", "https://" + ".".join(["a" * 63] * 4), "https://" + "a" * 300 + ".com",
        "https://example.com/%", "https://example.com/%zz", "https://example.com/%00", "https://example.com/\x00", "https://example.com/\ud800",
        "https://example.com/<script>alert(1)</script>", "https://example.com/\"><script>alert(1)</script>", "https://example.com/?a=1&b=2&amp;c=3", "https://example.com/'onmouseover='alert(1)",
        "https://example.com:443@evil.com/", "https://evil.com:443:80/", "http://1e3.com/", "http://[::1]:8080:90/", "http://[::1]:/", "http://[v1.fe]/"]
for u in urls:
    add("link_card", "linkCard", "buildLinkCard", U(u), "url=" + u[:60].encode("unicode_escape", "backslashreplace").decode())
for k, v in [("url", "null"), ("url", "5"), ("url", "[]"), ("url", '{}'), ("url", "true")]:
    add("link_card", "linkCard", "buildLinkCard", '[{"%s":%s}]' % (k, v), "tipo errado url=" + v)
for a in ['null', '[]', '"https://example.com"', '5', '{}', '{"u":"https://example.com"}', '[{"url":"https://example.com"}]', '[]']:
    add("link_card", "linkCard", "buildLinkCard", a if a.startswith("[") and a != "[]" else "[%s]" % a, "entrada=" + a[:40])
for t in ['null', '5', '[]', '{}', '""', '"  "', '"x"', '"<script>alert(1)</script>"', '"\\u0000a\\u001fb"', '"%s"' % ("t" * 121), '"%s"' % ("😀" * 70), '"%s"' % ("t" * 119 + "😀😀"), '"a\\u0085b"', '"a\\ufeffb"', '"\\u2028"']:
    add("link_card", "linkCard", "buildLinkCard", '[{"url":"https://example.com","title":%s,"description":%s}]' % (t, t), "title/description=" + t[:40])
add("link_card", "linkCard", "buildLinkCard", '[{"url":"https://example.com","title":"x","description":"%s"}]' % ("d" * 301), "descrição 301")
add("link_card", "linkCard", "buildLinkCard", '[{"url":"https://example.com","title":"x","description":"%s"}]' % ("d" * 299 + "😀😀"), "descrição emoji no corte")
add("link_card", "linkCard", "buildLinkCard", '[{"url":"https://example.com","title":"x","rel":"opener","target":"_self","class":"x\\" onclick=\\"y","html":"<b>x</b>","href":"javascript:1","__proto__":{"url":"javascript:1"}}]', "campos extras")
with open("cases.jsonl", "w", encoding="utf-8") as fh:
    for c in cases:
        fh.write(json.dumps(c, ensure_ascii=True) + "\n")
print("casos gerados:", len(cases))
