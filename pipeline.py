"""
Alt-ops extraction pipeline.

Four agents, run per document, fanned out concurrently:

  1. CLASSIFIER  - what kind of document is this?
  2. EXTRACTOR   - pull the type-specific schema, with a verbatim source quote
                   for every field (so a human can audit without opening the PDF)
  3. VALIDATOR   - check arithmetic identities and date ordering. This is the
                   part that makes the output trustworthy: an LLM that is
                   confidently wrong gets caught by the fund's own math.
  4. TRIAGE      - anything that fails validation, or is low-confidence on a
                   money-moving field, is routed to a human exception queue
                   with a specific reason. Everything else posts automatically.

The measure that matters to an ops buyer is not extraction accuracy. It is
straight-through rate: what fraction of documents cleared with zero human
touches, and did anything wrong slip through.
"""

import concurrent.futures as cf
import json
import os
import re
from datetime import date, datetime

from pypdf import PdfReader

from schemas import CRITICAL_FIELDS, SCHEMAS


def _load_dotenv(path=None):
    """Minimal .env loader. Real env vars always win over the file."""
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_load_dotenv()

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# providers that speak the OpenAI chat-completions wire format, keyed by
# provider name -> (base_url, api_key env var, default model)
OPENAI_COMPAT = {
    "openrouter": ("https://openrouter.ai/api/v1",
                   "OPENROUTER_API_KEY",
                   # free tier — rate-limits daily; no paid model assumed
                   "nvidia/nemotron-nano-9b-v2:free"),
    "nvidia": ("https://integrate.api.nvidia.com/v1",
               "NVIDIA_API_KEY",
               # nemotron-70b returns 404 on many NIM accounts; llama-3.1-70b is broadly enabled
               "meta/llama-3.1-70b-instruct"),
}
DEFAULT_MODELS = {
    "anthropic": "claude-haiku-4-5-20251001",
    "ollama": "llama3.1:8b",
    "openrouter": OPENAI_COMPAT["openrouter"][2],
    "nvidia": OPENAI_COMPAT["nvidia"][2],
}
CONFIDENCE_BAR = 0.80
LP_NAME = os.environ.get("ALTOPS_LP", "Ridgeline Family Office LP")


# ---------------------------------------------------------------- LLM client

def _ollama_available():
    try:
        import urllib.request
        urllib.request.urlopen(f"{OLLAMA_HOST}/api/version", timeout=1)
        return True
    except Exception:
        return False


def _provider():
    p = os.environ.get("ALTOPS_PROVIDER")
    if p:
        return p
    # Prefer NVIDIA (reliable NIM), then OpenRouter, then Anthropic.
    if os.environ.get("NVIDIA_API_KEY"):
        return "nvidia"
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if _ollama_available():
        return "ollama"
    return None


def _model_for(provider, honor_env_model=True):
    if honor_env_model and os.environ.get("ALTOPS_MODEL"):
        return os.environ["ALTOPS_MODEL"]
    if provider == "ollama":
        return _ollama_preferred_model() or DEFAULT_MODELS["ollama"]
    return DEFAULT_MODELS.get(provider, "claude-haiku-4-5-20251001")


def available_providers():
    """Providers with credentials configured, for the demo UI."""
    out = []
    if os.environ.get("NVIDIA_API_KEY"):
        out.append({"id": "nvidia", "label": "NVIDIA",
                    "model": DEFAULT_MODELS["nvidia"]})
    if os.environ.get("OPENROUTER_API_KEY"):
        out.append({"id": "openrouter", "label": "OpenRouter",
                    "model": DEFAULT_MODELS["openrouter"]})
    if os.environ.get("ANTHROPIC_API_KEY"):
        out.append({"id": "anthropic", "label": "Anthropic",
                    "model": DEFAULT_MODELS["anthropic"]})
    if _ollama_available():
        # Prefer a locally installed chat model when we can discover one.
        model = _ollama_preferred_model() or DEFAULT_MODELS["ollama"]
        out.append({"id": "ollama", "label": "Ollama (local)", "model": model})
    out.append({"id": "deterministic", "label": "Deterministic only",
                "model": None})
    return out


