# PoE2 Reference

A personal Path of Exile 2 crafting reference built from [poe2db.tw](https://poe2db.tw/us/). It holds numbers and stat lines only, with a link back to poe2db on every page. It has no flavor text, descriptions or art.

## Sections

- **Mod pools by base**: built. Prefix and suffix tables for 43 item classes, with tier, level, weight and the chance to roll each mod at the item level you pick.
- **Currency and crafting, Item bases, Skills and support gems**: stubs. Each needs a scraper written against poe2db's live pages.

## Run it locally

    python build.py

Then open `site/index.html`. No install needed, stdlib Python only.

## How it stays up to date

`.github/workflows/update.yml` runs every day at 09:17 UTC. Run it by hand from the Actions tab right after a content release. Each run:

1. Scrapes poe2db (`scrape/mods.py`, one request every 0.7 s, about 45 requests).
2. Commits `data/` only if the numbers changed, so the git history doubles as a patch-by-patch record.
3. Rebuilds the site and publishes it to GitHub Pages.

If the scrape fails or comes back nearly empty, which usually means poe2db changed its page layout, the old data stays, the site still publishes, and the run is marked failed so GitHub emails you.

## One-time setup

Settings > Pages > Source: **GitHub Actions**.
