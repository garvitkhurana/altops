"""
Altline -- private credit facility checker.

    pip install fastapi uvicorn pypdf reportlab
    python3 credit_corpus.py     # build the agreement + notice traffic
    python3 app.py               # -> http://localhost:8000

Provider keys live in .env; auto-detect order is NVIDIA, OpenRouter,
Anthropic. Without one the deterministic parser runs alone.

This demo makes one argument: the model reads, the engine computes.
Gate 1 scores extraction against the corpus seed. Gate 2 recomputes
every notice and scores detection against seeded defects.
"""

import json
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

import facility
import pipeline

HERE = os.path.dirname(os.path.abspath(__file__))

_envfile = os.path.join(HERE, ".env")
if os.path.exists(_envfile):
    for _line in open(_envfile).read().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            if _v.strip() and not os.environ.get(_k.strip()):
                os.environ[_k.strip()] = _v.strip()

app = FastAPI(title="Altline")
_cache = {}


def _public_site():
    return os.environ.get("ALTLINE_PUBLIC", "").lower() in ("1", "true", "yes")


def run(refresh=False, provider=None, agreement=None):
    key = (provider or "auto", agreement or "default")
    if refresh or key not in _cache:
        use_llm = provider != "deterministic"
        _cache[key] = facility.run(
            use_llm=use_llm,
            provider=None if provider in (None, "auto") else provider,
            agreement=agreement)
    return _cache[key]


@app.get("/api/options")
def api_options():
    facilities = facility.list_facilities()
    if _public_site():
        providers = [{"id": "deterministic", "label": "Sample audit", "model": None}]
        default_provider = "deterministic"
    else:
        providers = pipeline.available_providers()
        default_provider = pipeline._provider() or "deterministic"
    return JSONResponse({
        "public": _public_site(),
        "facilities": facilities,
        "providers": providers,
        "default_facility": facilities[0]["id"] if facilities else None,
        "default_provider": default_provider,
    })


@app.get("/api/run")
async def api_run(refresh: bool = False, provider: str = None, facility_id: str = None):
    import asyncio
    if _public_site():
        provider = "deterministic"
    try:
        data = await asyncio.to_thread(run, refresh, provider, facility_id)
        return JSONResponse(json.loads(json.dumps(data, default=str)))
    except Exception as e:
        return JSONResponse(
            {"error": f"{type(e).__name__}: {str(e)[:240]}",
             "extraction": {"mode": "error", "note": str(e)[:240],
                            "provider": provider, "attempted": provider},
             "facility": {}, "citations": {}, "findings": [],
             "summary": {}},
            status_code=500)


@app.get("/", response_class=HTMLResponse)
def index():
    return LANDING_HTML


@app.get("/demo", response_class=HTMLResponse)
def demo():
    flag = "true" if _public_site() else "false"
    return HTML.replace("__PUBLIC_DEMO__", flag)


