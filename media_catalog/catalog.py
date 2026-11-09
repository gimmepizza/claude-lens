"""Catalogue a folder or zip of photos and videos so they can be searched and extracted later.

    python -m media_catalog prepare "Thailand 2026-1-001.zip" --out thailand
    python -m media_catalog describe thailand --context "Thailand trip, Jan 2026"   # Claude API
    python -m media_catalog todo thailand --batch 20     # ...or describe from a Claude session
    python -m media_catalog apply thailand descriptions.json
    python -m media_catalog find thailand --category art_creative
    python -m media_catalog extract thailand --category nature --to nature_picks
    python -m media_catalog export thailand              # catalog.csv + index.html gallery
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import io
import json
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps

try:  # iPhone HEIC photos
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:  # pragma: no cover
    pillow_heif = None

PHOTO_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".3gp", ".webm", ".mts"}
THUMB_PX = 1024

# Fixed taxonomy: the same words always mean the same thing, so later searches are reliable.
CATEGORIES = {
    "nature": "plants, forests, waterfalls, mountains, rivers, sky, natural scenery",
    "landscape": "wide scenic views, vistas, panoramas (natural or urban)",
    "beach_sea": "beaches, sea, islands, boats on water, underwater",
    "wildlife_animals": "animals of any kind: elephants, monkeys, fish, birds, pets",
    "temple_religious": "temples, Buddha statues, shrines, monks, religious ceremonies",
    "architecture": "buildings, interiors of note, bridges, skylines, structural detail",
    "street_city": "streets, traffic, city life, alleys, everyday urban scenes",
    "market_shopping": "markets, stalls, shops, malls, vendors",
    "food_drink": "meals, street food, drinks, cafes, cooking",
    "people_portrait": "one or two people as the main subject",
    "group_selfie": "selfies and group photos of the travellers",
    "art_creative": "artworks, murals, street art, crafts, or photos with a deliberately artistic "
                    "composition (reflections, silhouettes, abstract, unusual angles, bokeh)",
    "night_nightlife": "night scenes, lights, bars, shows, fireworks",
    "activity_adventure": "diving, hiking, boat trips, kayaking, rides, sports, tours",
    "transport_travel": "planes, airports, tuk-tuks, trains, ferries, roads, travel logistics",
    "accommodation": "hotels, rooms, pools, resorts",
    "documents_screenshots": "screenshots, tickets, maps, receipts, signs photographed for information",
    "other": "anything that fits none of the above",
}
TIME_OF_DAY = ["sunrise", "day", "golden_hour", "sunset", "blue_hour", "night", "indoor", "unknown"]
PEOPLE = ["none", "one", "two", "small_group", "crowd"]
QUALITY = ["sharp", "ok", "blurry_or_poor"]

DESCRIPTION_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {"type": "string", "description": "2-3 concrete sentences: subject, setting, mood"},
        "primary_category": {"type": "string", "enum": list(CATEGORIES)},
        "categories": {"type": "array", "items": {"type": "string", "enum": list(CATEGORIES)},
                       "description": "1-4 categories, primary first"},
        "tags": {"type": "array", "items": {"type": "string"},
                 "description": "5-15 lowercase search keywords: objects, colours, places, activities"},
        "location_guess": {"type": "string", "description": "place name if identifiable, else empty"},
        "time_of_day": {"type": "string", "enum": TIME_OF_DAY},
        "people": {"type": "string", "enum": PEOPLE},
        "quality": {"type": "string", "enum": QUALITY},
        "highlight": {"type": "integer", "description": "1-5: how strong a keeper/showcase shot this is"},
    },
    "required": ["description", "primary_category", "categories", "tags", "location_guess",
                 "time_of_day", "people", "quality", "highlight"],
    "additionalProperties": False,
}
DESCRIBED_FIELDS = DESCRIPTION_SCHEMA["required"]

PROMPT = """You are cataloguing a personal travel photo library so the owner can later ask for things
like "all nature shots", "all creative/art photos" or "the best sunset pictures".

Describe this {kind}. {video_note}Known metadata: {meta}
{context}
Categories (use only these keys; pick 1-4, most important first):
{categories}

