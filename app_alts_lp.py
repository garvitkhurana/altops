"""
Alt-ops autopilot -- demo server.

    pip install fastapi uvicorn anthropic pypdf reportlab
    python generate_corpus.py          # build the sample GP document set
    export ANTHROPIC_API_KEY=sk-...    # optional; without it the offline
                                       # deterministic parser runs instead
    python app.py                      # -> http://localhost:8000
"""

import json
import os
from datetime import date

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

import pipeline

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "corpus")

app = FastAPI(title="alt-ops autopilot")
_cache = {}


def run():
    if "data" not in _cache:
        results = pipeline.process_dir(CORPUS)
        recon = pipeline.reconcile(results, today=date(2026, 7, 27))

        # Migration reconciliation: the legacy system's view vs. the documents.
        import legacy_export
        import migration
        legacy_export.build()
        mig = migration.reconcile_migration(
            migration.load_legacy(), recon, results)

        _cache["data"] = {
            "results": results,
            "reconciliation": recon,
            "migration": mig,
            "summary": pipeline.summarize(results, recon),
        }
    return _cache["data"]


@app.get("/api/run")
def api_run(refresh: bool = False):
    if refresh:
        _cache.pop("data", None)
    return JSONResponse(json.loads(json.dumps(run(), default=str)))


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML


HTML = r"""
<!doctype html><html><head><meta charset="utf-8">
<title>alt-ops autopilot</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#0d1117;color:#e6edf3;
  font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{padding:22px 30px;border-bottom:1px solid #21262d;display:flex;
  align-items:baseline;gap:14px;flex-wrap:wrap}
h1{font-size:17px;margin:0;font-weight:650;letter-spacing:-.2px}
.sub{color:#7d8590;font-size:12.5px}
.mode{margin-left:auto;font-size:11px;padding:4px 10px;border-radius:20px;
  border:1px solid #30363d;color:#7d8590}
.mode.live{color:#3fb950;border-color:#238636}
main{padding:24px 30px;max-width:1240px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));
  gap:12px;margin-bottom:26px}
.kpi{background:#161b22;border:1px solid #21262d;border-radius:9px;padding:14px 16px}
.kpi .v{font-size:25px;font-weight:640;letter-spacing:-.6px}
.kpi .l{color:#7d8590;font-size:11.5px;margin-top:3px}
.g{color:#3fb950}.r{color:#f85149}.y{color:#d29922}.b{color:#58a6ff}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.7px;color:#7d8590;
  margin:30px 0 11px;font-weight:600}
table{width:100%;border-collapse:collapse;background:#161b22;
  border:1px solid #21262d;border-radius:9px;overflow:hidden}
th{text-align:left;padding:9px 13px;font-size:11px;text-transform:uppercase;
  letter-spacing:.5px;color:#7d8590;border-bottom:1px solid #21262d;font-weight:600}
td{padding:9px 13px;border-bottom:1px solid #1c2128;font-size:13px;
  vertical-align:top}
tr:last-child td{border-bottom:none}
.num{text-align:right;font-variant-numeric:tabular-nums;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px}
.pill{display:inline-block;padding:1.5px 8px;border-radius:20px;font-size:11px;
  font-weight:560}
.pill.ok{background:#12261a;color:#3fb950}
.pill.exc{background:#2d1416;color:#f85149}
.pill.soon{background:#2b2213;color:#d29922}
.reason{color:#f85149;font-size:12px}
.note{color:#7d8590;font-size:12px}
.muted{color:#7d8590}
details{background:#161b22;border:1px solid #21262d;border-radius:9px;
  padding:10px 14px;margin-bottom:7px}
summary{cursor:pointer;font-size:13px;display:flex;gap:10px;align-items:center}
summary::-webkit-details-marker{display:none}
summary:before{content:"\25B8";color:#7d8590;font-size:10px}
details[open] summary:before{content:"\25BE"}
.fname{font-family:ui-monospace,monospace;font-size:12px}
.fields{margin-top:11px;display:grid;
  grid-template-columns:minmax(150px,auto) minmax(110px,auto) 58px 1fr;
  gap:5px 14px;font-size:12px;align-items:baseline}
.fields .k{color:#7d8590}
.fields .q{color:#6e7681;font-style:italic;font-size:11.5px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.conf{font-family:ui-monospace,monospace;font-size:11px}
.chk{font-size:12px;margin-top:9px;padding-top:9px;border-top:1px solid #21262d}
.chk div{margin:2.5px 0}
.loading{padding:60px;text-align:center;color:#7d8590}
.bar{height:5px;background:#21262d;border-radius:3px;overflow:hidden;margin-top:8px}
.bar i{display:block;height:100%;background:#3fb950}
.warn{background:#1c1710;border:1px solid #3d2f11;color:#d29922;padding:10px 14px;
  border-radius:8px;font-size:12.5px;margin-bottom:20px}
</style></head><body>
<header>
  <h1>alt-ops autopilot</h1>
  <span class="sub">Ridgeline Family Office LP &mdash; portfolio migration reconciliation</span>
  <span class="mode" id="mode">&mdash;</span>
</header>
<main id="app"><div class="loading">Processing document set&hellip;</div></main>
<script>
const f0=n=>n==null?'&mdash;':n.toLocaleString('en-US',{maximumFractionDigits:0});
const esc=s=>String(s==null?'':s).replace(/[<>&]/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]));

fetch('/api/run').then(r=>r.json()).then(d=>{
  const s=d.summary, R=d.reconciliation;
  document.getElementById('mode').textContent =
    s.live_llm ? 'live · '+s.model : 'offline deterministic parser';
  if(s.live_llm) document.getElementById('mode').className='mode live';

  let h='';
  if(!s.live_llm) h+=`<div class="warn"><b>Offline mode.</b> Running the
    deterministic regex fallback, not the model. It only handles label phrasings
    it has already seen &mdash; which is precisely why rules-based extraction
    loses here. Set <code>ANTHROPIC_API_KEY</code> and reload for the real path.</div>`;

  const M=d.migration, ms=M.summary;
  h+=`<div class="kpis">
    <div class="kpi"><div class="v r">${ms.total_breaks}</div>
      <div class="l">migration breaks found</div></div>
    <div class="kpi"><div class="v r">$${f0(ms.cash_at_risk)}</div>
      <div class="l">misstated if loaded as-is</div></div>
    <div class="kpi"><div class="v">${s.documents}</div><div class="l">documents ingested</div></div>
    <div class="kpi"><div class="v g">${s.straight_through_rate}%</div>
      <div class="l">straight-through, no human touch</div>
      <div class="bar"><i style="width:${s.straight_through_rate}%"></i></div></div>
    <div class="kpi"><div class="v ${s.checks_failed?'r':'g'}">${s.checks_run-s.checks_failed}/${s.checks_run}</div>
      <div class="l">arithmetic checks passed</div></div>
  </div>`;

  // ---- migration reconciliation: the headline view ----
  h+=`<h2>Migration reconciliation &mdash; legacy export vs. source documents</h2>`;
  h+=`<div class="note" style="margin-bottom:11px">
    ${ms.legacy_positions} positions in the legacy export ·
    ${ms.document_positions} reconstructed from documents ·
    ${ms.matched} matched ·
    <span class="r">${ms.critical} critical</span>,
    <span class="y">${ms.high} high</span>,
    ${ms.medium} medium.
    A loader would have carried every one of these into the new system.</div>`;
  M.breaks.forEach(b=>{
    const sev=b.severity==='critical'?'exc':b.severity==='high'?'exc':'soon';
    h+=`<details><summary>
      <span class="pill ${sev}">${esc(b.severity)}</span>
      <span>${esc(b.fund||b.legacy_fund)}</span>
      <span class="muted">${esc(b.type)}</span></summary>
      <div style="margin-top:9px;font-size:13px">${esc(b.detail)}</div>`;
    if(b.legacy_value!=null||b.document_value!=null){
      h+=`<div class="fields" style="grid-template-columns:150px 1fr">
        <div class="k">legacy system</div><div class="num">${f0(b.legacy_value)}</div>
        <div class="k">documents say</div><div class="num">${f0(b.document_value)}</div>`;
      if(b.delta!=null) h+=`<div class="k">delta</div><div class="num r">${f0(b.delta)}</div>`;
      h+='</div>';}
    if(b.evidence&&b.evidence.length)
      h+=`<div class="chk"><span class="muted">evidence:</span>
        <span class="fname">${b.evidence.map(esc).join(', ')}</span></div>`;
    h+=`<div class="chk"><span class="g">fix:</span> ${esc(b.fix)}</div></details>`;});

  h+='<h2>Cash calendar &mdash; capital calls coming due</h2>';
  h+='<table><tr><th>Due</th><th>In</th><th>Fund</th><th class="num">Amount</th><th>Source</th></tr>';
  if(!R.calendar.length) h+='<tr><td colspan=5 class="muted">No upcoming calls.</td></tr>';
  R.calendar.forEach(c=>{
    h+=`<tr><td>${c.due}</td>
      <td><span class="pill ${c.days<=7?'soon':'ok'}">${c.days}d</span></td>
      <td>${esc(c.fund)}</td>
      <td class="num">${c.currency} ${f0(c.amount)}</td>
      <td class="fname muted">${esc(c.file)}</td></tr>`;});
  h+='</table>';

  h+='<h2>Position ledger</h2>';
  h+=`<table><tr><th>Fund</th><th class="num">Commitment</th><th class="num">Called</th>
    <th class="num">%</th><th class="num">Unfunded</th><th class="num">Distributed</th>
    <th class="num">NAV</th><th>Breaks</th></tr>`;
  R.positions.forEach(p=>{
    h+=`<tr><td>${esc(p.fund)}<div class="note">${esc(p.manager||'')}</div></td>
      <td class="num">${f0(p.commitment)}</td>
      <td class="num">${f0(p.called)}</td>
      <td class="num">${p.pct_called==null?'&mdash;':p.pct_called+'%'}</td>
      <td class="num">${f0(p.unfunded)}</td>
      <td class="num">${f0(p.distributed)}</td>
      <td class="num">${f0(p.latest_nav)}<div class="note">${p.nav_date||''}</div></td>
      <td class="reason">${p.breaks.map(esc).join('<br>')||'<span class="pill ok">clean</span>'}</td>
      </tr>`;});
  h+='</table>';

  const exc=d.results.filter(r=>r.triage.status==='exception');
  h+=`<h2>Exception queue &mdash; ${exc.length} items need a human</h2>`;
  exc.forEach(r=>h+=card(r));

  h+=`<h2>Auto-posted &mdash; ${d.results.length-exc.length} items</h2>`;
  d.results.filter(r=>r.triage.status!=='exception').forEach(r=>h+=card(r));

  document.getElementById('app').innerHTML=h;
});

function card(r){
  const bad=r.triage.status==='exception';
  let h=`<details><summary>
    <span class="pill ${bad?'exc':'ok'}">${bad?'exception':'auto'}</span>
    <span class="fname">${esc(r.file)}</span>
    <span class="muted">${esc(r.doc_type)}</span>`;
  if(bad) h+=`<span class="reason">${r.triage.reasons.map(esc).join(' · ')}</span>`;
  h+='</summary><div class="fields">';
  Object.entries(r.fields||{}).forEach(([k,v])=>{
    const c=v.confidence||0;
    const col=c>=0.8?'g':c>=0.5?'y':'r';
    h+=`<div class="k">${esc(k)}</div>
        <div>${v.value==null?'<span class="r">not found</span>':esc(v.value)}</div>
        <div class="conf ${col}">${(c*100).toFixed(0)}%</div>
        <div class="q" title="${esc(v.quote)}">${esc(v.quote)}</div>`;});
  h+='</div>';
  if(r.checks&&r.checks.length){
    h+='<div class="chk">';
    r.checks.forEach(c=>{
      const col=c.status==='FAIL'?'r':c.status==='pass'?'g':'muted';
      h+=`<div><span class="${col}">${c.status==='pass'?'✓':c.status==='FAIL'?'✗':'–'}</span>
        ${esc(c.check)} <span class="muted">${esc(c.detail)}</span></div>`;});
    h+='</div>';}
  if(r.notes) h+=`<div class="chk note">${r.notes.map(esc).join('<br>')}</div>`;
  return h+'</details>';
}
</script></body></html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
