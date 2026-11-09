# media_catalog

Turns a zip or folder of trip photos and videos into a searchable catalogue. Each item gets
a description, categories from a fixed list, search tags, a location guess and a 1–5
highlight score. Later you can ask for "all creative/art photos" or "the best nature shots"
and get exactly those files copied out.

It reads the real metadata (date taken, GPS, camera, video length, Google Takeout `.json`
sidecars, iPhone HEIC) and makes a small preview of every photo, plus a 3-frame strip for
every video.

## Run it on your Windows PC

The photos stay on your computer, so this runs there (PowerShell):

```powershell
git clone https://github.com/gimmepizza/claude-lens; cd claude-lens
git checkout claude/quirky-archimedes-e1p985
pip install -r media_catalog/requirements.txt
winget install ffmpeg          # for video previews; photos work without it

python -m media_catalog prepare "C:\Users\benim\Downloads\Thailand 2026-1-001.zip" --out "C:\Users\benim\Pictures\thailand-catalog"
```

Then pick **one** way to write the descriptions:

**A) A Claude session on your PC (no API key).** Open the Claude desktop app (or run
`claude` in a terminal) in the `claude-lens` folder and paste:

> Catalogue my photos in `C:\Users\benim\Pictures\thailand-catalog`. Loop until done: run
> `python -m media_catalog todo <catalog> --batch 20`, look at each preview image it lists,
> write the descriptions to a JSON file in the format it shows, run
> `python -m media_catalog apply <catalog> <file>`. Context: Thailand trip, January 2026.
> When finished, run `stats` and `export`.

**B) The Claude API (needs `ANTHROPIC_API_KEY`).** It runs unattended and can be resumed
(progress is saved after every item):

```powershell
$env:ANTHROPIC_API_KEY = "..."
python -m media_catalog describe "C:\Users\benim\Pictures\thailand-catalog" --context "Thailand trip, Jan 2026: Bangkok, Chiang Mai, Krabi"
```

The default model is Claude Opus 5.5 at low effort: roughly $0.02 per item, or about $20
per 1,000 photos. `--model claude-haiku-5-5` costs about a fiftieth of that, with simpler
descriptions. Requests opt into server-side fallback, so if the model declines an image it's
retried on a fallback model.

## Using the catalogue

```powershell
$C = "C:\Users\benim\Pictures\thailand-catalog"
python -m media_catalog stats $C                                   # counts per category
python -m media_catalog find $C --category art_creative            # list matches
python -m media_catalog find $C --category nature landscape --min-highlight 4 --exclude-poor
python -m media_catalog find $C --text "long-tail boat" --time sunset golden_hour
python -m media_catalog extract $C --category art_creative --to "$HOME\Pictures\thailand-art"
python -m media_catalog export $C     # catalog.csv (opens in Excel) + index.html gallery
```

Open `index.html` to browse visually, with category chips, search, a photo/video filter and
a rating filter. Clicking a card opens the original.

Later you can just ask Claude: *"from my Thailand catalogue, copy every creative/art photo
rated 3+ into a folder"*. It maps that onto `extract --category art_creative --min-highlight 3`.

### Categories (fixed)

`nature`, `landscape`, `beach_sea`, `wildlife_animals`, `temple_religious`, `architecture`,
`street_city`, `market_shopping`, `food_drink`, `people_portrait`, `group_selfie`,
`art_creative` (artworks *and* artistically composed shots), `night_nightlife`,
`activity_adventure`, `transport_travel`, `accommodation`, `documents_screenshots`, `other`.

Each item has 1–4 categories, so a sunset with a boat silhouette can be both `beach_sea` and
`art_creative`. Other filters: `--time` (sunrise, day, golden_hour, sunset, blue_hour, night,
indoor), `--people` (none, one, two, small_group, crowd), `--type photo|video`.

## Files it writes

```
thailand-catalog/
  originals/      the extracted zip (untouched files)
  thumbs/         one preview per item (1024px; videos as a 3-frame strip)
  catalog.json    everything: metadata + descriptions (the source of truth)
  catalog.csv     the same, for Excel
  index.html      browsable gallery
```

Re-running `prepare` on the same zip or folder only adds new files; existing descriptions are kept.

## Tests

```bash
python -m pytest media_catalog/tests -q
```