def _ollama_preferred_model():
    """Pick the best installed Ollama chat model for a 32GB machine."""
    preferred = [
        "llama3.1:8b",
        "llama3.1:8b-instruct-q4_K_M",
        "qwen2.5:14b",
        "qwen3-coder:30b",
        "qwen2.5:32b",
        "llama3.1:70b",
        "llama3.3:70b",
        "llama3.2:latest",
        "llama3.2",
    ]
    try:
        import urllib.request
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=2) as resp:
            names = {m.get("name") for m in json.loads(resp.read()).get("models", [])}
    except Exception:
        return None
    env = os.environ.get("ALTOPS_MODEL") or os.environ.get("OLLAMA_MODEL")
    if env and env in names:
        return env
    for name in preferred:
        if name in names:
            return name
    # Fall back to any non-embed model.
    for name in sorted(names):
        if "embed" not in name.lower():
            return name
    return None


# Resolved at import for CLI convenience; runtime paths re-call _provider().
PROVIDER = _provider()
MODEL = _model_for(PROVIDER)


def _client(provider=None):
    provider = provider or _provider()
    if provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            return None
        try:
            import anthropic
            return anthropic.Anthropic(api_key=key)
        except Exception:
            return None
    if provider == "ollama":
        return "ollama"
    if provider in OPENAI_COMPAT:
        _, key_var, _ = OPENAI_COMPAT[provider]
        return provider if os.environ.get(key_var) else None
    return None


def _ollama_ask(system, user, model=None):
    import urllib.request
    model = model or _model_for("ollama")
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/chat", data=payload,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
    return data["message"]["content"]


def _openai_compat_ask(provider, system, user, max_tokens, model=None):
    import urllib.request, urllib.error, time
    base_url, key_var, _ = OPENAI_COMPAT[provider]
    model = model or _model_for(provider)
    payload = json.dumps({
        "model": model,
        # reasoning models (nemotron, etc.) spend budget on a separate
        # "reasoning" pass before writing content -- give them headroom
        # or content comes back empty/truncated.
        "max_tokens": max(max_tokens, 4000),
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }).encode()
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {os.environ[key_var]}"}
    if provider == "openrouter":
        headers["HTTP-Referer"] = "http://localhost:8000"
        headers["X-Title"] = "Altline"

    # Retry transient 429s briefly. Daily free-tier caps (OpenRouter
    # free-models-per-day) will not clear on backoff -- fail fast so the UI
    # does not hang for ~45s looking stuck.
    body = b""
    for attempt in range(3):
        req = urllib.request.Request(
            f"{base_url}/chat/completions", data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read())
            msg = data["choices"][0]["message"]
            return msg.get("content") or msg.get("reasoning") or ""
        except urllib.error.HTTPError as e:
            body = e.read() if hasattr(e, "read") else b""
            detail = body.decode("utf-8", errors="replace")[:240]
            permanent = e.code == 429 and any(
                s in detail.lower()
                for s in ("free-models-per-day", "daily", "add 10 credits",
                          "quota", "insufficient"))
            if e.code == 429 and not permanent and attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            # Re-raise with the body so callers see the real reason.
            raise urllib.error.HTTPError(
                e.url, e.code, f"{e.reason}: {detail}", e.headers, None) from None


def _ask(client, system, user, max_tokens=2000, model=None):
    """Single LLM turn that must return JSON."""
    if client == "ollama":
        text = _ollama_ask(system, user, model=model)
    elif client in OPENAI_COMPAT:
        text = _openai_compat_ask(client, system, user, max_tokens,
                                  model=model or _model_for(client, honor_env_model=False))
    else:
        r = client.messages.create(
            model=model or _model_for("anthropic"),
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in r.content if b.type == "text")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"no JSON in response: {text[:200]}")
    return json.loads(m.group(0))


# ------------------------------------------------------------------- agent 1

CLASSIFY_SYS = """You classify documents sent by private fund general partners \
to their limited partners. Different GPs use wildly different titles for the \
same document type.

Document types:
- capital_call: the GP is requiring the LP to send money. Titles vary: Capital \
Call Notice, Drawdown Notice, Drawdown Request, Funding Notice, Notice of \
Capital Contribution.
- distribution: the GP is sending money to the LP. Titles vary: Distribution \
Notice, Distribution Advice, Notice of Distribution.
- capital_account_statement: a periodic roll-forward of the LP's capital \
account (beginning balance, activity, ending balance). Often quarterly.
- other: anything else (K-1s, side letters, LPAs, subscription docs, marketing).

Respond with JSON only: {"doc_type": "...", "confidence": 0.0-1.0, \
"reason": "one short sentence"}"""


