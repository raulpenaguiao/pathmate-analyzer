"""Build the Agent Journal Archive artifact page from journal_archive.md.

Usage: .venv/bin/python agents/kart/context/build_journal_page.py OUT.html
Each "# Agent journal: ..." section becomes one entry; newest (first) is open.
Republish OUT.html to the archive artifact URL in agents/kart/context/README.md.
"""
import html
import re
import sys
from pathlib import Path

ARCHIVE = Path(__file__).resolve().parents[1] / "journal_archive.md"

text = ARCHIVE.read_text()
parts = re.split(r"(?m)^(?=# Agent journal: )", text)
entries = []
for p in parts:
    if not p.startswith("# Agent journal: "):
        continue
    first, _, body = p.partition("\n")
    span = first.removeprefix("# Agent journal: ").strip()
    body = re.sub(r"\n-{3,}\s*$", "", body.strip())
    entries.append((span, body))

def block(i, span, body):
    safe = body.replace("</script", "<\\/script")
    is_open = " open" if i == 0 else ""
    tag = '<span class="tag">latest</span>' if i == 0 else ""
    return f"""<details class="entry"{is_open} id="d{len(entries)-i}">
  <summary><span class="span">{html.escape(span)}</span>{tag}</summary>
  <div class="md" data-src="md{i}"><pre class="raw">{html.escape(body)}</pre></div>
  <script type="text/markdown" id="md{i}">{safe}</script>
</details>"""

blocks = "\n".join(block(i, s, b) for i, (s, b) in enumerate(entries))

page = f"""<title>Agent Journal Archive</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
<style>
:root{{
  --paper:#f4f5f8; --surface:#ffffff; --ink:#18202b; --soft:#56617a;
  --line:#dce0e8; --accent:#2f5bb8; --accent-soft:#e7edf9; --code:#eef1f6;
}}
@media (prefers-color-scheme: dark){{
  :root:not([data-theme="light"]){{
    color-scheme:dark;
    --paper:#0f141b; --surface:#161d27; --ink:#e4e8ef; --soft:#9aa6ba;
    --line:#27303e; --accent:#86a4ff; --accent-soft:#1c2744; --code:#1d2531;
  }}
}}
:root[data-theme="dark"]{{
  color-scheme:dark;
  --paper:#0f141b; --surface:#161d27; --ink:#e4e8ef; --soft:#9aa6ba;
  --line:#27303e; --accent:#86a4ff; --accent-soft:#1c2744; --code:#1d2531;
}}
*{{box-sizing:border-box;}}
body{{background:var(--paper); color:var(--ink); font-family:"IBM Plex Sans",system-ui,sans-serif;
  font-size:15px; line-height:1.6; padding-inline:16px; padding-block:32px 56px;}}
.wrap{{max-width:780px; margin:0 auto; display:flex; flex-direction:column; gap:14px;}}
header{{display:flex; flex-direction:column; gap:6px; margin-bottom:10px;}}
.eyebrow{{font-family:"IBM Plex Mono",monospace; font-size:.72rem; letter-spacing:.1em; text-transform:uppercase; color:var(--accent); font-weight:600; margin:0;}}
h1{{font-size:clamp(1.5rem,1.2rem + 1.2vw,2rem); line-height:1.2; margin:0; text-wrap:balance;}}
.sub{{color:var(--soft); margin:0; max-width:62ch;}}
details.entry{{background:var(--surface); border:1px solid var(--line); border-radius:10px;}}
details.entry > summary{{cursor:pointer; list-style:none; display:flex; align-items:center; gap:10px; flex-wrap:wrap;
  padding:14px 18px; font-family:"IBM Plex Mono",monospace; font-size:.9rem; font-weight:600;}}
details.entry > summary::-webkit-details-marker{{display:none;}}
details.entry > summary::before{{content:"▸"; color:var(--soft); transition:transform .15s;}}
details.entry[open] > summary::before{{transform:rotate(90deg);}}
details.entry > summary:focus-visible{{outline:2px solid var(--accent); outline-offset:2px; border-radius:10px;}}
.tag{{font-size:.68rem; background:var(--accent-soft); color:var(--accent); padding:2px 8px; border-radius:99px; letter-spacing:.04em;}}
.md{{padding:0 22px 22px; border-top:1px solid var(--line);}}
.md h1{{display:none;}}
.md h2{{font-size:1.1rem; margin:28px 0 8px; padding-top:14px; border-top:1px solid var(--line);}}
.md h2:first-child{{border-top:0;}}
.md h3{{font-size:.95rem; margin:18px 0 6px;}}
.md p, .md li{{max-width:68ch;}}
.md ul, .md ol{{padding-left:22px;}}
.md li{{margin:3px 0;}}
.md code{{font-family:"IBM Plex Mono",monospace; font-size:.85em; background:var(--code); padding:1px 5px; border-radius:4px; overflow-wrap:anywhere;}}
.md a{{color:var(--accent); overflow-wrap:anywhere;}}
.md hr{{border:0; border-top:1px solid var(--line); margin:22px 0;}}
.md .tablewrap{{overflow-x:auto;}}
.md table{{border-collapse:collapse; font-size:.88rem; margin:10px 0;}}
.md th, .md td{{border:1px solid var(--line); padding:6px 10px; text-align:left; vertical-align:top;}}
.md th{{background:var(--code);}}
.raw{{white-space:pre-wrap; font-family:"IBM Plex Mono",monospace; font-size:.82rem;}}
footer{{color:var(--soft); font-size:.8rem; margin-top:14px;}}
@media (prefers-reduced-motion: reduce){{ details.entry > summary::before{{transition:none;}} }}
</style>

<div class="wrap">
  <header>
    <p class="eyebrow">pathmate-analyzer · compiled by Kart</p>
    <h1>Agent Journal Archive</h1>
    <p class="sub">Every daily digest of what the agents did, newest first. Each one covers the time since the one before it; open an entry to read it.</p>
  </header>
{blocks}
  <footer>{len(entries)} digests. Source: <code>agents/kart/journal_archive.md</code> in the repo.</footer>
</div>

<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script>
(function(){{
  if (!window.marked) return;
  document.querySelectorAll('.md[data-src]').forEach(function(el){{
    var src = document.getElementById(el.dataset.src);
    if (!src) return;
    el.innerHTML = marked.parse(src.textContent);
    el.querySelectorAll('table').forEach(function(t){{
      var w = document.createElement('div'); w.className = 'tablewrap';
      t.parentNode.insertBefore(w, t); w.appendChild(t);
    }});
  }});
}})();
</script>
"""
Path(sys.argv[1]).write_text(page)
print(f"{len(entries)} entries -> {sys.argv[1]}")
