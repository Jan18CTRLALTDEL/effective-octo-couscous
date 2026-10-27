"""Build the static site in site/ from the JSON in data/.

Stdlib only: `python build.py`, then open site/index.html.
Every page links back to its poe2db source.
"""
import html
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site")
POE2DB = "https://poe2db.tw/us/"

CSS = """body{font-family:system-ui,sans-serif;color:#000;background:#fff;max-width:960px;margin:0 auto;padding:16px;line-height:1.4}
a{color:#0645ad}h1,h2,h3{font-weight:bold}nav{margin-bottom:16px}
table{border-collapse:collapse;width:100%;margin:8px 0 24px}th,td{border:1px solid #999;padding:4px 6px;text-align:left;vertical-align:top}
th{font-weight:bold}td.n{text-align:right;white-space:nowrap}tr.out{color:#999}
.note{font-size:.9em}input{font-size:1em;padding:4px;margin:0 8px 8px 0}
.wrap{overflow-x:auto}"""

# Recomputes the Chance column for the chosen item level and filters by text.
JS = """function upd(){var lv=+document.getElementById('ilvl').value||100,q=document.getElementById('q').value.toLowerCase();
document.querySelectorAll('table.pool').forEach(function(t){var rows=t.querySelectorAll('tbody tr'),tot=0;
rows.forEach(function(r){if(+r.dataset.l<=lv)tot+=+r.dataset.w});
rows.forEach(function(r){var ok=+r.dataset.l<=lv,c=r.querySelector('.c');r.className=ok?'':'out';
c.textContent=ok&&tot?(100*r.dataset.w/tot).toFixed(2)+'%':'-';r.style.display=r.textContent.toLowerCase().indexOf(q)<0?'none':''});
t.parentNode.previousElementSibling.querySelector('.tot').textContent=tot});}
document.getElementById('ilvl').oninput=upd;document.getElementById('q').oninput=upd;upd();"""

SECTIONS = [
    ("mods", "Mod pools by base", "Modifiers"),
    ("currency", "Currency and crafting", "Currency"),
    ("bases", "Item bases", "Items"),
    ("gems", "Skills and support gems", "Gems"),
]


def esc(s):
    return html.escape(str(s))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def page(title, body, depth, src):
    up = "../" * depth
    links = " | ".join(f'<a href="{up}{k}/index.html">{esc(t)}</a>' for k, t, _ in SECTIONS)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>
<style>{CSS}</style></head><body>
<nav><a href="{up}index.html"><b>PoE2 Reference</b></a> | {links}</nav>
{body}
<p class="note">Source: <a href="{esc(src)}">{esc(src)}</a>. Game data belongs to Grinding Gear Games.</p>
</body></html>"""


def write(rel, text):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def pool_table(rows, side_name):
    """rows: (level, weight, family, text). Tiers count down from the highest level, so T1 is best."""
    fams = {}
    for r in rows:
        fams.setdefault(r[2], []).append(r)
    body = []
    for fam in sorted(fams):
        tiers = sorted(fams[fam], key=lambda r: -r[0])
        for n, (lvl, w, _, text) in enumerate(tiers, 1):
            body.append(
                f'<tr data-l="{lvl}" data-w="{w}"><td>{esc(fam)}</td><td class="n">T{n}</td>'
                f'<td>{esc(text).replace(chr(10), "<br>")}</td><td class="n">{lvl}</td>'
                f'<td class="n">{w}</td><td class="n c"></td></tr>')
    return (f'<h2>{side_name}</h2><p class="note">Total weight at this item level: <b class="tot"></b>. '
            f'Chance = mod weight / total weight.</p><div class="wrap"><table class="pool"><thead><tr>'
            f'<th>Family</th><th>Tier</th><th>Stat</th><th>Level</th><th>Weight</th><th>Chance</th>'
            f'</tr></thead><tbody>{"".join(body)}</tbody></table></div>')


def build_mods(data):
    mods = data["mods"]
    groups = {}
    for c in data["classes"]:
        groups.setdefault(c["g"], []).append(c)
        rows = {1: [], 2: []}
        for i in c["i"]:
            side, lvl, w, fam, text = mods[i]
            rows[side].append((lvl, w, fam, text))
        broken = ""
        if c["x"]:
            broken = ("<p class=\"note\">Left out because poe2db shows no real weight: "
                      + esc(", ".join(c["x"])) + ".</p>")
        body = (f'<h1>{esc(c["t"])}</h1><p class="note">{esc(data["src"])}. Normal pool only '
                f'(what Transmutation, Augmentation, Exalted and Chaos Orbs roll from).</p>'
                f'<label>Item level <input id="ilvl" type="number" value="82" min="1" max="100"></label>'
                f'<label>Filter <input id="q" type="search" placeholder="e.g. life"></label>{broken}'
                + pool_table(rows[1], "Prefixes") + pool_table(rows[2], "Suffixes")
                + f"<script>{JS}</script>")
        write(f'mods/{slug(c["h"])}.html', page(c["t"] + " mods", body, 1, POE2DB + c["h"]))
    parts = [f'<h1>Mod pools by base</h1><p class="note">{esc(data["src"])}. '
             f'{len(data["classes"])} item classes, {len(mods)} mods.</p>']
    for g, cs in groups.items():
        items = "".join(f'<li><a href="{slug(c["h"])}.html">{esc(c["t"])}</a> ({len(c["i"])} mods)</li>' for c in cs)
        parts.append(f"<h2>{esc(g)}</h2><ul>{items}</ul>")
    write("mods/index.html", page("Mod pools by base", "".join(parts), 1, POE2DB + "Modifiers"))
    return data["src"]


def build_stub(key, title, src_page):
    body = (f"<h1>{esc(title)}</h1><p>Not built yet. This section needs a scraper for "
            f'<a href="{POE2DB + src_page}">poe2db\'s {esc(src_page)} pages</a>, written against '
            f"the live page layout.</p>")
    write(f"{key}/index.html", page(title, body, 1, POE2DB + src_page))


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    status = {}
    with open(os.path.join(ROOT, "data", "moddata.json"), encoding="utf-8") as f:
        status["mods"] = build_mods(json.load(f))
    for key, title, src in SECTIONS:
        if key not in status:
            build_stub(key, title, src)
            status[key] = "not built yet"
    items = "".join(f'<li><a href="{k}/index.html">{esc(t)}</a>: {esc(status[k])}</li>' for k, t, _ in SECTIONS)
    body = (f"<h1>PoE2 Reference</h1><p>A personal crafting reference built from "
            f'<a href="{POE2DB}">poe2db.tw</a>. Numbers only; see poe2db for full details.</p><ul>{items}</ul>')
    write("index.html", page("PoE2 Reference", body, 0, POE2DB))
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    print("built", sum(len(fs) for _, _, fs in os.walk(OUT)), "files in site/")


if __name__ == "__main__":
    main()