LANDING_HTML = r"""
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Altline | Verify private credit</title>
<link rel="icon" href="data:,">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<style>
:root{--ink:#15221e;--muted:#66736d;--line:#d7dfd9;--paper:#f5f7f2;--panel:#fbfcf9;--mint:#dbece1;--green:#147a54;--orange:#cc5b2d}
*{box-sizing:border-box;margin:0;padding:0}body{background:var(--paper);color:var(--ink);font:15px/1.55 "DM Sans",sans-serif}
a{color:inherit;text-decoration:none}.wrap{max-width:1160px;margin:0 auto;padding:0 28px}
header{height:76px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line)}
.brand,.brand:visited{display:inline-block;color:var(--ink);text-decoration:none;font:700 24px/1 "Space Grotesk",sans-serif;letter-spacing:-1px}.brand span{color:var(--green)}
nav{display:flex;align-items:center;gap:28px;color:var(--muted);font-size:13px}nav a:hover{color:var(--ink)}
.nav-cta{background:var(--ink);color:#fff;padding:10px 16px;border-radius:5px;font-weight:600}
.hero{display:grid;grid-template-columns:minmax(0,1fr) 390px;gap:84px;padding:96px 0 82px;align-items:center}
.kicker{color:var(--green);font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin-bottom:18px}
h1{font:600 clamp(50px,7vw,84px)/.96 "Space Grotesk",sans-serif;letter-spacing:-4px;max-width:700px}
.hero-copy{color:var(--muted);font-size:18px;max-width:550px;margin-top:25px}.actions{display:flex;gap:12px;margin-top:30px;align-items:center}
.primary{background:var(--green);color:#fff;padding:13px 19px;border-radius:5px;font-weight:700}.secondary{padding:12px 2px;color:var(--muted);font-weight:600}
.window{background:var(--panel);border:1px solid var(--line);box-shadow:15px 18px 0 var(--mint);padding:19px;border-radius:7px;transform:rotate(1.5deg)}
.window-top{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding-bottom:15px;font-size:12px}.dots{display:flex;gap:5px}.dots i{width:7px;height:7px;border-radius:50%;background:#c7d2ca}.live{color:var(--green);font-size:11px;font-weight:700}
.window-title{font:600 25px/1.05 "Space Grotesk",sans-serif;margin:21px 0 18px}.impact{font:600 37px/1 "Space Grotesk",sans-serif;color:var(--orange);letter-spacing:-2px}.impact-label{font-size:12px;color:var(--muted);margin-top:5px}.metric-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:23px}.metric{border-top:1px solid var(--line);padding-top:10px}.metric b{font:600 21px "Space Grotesk",sans-serif}.metric small{display:block;color:var(--muted);font-size:11px;margin-top:2px}
.band{border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:19px 0;color:var(--muted);font-size:13px}.band strong{color:var(--ink);font-weight:600;margin-right:34px}
.section{padding:92px 0}.section-head{display:grid;grid-template-columns:1fr 1fr;gap:70px;margin-bottom:42px}.section h2{font:600 42px/.98 "Space Grotesk",sans-serif;letter-spacing:-2px}.section-intro{color:var(--muted);max-width:390px;font-size:16px}
.features{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);border:1px solid var(--line)}.feature{background:var(--panel);padding:25px;min-height:220px}.number{color:var(--orange);font:600 13px "Space Grotesk",sans-serif}.feature h3{font:600 21px "Space Grotesk",sans-serif;margin:48px 0 8px}.feature p{color:var(--muted);font-size:13px;max-width:280px}
.proof{background:var(--ink);color:#f3f7f2;padding:78px 0}.proof-grid{display:grid;grid-template-columns:1fr 1fr;gap:70px;align-items:center}.proof h2{font:600 42px/.98 "Space Grotesk",sans-serif;letter-spacing:-2px}.proof p{color:#a9b8af;margin-top:18px;max-width:430px}.proof-stat{border-left:1px solid #405148;padding-left:30px}.stat{font:600 55px/1 "Space Grotesk",sans-serif;color:#d9f0df;letter-spacing:-3px}.stat-label{color:#a9b8af;font-size:13px;margin-top:8px}.proof-stat hr{border:none;border-top:1px solid #405148;margin:25px 0}.small-stat{display:flex;justify-content:space-between;color:#d9f0df;font-size:14px}.small-stat span{color:#a9b8af}
.closing{padding:92px 0 105px;text-align:center}.closing h2{font:600 49px/.98 "Space Grotesk",sans-serif;letter-spacing:-2px}.closing p{color:var(--muted);margin:17px auto 28px;max-width:450px}
footer{border-top:1px solid var(--line);padding:23px 0;color:var(--muted);font-size:12px;display:flex;justify-content:space-between}
@media(max-width:800px){nav a:not(.nav-cta){display:none}.hero{grid-template-columns:1fr;gap:55px;padding:70px 0}.window{max-width:420px}.section-head,.proof-grid{grid-template-columns:1fr;gap:24px}.features{grid-template-columns:1fr}.feature{min-height:0}.proof-stat{border-left:0;border-top:1px solid #405148;padding:25px 0 0}.closing h2{font-size:40px}}
</style></head><body>
<header class="wrap"><a class="brand" href="/">alt<span>line</span></a><nav><a href="#product">Product</a><a href="#proof">Why Altline</a><a class="nav-cta" href="/demo">See the demo</a></nav></header>
<main>
  <section class="wrap hero"><div><div class="kicker">Verification infrastructure for alternative assets</div><h1>The number on the notice is not the truth.</h1><p class="hero-copy">Altline independently checks private credit agent notices against the agreement that governs them, before a wrong number becomes a booked number.</p><div class="actions"><a class="primary" href="/demo">See a live audit</a><a class="secondary" href="#product">Explore the product &rarr;</a></div></div>
  <div class="window"><div class="window-top"><div class="dots"><i></i><i></i><i></i></div><div class="live">● AUDIT COMPLETE</div></div><div class="window-title">Meridian Packaging</div><div class="impact">$5,453.47</div><div class="impact-label">interest impact found in one period</div><div class="metric-row"><div class="metric"><b>10</b><small>findings surfaced</small></div><div class="metric"><b>3 / 4</b><small>notices challenged</small></div></div></div></section>
  <div class="band"><div class="wrap"><strong>BUILT FOR THE BACK OFFICE</strong> Agreements &nbsp;·&nbsp; Borrowing notices &nbsp;·&nbsp; Agent calculations &nbsp;·&nbsp; Audit evidence</div></div>
  <section class="wrap section" id="product"><div class="section-head"><h2>Quiet software for expensive mistakes.</h2><p class="section-intro">The work arrives as PDFs. The answer is buried in negotiated language. Altline turns that language into a checkable control for every notice that follows.</p></div><div class="features"><article class="feature"><div class="number">01 / COMPILE</div><h3>Agreement into a specification</h3><p>Key terms become structured, cited rules: margins, day counts, notice periods, availability and more.</p></article><article class="feature"><div class="number">02 / VERIFY</div><h3>Every number recomputed</h3><p>Deterministic checks independently recalculate interest and test each request against the contract.</p></article><article class="feature"><div class="number">03 / PROVE</div><h3>Exceptions with evidence</h3><p>See the broken clause, the agent's figure, the corrected arithmetic and the precise action to take.</p></article></div></section>
  <section class="proof" id="proof"><div class="wrap proof-grid"><div><div class="kicker">One facility. One test corpus.</div><h2>Make “your agent is wrong” an evidence trail.</h2><p>Altline is designed for the work nobody has time to repeat by hand, but everybody pays for when it goes wrong.</p></div><div class="proof-stat"><div class="stat">$5.4k</div><div class="stat-label">mispricing found in the demo facility</div><hr><div class="small-stat"><span>Seeded defects caught</span><b>7 / 7</b></div><div class="small-stat"><span>Availability breach found</span><b>$1.5m</b></div></div></div></section>
  <section class="wrap closing"><h2>Start with the notices you already receive.</h2><p>Bring six months of agent traffic. We will show you what the agreement says, what the notice says, and what the difference is worth.</p><a class="primary" href="/demo">Open the product demo</a></section>
</main><footer class="wrap"><span>altline / private credit verification</span><span>Confidential by design</span></footer>
</body></html>
"""


