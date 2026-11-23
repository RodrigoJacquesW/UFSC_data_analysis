"""Download the "relação candidato/vaga" source files published by Coperve/UFSC.

Every year of the vestibular has its own website with a different layout, so the
sources are listed by hand in SOURCES. For 2013+ the page lists one PDF per quota
category; all PDFs linked from it are downloaded together with their link text,
which says which category each file is.

Output: data/sources/<year>/<file> (not versioned) and data/sources/manifest.csv
(versioned: year, label, url, file, sha256).
"""

import csv
import gzip
import hashlib
import re
import tempfile
import time
from html import unescape
from pathlib import Path
from urllib.parse import urljoin

import certifi
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sources"
CHAIN = Path(__file__).parent / "certs" / "letsencrypt_yr_chain.pem"
HEADERS = {"User-Agent": "Mozilla/5.0 (portfolio data project)"}

OLD = "https://dados.coperve.ufsc.br/vestibular{y}/{f}"
SOURCES: dict[int, tuple[str, str]] = {
    # (kind, url) - "file": the table itself; "page": a page that links one PDF per category
    2003: ("file", OLD.format(y=2003, f="relacaocandvaga.html")),
    2004: ("file", OLD.format(y=2004, f="indicecv.html")),
    2005: ("file", OLD.format(y=2005, f="vestcva02.html")),
    2006: ("file", OLD.format(y=2006, f="vestcva02.html")),
    2007: ("file", OLD.format(y=2007, f="vestcva02.html")),
    2008: ("file", OLD.format(y=2008, f="vestcva02.html")),
    2009: ("file", OLD.format(y=2009, f="vestcva02.html")),
    2010: ("file", OLD.format(y=2010, f="candidatovaga.html")),
    2011: ("file", OLD.format(y=2011, f="candidatovaga.pdf")),
    2012: ("file", OLD.format(y=2012, f="relacao_candidatosVaga.pdf")),
    2013: ("page", "http://www.vestibular2013.ufsc.br/relacao-candidatos-vaga/"),
    2014: ("page", "http://www.vestibular2014.ufsc.br/relacao-candidatos-vaga/"),
    2015: ("page", "http://www.vestibular2015.ufsc.br/relacao-candidatos-vaga/"),
    2016: ("page", "http://vestibular2016.paginas.ufsc.br/relacao-candidatos-vaga/"),
    2017: ("page", "http://vestibular2017.paginas.ufsc.br/relacao-candidatos-vaga/"),
    2018: ("page", "http://vestibular2018.ufsc.br/relacao-candidatos-vaga/"),
    2019: ("page", "https://vestibular2019.ufsc.br/relacao-candidatos-vaga/"),
    2020: ("page", "https://vestibular2020.ufsc.br/relacao-candidatos-vaga/"),
    2021: ("page", "https://vestibular2021.ufsc.br/relacao-candidatos-vaga/"),
    2022: ("page", "https://vestibular2022.ufsc.br/relacao-candidatos-vaga/"),
    2023: ("page", "http://vestibular2023.ufsc.br/relacao-candidato-vaga/"),
    2024: ("page", "http://vestibular2024.paginas.ufsc.br/relacao-candidato-vaga/"),
    2025: ("page", "https://vestibular2025.ufsc.br/relacao-candidato-vaga/"),
}

LINK = re.compile(r'href="([^"]+\.pdf)(?:\?[^"]*)?"[^>]*>(.*?)</a>', re.I | re.S)


def _session() -> requests.Session:
    bundle = tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False)
    bundle.write(Path(certifi.where()).read_text() + CHAIN.read_text())
    bundle.close()
    s = requests.Session()
    s.headers.update(HEADERS)
    s.verify = bundle.name
    return s


def _get(s: requests.Session, url: str) -> requests.Response:
    for attempt in range(3):
        try:
            r = s.get(url, timeout=60)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(3)


def main() -> None:
    s = _session()
    rows = []
    for year, (kind, url) in SOURCES.items():
        if kind == "file":
            files = [(url, "relacao candidato/vaga")]
        else:
            raw = _get(s, url).content
            # some of these WordPress sites send gzip without a Content-Encoding header
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            page = raw.decode("utf-8", errors="replace")
            files = [
                (urljoin(url, href), re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", text))).strip())
                for href, text in LINK.findall(page)
            ]
            files = [(u, t) for u, t in files if re.search(r"candidat|relacao[-_]?CV", u, re.I)]
        for file_url, label in dict.fromkeys(files):
            path = OUT / str(year) / file_url.rsplit("/", 1)[-1]
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(_get(s, file_url).content)
                time.sleep(0.3)
            rows.append({
                "year": year, "label": label, "url": file_url,
                "file": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
        print(f"{year}: {sum(r['year'] == year for r in rows)} file(s)")

    with open(OUT / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
