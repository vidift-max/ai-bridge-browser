"""Clean-room, local-only implementations for the five AI Tool Hub capabilities.

These implementations are independently authored for AI Bridge Browser.
They do not import or execute the archived AI Tool Hub package.
No network, filesystem, shell, browser DOM, or external process access.
"""
import ipaddress
import math
import re
from urllib.parse import urlsplit, urlunsplit

TOOL_IDS = ("duration_timer", "recipe_scaler", "quiz_engine", "svg_chart", "link_card")
MAX_INPUT_BYTES = 10_000
MAX_OUTPUT_BYTES = 32_000


class ToolInputError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _object(value, allowed, required):
    if not isinstance(value, dict) or set(value) - set(allowed) or not set(required).issubset(value):
        raise ToolInputError("INVALID_REQUEST")
    return value


def _text(value, maximum, code="INVALID_REQUEST", allow_empty=False):
    if not isinstance(value, str) or len(value) > maximum or (not allow_empty and not value.strip()):
        raise ToolInputError(code)
    if any(ord(ch) < 32 and ch not in "\t\n\r" for ch in value):
        raise ToolInputError(code)
    return value


def _number(value, minimum=None, maximum=None, code="INVALID_REQUEST"):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ToolInputError(code)
    number = float(value)
    if not math.isfinite(number) or (minimum is not None and number < minimum) or (maximum is not None and number > maximum):
        raise ToolInputError(code)
    return number