def classify(client, text):
    if client is None:
        import offline
        return offline.classify(text)
    return _ask(client, CLASSIFY_SYS, f"<document>\n{text[:6000]}\n</document>", 300)


# ------------------------------------------------------------------- agent 2

EXTRACT_SYS = """You extract structured data from private fund documents for a \
family office back office. Accuracy matters more than completeness: a wrong \
number moves real money.

Rules:
1. Numbers: strip all currency symbols, commas and parentheses. Amounts shown \
in parentheses are NEGATIVE. Return plain numbers.
2. Dates: normalize to ISO YYYY-MM-DD. Be extremely careful with ambiguous \
formats. A European manager (S.a r.l., SCSp, GmbH, or amounts in EUR) writing \
"03/04/2026" means 3 April 2026, not 4 March 2026. If the day is >12 the order \
is unambiguous -- use that to infer the document's convention, then apply it \
consistently.
3. Every field needs a verbatim "quote": the exact substring of the document \
you took it from. If you cannot find the field, set value to null, confidence \
to 0.0, and quote to "".
4. Per-field confidence 0.0-1.0. Be honest. Lower it when the label is \
ambiguous, the value is inferred rather than stated, or a date format is \
uncertain.

Return JSON only, shaped:
{"fields": {"<field>": {"value": <number|string|null>, "confidence": 0.0-1.0, \
"quote": "<verbatim>"}, ...}}"""


def extract(client, text, doc_type):
    spec = SCHEMAS[doc_type]
    field_lines = "\n".join(f"- {k}: {v}" for k, v in spec["fields"].items())

    if client is None:
        import offline
        return offline.extract(text, doc_type)

    user = (f"Extract these fields:\n{field_lines}\n\n"
            f"<document>\n{text[:12000]}\n</document>")
    return _ask(client, EXTRACT_SYS, user, 3000)


# ------------------------------------------------------------------- agent 3

def _num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d.\-]", "", str(v).replace("(", "-"))
    try:
        return float(s)
    except ValueError:
        return None


def _parse_date(v):
    if not v:
        return None
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def validate(doc_type, fields):
    """Run the document's own arithmetic against itself."""
    spec = SCHEMAS[doc_type]
    vals = {k: _num(f.get("value")) for k, f in fields.items()}
    checks = []

    for label, expr, tol in spec["identities"]:
        lhs_s, rhs_s = expr.split("==") if "==" in expr else expr.split("<=")
        op = "==" if "==" in expr else "<="
        try:
            env = {k: v for k, v in vals.items() if v is not None}
            missing = [t for t in re.findall(r"[a-z_]+", expr)
                       if t not in env and t in spec["fields"]]
            if missing:
                checks.append({"check": label, "status": "skipped",
                               "detail": f"missing {', '.join(missing)}"})
                continue
            lhs = eval(lhs_s, {"__builtins__": {}}, env)
            rhs = eval(rhs_s, {"__builtins__": {}}, env)
            if op == "==":
                ok = abs(lhs - rhs) <= max(tol, abs(rhs) * 1e-6)
                detail = (f"{lhs:,.2f} vs {rhs:,.2f}"
                          if not ok else f"ties at {lhs:,.2f}")
            else:
                ok = lhs <= rhs + tol
                detail = f"{lhs:,.2f} <= {rhs:,.2f}"
            checks.append({"check": label,
                           "status": "pass" if ok else "FAIL",
                           "detail": detail})
        except Exception as e:
            checks.append({"check": label, "status": "skipped",
                           "detail": str(e)[:60]})

    for earlier, later in spec["date_order"]:
        d1 = _parse_date(fields.get(earlier, {}).get("value"))
        d2 = _parse_date(fields.get(later, {}).get("value"))
        if d1 and d2:
            ok = d1 <= d2
            checks.append({
                "check": f"{earlier} on or before {later}",
                "status": "pass" if ok else "FAIL",
                "detail": f"{d1} -> {d2}",
            })
    return checks


# ------------------------------------------------------------------- agent 4

def triage(doc_type, fields, checks, cls):
    """Decide: post automatically, or route to a human and say exactly why."""
    reasons = []

    if cls.get("confidence", 0) < CONFIDENCE_BAR:
        reasons.append(f"document type uncertain ({cls.get('confidence', 0):.0%})")

    for f in CRITICAL_FIELDS.get(doc_type, []):
        fd = fields.get(f) or {}
        if fd.get("value") in (None, ""):
            reasons.append(f"{f} not found")
        elif float(fd.get("confidence") or 0) < CONFIDENCE_BAR:
            reasons.append(f"{f} low confidence "
                           f"({float(fd.get('confidence') or 0):.0%})")

    for c in checks:
        if c["status"] == "FAIL":
            reasons.append(f"{c['check']} ({c['detail']})")

    return {"status": "exception" if reasons else "auto_posted",
            "reasons": reasons}


# ----------------------------------------------------------------- per-doc run

def read_pdf(path):
    return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)


