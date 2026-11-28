import sys, time
from ai_tool_hub import duration_timer as d
for n in (2000, 4000, 8000, 16000, 32000):
    s = "1" * n + "x"
    t = time.time()
    try: d.parse_duration(s)
    except Exception as e: r = type(e).__name__ + ":" + getattr(e, "code", "")
    print("python parse_duration('1'*%d+'x') %.3fs -> %s" % (n, time.time() - t, r), flush=True)