def duration_timer(payload):
    data = _object(payload, {"duration", "operation"}, {"duration"})
    duration = data["duration"]
    operation = data.get("operation", "format")
    if operation not in ("format", "seconds"):
        raise ToolInputError("INVALID_REQUEST")
    if isinstance(duration, (int, float)) and not isinstance(duration, bool):
        seconds = _number(duration, 0, 604800, "OUT_OF_RANGE")
    elif isinstance(duration, str):
        value = _text(duration, 64, "INVALID_FORMAT")
        # Linear parser: sequence of number+unit tokens, no backtracking regex.
        token = re.compile(r"([0-9]{1,9}(?:\.[0-9]{1,3})?)([dhms])")
        pos, seconds = 0, 0.0
        while pos < len(value):
            while pos < len(value) and value[pos] in " \t":
                pos += 1
            match = token.match(value, pos)
            if not match:
                raise ToolInputError("INVALID_FORMAT")
            amount = float(match.group(1))
            unit = match.group(2)
            seconds += amount * {"d": 86400, "h": 3600, "m": 60, "s": 1}[unit]
            if not math.isfinite(seconds) or seconds > 604800:
                raise ToolInputError("OUT_OF_RANGE")
            pos = match.end()
        if seconds <= 0:
            raise ToolInputError("OUT_OF_RANGE")
    else:
        raise ToolInputError("INVALID_FORMAT")
    total = int(seconds)
    if operation == "seconds":
        return {"seconds": total}
    days, remainder = divmod(total, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if secs or not parts: parts.append(f"{secs}s")
    return {"seconds": total, "formatted": " ".join(parts)}


_UNIT_GROUPS = {
    "g": "mass", "kg": "mass", "mg": "mass",
    "ml": "volume", "l": "volume",
    "tsp": "volume", "tbsp": "volume", "cup": "volume",
    "piece": "count", "pieces": "count",
}


def recipe_scaler(payload):
    data = _object(payload, {"ingredients", "originalServings", "targetServings"}, 
                   {"ingredients", "originalServings", "targetServings"})
    original = _number(data["originalServings"], 0.000001, 10000)
    target = _number(data["targetServings"], 0.000001, 10000)
    ingredients = data["ingredients"]
    if not isinstance(ingredients, list) or not 1 <= len(ingredients) <= 100:
        raise ToolInputError("INVALID_RECIPE")
    factor = target / original
    result = []
    for item in ingredients:
        item = _object(item, {"name", "amount", "unit"}, {"name", "amount", "unit"})
        name = _text(item["name"], 100)
        unit = item["unit"]
        if not isinstance(unit, str) or unit not in _UNIT_GROUPS:
            raise ToolInputError("UNKNOWN_UNIT")
        amount = _number(item["amount"], 0, 1_000_000)
        scaled = amount * factor
        if not math.isfinite(scaled) or scaled > 1_000_000_000:
            raise ToolInputError("OUT_OF_RANGE")
        result.append({"name": name, "amount": round(scaled, 6), "unit": unit})
    return {"originalServings": original, "targetServings": target, "ingredients": result}


def quiz_engine(payload):
    data = _object(payload, {"questions", "answers"}, {"questions"})
    questions = data["questions"]
    if not isinstance(questions, list) or not 1 <= len(questions) <= 100:
        raise ToolInputError("INVALID_QUIZ")
    normalized, ids = [], set()
    for question in questions:
        question = _object(question, {"id", "prompt", "options", "correctOptionId", "explanation"},
                           {"id", "prompt", "options", "correctOptionId"})
        qid = _text(question["id"], 80)
        if qid in ids: raise ToolInputError("INVALID_QUIZ")
        ids.add(qid)
        prompt = _text(question["prompt"], 1000)
        options = question["options"]
        if not isinstance(options, list) or not 2 <= len(options) <= 10:
            raise ToolInputError("INVALID_QUIZ")
        option_ids, clean_options = set(), []
        for option in options:
            option = _object(option, {"id", "text"}, {"id", "text"})
            oid = _text(option["id"], 80)
            if oid in option_ids: raise ToolInputError("INVALID_QUIZ")
            option_ids.add(oid)
            clean_options.append({"id": oid, "text": _text(option["text"], 500)})
        correct = _text(question["correctOptionId"], 80)
        if correct not in option_ids: raise ToolInputError("INVALID_QUIZ")
        normalized.append({"id": qid, "prompt": prompt, "options": clean_options,
                           "correctOptionId": correct,
                           "explanation": _text(question.get("explanation", ""), 1000, allow_empty=True)})
    if "answers" not in data:
        return {"questionCount": len(normalized),
                "questions": [{k: v for k, v in q.items() if k != "correctOptionId"} for q in normalized]}
    answers = data["answers"]
    if not isinstance(answers, dict) or set(answers) - ids:
        raise ToolInputError("INVALID_ANSWERS")
    correct_count, details = 0, []
    for question in normalized:
        answer = answers.get(question["id"])
        valid_ids = {option["id"] for option in question["options"]}
        if answer is not None and (not isinstance(answer, str) or answer not in valid_ids):
            raise ToolInputError("INVALID_ANSWERS")
        correct = answer == question["correctOptionId"]
        correct_count += int(correct)
        details.append({"questionId": question["id"], "correct": correct,
                        "explanation": question["explanation"]})
    return {"total": len(normalized), "correct": correct_count,
            "scorePercent": round(correct_count * 100 / len(normalized), 2), "results": details}


def svg_chart(payload):
    from xml.sax.saxutils import escape
    data = _object(payload, {"title", "labels", "series", "width", "height", "type"},
                   {"labels", "series"})
    labels, series = data["labels"], data["series"]
    if not isinstance(labels, list) or not 1 <= len(labels) <= 50:
        raise ToolInputError("INVALID_SPEC")
    labels = [_text(label, 80) for label in labels]
    if not isinstance(series, list) or not 1 <= len(series) <= 6:
        raise ToolInputError("INVALID_SPEC")
    width = data.get("width", 640)
    height = data.get("height", 360)
    if type(width) is not int or type(height) is not int or not 200 <= width <= 2000 or not 150 <= height <= 2000:
        raise ToolInputError("INVALID_SIZE")
    chart_type = data.get("type", "bar")
    if chart_type not in ("bar", "line"):
        raise ToolInputError("INVALID_SPEC")
    title = _text(data.get("title", "Chart"), 120)
    clean_series = []
    for index, item in enumerate(series):
        item = _object(item, {"name", "values"}, {"name", "values"})
        name = _text(item["name"], 40)
        values = item["values"]
        if not isinstance(values, list) or len(values) != len(labels):
            raise ToolInputError("LENGTH_MISMATCH")
        clean_series.append((name, [_number(v, 0, 1_000_000) for v in values]))
    maximum = max(max(values) for _, values in clean_series)
    maximum = maximum if maximum > 0 else 1
    colors = ("#3366cc", "#dc3912", "#109618", "#990099", "#ff9900", "#0099c6")
    plot_left, plot_top = 48, 48
    plot_width, plot_height = width - 64, height - 100
    chunks = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">',
              f'<title>{escape(title)}</title>',
              f'<text x="{width/2:.1f}" y="24" text-anchor="middle">{escape(title)}</text>',
              f'<line x1="{plot_left}" y1="{plot_top+plot_height}" x2="{plot_left+plot_width}" y2="{plot_top+plot_height}" stroke="#333"/>']
    group_width = plot_width / len(labels)
    if chart_type == "bar":
        bar_width = group_width / (len(clean_series) + 1)
        for s_index, (name, values) in enumerate(clean_series):
            for i, value in enumerate(values):
                bar_height = value / maximum * (plot_height - 8)
                x = plot_left + i * group_width + (s_index + 0.5) * bar_width
                y = plot_top + plot_height - bar_height
                chunks.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width*0.8:.2f}" height="{bar_height:.2f}" fill="{colors[s_index]}"/>')
    else:
        for s_index, (name, values) in enumerate(clean_series):
            points = []
            for i, value in enumerate(values):
                x = plot_left + (i + 0.5) * group_width
                y = plot_top + plot_height - value / maximum * (plot_height - 8)
                points.append(f"{x:.2f},{y:.2f}")
            chunks.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{colors[s_index]}" stroke-width="2"/>')
    for i, label in enumerate(labels):
        x = plot_left + (i + 0.5) * group_width
        chunks.append(f'<text x="{x:.2f}" y="{plot_top+plot_height+22}" text-anchor="middle">{escape(label)}</text>')
    chunks.append("</svg>")
    svg = "".join(chunks)
    if len(svg.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise ToolInputError("OUTPUT_TOO_LARGE")
    return {"mimeType": "image/svg+xml", "svg": svg}


def link_card(payload):
    data = _object(payload, {"url", "title", "description"}, {"url"})
    raw = _text(data["url"], 2048, "INVALID_URL")
    if any(ord(ch) <= 32 or ord(ch) == 127 for ch in raw) or "\\" in raw:
        raise ToolInputError("INVALID_URL")
    try:
        parts = urlsplit(raw)
        if parts.scheme.lower() not in ("http", "https") or not parts.hostname or parts.username is not None or parts.password is not None:
            raise ToolInputError("INVALID_URL")
        host = parts.hostname.encode("idna").decode("ascii").lower().rstrip(".")
        if not host or len(host) > 253:
            raise ToolInputError("INVALID_URL")
        try:
            address = ipaddress.ip_address(host)
            if not address.is_global:
                raise ToolInputError("INVALID_URL")
            canonical_host = address.compressed
        except ValueError:
            labels = host.split(".")
            if host == "localhost" or host.endswith(".localhost") or len(labels) < 2:
                raise ToolInputError("INVALID_URL")
            # Reject legacy WHATWG IPv4 spellings (127.1, 0x7f.1, integer hosts).
            if all(re.fullmatch(r"(?:[0-9]+|0x[0-9a-f]+)", label) for label in labels):
                raise ToolInputError("INVALID_URL")
            if any(not label or len(label) > 63 or label.startswith("-") or label.endswith("-")
                   or not re.fullmatch(r"[a-z0-9-]+", label) for label in labels):
                raise ToolInputError("INVALID_URL")
            canonical_host = host
        port = parts.port
        if port is not None and not 1 <= port <= 65535:
            raise ToolInputError("INVALID_URL")
        netloc = f"[{canonical_host}]" if ":" in canonical_host else canonical_host
        if port is not None and not ((parts.scheme.lower() == "http" and port == 80) or
                                     (parts.scheme.lower() == "https" and port == 443)):
            netloc += f":{port}"
        path = parts.path or "/"
        canonical = urlunsplit((parts.scheme.lower(), netloc, path, parts.query, parts.fragment))
    except (UnicodeError, ValueError):
        raise ToolInputError("INVALID_URL")
    return {"url": canonical,
            "title": _text(data.get("title", canonical_host), 120),
            "description": _text(data.get("description", ""), 300, allow_empty=True),
            "target": "_blank", "rel": "noopener noreferrer nofollow"}


ADAPTERS = {
    "duration_timer": duration_timer,
    "recipe_scaler": recipe_scaler,
    "quiz_engine": quiz_engine,
    "svg_chart": svg_chart,
    "link_card": link_card,
}


def execute_tool(tool_id, payload):
    if tool_id not in ADAPTERS:
        raise ToolInputError("TOOL_NOT_FOUND")
    return ADAPTERS[tool_id](payload)
