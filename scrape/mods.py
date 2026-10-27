"""Pull base-pool modifier weights from poe2db.tw for every equipment class.

Only the "normal" pool is kept (what transmutes, augments, exalts and chaos
orbs roll from). Desecrated, essence, corrupted, rune/socketable and other
special pools live in separate lists on poe2db and are ignored.

Mods whose weight is missing or a placeholder (1) are dropped and recorded
per class so the app can warn about them.
"""
import html
import json
import re
import time
import urllib.request

BASE = "https://poe2db.tw/us/"
UA = "Mozilla/5.0 (poe2-reference-site; personal use)"
SKIP_GROUPS = {"Flasks"}


def _get(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _strip(h):
    h = re.sub(r"<br\s*/?>", "\n", str(h))
    t = html.unescape(re.sub(r"<[^>]+>", "", h))
    return t.replace("—", "-").strip()


def list_classes(index_html):
    out, cur = [], None
    for m in re.finditer(r'<span class="disabled">(.*?)</span>|href="/us/([^"#]+)#ModifiersCalc"[^>]*>(.*?)</a>', index_html):
        if m.group(1):
            cur = _strip(m.group(1))
        else:
            out.append((cur, m.group(2), _strip(m.group(3))))
    return out


def parse_class(page_html):
    i = page_html.find("new ModsView(")
    if i < 0:
        return None
    obj, _ = json.JSONDecoder().raw_decode(page_html[i + len("new ModsView("):])
    good, broken = [], set()
    for m in obj.get("normal", []):
        dc = m.get("DropChance")
        fam = "/".join(m.get("ModFamilyList") or [])
        if not (isinstance(dc, str) and dc.isdigit() and int(dc) > 1):
            broken.add(fam)
            continue
        side = 1 if str(m.get("ModGenerationTypeID")) == "1" else 2
        good.append((side, int(m["Level"]), int(dc), fam, _strip(m["str"])))
    return good, sorted(broken)


def build(fetch=_get, delay=0.7, log=print):
    classes = list_classes(fetch(BASE + "Modifiers"))
    mods, index, out_classes = [], {}, []
    for group, href, title in classes:
        if group in SKIP_GROUPS:
            continue
        try:
            parsed = parse_class(fetch(BASE + href))
        except Exception as e:  # keep going; report at the end
            log(f"skip {href}: {e}")
            continue
        time.sleep(delay)
        if not parsed or not parsed[0]:
            log(f"skip {href}: no usable weights")
            continue
        good, broken = parsed
        ids = []
        for k in good:
            if k not in index:
                index[k] = len(mods)
                mods.append(list(k))
            ids.append(index[k])
        out_classes.append({"g": group, "h": href, "t": title, "i": ids, "x": broken})
        log(f"{title}: {len(good)} mods, {len(broken)} broken families")
    return {"src": "poe2db.tw, pulled " + time.strftime("%Y-%m-%d"), "mods": mods, "classes": out_classes}


if __name__ == "__main__":
    data = build()
    # A layout change on poe2db can return a near-empty pull; keep the old data instead.
    if len(data["classes"]) < 30:
        raise SystemExit(f"only {len(data['classes'])} classes scraped; keeping old data")
    with open("data/moddata.json", "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
    print("classes:", len(data["classes"]), "mods:", len(data["mods"]))
