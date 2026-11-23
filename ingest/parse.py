"""Parse the downloaded Coperve files into one long table: data/raw/candidato_vaga.csv

One row = year x course x category. Categories:
  total         all candidates / all vacancies of the course
  geral         "Classificação Geral": ALL candidates, but only the general-list vacancies
  nao_optantes  candidates who did not opt into the affirmative action program (PAA)
  paa_<code>    one PAA quota category (vacancies reserved for it; candidates who opted in)

Source layouts:
  2003–2007  HTML, one table: vacancies + 1st-option applicants (all candidates)
  2008       HTML: "Geral" (whole course) + PAA groups
  2009–2010  HTML: Total + Não optantes + PAA groups
  2011–2012  PDF, same columns as 2009–2010
  2013+      one PDF per category, link text says which one; from 2020 also a "Total" file.
             2020 lists UFSC and UFFS, 2023+ UFSC, IFSC and IFC: only UFSC is kept.
"""

import csv
import io
import re
from pathlib import Path

import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "sources" / "manifest.csv"
OUTPUT = ROOT / "data" / "raw" / "candidato_vaga.csv"

UFSC = "UNIVERSIDADE FEDERAL DE SANTA CATARINA"
NUM = r"(\d+)"
CV = r"([\d.,]+|-+)"
# code, name, vacancies, applicants, c/v  (+ optional "Opção 1A" column)
CATEGORY_LINE = re.compile(rf"^(\d{{3,7}})\s+(.+?)\s+{NUM}\s+{NUM}\s+{CV}(?:\s+(?:\d+|-+))?$")
WRAPPED_LINE = re.compile(rf"^(\d{{3,7}})\s+{NUM}\s+{NUM}\s+{CV}(?:\s+(?:\d+|-+))?$")
NO_VACANCY_LINE = re.compile(r"^(999)\s+(.+?)\s+(\d+)\s+0\s+-+$")
# 2011–2012: code, name, then 4 groups of (vacancies, applicants, c/v)
WIDE_LINE = re.compile(rf"^(\d{{3}})\s+(.+?)" + rf"\s+{NUM}\s+{NUM}\s+{CV}" * 4 + "$")


def _row(year, category, code, name, vagas, inscritos, source, modality="vestibular"):
    return {
        "year": year, "modality": modality, "category": category, "course_code": str(code).strip(),
        "course_name": re.sub(r"\s+", " ", str(name)).strip(),
        "vagas": int(vagas), "inscritos": int(inscritos), "source_file": source,
    }


def _html_table(path: Path) -> pd.DataFrame:
    raw = path.read_bytes()
    try:
        html = raw.decode("utf-8")
    except UnicodeDecodeError:
        html = raw.decode("latin-1")
    table = max(pd.read_html(io.StringIO(html)), key=len)
    table = table[pd.to_numeric(table.iloc[:, 0], errors="coerce").notna()]
    return table


def parse_html(year: int, path: Path, source: str) -> list[dict]:
    t = _html_table(path)
    rows = []
    for r in t.itertuples(index=False):
        v = list(r)
        code, name = int(v[0]), v[1]
        if year <= 2007:
            # Código | Nome | Total vagas | Opção 1 inscritos | C/V | Opção 2 | Opção 1A
            rows.append(_row(year, "total", code, name, v[2], v[3], source))
        elif year == 2008:
            # Geral (vagas, inscritos, c/v) | Negros (...) | Escola Pública (...)
            rows.append(_row(year, "total", code, name, v[2], v[3], source))
            rows.append(_row(year, "paa_negros", code, name, v[5], v[6], source))
            rows.append(_row(year, "paa_escola_publica", code, name, v[8], v[9], source))
        else:
            # Total | Não optantes | Negros | Escola Pública, each (vagas, inscritos, c/v)
            for cat, i in (("total", 2), ("nao_optantes", 5), ("paa_negros", 8), ("paa_escola_publica", 11)):
                if pd.notna(v[i]) and pd.notna(v[i + 1]):
                    rows.append(_row(year, cat, code, name, v[i], v[i + 1], source))
    return rows


