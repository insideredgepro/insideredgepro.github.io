#!/usr/bin/env python3
"""
Generate static per-politician SEO pages from data/trades-recent.json.

Outputs:
  politician/<slug>.html   one page per politician
  politician/index.html    directory of all tracked politicians
  politician/index.json    manifest {slug: name} used by congress.html to linkify names
  sitemap.xml              regenerated including all politician pages

Run from the repository root:  python3 generate_politician_pages.py
"""
import json
import re
import html as h
import pathlib
import datetime
import collections

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / 'data' / 'trades-recent.json'
OUT = ROOT / 'politician'
SITE = 'https://insideredgepro.github.io'
MAX_TRADES_PER_PAGE = 100


def slugify(name: str) -> str:
    s = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return s or 'unknown'


def esc(x) -> str:
    return h.escape(str(x if x is not None else ''), quote=True)


TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-BM57ZCD9G3"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-BM57ZCD9G3');</script>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="theme-color" content="#04080f" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <meta name="keywords" content="{keywords}" />
  <link rel="canonical" href="{url}" />
  <meta property="og:type" content="profile" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:url" content="{url}" />
  <meta name="twitter:card" content="summary" />
  <link rel="icon" href="/favicon.ico" />
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet" />
  <script type="application/ld+json">{person_ld}</script>
  <script type="application/ld+json">{breadcrumb_ld}</script>
  <style>
    :root {{ --bg:#04080f; --surf:#0a1220; --surf2:#0e1a2e; --border:rgba(255,255,255,.08);
      --cyan:#1abcdb; --cyan-b:#4dd0e1; --green:#10d98a; --red:#ef4444;
      --text:#e2eaf4; --text2:#7a97b8; --muted:#4d6470; --fm:'JetBrains Mono',monospace; }}
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background:var(--bg); color:var(--text); font-family:'DM Sans',sans-serif; min-height:100vh; }}
    a {{ color:var(--cyan); text-decoration:none; }}
    header {{ position:sticky; top:0; z-index:100; height:58px; display:flex; align-items:center; justify-content:space-between;
      padding:0 24px; background:rgba(4,8,15,.92); backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px);
      border-bottom:1px solid var(--border); }}
    .brand {{ display:flex; align-items:center; gap:10px; font-weight:700; font-size:15px; color:var(--text); }}
    .brand img {{ height:28px; width:28px; border-radius:50%; }}
    nav a {{ color:var(--text2); font-size:13px; margin-left:18px; }}
    nav a:hover {{ color:var(--text); }}
    .wrap {{ max-width:1100px; margin:0 auto; padding:36px 20px 60px; }}
    .crumbs {{ font-size:12px; color:var(--muted); margin-bottom:20px; }}
    .crumbs a {{ color:var(--text2); }}
    .pol-head {{ display:flex; align-items:flex-start; justify-content:space-between; gap:16px; flex-wrap:wrap; margin-bottom:8px; }}
    h1 {{ font-size:clamp(24px,4vw,34px); font-weight:700; letter-spacing:-.02em; }}
    .sub {{ color:var(--text2); font-size:14px; margin-top:6px; }}
    .tag {{ display:inline-block; font-size:11px; font-weight:600; padding:3px 10px; border-radius:999px; margin-right:6px; }}
    .tag-party {{ background:rgba(26,188,219,.12); color:var(--cyan-b); border:1px solid rgba(26,188,219,.3); }}
    .tag-chamber {{ background:rgba(139,92,246,.12); color:#b79bff; border:1px solid rgba(139,92,246,.3); }}
    .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin:26px 0; }}
    .stat {{ background:var(--surf); border:1px solid var(--border); border-radius:12px; padding:16px 18px; }}
    .stat-v {{ font-family:var(--fm); font-size:22px; font-weight:700; color:var(--cyan-b); }}
    .stat-l {{ font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; margin-top:4px; }}
    h2 {{ font-size:18px; margin:32px 0 14px; }}
    .table-wrap {{ overflow-x:auto; border:1px solid var(--border); border-radius:12px; background:var(--surf); }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; min-width:720px; }}
    th {{ text-align:left; font-size:10.5px; text-transform:uppercase; letter-spacing:.07em; color:var(--muted);
      padding:12px 14px; border-bottom:1px solid var(--border); background:var(--surf2); }}
    td {{ padding:11px 14px; border-bottom:1px solid rgba(255,255,255,.04); color:var(--text2); }}
    tr:last-child td {{ border-bottom:none; }}
    tr:hover td {{ background:rgba(255,255,255,.025); }}
    .tk {{ font-family:var(--fm); font-weight:700; color:var(--text); }}
    .buy {{ color:var(--green); font-weight:600; }}
    .sell {{ color:var(--red); font-weight:600; }}
    .mono {{ font-family:var(--fm); font-size:12px; }}
    .more-link {{ margin-top:22px; text-align:center; }}
    .btn {{ display:inline-block; background:var(--cyan); color:#04121a; font-weight:700; font-size:13.5px;
      padding:11px 26px; border-radius:10px; }}
    .iep-legal-disclaimer {{ max-width:1100px; margin:28px auto 8px; padding:14px 18px;
      border:1px solid rgba(240,180,60,.35); background:rgba(240,180,60,.07); border-radius:10px;
      font-size:12.5px; line-height:1.65; color:#d8c9a3; }}
    .iep-legal-disclaimer strong, .iep-legal-disclaimer a {{ color:#f0c060; }}
    footer {{ border-top:1px solid var(--border); padding:26px 20px; text-align:center;
      color:var(--muted); font-size:12px; }}
    footer a {{ color:var(--text2); margin:0 8px; }}
    @media (max-width:640px) {{ header {{ padding:0 14px; }} nav a {{ margin-left:10px; font-size:12px; }} }}
  </style>
</head>
<body>
<header>
  <a class="brand" href="/"><img src="/insideredge_logo_cyan_v2.png" alt="" />InsiderEdgePro</a>
  <nav>
    <a href="/us.html">US Insiders</a>
    <a href="/congress.html">Congress</a>
    <a href="/canada.html">Canada</a>
    <a href="/politician/">Politicians</a>
  </nav>
</header>
<div class="wrap">
  <div class="crumbs"><a href="/">Home</a> &rsaquo; <a href="/congress.html">Congress Trades</a> &rsaquo; {name}</div>
  <div class="pol-head">
    <div>
      <h1>{name} Trading Activity &amp; Stock Trades</h1>
      <p class="sub">{party} &middot; {chamber}{state_part} &middot; {trade_count} disclosed trades tracked</p>
    </div>
    <div>
      <span class="tag tag-party">{party}</span><span class="tag tag-chamber">{chamber}</span>
    </div>
  </div>

  <p class="sub" style="margin-top:14px;max-width:760px">
    Follow <strong>{name}&rsquo;s trading activity</strong> with the free InsiderEdgePro {name} stock trade tracker.
    Every stock purchase and sale disclosed by {name} under the STOCK Act is listed below &mdash;
    including tickers, amounts, filing dates, and who made the trade &mdash; updated daily as new filings appear.
  </p>

  <div class="stats">
    <div class="stat"><div class="stat-v">{trade_count}</div><div class="stat-l">Disclosed Trades</div></div>
    <div class="stat"><div class="stat-v">{buys}</div><div class="stat-l">Purchases</div></div>
    <div class="stat"><div class="stat-v">{sells}</div><div class="stat-l">Sales</div></div>
    <div class="stat"><div class="stat-v">{tickers}</div><div class="stat-l">Unique Tickers</div></div>
    <div class="stat"><div class="stat-v">{latest}</div><div class="stat-l">Latest Filing</div></div>
  </div>

  <h2>{name}&rsquo;s Recent STOCK Act Disclosures</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Published</th><th>Ticker</th><th>Asset</th><th>Type</th><th>Amount</th><th>Owner</th><th>Filed After</th></tr></thead>
      <tbody>
{rows}
      </tbody>
    </table>
  </div>

  <div class="more-link">
    <a class="btn" href="/congress.html">Track All Congress Trades Live &rarr;</a>
  </div>

  <div class="iep-legal-disclaimer">
    <strong>&#9878;&#65039; Legal Disclaimer:</strong> All trades shown are <strong>legal, publicly disclosed transactions</strong> filed under the U.S. STOCK Act. Inclusion of {name} on this site <strong>does not imply illegal insider trading or any wrongdoing</strong>. Content is for informational purposes only and is <strong>not financial advice</strong>. See our <a href="/terms.html">Terms</a>.
  </div>
</div>
<footer>
  <a href="/about.html">About</a><a href="/methodology.html">Methodology</a><a href="/privacy.html">Privacy</a><a href="/terms.html">Terms</a>
  <div style="margin-top:10px">&copy; {year} InsiderEdgePro. Data from public House &amp; Senate STOCK Act disclosures.</div>
</footer>
</body>
</html>
'''

INDEX_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-BM57ZCD9G3"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-BM57ZCD9G3');</script>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Politician Stock Trades — All Tracked Members of Congress | InsiderEdgePro</title>
  <meta name="description" content="Browse stock trades disclosed under the STOCK Act by {count} members of the U.S. Congress. Free, updated daily." />
  <link rel="canonical" href="{site}/politician/" />
  <link rel="icon" href="/favicon.ico" />
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    :root {{ --bg:#04080f; --surf:#0a1220; --border:rgba(255,255,255,.08); --cyan:#1abcdb; --text:#e2eaf4; --text2:#7a97b8; --muted:#4d6470; }}
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background:var(--bg); color:var(--text); font-family:'DM Sans',sans-serif; }}
    a {{ color:var(--cyan); text-decoration:none; }}
    header {{ position:sticky; top:0; z-index:100; height:58px; display:flex; align-items:center; justify-content:space-between;
      padding:0 24px; background:rgba(4,8,15,.92); backdrop-filter:blur(16px); border-bottom:1px solid var(--border); }}
    .brand {{ display:flex; align-items:center; gap:10px; font-weight:700; font-size:15px; color:var(--text); }}
    .brand img {{ height:28px; width:28px; border-radius:50%; }}
    nav a {{ color:var(--text2); font-size:13px; margin-left:18px; }}
    .wrap {{ max-width:1100px; margin:0 auto; padding:36px 20px 60px; }}
    h1 {{ font-size:clamp(24px,4vw,34px); letter-spacing:-.02em; margin-bottom:8px; }}
    .sub {{ color:var(--text2); font-size:14px; margin-bottom:28px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:12px; }}
    .card {{ display:block; background:var(--surf); border:1px solid var(--border); border-radius:12px; padding:16px 18px; transition:.2s; }}
    .card:hover {{ border-color:rgba(26,188,219,.4); transform:translateY(-2px); }}
    .card-n {{ font-weight:700; color:var(--text); font-size:15px; }}
    .card-m {{ color:var(--muted); font-size:12px; margin-top:4px; }}
    footer {{ border-top:1px solid var(--border); padding:26px 20px; text-align:center; color:var(--muted); font-size:12px; }}
    footer a {{ color:var(--text2); margin:0 8px; }}
  </style>
</head>
<body>
<header>
  <a class="brand" href="/"><img src="/insideredge_logo_cyan_v2.png" alt="" />InsiderEdgePro</a>
  <nav><a href="/us.html">US Insiders</a><a href="/congress.html">Congress</a><a href="/canada.html">Canada</a></nav>
</header>
<div class="wrap">
  <h1>Politician Stock Trades</h1>
  <p class="sub">{count} members of Congress with STOCK Act disclosures currently tracked &mdash; free, updated daily.</p>
  <div class="grid">
{cards}
  </div>
</div>
<footer>
  <a href="/about.html">About</a><a href="/methodology.html">Methodology</a><a href="/privacy.html">Privacy</a><a href="/terms.html">Terms</a>
  <div style="margin-top:10px">&copy; {year} InsiderEdgePro. Not financial advice.</div>
</footer>
</body>
</html>
'''


def main():
    trades = json.load(open(DATA, encoding='utf-8'))
    trades = [t for t in trades if t.get('politician_name')]
    by_pol = collections.defaultdict(list)
    for t in trades:
        by_pol[t['politician_name']].append(t)

    OUT.mkdir(exist_ok=True)
    manifest = {}
    today = datetime.date.today().isoformat()
    year = datetime.date.today().year

    for name, rows in sorted(by_pol.items()):
        slug = slugify(name)
        manifest[slug] = name
        rows = rows[:MAX_TRADES_PER_PAGE]
        party = rows[0].get('party', '')
        chamber = rows[0].get('chamber', '')
        state = rows[0].get('state', '')
        buys = sum(1 for t in rows if (t.get('transaction_type') or '').upper() == 'BUY')
        sells = sum(1 for t in rows if (t.get('transaction_type') or '').upper() == 'SELL')
        tickers = len({t.get('ticker') for t in rows if t.get('ticker')})
        latest = max((t.get('trade_published') or '' for t in rows), default='')
        state_part = f' &middot; {esc(state)}' if state else ''

        trs = []
        for t in rows:
            typ = (t.get('transaction_type') or '').upper()
            cls = 'buy' if typ == 'BUY' else ('sell' if typ == 'SELL' else '')
            trs.append(
                '        <tr>'
                f'<td class="mono">{esc(t.get("trade_published") or "—")}</td>'
                f'<td class="tk">{esc(t.get("ticker") or "—")}</td>'
                f'<td>{esc((t.get("company") or "")[:40])}</td>'
                f'<td class="{cls}">{esc(typ or "—")}</td>'
                f'<td class="mono">{esc(t.get("amount") or "—")}</td>'
                f'<td>{esc(t.get("owner") or "—")}</td>'
                f'<td class="mono">{esc(str(t.get("filed_after_days") or "—") + ("d" if t.get("filed_after_days") else ""))}</td>'
                '</tr>'
            )

        url = f'{SITE}/politician/{slug}.html'
        title = f'{name} Trading Activity & Stock Trade Tracker | InsiderEdgePro'
        desc = (f'Track {name}\'s trading activity in real time — {name} stock trades, purchases and sales '
                f'disclosed under the STOCK Act. {len(rows)} recent trades across {tickers} tickers '
                f'({buys} buys, {sells} sells). Free {name} trade tracker, updated daily.')
        keywords = (f'{name} trading activity, {name} stock trades, {name} trade tracker, '
                    f'{name} stock tracker, {name} STOCK Act, {name} insider trades, '
                    f'{name} portfolio, {name} congress trades, politician stock tracker, '
                    f'congressional stock trades')

        person_ld = json.dumps({
            '@context': 'https://schema.org', '@type': 'Person', 'name': name,
            'jobTitle': f'U.S. {chamber}'.strip(), 'affiliation': party,
            'description': f'{name} trading activity and stock trade tracker — STOCK Act disclosures.',
        })
        breadcrumb_ld = json.dumps({
            '@context': 'https://schema.org', '@type': 'BreadcrumbList',
            'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE + '/'},
                {'@type': 'ListItem', 'position': 2, 'name': 'Congress Trades', 'item': SITE + '/congress.html'},
                {'@type': 'ListItem', 'position': 3, 'name': name, 'item': url},
            ]})

        page = TEMPLATE.format(
            title=esc(title), desc=esc(desc), keywords=esc(keywords), url=url, name=esc(name),
            party=esc(party), chamber=esc(chamber), state_part=state_part,
            trade_count=len(rows), buys=buys, sells=sells, tickers=tickers,
            latest=esc(latest), rows='\n'.join(trs), year=year,
            person_ld=person_ld, breadcrumb_ld=breadcrumb_ld)
        (OUT / f'{slug}.html').write_text(page, encoding='utf-8')

    # index page
    cards = []
    for slug, name in sorted(manifest.items(), key=lambda kv: kv[1]):
        rows = by_pol[name]
        cards.append(
            f'    <a class="card" href="/politician/{slug}.html">'
            f'<div class="card-n">{esc(name)}</div>'
            f'<div class="card-m">{esc(rows[0].get("party",""))} &middot; {esc(rows[0].get("chamber",""))} &middot; {len(rows)} trades</div></a>')
    (OUT / 'index.html').write_text(INDEX_TEMPLATE.format(
        count=len(manifest), site=SITE, cards='\n'.join(cards), year=year), encoding='utf-8')

    # manifest for congress.html linkification
    (OUT / 'index.json').write_text(json.dumps(manifest, indent=1), encoding='utf-8')

    # rebuild sitemap with politician pages included
    static_pages = [
        ('/', '1.0', 'hourly'), ('/us.html', '0.98', 'hourly'),
        ('/congress.html', '0.95', 'hourly'), ('/canada.html', '0.95', 'hourly'),
        ('/performance.html', '0.8', 'daily'), ('/politician/', '0.85', 'daily'),
        ('/nancy-pelosi-stock-tracker.html', '0.9', 'daily'),
        ('/about.html', '0.4', 'monthly'), ('/methodology.html', '0.4', 'monthly'),
        ('/privacy.html', '0.2', 'yearly'), ('/terms.html', '0.2', 'yearly'),
    ]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, pri, freq in static_pages:
        lines.append(f'  <url><loc>{SITE}{loc}</loc><lastmod>{today}</lastmod>'
                     f'<changefreq>{freq}</changefreq><priority>{pri}</priority></url>')
    for slug in sorted(manifest):
        lines.append(f'  <url><loc>{SITE}/politician/{slug}.html</loc><lastmod>{today}</lastmod>'
                     f'<changefreq>daily</changefreq><priority>0.7</priority></url>')
    lines.append('</urlset>')
    (ROOT / 'sitemap.xml').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print(f'Generated {len(manifest)} politician pages + index + sitemap ({len(static_pages)+len(manifest)} URLs)')


if __name__ == '__main__':
    main()