def process(path):
    name = os.path.basename(path)
    client = _client()
    text = read_pdf(path)

    cls = classify(client, text)
    doc_type = cls.get("doc_type", "other")

    if doc_type not in SCHEMAS:
        return {"file": name, "doc_type": doc_type, "classification": cls,
                "fields": {}, "checks": [],
                "triage": {"status": "exception",
                           "reasons": ["unrecognized document type"]}}

    ex = extract(client, text, doc_type)
    fields = ex.get("fields", {})
    checks = validate(doc_type, fields)
    tri = triage(doc_type, fields, checks, cls)

    return {"file": name, "doc_type": doc_type, "classification": cls,
            "fields": fields, "checks": checks, "triage": tri}


def process_dir(corpus_dir, workers=12, progress=None):
    paths = sorted(os.path.join(corpus_dir, f)
                   for f in os.listdir(corpus_dir) if f.endswith(".pdf"))
    out = []
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(process, p): p for p in paths}
        for i, fut in enumerate(cf.as_completed(futs), 1):
            try:
                out.append(fut.result())
            except Exception as e:
                out.append({"file": os.path.basename(futs[fut]),
                            "doc_type": "error", "classification": {},
                            "fields": {}, "checks": [],
                            "triage": {"status": "exception",
                                       "reasons": [f"pipeline error: {e}"]}})
            if progress:
                progress(i, len(paths))
    return sorted(out, key=lambda r: r["file"])


# ------------------------------------------------------- cross-doc reconcile

