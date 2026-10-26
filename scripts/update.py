import json, re, urllib.parse, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
from email.utils import parsedate_to_datetime
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
docs = root / "docs"
archive = docs / "archive"
archive.mkdir(parents=True, exist_ok=True)
tz = ZoneInfo("America/Santiago")
now = datetime.now(tz)
today = now.date()
queries = [
    "parking technology OR smart parking OR parking management",
    "parking enforcement license plate recognition",
    "parking payments OR dynamic parking pricing",
    "on street parking OR off street parking",
    "estacionamientos tecnología fiscalización",
]
keywords = ("parking", "estacionamiento", "parquímetro", "car park", "carpark", "kerbside", "curbside")
seen = set()
items = []
for q in queries:
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
        "q": q + " when:1d", "hl": "en-US", "gl": "US", "ceid": "US:en"
    })
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as response:
            tree = ET.fromstring(response.read())
        for item in tree.findall("./channel/item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            date = (item.findtext("pubDate") or "").strip()
            if not (title and link and date):
                continue
            published = parsedate_to_datetime(date).astimezone(tz)
            if published.date() != today or not any(w in title.lower() for w in keywords):
                continue
            norm = re.sub(r"\W+", "", title.lower())
            if norm in seen:
                continue
            seen.add(norm)
            source = item.find("source")
            items.append({"title": title, "url": link, "published": published.isoformat(),
                         "source": source.text if source is not None and source.text else "Fuente externa"})
    except Exception as exc:
        print("Aviso fuente RSS:", str(exc)[:160])
items = sorted(items, key=lambda x: x["published"], reverse=True)[:30]
report = {
    "date": today.isoformat(), "generated_at": now.isoformat(), "timezone": "America/Santiago",
    "items": items,
    "note": "Titulares extraídos de RSS; la fecha y el contenido no se han verificado independientemente."
}
(archive / (str(today) + ".json")).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
(docs / "latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
days = sorted((x.stem for x in archive.glob("????-??-??.json")), reverse=True)
(docs / "archive-index.json").write_text(json.dumps(days, ensure_ascii=False, indent=2), encoding="utf-8")
print("Informe generado:", today, len(items), "publicaciones")