Rules:
- Description: concrete and specific (what, where, notable details, mood). No guessing names of people.
- Tags: lowercase single words or short phrases useful for search (e.g. "long-tail boat", "limestone cliffs").
- art_creative: include it whenever the composition itself is artistic, not only for artworks.
- location_guess: only when the scene or GPS makes it reasonably identifiable.
- highlight: 5 = portfolio-worthy, 3 = nice memory, 1 = throwaway/duplicate-looking.
"""


# ── catalog file ──────────────────────────────────────────────────


def catalog_path(root: Path) -> Path:
    return root / "catalog.json"


def load(root: Path) -> dict:
    p = catalog_path(root)
    if not p.exists():
        sys.exit(f"No catalog at {p}. Run `prepare` first.")
    return json.loads(p.read_text(encoding="utf-8"))


def save(root: Path, cat: dict) -> None:
    tmp = catalog_path(root).with_suffix(".tmp")
    tmp.write_text(json.dumps(cat, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(catalog_path(root))  # atomic: a crash never leaves a half-written catalog


def is_described(item: dict) -> bool:
    return bool(item.get("description"))


# ── metadata ──────────────────────────────────────────────────────


def _ratio(v) -> float:
    try:
        return float(v)
    except TypeError:
        return v[0] / v[1]


def _dms(dms, ref) -> float | None:
    try:
        d, m, s = (_ratio(x) for x in dms)
    except Exception:
        return None
    val = d + m / 60 + s / 3600
    return -val if ref in ("S", "W") else val


def photo_meta(img: Image.Image) -> dict:
    out: dict = {"width": img.width, "height": img.height}
    exif = img.getexif()
    if not exif:
        return out
    sub = exif.get_ifd(0x8769)
    dt = sub.get(36867) or exif.get(306)  # DateTimeOriginal, else DateTime
    if dt:
        try:
            out["taken_at"] = datetime.strptime(str(dt).strip("\x00"), "%Y:%m:%d %H:%M:%S").isoformat()
        except ValueError:
            pass
    make, model = exif.get(271), exif.get(272)
    if make or model:
        out["camera"] = " ".join(str(x).strip("\x00 ") for x in (make, model) if x)
    gps = exif.get_ifd(0x8825)
    if gps and 2 in gps and 4 in gps:
        lat, lon = _dms(gps[2], gps.get(1)), _dms(gps[4], gps.get(3))
        if lat is not None and lon is not None and (lat or lon):
            out["lat"], out["lon"] = round(lat, 6), round(lon, 6)
    return out


def _iso6709(s: str) -> tuple[float, float] | None:
    import re
    m = re.match(r"([+-]\d+(?:\.\d+)?)([+-]\d+(?:\.\d+)?)", s or "")
    return (float(m.group(1)), float(m.group(2))) if m else None


def video_meta(path: Path) -> dict:
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams",
                            str(path)], capture_output=True, text=True, timeout=60)
        info = json.loads(r.stdout or "{}")
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return {}
    out: dict = {}
    fmt = info.get("format", {})
    if fmt.get("duration"):
        out["duration_s"] = round(float(fmt["duration"]), 1)
    v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    if v:
        out["width"], out["height"] = v.get("width"), v.get("height")
    tags = {k.lower(): val for k, val in (fmt.get("tags") or {}).items()}
    if tags.get("creation_time"):
        out["taken_at"] = tags["creation_time"].replace("Z", "+00:00")
    loc = _iso6709(tags.get("location") or tags.get("com.apple.quicktime.location.iso6709", ""))
    if loc:
        out["lat"], out["lon"] = loc
    if tags.get("com.apple.quicktime.model"):
        out["camera"] = tags["com.apple.quicktime.model"]
    return out


def sidecar_meta(path: Path) -> dict:
    """Google Takeout writes `<name>.json` / `<name>.supplemental-metadata.json` next to each file."""
    candidates = [path.with_name(path.name + ".json"),
                  path.with_name(path.name + ".supplemental-metadata.json")]
    candidates += sorted(path.parent.glob(path.name[:46] + "*.json"))  # Takeout truncates long names
    for c in candidates:
        if not c.exists():
            continue
        try:
            j = json.loads(c.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        out: dict = {}
        ts = (j.get("photoTakenTime") or {}).get("timestamp")
        if ts:
            out["taken_at"] = datetime.fromtimestamp(int(ts), timezone.utc).isoformat()
        geo = j.get("geoDataExif") or j.get("geoData") or {}
        if geo.get("latitude") or geo.get("longitude"):
            out["lat"], out["lon"] = geo["latitude"], geo["longitude"]
        if j.get("description"):
            out["owner_caption"] = j["description"]
        return out
    return {}


# ── previews ──────────────────────────────────────────────────────


def make_photo_thumb(src: Path, dst: Path) -> dict:
    with Image.open(src) as im:
        meta = photo_meta(im)
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((THUMB_PX, THUMB_PX))
        im.save(dst, "JPEG", quality=82)
    return meta


def make_video_strip(src: Path, dst: Path, duration: float | None) -> bool:
    """Three frames (10%, 50%, 90%) side by side, so one image shows how the clip unfolds."""
    if not shutil.which("ffmpeg"):
        return False
    points = [0.1, 0.5, 0.9] if duration and duration > 1 else [0.0]
    frames = []
    for p in points:
        t = (duration or 0) * p
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1",
                            "-vf", "scale=640:-2", "-f", "image2pipe", "-vcodec", "mjpeg", "-"],
                           capture_output=True, timeout=120)
        if r.returncode == 0 and r.stdout:
            frames.append(Image.open(io.BytesIO(r.stdout)).convert("RGB"))
    if not frames:
        return False
    h = min(f.height for f in frames)
    frames = [f.resize((int(f.width * h / f.height), h)) for f in frames]
    gap = 8
    strip = Image.new("RGB", (sum(f.width for f in frames) + gap * (len(frames) - 1), h), "white")
    x = 0
    for f in frames:
        strip.paste(f, (x, 0))
        x += f.width + gap
    strip.thumbnail((THUMB_PX * 2, THUMB_PX))
    strip.save(dst, "JPEG", quality=82)
    return True


# ── commands ──────────────────────────────────────────────────────


def safe_extract(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path) as z:
        for m in z.infolist():
            target = (dest / m.filename).resolve()
            if not str(target).startswith(str(dest.resolve())):
                raise ValueError(f"unsafe path in zip: {m.filename}")
        z.extractall(dest)


def cmd_prepare(a) -> None:
    src, root = Path(a.source), Path(a.out)
    originals, thumbs = root / "originals", root / "thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    if src.is_file() and src.suffix.lower() == ".zip":
        if not originals.exists():
            print(f"Extracting {src} → {originals}")
            safe_extract(src, originals)
        base = originals
    elif src.is_dir():
        base = src.resolve()
    else:
        sys.exit(f"{src} is not a zip or folder")

    cat = json.loads(catalog_path(root).read_text(encoding="utf-8")) if catalog_path(root).exists() else \
        {"source": str(src), "base": str(base), "items": {}}
    files = sorted(p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in PHOTO_EXT | VIDEO_EXT)
    added = 0
    for i, f in enumerate(files, 1):
        rel = f.relative_to(base).as_posix()
        iid = hashlib.sha1(rel.encode()).hexdigest()[:10]
        if iid in cat["items"]:
            continue
        kind = "video" if f.suffix.lower() in VIDEO_EXT else "photo"
        item = {"id": iid, "file": rel, "type": kind, "size_mb": round(f.stat().st_size / 1e6, 2)}
        thumb = thumbs / f"{iid}.jpg"
        try:
            if kind == "photo":
                item.update(make_photo_thumb(f, thumb))
            else:
                item.update(video_meta(f))
                if not make_video_strip(f, thumb, item.get("duration_s")):
                    item["warning"] = "no preview (install ffmpeg)"
        except Exception as e:  # unreadable/corrupt file: keep it listed, flag it
            item["warning"] = f"could not read: {e}"
        for k, v in sidecar_meta(f).items():
            item.setdefault(k, v)
        if thumb.exists():
            item["thumb"] = f"thumbs/{iid}.jpg"
        cat["items"][iid] = item
        added += 1
        if i % 25 == 0:
            print(f"  {i}/{len(files)}")
            save(root, cat)
    save(root, cat)
    items = cat["items"].values()
    print(f"Catalog: {root / 'catalog.json'} — {sum(i['type'] == 'photo' for i in items)} photos, "
          f"{sum(i['type'] == 'video' for i in items)} videos ({added} new). "
          f"{sum(not is_described(i) for i in items)} still need descriptions.")


def _meta_line(item: dict) -> str:
    keys = ["file", "taken_at", "lat", "lon", "camera", "duration_s", "owner_caption"]
    return json.dumps({k: item[k] for k in keys if item.get(k) is not None}, ensure_ascii=False)


def _prompt(item: dict, context: str) -> str:
    return PROMPT.format(
        kind="video (three frames from start, middle and end)" if item["type"] == "video" else "photo",
        video_note=f"It lasts {item.get('duration_s', '?')} seconds. " if item["type"] == "video" else "",
        meta=_meta_line(item),
        context=f"Album context from the owner: {context}\n" if context else "",
        categories="\n".join(f"- {k}: {v}" for k, v in CATEGORIES.items()),
    )


def normalise(desc: dict) -> dict:
    """Validate/clean a description from any source (API or a Claude session)."""
    missing = [k for k in DESCRIBED_FIELDS if k not in desc]
    if missing:
        raise ValueError(f"missing fields {missing}")
    cats = [c for c in dict.fromkeys([desc["primary_category"], *desc["categories"]]) if c in CATEGORIES]
    if not cats:
        raise ValueError(f"no valid categories in {desc['categories']}")
    return {
        "description": str(desc["description"]).strip(),
        "primary_category": cats[0],
        "categories": cats[:4],
        "tags": sorted({str(t).strip().lower() for t in desc["tags"] if str(t).strip()}),
        "location_guess": str(desc.get("location_guess") or "").strip(),
        "time_of_day": desc["time_of_day"] if desc["time_of_day"] in TIME_OF_DAY else "unknown",
        "people": desc["people"] if desc["people"] in PEOPLE else "none",
        "quality": desc["quality"] if desc["quality"] in QUALITY else "ok",
        "highlight": max(1, min(5, int(desc["highlight"]))),
    }


def describe_with_api(client, model: str, item: dict, root: Path, context: str, effort: str) -> dict:
    data = base64.standard_b64encode((root / item["thumb"]).read_bytes()).decode()
    resp = client.beta.messages.create(
        model=model,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # if the model declines, the API retries on a fallback model
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": DESCRIPTION_SCHEMA}},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}},
            {"type": "text", "text": _prompt(item, context)},
        ]}],
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("declined by the model")
    text = next(b.text for b in resp.content if b.type == "text")
    return normalise(json.loads(text))


def cmd_describe(a) -> None:
    import anthropic

    root = Path(a.catalog)
    cat = load(root)
    todo = [i for i in cat["items"].values() if not is_described(i) and i.get("thumb")]
    if a.limit:
        todo = todo[: a.limit]
    if not todo:
        print("Nothing to describe.")
        return
    client = anthropic.Anthropic()
    print(f"Describing {len(todo)} items with {a.model} …")
    for n, item in enumerate(todo, 1):
        for attempt in range(3):
            try:
                item.update(describe_with_api(client, a.model, item, root, a.context or cat.get("context", ""),
                                              a.effort))
                item.pop("error", None)
                break
            except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError) as e:
                time.sleep(10 * (attempt + 1))
                item["error"] = str(e)[:200]
            except (anthropic.BadRequestError, RuntimeError, ValueError, json.JSONDecodeError) as e:
                item["error"] = str(e)[:200]
                break
        save(root, cat)  # resumable: progress is kept after every item
        status = item.get("primary_category") or f"ERROR {item.get('error')}"
        print(f"  [{n}/{len(todo)}] {item['file']}: {status}")
    if a.context:
        cat["context"] = a.context
        save(root, cat)


def cmd_todo(a) -> None:
    """For describing inside a Claude session (no API key): list the next previews to look at."""
    root = Path(a.catalog).resolve()
    cat = load(root)
    todo = [i for i in cat["items"].values() if not is_described(i) and i.get("thumb")][: a.batch]
    left = sum(not is_described(i) and i.get("thumb") for i in cat["items"].values())
    no_prev = [i["file"] for i in cat["items"].values() if not i.get("thumb")]
    print(f"{left} items still need descriptions. Next {len(todo)}:\n")
    for i in todo:
        print(f"{i['id']}  {root / i['thumb']}  {_meta_line(i)}")
    print("\nWrite a JSON list of objects with \"id\" plus these fields, then run `apply`:")
    print(json.dumps({k: DESCRIPTION_SCHEMA["properties"][k].get("enum", DESCRIPTION_SCHEMA["properties"][k]
                                                                 .get("description", "")) for k in DESCRIBED_FIELDS},
                     ensure_ascii=False))
    print("categories: " + ", ".join(CATEGORIES))
    if no_prev:
        print(f"\n{len(no_prev)} file(s) have no preview and can't be described: {', '.join(no_prev[:5])}")


def cmd_apply(a) -> None:
    root = Path(a.catalog)
    cat = load(root)
    entries = json.loads(Path(a.file).read_text(encoding="utf-8"))
    ok, bad = 0, []
    for e in entries:
        iid = e.get("id")
        if iid not in cat["items"]:
            bad.append(f"{iid}: unknown id")
            continue
        try:
            cat["items"][iid].update(normalise(e))
            cat["items"][iid].pop("error", None)
            ok += 1
        except (ValueError, TypeError) as err:
            bad.append(f"{iid}: {err}")
    save(root, cat)
    print(f"Applied {ok} descriptions." + (f" Rejected {len(bad)}:\n  " + "\n  ".join(bad) if bad else ""))


def matches(item: dict, a) -> bool:
    if a.type and item["type"] != a.type:
        return False
    if a.category and not set(a.category) & set(item.get("categories", [])):
        return False
    if a.tag and not all(any(t.lower() in tag for tag in item.get("tags", [])) for t in a.tag):
        return False
    if a.text:
        hay = " ".join([item.get("description", ""), item.get("location_guess", ""), item["file"],
                        " ".join(item.get("tags", []))]).lower()
        if not all(w.lower() in hay for w in a.text.split()):
            return False
    if a.min_highlight and item.get("highlight", 0) < a.min_highlight:
        return False
    if a.time and item.get("time_of_day") not in a.time:
        return False
    if a.people and item.get("people") not in a.people:
        return False
    if a.exclude_poor and item.get("quality") == "blurry_or_poor":
        return False
    return True


def selected(a) -> tuple[Path, dict, list[dict]]:
    root = Path(a.catalog)
    cat = load(root)
    items = [i for i in cat["items"].values() if matches(i, a)]
    items.sort(key=lambda i: (i.get("taken_at") or "", i["file"]))
    return root, cat, items


def cmd_find(a) -> None:
    _, _, items = selected(a)
    for i in items:
        print(f"{i['file']}\t{i.get('primary_category', '-')}\t★{i.get('highlight', '-')}\t"
              f"{(i.get('description') or '')[:100]}")
    print(f"\n{len(items)} matching", file=sys.stderr)


def cmd_extract(a) -> None:
    root, cat, items = selected(a)
    base, dest = Path(cat["base"]), Path(a.to)
    dest.mkdir(parents=True, exist_ok=True)
    for i in items:
        src = base / i["file"]
        target = dest / Path(i["file"]).name
        if target.exists() and target.stat().st_size != src.stat().st_size:
            target = dest / f"{target.stem}_{i['id']}{target.suffix}"
        shutil.copy2(src, target)
    print(f"Copied {len(items)} files to {dest}")


def cmd_stats(a) -> None:
    cat = load(Path(a.catalog))
    items = list(cat["items"].values())
    done = [i for i in items if is_described(i)]
    print(f"{len(items)} items ({sum(i['type'] == 'photo' for i in items)} photos, "
          f"{sum(i['type'] == 'video' for i in items)} videos); {len(done)} described, "
          f"{sum(1 for i in items if i.get('error'))} errors, {sum(1 for i in items if i.get('warning'))} warnings")
    counts = {c: sum(c in i.get("categories", []) for i in done) for c in CATEGORIES}
    for c, n in sorted(counts.items(), key=lambda x: -x[1]):
        if n:
            print(f"  {c:<22}{n}")


EXPORT_FIELDS = ["id", "file", "type", "taken_at", "primary_category", "categories", "tags", "description",
                 "location_guess", "time_of_day", "people", "quality", "highlight", "lat", "lon", "camera",
                 "duration_s", "size_mb"]


def cmd_export(a) -> None:
    root = Path(a.catalog)
    cat = load(root)
    items = sorted(cat["items"].values(), key=lambda i: (i.get("taken_at") or "", i["file"]))
    with open(root / "catalog.csv", "w", newline="", encoding="utf-8-sig") as f:  # BOM: opens cleanly in Excel
        w = csv.DictWriter(f, EXPORT_FIELDS, extrasaction="ignore")
        w.writeheader()
        for i in items:
            w.writerow({**i, "categories": ";".join(i.get("categories", [])), "tags": ";".join(i.get("tags", []))})
    base_rel = Path(cat["base"])
    try:
        base_rel = base_rel.resolve().relative_to(root.resolve())
    except ValueError:
        base_rel = base_rel.resolve()
    data = [{"id": i["id"], "file": f"{base_rel.as_posix()}/{i['file']}", "name": Path(i["file"]).name,
             "type": i["type"], "thumb": i.get("thumb", ""), "date": (i.get("taken_at") or "")[:10],
             "cats": i.get("categories", []), "tags": i.get("tags", []), "desc": i.get("description", ""),
             "loc": i.get("location_guess", ""), "hl": i.get("highlight", 0)} for i in items]
    title = html.escape(a.title or Path(cat["source"]).stem)
    (root / "index.html").write_text(
        GALLERY.replace("__TITLE__", title).replace("__DATA__", json.dumps(data, ensure_ascii=False))
        .replace("__CATS__", json.dumps(list(CATEGORIES))), encoding="utf-8")
    print(f"Wrote {root / 'catalog.csv'} and {root / 'index.html'}")


GALLERY = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>__TITLE__</title>
<style>
:root{color-scheme:light;--bg:#fcfcfb;--card:#fff;--text:#0b0b0b;--text2:#52514e;--muted:#8a8984;--border:#e3e2de;--accent:#2a78d6;--chip:#f1f0ec}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#1a1a19;--card:#222221;--text:#f0efec;--text2:#c3c2b7;--muted:#8f8e86;--border:#3a3a36;--accent:#3987e5;--chip:#2c2c2a}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#1a1a19;--card:#222221;--text:#f0efec;--text2:#c3c2b7;--muted:#8f8e86;--border:#3a3a36;--accent:#3987e5;--chip:#2c2c2a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--border);padding:12px 16px;z-index:2}
h1{font-size:18px;margin:0 0 8px}.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
input,select{font:inherit;padding:6px 10px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--text)}
input{flex:1;min-width:180px}.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.chip{border:1px solid var(--border);background:var(--chip);color:var(--text2);border-radius:999px;padding:3px 10px;cursor:pointer;font-size:12px}
.chip[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:#fff}
#count{color:var(--muted);font-size:12px}main{padding:16px;display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden;display:flex;flex-direction:column}
.card img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;background:var(--chip)}
.body{padding:8px 10px}.meta{color:var(--muted);font-size:12px;display:flex;justify-content:space-between}
.desc{margin:4px 0;color:var(--text)}.tags{color:var(--text2);font-size:12px}a{color:inherit;text-decoration:none}
.badge{font-size:11px;color:var(--text2)}
.noprev{aspect-ratio:4/3;display:flex;align-items:center;justify-content:center;background:var(--chip);color:var(--muted);font-size:12px;padding:8px;text-align:center}
</style></head><body>
<header><h1>__TITLE__</h1>
<div class="row"><input id="q" placeholder="Search descriptions, tags, places…" aria-label="Search">
<select id="type" aria-label="Type"><option value="">Photos &amp; videos</option><option value="photo">Photos</option><option value="video">Videos</option></select>
<select id="hl" aria-label="Minimum highlight"><option value="0">Any rating</option><option value="3">★3+</option><option value="4">★4+</option><option value="5">★5</option></select>
<span id="count"></span></div><div class="chips" id="chips"></div></header>
<main id="grid"></main>
<script>
const D=__DATA__,C=__CATS__,on=new Set();
const chips=document.getElementById('chips');
C.forEach(c=>{const n=D.filter(d=>d.cats.includes(c)).length;if(!n)return;const b=document.createElement('button');
b.className='chip';b.textContent=`${c.replace(/_/g,' ')} (${n})`;b.setAttribute('aria-pressed','false');
b.onclick=()=>{on.has(c)?on.delete(c):on.add(c);b.setAttribute('aria-pressed',on.has(c));draw()};chips.appendChild(b)});
const esc=s=>String(s).replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
function draw(){const q=document.getElementById('q').value.toLowerCase().split(/\s+/).filter(Boolean),
t=document.getElementById('type').value,h=+document.getElementById('hl').value;
const r=D.filter(d=>(!t||d.type===t)&&d.hl>=h&&(!on.size||d.cats.some(c=>on.has(c)))&&
q.every(w=>(d.desc+' '+d.tags.join(' ')+' '+d.loc+' '+d.name).toLowerCase().includes(w)));
document.getElementById('count').textContent=`${r.length} of ${D.length}`;
document.getElementById('grid').innerHTML=r.map(d=>`<a class="card" href="${encodeURI(d.file)}" target="_blank" rel="noopener">
${d.thumb?`<img loading="lazy" src="${esc(d.thumb)}" alt="${esc(d.desc||d.name)}">`:`<div class="noprev">no preview · ${esc(d.name)}</div>`}<div class="body">
<div class="meta"><span>${esc(d.date)} ${d.type==='video'?'· video':''}</span><span class="badge">${d.hl?'★'+d.hl:''}</span></div>
<p class="desc">${esc(d.desc||'(not described yet)')}</p><div class="tags">${esc([d.loc,...d.cats.map(c=>c.replace(/_/g,' '))].filter(Boolean).join(' · '))}</div></div></a>`).join('')}
['q','type','hl'].forEach(id=>document.getElementById(id).addEventListener('input',draw));draw();
</script></body></html>"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="media_catalog", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("prepare", help="extract, read metadata, make previews")
    s.add_argument("source", help="zip file or folder")
    s.add_argument("--out", required=True, help="catalog folder to create")
    s = sub.add_parser("describe", help="describe items with the Claude API (needs ANTHROPIC_API_KEY)")
    s.add_argument("catalog")
    s.add_argument("--context", help='e.g. "Thailand trip, Jan 2026: Bangkok, Chiang Mai, Krabi"')
    s.add_argument("--model", default="claude-opus-5-5")
    s.add_argument("--effort", default="low", choices=["low", "medium", "high"])
    s.add_argument("--limit", type=int, default=0)
    s = sub.add_parser("todo", help="list the next items to describe from a Claude session")
    s.add_argument("catalog")
    s.add_argument("--batch", type=int, default=20)
    s = sub.add_parser("apply", help="merge descriptions written in a Claude session")
    s.add_argument("catalog")
    s.add_argument("file")
    s = sub.add_parser("stats", help="counts per category")
    s.add_argument("catalog")
    s = sub.add_parser("export", help="write catalog.csv and an index.html gallery")
    s.add_argument("catalog")
    s.add_argument("--title")
    for name, hlp in [("find", "list matching items"), ("extract", "copy matching originals to a folder")]:
        s = sub.add_parser(name, help=hlp)
        s.add_argument("catalog")
        s.add_argument("--category", nargs="+", choices=list(CATEGORIES), help="any of these categories")
        s.add_argument("--tag", nargs="+", help="all of these tags (substring match)")
        s.add_argument("--text", help="words that must appear in description/tags/location")
        s.add_argument("--type", choices=["photo", "video"])
        s.add_argument("--min-highlight", type=int)
        s.add_argument("--time", nargs="+", choices=TIME_OF_DAY)
        s.add_argument("--people", nargs="+", choices=PEOPLE)
        s.add_argument("--exclude-poor", action="store_true")
        if name == "extract":
            s.add_argument("--to", required=True)
    return p


COMMANDS = {"prepare": cmd_prepare, "describe": cmd_describe, "todo": cmd_todo, "apply": cmd_apply,
            "find": cmd_find, "extract": cmd_extract, "stats": cmd_stats, "export": cmd_export}


def main(argv=None) -> None:
    a = build_parser().parse_args(argv)
    COMMANDS[a.cmd](a)