HTML = r"""
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Altline | Audit demo</title>
<link rel="icon" href="data:,">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --ink:#1a1f2a; --muted:#5c6575; --line:#d8dde6; --paper:#f3f1eb;
  --paper2:#e9e6de; --panel:#fffcf7; --red:#b42318; --green:#1f6b45;
  --blue:#2a5a8a; --warn:#8a6a12;
}
*{box-sizing:border-box;margin:0;padding:0}
body{
  background:
    radial-gradient(1200px 500px at 10% -10%, #ebe4d4 0%, transparent 55%),
    radial-gradient(900px 400px at 100% 0%, #dfe6ef 0%, transparent 50%),
    var(--paper);
  color:var(--ink);
  font:15px/1.55 "IBM Plex Sans",system-ui,sans-serif;
  min-height:100vh;
}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums}
.display{font-family:Fraunces,Georgia,serif}

header{
  padding:15px 28px;display:flex;align-items:center;gap:28px;flex-wrap:wrap;
  border-bottom:1px solid var(--line);background:rgba(255,252,247,.72);
  backdrop-filter:blur(8px);position:sticky;top:0;z-index:5;
}
.brand,.brand:visited{display:inline-block;color:var(--ink);text-decoration:none;
  font:700 24px/1 "Space Grotesk",sans-serif;letter-spacing:-1px}
.brand span{color:var(--green)}
.tagline{color:var(--muted);font-size:13px;max-width:280px}
.nav{display:flex;gap:18px;align-items:center;color:var(--muted);font-size:12px}
.nav a{color:inherit;text-decoration:none;padding:8px 0;border-bottom:1px solid transparent}
.nav a:first-child,.nav a:hover{color:var(--ink);border-color:var(--red)}
.controls{margin-left:auto;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.controls button{
  background:var(--ink);color:#f7f4ee;border:none;border-radius:6px;
  padding:8px 14px;font:12.5px/1 "IBM Plex Sans",sans-serif;font-weight:600;
  cursor:pointer;
}
.controls button:hover{opacity:.92}
.controls button:disabled{opacity:.5;cursor:wait}
.controls .more{position:relative}
.controls .more > summary{
  list-style:none;cursor:pointer;font-size:12px;color:var(--muted);
  padding:7px 10px;border:1px solid var(--line);border-radius:6px;background:var(--panel);
  user-select:none;
}
.controls .more > summary::-webkit-details-marker{display:none}
.controls .more[open] > summary{border-color:#b0b8c6;color:var(--ink)}
.controls .drawer{
  position:absolute;right:0;top:calc(100% + 6px);min-width:260px;
  background:var(--panel);border:1px solid var(--line);border-radius:8px;
  padding:12px;display:flex;flex-direction:column;gap:10px;
  box-shadow:0 10px 30px rgba(26,31,42,.08);z-index:8;
}
.controls .drawer label{display:flex;flex-direction:column;gap:4px;color:var(--muted);font-size:11px}
.controls .drawer select{
  background:#fff;border:1px solid var(--line);border-radius:6px;
  padding:7px 10px;font:12.5px "IBM Plex Sans",sans-serif;color:var(--ink);
}
.mode{font-size:11px;padding:4px 10px;border-radius:999px;border:1px solid var(--line);
  color:var(--muted);background:var(--panel)}
.mode.live{color:var(--green);border-color:#b7d7c4;background:#eef7f1}

main{max-width:980px;padding:0 28px 72px;margin:0 auto}

.hero{padding:48px 0 36px;animation:rise .7s ease both}
.hero-grid{display:grid;grid-template-columns:minmax(0,1fr) 270px;gap:42px;align-items:end}
.hero .eyebrow{font-size:12px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);font-weight:600;margin-bottom:14px}
.hero .big{font-family:Fraunces,Georgia,serif;font-size:clamp(48px,9vw,76px);
  font-weight:650;letter-spacing:-2.5px;color:var(--red);line-height:.95}
.hero .cap{margin-top:14px;font-size:18px;max-width:34em;color:var(--ink)}
.hero .sub{margin-top:12px;color:var(--muted);font-size:13.5px}
.hero-panel{border-left:1px solid var(--line);padding:5px 0 5px 22px}
.hero-panel .panel-label{font-size:10px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);font-weight:600}
.hero-panel .panel-value{font-family:Fraunces,Georgia,serif;font-size:25px;margin:5px 0 3px}
.hero-panel .panel-note{font-size:12px;color:var(--muted);line-height:1.45}
.signal{height:5px;background:#e7e3da;border-radius:5px;overflow:hidden;margin:13px 0 9px}
.signal i{display:block;height:100%;width:72%;background:var(--red);border-radius:5px}

.gates{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:8px 0 28px}
.gate{padding:14px 16px;border:1px solid var(--line);border-radius:10px;
  background:var(--panel)}
.gate .gk{font-size:11px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--muted);font-weight:600}
.gate .gv{font-family:Fraunces,Georgia,serif;font-size:28px;font-weight:650;
  margin-top:4px}
.gate.ok .gv{color:var(--green)}
.gate.bad .gv{color:var(--red)}
.gate .gs{color:var(--muted);font-size:12.5px;margin-top:4px}

.split{display:grid;grid-template-columns:1fr 1fr;gap:28px;padding:22px 0 8px;
  border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin-bottom:8px}
.split h3{font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);margin-bottom:6px}
.split p{font-size:14.5px;color:var(--ink);max-width:36em}

h2{font-family:Fraunces,Georgia,serif;font-size:26px;font-weight:650;
  letter-spacing:-.4px;margin:40px 0 8px}
.lede{color:var(--muted);font-size:14px;margin-bottom:16px;max-width:40em}

.spec{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.term{background:var(--panel);padding:14px 15px}
.term .k{font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
.term .v{font-size:15px;margin-top:5px;font-weight:500}
.term .c{color:var(--blue);font-size:11.5px;margin-top:6px;font-weight:600}

.notice{border-top:1px solid var(--line);padding:18px 0}
.notice:first-of-type{border-top:none}
.nhead{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px}
.pill{font-size:10.5px;padding:2px 9px;border-radius:999px;font-weight:600;
  letter-spacing:.02em}
.pill.ok{background:#eef7f1;color:var(--green)}
.pill.crit{background:#f8e8e6;color:var(--red)}
.pill.high{background:#f5efd8;color:var(--warn)}
.pill.seed{background:#eef2f8;color:var(--blue)}
.fn{font-size:13px;color:var(--muted)}
.btitle{font-size:15px;font-weight:600;margin-top:10px}
.bsec{color:var(--blue);font-size:12.5px;font-weight:600;margin-left:6px}
.bdet{color:var(--muted);font-size:13.5px;margin-top:4px;max-width:48em}
.calc{margin-top:12px;padding:14px 0;border-top:1px dashed var(--line)}
.calc .formula{font-size:13px;color:var(--muted);margin-bottom:10px}
.calc .row{display:flex;gap:16px;padding:3px 0;align-items:baseline}
.calc .lbl{width:140px;color:var(--muted);font-size:12px;flex:none}
.delta{color:var(--red);font-weight:600}
.ours{color:var(--green);font-weight:600}
.fix{margin-top:10px;font-size:13px;color:var(--muted)}
.fix b{color:var(--green)}
.lead{background:linear-gradient(180deg,#fff8f6,#fffcf7);
  border:1px solid #e8cfc9;border-radius:12px;padding:20px 22px;margin:12px 0 20px;
  animation:rise .8s .15s ease both}
.lead .eyebrow{font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--red);font-weight:600;margin-bottom:8px}

.honest{margin-top:48px;padding:18px 0;border-top:1px solid var(--line);
  color:var(--muted);font-size:13px;max-width:40em}
.loading{padding:80px 0;text-align:center;color:var(--muted)}
.warn{background:#f5efd8;border:1px solid #e2d4a0;color:#6a5410;
  padding:12px 14px;border-radius:8px;font-size:13px;margin:16px 0}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@media(max-width:720px){
  .gates,.split{grid-template-columns:1fr}
  .hero-grid{grid-template-columns:1fr;gap:25px}
  .hero-panel{border-left:none;border-top:1px solid var(--line);padding:17px 0 0}
  .nav{order:3;width:100%;border-top:1px solid var(--line);padding-top:10px}
  header{align-items:flex-start}
  .controls{margin-left:0;width:100%}
}
</style></head><body>
<header>
  <div>
    <a class="brand" href="/" aria-label="Return to Altline homepage">alt<span>line</span></a>
    <div class="tagline">We audit private credit agents&rsquo; math</div>
  </div>
  <nav class="nav" aria-label="Primary">
    <a href="#overview">Overview</a>
    <a href="#agreement">Agreement</a>
    <a href="#notices">Verification log</a>
  </nav>
  <div class="controls">
    <span class="mode" id="mode">&mdash;</span>
    <button id="runBtn" type="button">Run with model</button>
    <details class="more">
      <summary>Options</summary>
      <div class="drawer">
        <label>Facility <select id="facility"></select></label>
        <label>Provider <select id="provider"></select></label>
      </div>
    </details>
  </div>
</header>
<main id="app"><div class="loading">Compiling agreement&hellip;</div></main>
<script>
const PUBLIC = __PUBLIC_DEMO__;
const esc=s=>String(s==null?'':s).replace(/[<>&]/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]));
const m2=n=>n==null?'&mdash;':'$'+Number(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const m0=n=>n==null?'&mdash;':'$'+Number(n).toLocaleString('en-US',{maximumFractionDigits:0});

const facilitySel=document.getElementById('facility');
const providerSel=document.getElementById('provider');
const runBtn=document.getElementById('runBtn');
if(PUBLIC) document.querySelector('.controls').style.display='none';

function setBusy(b,label){
  if(PUBLIC) return;
  runBtn.disabled=b; facilitySel.disabled=b; providerSel.disabled=b;
  runBtn.textContent=b?(label||'Running\u2026'):'Run with model';
}

async function loadOptions(){
  const o=await fetch('/api/options').then(r=>r.json());
  facilitySel.innerHTML=o.facilities.map(f=>
    `<option value="${esc(f.id)}"${f.id===o.default_facility?' selected':''}>${esc(f.label)}</option>`
  ).join('');
  // Prefer deterministic in the dropdown for instant paint; live models via Run.
  const prefs=['deterministic',...o.providers.map(p=>p.id).filter(id=>id!=='deterministic')];
  const ordered=[...new Map(o.providers.map(p=>[p.id,p])).entries()].map(([,p])=>p);
  ordered.sort((a,b)=>prefs.indexOf(a.id)-prefs.indexOf(b.id));
  providerSel.innerHTML=ordered.map(p=>{
    const label=p.model?`${p.label} · ${p.model}`:p.label;
    const sel=p.id==='deterministic'?' selected':'';
    return `<option value="${esc(p.id)}"${sel}>${esc(label)}</option>`;
  }).join('');
}

let inflight=null;
async function run(refresh=true, providerOverride=null){
  if(inflight) return;
  const provider=providerOverride||providerSel.value;
  const llm=provider!=='deterministic';
  setBusy(true, llm?'Calling model\u2026':'Running\u2026');
  document.getElementById('app').innerHTML=llm
    ? `<div class="loading">Calling <b>${esc(provider)}</b> to extract terms&hellip;<br>
       <span style="font-size:12px">Usually 6&ndash;40s. Gate 2 still runs in code.</span></div>`
    : '<div class="loading">Compiling agreement&hellip;</div>';
  const q=new URLSearchParams({
    refresh: refresh?'true':'false', provider, facility_id: facilitySel.value,
  });
  inflight=fetch('/api/run?'+q).then(async r=>{
    const text=await r.text();
    let d; try{d=JSON.parse(text);}catch(e){throw new Error(r.status+' '+text.slice(0,180));}
    if(!r.ok) throw new Error(d.error||d.extraction?.note||text.slice(0,180));
    return d;
  });
  try{ render(await inflight); }
  catch(e){
    document.getElementById('app').innerHTML=
      '<div class="warn">Failed to load: '+esc(e.message||e)+'</div>';
  }finally{ inflight=null; setBusy(false); }
}

function render(d){
  const F=d.facility||{}, C=d.citations||{}, s=d.summary||{}, X=d.extraction||{};
  const gt=X.gt||{}, det=s.detection||{};
  const el=document.getElementById('mode');
  el.className='mode';
  if(PUBLIC){
    el.textContent='sample audit';
  }else if(X.mode==='llm+deterministic'){
    el.textContent='live · '+(X.provider||'model')+' + engine';
    el.className='mode live';
  }else if(X.attempted && X.attempted!=='deterministic'){
    el.textContent=X.attempted+' failed · deterministic';
  }else el.textContent='deterministic parser';

  let h='';
  h+=`<section class="hero" id="overview">
    <div class="hero-grid">
      <div>
        <div class="eyebrow">${esc(F.borrower||'Facility')} · ${m0(s.total_commitments)} senior facility</div>
        <div class="big mono">${m2(s.interest_impact)}</div>
        <div class="cap">of interest mispriced across ${s.mispriced_notices} of 4 agent
          notices &mdash; in a single interest period, on one facility.</div>
        <div class="sub">${s.total_breaks} findings · ${s.critical} critical · ${s.high} high ·
          ${m0(s.availability_breach)} availability breach · leverage ${s.leverage}x</div>
      </div>
      <aside class="hero-panel">
        <div class="panel-label">Verification coverage</div>
        <div class="panel-value">${s.total_breaks} findings surfaced</div>
        <div class="signal"><i></i></div>
        <div class="panel-note">Every notice is checked against the compiled agreement. Exceptions include the proving clause and arithmetic.</div>
      </aside>
    </div>
  </section>`;

  h+=`<div class="split">
    <div><h3>The model reads</h3>
      <p>Extracts terms from the agreement, each with the clause it came from.
      Language work. Gate 1 checks those terms against the seed that wrote the PDF.</p></div>
    <div><h3>The engine computes</h3>
      <p>Recomputes every interest figure in code &mdash; never the model.
      Gate 2 checks that planted defects are caught and clean notices stay clean.</p></div>
  </div>`;

  h+=`<div class="gates">
    <div class="gate ${gt.ok?'ok':'bad'}">
      <div class="gk">Gate 1 · Extraction vs seed</div>
      <div class="gv mono">${esc(gt.score||'\u2014')}</div>
      <div class="gs">${gt.ok?'All checkable terms match the corpus seed.'
        :esc((gt.mismatched||[]).concat(gt.missing||[]).join(', ')||'Incomplete')}</div>
    </div>
    <div class="gate ${det.ok?'ok':'bad'}">
      <div class="gk">Gate 2 · Seeded defects caught</div>
      <div class="gv mono">${esc(det.score||'\u2014')}</div>
      <div class="gs">${det.n_clean_ok||0} clean notices stayed clean${det.n_false_positives?
        ` · ${det.n_false_positives} false positive`:''}</div>
    </div>
  </div>`;

  if(X.note && X.mode!=='llm+deterministic')
    h+=`<div class="warn"><b>Fell back to deterministic.</b> ${esc(X.note)}</div>`;

  // Gate 1 detail
  h+=`<h2 id="agreement">Gate 1 &mdash; Agreement, compiled</h2>
  <div class="lede">${X.note?esc(X.note):'Terms extracted from the PDF. Scored against the corpus seed (not the model).'}
    ${gt.score?` Extract score <b class="mono">${esc(gt.score)}</b>.`:''}</div>
  <div class="spec">`;
  const grid=(F.pricing_grid||[]).map(t=>{
    const lo=t.min_leverage, hi=t.max_leverage;
    return (lo!=null&&hi!=null)?`&gt;${lo.toFixed(2)}&ndash;${hi.toFixed(2)}x &rarr; ${t.margin}%`
         : lo!=null?`&gt;${lo.toFixed(2)}x &rarr; ${t.margin}%`
         : `&le;${hi.toFixed(2)}x &rarr; ${t.margin}%`;}).join('<br>');
  const csa=Object.entries(F.credit_spread_adjustment||{})
    .map(([k,v])=>`${k}mo &rarr; ${v}%`).join(' · ');
  const terms=[
    ['Borrower',F.borrower?esc(F.borrower):null,'borrower'],
    ['Administrative agent',F.administrative_agent?esc(F.administrative_agent):null,'administrative_agent'],
    ['Total commitments',F.tranches?m0(Object.values(F.tranches).reduce((a,b)=>a+b,0)):null,'tranches'],
    ['Permitted interest periods',
      F.permitted_interest_periods?F.permitted_interest_periods.join(', ')+' months':null,
      'permitted_interest_periods'],
    ['Day count (SOFR)',F.day_count_sofr?'Actual/'+F.day_count_sofr:null,'day_count_sofr'],
    ['Credit spread adjustment',csa||null,'credit_spread_adjustment'],
    ['Applicable margin grid',grid||null,'pricing_grid'],
    ['Minimum borrowing',
      F.minimum_borrowing?m0(F.minimum_borrowing)+' / multiples of '+m0(F.borrowing_multiple):null,
      'minimum_borrowing'],
    ['SOFR notice',F.notice_days_sofr?F.notice_days_sofr+' business days':null,'notice_days_sofr'],
    ['LC sublimit',F.lc_sublimit?m0(F.lc_sublimit):null,'lc_sublimit'],
  ];
  terms.forEach(([k,v,key])=>{
    if(!v) return;
    const st=(gt.details&&gt.details[key]&&gt.details[key].status)||'';
    const mark=st==='matched'?' · matched':st==='mismatched'?' · mismatched':st==='missing'?' · missing':'';
    const c=C[key];
    h+=`<div class="term"><div class="k">${esc(k)}${mark}</div>
      <div class="v mono">${v}</div>
      ${c&&c.section?`<div class="c">§${esc(c.section)}</div>`:''}</div>`;
  });
  h+='</div>';

  const K=X.consensus;
  if(K && !K.error){
    const nd=Object.keys(K.disputed||{}).length;
    h+=`<div class="lede" style="margin-top:14px">Reader consensus
      (<span class="mono">${esc((K.passes||[]).join(' · '))}</span>):
      ${K.agreed} agreed${nd?` · <span style="color:var(--red)">${nd} disputed</span> (checks keep deterministic)`:''}.</div>`;
  }

  // Gate 2 — lead with wrong margin
  const ag=d.findings.filter(f=>f.doc_type==='agent_notice');
  const bn=d.findings.filter(f=>f.doc_type==='borrowing_notice');
  const lead=ag.find(f=>f.breaks.some(b=>b.type==='wrong_applicable_margin'))
          || ag.find(f=>f.breaks.some(b=>b.type==='interest_miscalculation'));

  h+=`<h2 id="notices">Gate 2 &mdash; Notices recomputed</h2>
  <div class="lede">Detection vs planted defects:
    <b class="mono">${esc(det.score||'\u2014')}</b> caught.
    Arithmetic never goes through the model.</div>`;

  if(lead){
    const b=lead.breaks.find(x=>x.type==='interest_miscalculation')
          || lead.breaks[0];
    h+=`<div class="lead">
      <div class="eyebrow">Lead finding · ${esc(lead.file)}</div>
      <div class="btitle">${esc(b.type.replace(/_/g,' '))}
        <span class="bsec">§${esc(b.section)}</span></div>
      <div class="bdet">${esc(b.detail)}</div>`;
    if(b.type==='interest_miscalculation'){
      const mm=b.detail.match(/—\s*(.+?)\s*—\s*gives/);
      h+=`<div class="calc">
        ${mm?`<div class="formula mono">${esc(mm[1])}</div>`:''}
        <div class="row"><span class="lbl">Agent billed</span>
          <span class="val mono">${esc(b.actual)}</span></div>
        <div class="row"><span class="lbl">Altline computes</span>
          <span class="val mono ours">${esc(b.expected)}</span></div>
        <div class="row"><span class="lbl">Difference</span>
          <span class="val mono delta">${m2(Math.abs(b.impact))}</span></div>
      </div>`;
    }
    if(lead.seeded && lead.seeded!=='correct' && lead.seeded!=='clean')
      h+=`<div class="fix"><b>Seeded defect caught:</b> ${esc(lead.seeded)}</div>`;
    h+=`</div>`;
  }

  h+=`<h2 style="font-size:20px;margin-top:28px">Agent notices</h2>`;
  ag.forEach(f=>{ if(lead && f.file===lead.file) return; h+=card(f); });

  h+=`<h2 style="font-size:20px;margin-top:28px">Borrowing requests</h2>`;
  bn.forEach(f=>h+=card(f));

  h+=`<div class="honest">This agreement and these notices are synthetic &mdash;
    written to mirror structures worked with in production. Real credit agreements
    are confidential. Getting the first real one from a design partner is the next job.</div>`;

  document.getElementById('app').innerHTML=h;
}

function card(f){
  const bad=f.breaks.length>0;
  const worst=bad?(f.breaks.some(b=>b.severity==='critical')?'crit':'high'):'ok';
  const seeded=f.seeded && f.seeded!=='correct' && f.seeded!=='clean';
  let h=`<div class="notice">
    <div class="nhead">
      <span class="pill ${worst}">${bad?f.breaks.length+' finding'+(f.breaks.length>1?'s':''):'clean'}</span>
      ${seeded&&bad?`<span class="pill seed">seeded · caught</span>`:''}
      ${!bad&&(f.seeded==='clean'||f.seeded==='correct')?`<span class="pill ok">seeded clean</span>`:''}
      <span class="fn mono">${esc(f.file)}</span>
    </div>`;
  f.breaks.forEach(b=>{
    h+=`<div class="btitle">${esc(b.type.replace(/_/g,' '))}
      <span class="bsec">§${esc(b.section)}</span></div>
      <div class="bdet">${esc(b.detail)}</div>`;
    if(b.type==='interest_miscalculation'){
      const mm=b.detail.match(/—\s*(.+?)\s*—\s*gives/);
      h+=`<div class="calc">
        ${mm?`<div class="formula mono">${esc(mm[1])}</div>`:''}
        <div class="row"><span class="lbl">Agent billed</span>
          <span class="val mono">${esc(b.actual)}</span></div>
        <div class="row"><span class="lbl">Altline computes</span>
          <span class="val mono ours">${esc(b.expected)}</span></div>
        <div class="row"><span class="lbl">Difference</span>
          <span class="val mono delta">${m2(Math.abs(b.impact))}</span></div>
      </div>`;
    } else if(b.expected&&b.actual){
      h+=`<div class="calc">
        <div class="row"><span class="lbl">Agreement requires</span>
          <span class="val mono ours">${esc(b.expected)}</span></div>
        <div class="row"><span class="lbl">Notice says</span>
          <span class="val mono delta">${esc(b.actual)}</span></div>
      </div>`;
    }
    h+=`<div class="fix"><b>Fix:</b> ${esc(b.fix)}</div>`;
  });
  return h+'</div>';
}

if(!PUBLIC){
  runBtn.addEventListener('click',()=>{
    // If dropdown is still deterministic, pick first live provider.
    let p=providerSel.value;
    if(p==='deterministic'){
      const live=[...providerSel.options].map(o=>o.value)
        .find(v=>v!=='deterministic');
      if(live){ providerSel.value=live; p=live; }
    }
    run(true,p);
  });
  facilitySel.addEventListener('change',()=>run(true,'deterministic'));
}

loadOptions().then(()=>run(false,'deterministic')).catch(e=>{
  document.getElementById('app').innerHTML=
    '<div class="warn">Failed to load options: '+esc(e.message||e)+'</div>';
});
</script></body></html>
"""

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
