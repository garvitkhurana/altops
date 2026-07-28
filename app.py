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
    providers = pipeline.available_providers()
    default_provider = pipeline._provider() or "deterministic"
    return JSONResponse({
        "facilities": facilities,
        "providers": providers,
        "default_facility": facilities[0]["id"] if facilities else None,
        "default_provider": default_provider,
    })


@app.get("/api/run")
async def api_run(refresh: bool = False, provider: str = None, facility_id: str = None):
    import asyncio
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
    return HTML


HTML = r"""
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Altline</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
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
  padding:18px 28px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;
  border-bottom:1px solid var(--line);background:rgba(255,252,247,.72);
  backdrop-filter:blur(8px);position:sticky;top:0;z-index:5;
}
.brand{font-family:Fraunces,Georgia,serif;font-size:28px;font-weight:650;
  letter-spacing:-.6px;line-height:1}
.tagline{color:var(--muted);font-size:13px;max-width:280px}
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
.hero .eyebrow{font-size:12px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);font-weight:600;margin-bottom:14px}
.hero .big{font-family:Fraunces,Georgia,serif;font-size:clamp(48px,9vw,76px);
  font-weight:650;letter-spacing:-2.5px;color:var(--red);line-height:.95}
.hero .cap{margin-top:14px;font-size:18px;max-width:34em;color:var(--ink)}
.hero .sub{margin-top:12px;color:var(--muted);font-size:13.5px}

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
  header{align-items:flex-start}
  .controls{margin-left:0;width:100%}
}
</style></head><body>
<header>
  <div>
    <div class="brand">Altline</div>
    <div class="tagline">We audit private credit agents&rsquo; math</div>
  </div>
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
const esc=s=>String(s==null?'':s).replace(/[<>&]/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]));
const m2=n=>n==null?'&mdash;':'$'+Number(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const m0=n=>n==null?'&mdash;':'$'+Number(n).toLocaleString('en-US',{maximumFractionDigits:0});

const facilitySel=document.getElementById('facility');
const providerSel=document.getElementById('provider');
const runBtn=document.getElementById('runBtn');

function setBusy(b,label){
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
  if(X.mode==='llm+deterministic'){
    el.textContent='live · '+(X.provider||'model')+' + engine';
    el.className='mode live';
  }else if(X.attempted && X.attempted!=='deterministic'){
    el.textContent=X.attempted+' failed · deterministic';
  }else el.textContent='deterministic parser';

  let h='';
  h+=`<section class="hero">
    <div class="eyebrow">${esc(F.borrower||'Facility')} · ${m0(s.total_commitments)} senior facility</div>
    <div class="big mono">${m2(s.interest_impact)}</div>
    <div class="cap">of interest mispriced across ${s.mispriced_notices} of 4 agent
      notices &mdash; in a single interest period, on one facility.</div>
    <div class="sub">${s.total_breaks} findings · ${s.critical} critical · ${s.high} high ·
      ${m0(s.availability_breach)} availability breach · leverage ${s.leverage}x</div>
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
  h+=`<h2>Gate 1 &mdash; Agreement, compiled</h2>
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

  h+=`<h2>Gate 2 &mdash; Notices recomputed</h2>
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

loadOptions().then(()=>run(false,'deterministic')).catch(e=>{
  document.getElementById('app').innerHTML=
    '<div class="warn">Failed to load options: '+esc(e.message||e)+'</div>';
});
</script></body></html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
