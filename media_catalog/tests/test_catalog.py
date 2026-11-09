import json
import shutil
import subprocess
import zipfile
from types import SimpleNamespace

import pytest
from PIL import Image

from media_catalog import catalog as mc


def _exif(lat, lon, dt):
    e = Image.Exif()
    e[271], e[272] = "Apple", "iPhone 16"
    e.get_ifd(0x8769)[36867] = dt
    g = e.get_ifd(0x8825)
    g[1], g[2], g[3], g[4] = "N", (8, 0, 42.84), "E", (98, 50, 9.6)
    return e


@pytest.fixture
def album(tmp_path):
    d = tmp_path / "src" / "Trip"
    (d / "day2").mkdir(parents=True)
    Image.new("RGB", (800, 600), (200, 100, 50)).save(d / "a.jpg", exif=_exif(8.0119, 98.836, "2026:01:12 18:21:05"))
    Image.new("RGB", (600, 800), (20, 120, 40)).save(d / "day2" / "b.png")
    (d / "day2" / "b.png.supplemental-metadata.json").write_text(json.dumps(
        {"photoTakenTime": {"timestamp": "1768120000"}, "geoData": {"latitude": 13.69, "longitude": 100.75},
         "description": "airport"}))
    (d / "bad.jpg").write_bytes(b"nope")
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=10:duration=3",
                        "-metadata", "location=+07.7407+098.7784/", "-pix_fmt", "yuv420p", str(d / "v.mp4")],
                       check=True)
    z = tmp_path / "album.zip"
    with zipfile.ZipFile(z, "w") as zf:
        for f in (tmp_path / "src").rglob("*"):
            zf.write(f, f.relative_to(tmp_path / "src"))
    return z


def run(*args):
    mc.main([str(a) for a in args])


def items(root):
    return {i["file"]: i for i in mc.load(root)["items"].values()}


def test_prepare_reads_metadata_and_makes_previews(album, tmp_path):
    root = tmp_path / "cat"
    run("prepare", album, "--out", root)
    it = items(root)
    a = it["Trip/a.jpg"]
    assert a["taken_at"] == "2026-01-12T18:21:05" and a["camera"] == "Apple iPhone 16"
    assert a["lat"] == pytest.approx(8.0119, abs=1e-3) and a["lon"] == pytest.approx(98.836, abs=1e-3)
    assert (root / a["thumb"]).exists()
    b = it["Trip/day2/b.png"]
    assert b["lat"] == 13.69 and b["owner_caption"] == "airport" and b["taken_at"].startswith("2026-01-11")
    assert "warning" in it["Trip/bad.jpg"] and "thumb" not in it["Trip/bad.jpg"]
    if shutil.which("ffmpeg"):
        v = it["Trip/v.mp4"]
        assert v["type"] == "video" and v["duration_s"] == pytest.approx(3, abs=0.2)
        assert v["lat"] == pytest.approx(7.7407) and (root / v["thumb"]).exists()
    # re-running is incremental and keeps descriptions
    first = mc.load(root)
    run("prepare", album, "--out", root)
    assert mc.load(root) == first


def test_zip_slip_is_rejected(tmp_path):
    z = tmp_path / "evil.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("../../escape.txt", "x")
    with pytest.raises(ValueError):
        mc.safe_extract(z, tmp_path / "out")


DESC = {"description": "Sunset over the sea.", "primary_category": "beach_sea",
        "categories": ["beach_sea", "art_creative", "made_up"], "tags": ["Sunset", "boat", "sunset"],
        "location_guess": "", "time_of_day": "sunset", "people": "none", "quality": "sharp", "highlight": 9}


def test_normalise_cleans_input():
    n = mc.normalise(DESC)
    assert n["categories"] == ["beach_sea", "art_creative"]
    assert n["tags"] == ["boat", "sunset"] and n["highlight"] == 5
    with pytest.raises(ValueError):
        mc.normalise({"description": "x"})


def test_apply_find_extract_export(album, tmp_path, capsys):
    root = tmp_path / "cat"
    run("prepare", album, "--out", root)
    ids = {i["file"]: i["id"] for i in mc.load(root)["items"].values()}
    entries = [{"id": ids["Trip/a.jpg"], **DESC},
               {"id": ids["Trip/day2/b.png"], **DESC, "description": "Green forest.", "primary_category": "nature",
                "categories": ["nature"], "tags": ["forest"], "highlight": 2},
               {"id": "missing", **DESC}]
    f = tmp_path / "d.json"
    f.write_text(json.dumps(entries))
    run("apply", root, f)
    assert "Rejected 1" in capsys.readouterr().out

    run("find", root, "--category", "art_creative")
    assert "Trip/a.jpg" in capsys.readouterr().out
    run("find", root, "--category", "nature", "--min-highlight", "3")
    assert "Trip/day2/b.png" not in capsys.readouterr().out
    run("find", root, "--text", "forest")
    assert "Trip/day2/b.png" in capsys.readouterr().out

    run("extract", root, "--category", "nature", "beach_sea", "--to", tmp_path / "picks")
    assert sorted(p.name for p in (tmp_path / "picks").iterdir()) == ["a.jpg", "b.png"]

    run("export", root)
    html = (root / "index.html").read_text()
    assert "Sunset over the sea." in html and (root / "catalog.csv").exists()


class FakeAnthropic:
    """Stands in for anthropic.Anthropic(); records the request and returns a structured reply."""

    def __init__(self):
        self.calls = []
        outer = self

        class _Msgs:
            def create(self, **kw):
                outer.calls.append(kw)
                return SimpleNamespace(stop_reason="end_turn",
                                       content=[SimpleNamespace(type="text", text=json.dumps(DESC))])

        self.beta = SimpleNamespace(messages=_Msgs())


def test_describe_with_api_request_shape(album, tmp_path, monkeypatch):
    root = tmp_path / "cat"
    run("prepare", album, "--out", root)
    fake = FakeAnthropic()
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda: fake)
    run("describe", root, "--context", "Thailand trip", "--limit", "1")
    kw = fake.calls[0]
    assert kw["model"] == "claude-opus-5-5"
    assert kw["fallbacks"] == "default" and kw["betas"] == ["server-side-fallback-2026-07-01"]
    assert kw["output_config"]["format"]["schema"] is mc.DESCRIPTION_SCHEMA
    content = kw["messages"][0]["content"]
    assert content[0]["type"] == "image" and "Thailand trip" in content[1]["text"]
    described = [i for i in mc.load(root)["items"].values() if mc.is_described(i)]
    assert len(described) == 1 and described[0]["categories"] == ["beach_sea", "art_creative"]
    assert mc.load(root)["context"] == "Thailand trip"