def reconcile(results, today=None):
    """
    Roll extracted documents into a position ledger and a forward cash calendar,
    then look for breaks that no single document could reveal on its own.
    """
    today = today or date.today()
    funds = {}

    # Resolve fund-name variants onto canonical entities before aggregating,
    # and drop strings that are actually the LP or the management company.
    import entities
    raw_names = [(r["fields"].get("fund_name") or {}).get("value")
                 for r in results]
    raw_names = [n for n in raw_names if n]
    mgrs = [(r["fields"].get("gp_manager") or {}).get("value") for r in results]
    mgrs = [m for m in mgrs if m]
    name_map, rejected = entities.resolve(raw_names, LP_NAME, mgrs)

    for r in results:
        f = r["fields"]
        raw = (f.get("fund_name") or {}).get("value")
        if not raw:
            continue
        if raw in rejected:
            r["triage"]["status"] = "exception"
            r["triage"]["reasons"].append(
                f"fund name unusable: {rejected[raw]} (got '{raw}')")
            continue
        fund = name_map.get(raw, raw)
        if fund != raw:
            r.setdefault("notes", []).append(
                f"fund name '{raw}' resolved to '{fund}'")
        p = funds.setdefault(fund, {
            "fund": fund,
            "manager": (f.get("gp_manager") or {}).get("value"),
            "currency": (f.get("currency") or {}).get("value") or "USD",
            "commitment": None, "called": 0.0, "distributed": 0.0,
            "latest_nav": None, "nav_date": None,
            "calls": [], "distributions": [], "breaks": [],
        })

        if r["doc_type"] == "capital_call":
            amt = _num((f.get("amount") or {}).get("value")) or 0.0
            due = _parse_date((f.get("due_date") or {}).get("value"))
            commit = _num((f.get("commitment") or {}).get("value"))
            if commit:
                p["commitment"] = commit
            p["called"] += amt
            p["calls"].append({"amount": amt, "due": due.isoformat() if due else None,
                               "file": r["file"],
                               "status": r["triage"]["status"]})
        elif r["doc_type"] == "distribution":
            amt = _num((f.get("amount") or {}).get("value")) or 0.0
            pay = _parse_date((f.get("payment_date") or {}).get("value"))
            p["distributed"] += amt
            p["distributions"].append({"amount": amt,
                                       "date": pay.isoformat() if pay else None,
                                       "file": r["file"]})
        elif r["doc_type"] == "capital_account_statement":
            pe = _parse_date((f.get("period_end") or {}).get("value"))
            nav = _num((f.get("ending_nav") or {}).get("value"))
            if pe and nav is not None and (p["nav_date"] is None
                                           or pe.isoformat() > p["nav_date"]):
                p["nav_date"] = pe.isoformat()
                p["latest_nav"] = nav

    positions = []
    for p in funds.values():
        if p["commitment"]:
            p["unfunded"] = round(p["commitment"] - p["called"], 2)
            p["pct_called"] = round(p["called"] / p["commitment"] * 100, 1)
            if p["called"] > p["commitment"] * 1.0001:
                p["breaks"].append(
                    f"cumulative calls ({p['called']:,.0f}) exceed commitment "
                    f"({p['commitment']:,.0f})")
        else:
            p["unfunded"] = None
            p["pct_called"] = None
            p["breaks"].append("no commitment amount found in any document")

        if p["latest_nav"] is None:
            p["breaks"].append("no capital account statement on file")
        p["dpi"] = (round(p["distributed"] / p["called"], 2)
                    if p["called"] else None)
        p["called"] = round(p["called"], 2)
        p["distributed"] = round(p["distributed"], 2)
        positions.append(p)

    calendar = []
    for p in positions:
        for c in p["calls"]:
            if not c["due"]:
                continue
            d = _parse_date(c["due"])
            if d and d >= today:
                calendar.append({"fund": p["fund"], "currency": p["currency"],
                                 "amount": c["amount"], "due": c["due"],
                                 "days": (d - today).days, "file": c["file"],
                                 "status": c["status"]})
    calendar.sort(key=lambda x: x["due"])

    return {"positions": sorted(positions, key=lambda x: -(x["called"] or 0)),
            "calendar": calendar}


def summarize(results, recon):
    n = len(results)
    auto = sum(1 for r in results if r["triage"]["status"] == "auto_posted")
    exc = n - auto
    checks = [c for r in results for c in r["checks"]]
    cash_30 = sum(c["amount"] for c in recon["calendar"] if c["days"] <= 30)
    return {
        "documents": n,
        "auto_posted": auto,
        "exceptions": exc,
        "straight_through_rate": round(auto / n * 100, 1) if n else 0.0,
        "checks_run": len(checks),
        "checks_failed": sum(1 for c in checks if c["status"] == "FAIL"),
        "positions": len(recon["positions"]),
        "funds_with_breaks": sum(1 for p in recon["positions"] if p["breaks"]),
        "upcoming_calls": len(recon["calendar"]),
        "cash_due_30d": round(cash_30, 2),
        "model": MODEL,
        "live_llm": _client() is not None,
    }


if __name__ == "__main__":
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else "corpus"

    def prog(i, n):
        print(f"\r  {i}/{n} documents", end="", flush=True)

    # free-tier cloud endpoints rate-limit hard; keep concurrency modest
    workers = 3 if PROVIDER in OPENAI_COMPAT else 12
    res = process_dir(d, workers=workers, progress=prog)
    print()
    rec = reconcile(res, today=date(2026, 7, 27))
    summ = summarize(res, rec)
    with open("results.json", "w") as f:
        json.dump({"results": res, "reconciliation": rec, "summary": summ},
                  f, indent=2, default=str)
    print(json.dumps(summ, indent=2))
