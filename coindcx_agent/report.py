"""Self-contained HTML backtest report (inline SVG, no external scripts)."""

from __future__ import annotations

import html
import json

import pandas as pd

from .backtest import BacktestResult

MAX_POINTS = 600


def _series(s: pd.Series) -> list[list]:
    step = max(1, len(s) // MAX_POINTS)
    s = s.iloc[::step]
    return [[int(t.timestamp() * 1000), round(float(v), 4)] for t, v in s.items()]


def write_report(path: str, res: BacktestResult, strategy, symbol: str, cfg) -> None:
    m = res.metrics
    eq, bh = res.equity, res.benchmark
    data = {
        "equity": _series(eq),
        "bh": _series(bh),
        "dd": _series((eq / eq.cummax() - 1) * 100),
        "bhdd": _series((bh / bh.cummax() - 1) * 100),
    }
    pct = lambda x: f"{x:.1%}"  # noqa: E731
    num = lambda x: f"{x:,.2f}"  # noqa: E731
    rows = [
        ("Total return", pct(m["total_return"]), pct(m["bh_total_return"])),
        ("After estimated tax", pct(m["after_tax_return"]), "—"),
        ("CAGR", pct(m["cagr"]), pct(m["bh_cagr"])),
        ("Sharpe", num(m["sharpe"]), num(m["bh_sharpe"])),
        ("Max drawdown", pct(m["max_drawdown"]), pct(m["bh_max_drawdown"])),
        ("Time in market", pct(m["exposure"]), "100%"),
        ("Round trips", str(m["trades"]), "1"),
        ("Win rate", pct(m["win_rate"]), "—"),
        ("Fees + GST", num(m["fees"]), "—"),
        ("TDS withheld (creditable)", num(m["tds_withheld"]), "—"),
        ("Estimated tax on gains", num(m["est_tax"]), "—"),
    ]
    table = "\n".join(f"<tr><th scope='row'>{html.escape(a)}</th><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
    c = cfg.costs
    subtitle = (f"{symbol} · {strategy.interval} candles · {eq.index[0].date()} → {eq.index[-1].date()} · "
                f"fee {c.fee_pct}% + GST, spread {c.spread_pct}%, slippage {c.slippage_pct}%")
    doc = TEMPLATE.replace("__TITLE__", html.escape(f"{strategy.name} backtest")) \
        .replace("__SUB__", html.escape(subtitle)) \
        .replace("__PARAMS__", html.escape(json.dumps(strategy.params(), default=str))) \
        .replace("__TABLE__", table) \
        .replace("__DATA__", json.dumps(data))
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{color-scheme:light;--bg:#fcfcfb;--card:#ffffff;--text:#0b0b0b;--text2:#52514e;--muted:#8a8984;--grid:#e8e7e3;
--s1:#2a78d6;--s2:#eb6834;--border:#e3e2de}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#1a1a19;--card:#222221;
--text:#f0efec;--text2:#c3c2b7;--muted:#8f8e86;--grid:#33332f;--s1:#3987e5;--s2:#d95926;--border:#3a3a36}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#1a1a19;--card:#222221;--text:#f0efec;--text2:#c3c2b7;--muted:#8f8e86;
--grid:#33332f;--s1:#3987e5;--s2:#d95926;--border:#3a3a36}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 48px}h1{font-size:22px;margin:0 0 4px}
.sub{color:var(--text2);margin:0 0 4px}.params{color:var(--muted);font:12px ui-monospace,monospace;margin:0 0 20px;word-break:break-all}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;margin:0 0 16px}
h2{font-size:15px;margin:0 0 8px}.legend{display:flex;gap:16px;color:var(--text2);font-size:13px;margin:0 0 6px;flex-wrap:wrap}
.legend i{display:inline-block;width:14px;height:2px;vertical-align:middle;margin-right:6px}
.chart{position:relative}svg{display:block;width:100%;height:auto;overflow:visible}
.tip{position:absolute;pointer-events:none;background:var(--card);border:1px solid var(--border);border-radius:6px;
padding:6px 8px;font-size:12px;color:var(--text);box-shadow:0 2px 8px #0002;display:none;white-space:nowrap}
.tip b{font-weight:600}.tip .k{color:var(--text2)}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:6px 8px;border-bottom:1px solid var(--border);text-align:right}
th[scope=row]{text-align:left;font-weight:500;color:var(--text2)}thead th{color:var(--text2);font-weight:600}
.note{color:var(--muted);font-size:12px;margin-top:8px}
</style></head><body><main>
<h1>__TITLE__</h1><p class="sub">__SUB__</p><p class="params">params: __PARAMS__</p>
<section class="card"><h2>Equity</h2>
<div class="legend"><span><i style="background:var(--s1)"></i>Strategy</span><span><i style="background:var(--s2)"></i>Buy &amp; hold</span></div>
<div class="chart" id="c1"></div></section>
<section class="card"><h2>Drawdown from peak (%)</h2>
<div class="legend"><span><i style="background:var(--s1)"></i>Strategy</span><span><i style="background:var(--s2)"></i>Buy &amp; hold</span></div>
<div class="chart" id="c2"></div></section>
<section class="card"><h2>Results</h2>
<table><thead><tr><th></th><th>Strategy</th><th>Buy &amp; hold</th></tr></thead><tbody>__TABLE__</tbody></table>
<p class="note">Backtests are not predictions. Tax figures are a rough estimate under India's VDA rules (30% + cess on each gain,
no loss set-off, no fee deduction); buy &amp; hold is shown before tax because it is only taxed when sold. Not tax advice.</p>
</section></main>
<script>
const D=__DATA__;
const fmtD=t=>new Date(t).toISOString().slice(0,10);
const fmtN=v=>Math.abs(v)>=1e5?v.toLocaleString(undefined,{maximumFractionDigits:0}):v.toLocaleString(undefined,{maximumFractionDigits:2});
function chart(el,a,b,unit){
  const W=940,H=300,L=64,R=96,T=10,B=28,box=document.getElementById(el);
  const all=a.concat(b),x0=a[0][0],x1=a[a.length-1][0];
  let y0=Math.min(...all.map(p=>p[1])),y1=Math.max(...all.map(p=>p[1]));if(unit==='%'){y1=Math.max(0,y1)}
  const pad=(y1-y0)*0.06||1;y0-=pad;y1+=unit==='%'?0:pad;
  const X=t=>L+(t-x0)/(x1-x0)*(W-L-R),Y=v=>T+(y1-v)/(y1-y0)*(H-T-B);
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  svg.setAttribute('role','img');svg.setAttribute('aria-label',el==='c1'?'Equity curve, strategy vs buy and hold':'Drawdown, strategy vs buy and hold');
  const raw=(y1-y0)/4,mag=10**Math.floor(Math.log10(raw)),st=[1,2,2.5,5,10].map(k=>k*mag).find(k=>k>=raw);
  let g='';for(let v=Math.ceil(y0/st)*st;v<=y1+1e-9;v+=st){const y=Y(v);
    g+=`<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" stroke="var(--grid)" stroke-width="1"/><text x="${L-8}" y="${y+4}" text-anchor="end" font-size="11" fill="var(--muted)">${fmtN(v)}${unit}</text>`}
  for(let i=0;i<=4;i++){const t=x0+(x1-x0)*i/4;g+=`<text x="${X(t)}" y="${H-8}" text-anchor="middle" font-size="11" fill="var(--muted)">${fmtD(t)}</text>`}
  const path=s=>s.map((p,i)=>(i?'L':'M')+X(p[0]).toFixed(1)+','+Y(p[1]).toFixed(1)).join('');
  const la=a[a.length-1],lb=b[b.length-1];let ya=Y(la[1]),yb=Y(lb[1]);if(Math.abs(ya-yb)<14){if(ya<yb){ya-=7;yb+=7}else{ya+=7;yb-=7}}
  g+=`<path d="${path(b)}" fill="none" stroke="var(--s2)" stroke-width="2" stroke-linejoin="round"/>`;
  g+=`<path d="${path(a)}" fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round"/>`;
  g+=`<text x="${W-R+8}" y="${ya+4}" font-size="12" fill="var(--text)">Strategy</text><text x="${W-R+8}" y="${yb+4}" font-size="12" fill="var(--text2)">Buy &amp; hold</text>`;
  g+=`<line id="${el}x" y1="${T}" y2="${H-B}" stroke="var(--muted)" stroke-width="1" visibility="hidden"/>`;
  g+=`<circle id="${el}a" r="4" fill="var(--s1)" stroke="var(--card)" stroke-width="2" visibility="hidden"/><circle id="${el}b" r="4" fill="var(--s2)" stroke="var(--card)" stroke-width="2" visibility="hidden"/>`;
  g+=`<rect x="${L}" y="${T}" width="${W-L-R}" height="${H-T-B}" fill="transparent" id="${el}h"/>`;
  svg.innerHTML=g;box.appendChild(svg);
  const tip=document.createElement('div');tip.className='tip';box.appendChild(tip);
  const hit=svg.getElementById(el+'h'),cx=svg.getElementById(el+'x'),ca=svg.getElementById(el+'a'),cb=svg.getElementById(el+'b');
  const near=(s,t)=>{let lo=0,hi=s.length-1;while(hi-lo>1){const m=(lo+hi)>>1;s[m][0]<t?lo=m:hi=m}return Math.abs(s[lo][0]-t)<Math.abs(s[hi][0]-t)?s[lo]:s[hi]};
  function move(ev){const r=svg.getBoundingClientRect(),sx=(ev.clientX-r.left)/r.width*W,t=x0+(sx-L)/(W-L-R)*(x1-x0);
    const pa=near(a,t),pb=near(b,t);[cx,ca,cb].forEach(e=>e.setAttribute('visibility','visible'));
    cx.setAttribute('x1',X(pa[0]));cx.setAttribute('x2',X(pa[0]));ca.setAttribute('cx',X(pa[0]));ca.setAttribute('cy',Y(pa[1]));cb.setAttribute('cx',X(pb[0]));cb.setAttribute('cy',Y(pb[1]));
    tip.innerHTML=`<b>${fmtD(pa[0])}</b><br><span class="k">Strategy</span> ${fmtN(pa[1])}${unit}<br><span class="k">Buy &amp; hold</span> ${fmtN(pb[1])}${unit}`;
    tip.style.display='block';const px=X(pa[0])/W*r.width;tip.style.left=Math.min(px+12,r.width-tip.offsetWidth-4)+'px';tip.style.top='8px'}
  hit.addEventListener('pointermove',move);hit.addEventListener('pointerleave',()=>{tip.style.display='none';[cx,ca,cb].forEach(e=>e.setAttribute('visibility','hidden'))});
}
chart('c1',D.equity,D.bh,'');chart('c2',D.dd,D.bhdd,'%');
</script></body></html>
"""