def _pdf_lines(path: Path) -> tuple[str, list[str]]:
    with pdfplumber.open(path) as pdf:
        pages = [p.extract_text() or "" for p in pdf.pages]
    header = "\n".join(pages[0].splitlines()[:8]) if pages else ""
    return header, [line.strip() for page in pages for line in page.splitlines()]


def parse_pdf_wide(year: int, path: Path, source: str) -> list[dict]:
    rows = []
    for line in _pdf_lines(path)[1]:
        m = WIDE_LINE.match(line)
        if not m:
            continue
        g = m.groups()
        code, name = g[0], g[1]
        for cat, i in (("total", 2), ("nao_optantes", 5), ("paa_negros", 8), ("paa_escola_publica", 11)):
            rows.append(_row(year, cat, code, name, g[i], g[i + 1], source))
    return rows


def category_from_label(label: str, file: str) -> str:
    if label.startswith("Total de Candidatos"):
        return "total"
    if "Somente Não Optantes" in label or "somente_nao_optantes" in file:
        return "nao_optantes"
    if label.startswith("Classificação Geral"):
        return "geral"
    code = re.search(r"cat_?(\d+)", file) or re.search(r"_(\d{1,3})\.pdf$", file)
    return f"paa_{code.group(1)}" if code else "paa_" + re.sub(r"\W+", "_", label.lower())[:40]


def parse_pdf_category(year: int, path: Path, label: str, source: str) -> list[dict]:
    header, lines = _pdf_lines(path)
    if UFSC not in header.upper().replace("\n", " ") or re.search(r"FRONTEIRA SUL|INSTITUTO FEDERAL", header.upper()):
        return []  # another institution of the unified vestibular
    category = category_from_label(label, path.name)
    # 2021 (pandemic, no exam): two parallel processes, by ENEM score or by previous vestibular scores
    modality = "vestibular"
    if "ENEM" in header:
        modality = "enem"
    elif "Vestibulares" in header and "Anteriores" in header:
        modality = "vestibulares_anteriores"
    rows = []
    for i, line in enumerate(lines):
        if m := NO_VACANCY_LINE.match(line):
            # "999 CURSO TREINAMENTO - CANDIDATO POR EXPERIÊNCIA - 1544 0 --": practice-only
            # candidates (treineiros), no vacancies. Kept with vagas = 0, excluded in staging.
            code, name, inscritos = m.groups()
            vagas = 0
        elif m := CATEGORY_LINE.match(line):
            code, name, vagas, inscritos, _ = m.groups()
        elif m := WRAPPED_LINE.match(line):
            # long course names are split around the numbers:
            # "ENGENHARIA DE CONTROLE E AUTOMAÇÃO - BEL - INT -" / "220 51 108 2.12 175" / "FLORIANÓPOLIS"
            code, vagas, inscritos, _ = m.groups()
            name = f"{lines[i - 1]} {lines[i + 1] if i + 1 < len(lines) else ''}"
        else:
            continue
        rows.append(_row(year, category, code, name, vagas, inscritos, source, modality))
    return rows


def main() -> None:
    manifest = list(csv.DictReader(open(MANIFEST, encoding="utf-8")))
    out = []
    for m in manifest:
        year, path = int(m["year"]), ROOT / m["file"]
        source = m["url"]
        if path.suffix.lower() in (".html", ".htm"):
            rows = parse_html(year, path, source)
        elif year in (2011, 2012):
            rows = parse_pdf_wide(year, path, source)
        else:
            rows = parse_pdf_category(year, path, m["label"], source)
        out.extend(rows)

    df = pd.DataFrame(out)
    # The same category can appear in two files of one year (e.g. a re-published PDF).
    dupes = df.duplicated(["year", "modality", "category", "course_code"], keep=False)
    if dupes.any():
        print("duplicated rows:\n", df[dupes].sort_values(["year", "category", "course_code"]).head(20))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False)
    print(df.groupby(["year", "modality"]).agg(rows=("course_code", "size"), categories=("category", "nunique")).to_string())


if __name__ == "__main__":
    main()
