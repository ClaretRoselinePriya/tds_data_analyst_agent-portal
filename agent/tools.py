from __future__ import annotations
import os, re, json, requests
from typing import Dict, Any, List
import pandas as pd

# --- Simple question extractor ---
_QPAT = re.compile(r"^\s*(?:\d+[\).]|[-*])\s+(.*\S)", re.M)
def parse_questions(text: str) -> List[str]:
    qs = _QPAT.findall(text)
    if not qs:
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        return parts
    return qs

# --- HTTP fetch with allowlist ---
def _allowed(host: str, allowlist: tuple[str,...]) -> bool:
    if not allowlist:
        return True
    return any(host.endswith(a) or host == a for a in allowlist)

def http_fetch(url: str, allowlist: tuple[str,...]=()) -> bytes:
    import urllib.parse as up
    host = up.urlparse(url).hostname or ""
    if not _allowed(host, allowlist):
        raise RuntimeError(f"Host not allowed: {host}")
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.content

# --- HTML table to CSV ---
def html_table_to_csv(html: str, css_selector: str|None, out_csv_path: str) -> str:
    tables = pd.read_html(html)
    if not tables:
        raise RuntimeError("No tables found in HTML")
    tables[0].to_csv(out_csv_path, index=False)
    return out_csv_path

# --- PDF/Text/Image ingest ---
def pdf_to_text(path: str) -> str:
    import pdfplumber
    text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text() or "")
    out = path + ".txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(text))
    return out

def pdf_tables_to_csv(path: str, out_dir: str) -> List[str]:
    import pdfplumber
    os.makedirs(out_dir, exist_ok=True)
    csv_paths = []
    with pdfplumber.open(path) as pdf:
        for pi, page in enumerate(pdf.pages):
            tables = page.extract_tables() or []
            for ti, tbl in enumerate(tables):
                if not tbl or not tbl[0]:
                    continue
                import pandas as pd
                df = pd.DataFrame(tbl[1:], columns=tbl[0])
                out = os.path.join(out_dir, f"{os.path.basename(path)}.p{pi}.t{ti}.csv")
                df.to_csv(out, index=False)
                csv_paths.append(out)
    return csv_paths

def image_ocr_to_text(path: str) -> str:
    import pytesseract
    from PIL import Image
    img = Image.open(path)
    txt = pytesseract.image_to_string(img)
    out = path + ".txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write(txt)
    return out

# --- File loaders ---
def csv_to_df(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def excel_to_df(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

def json_load(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- SQL to SQLite ---
def sql_to_sqlite(sql_path: str|None, sql_str: str|None, out_db: str) -> str:
    import sqlite3
    conn = sqlite3.connect(out_db)
    cur = conn.cursor()
    try:
        if sql_path:
            sql = open(sql_path, "r", encoding="utf-8", errors="ignore").read()
            cur.executescript(sql)
        elif sql_str:
            cur.executescript(sql_str)
        conn.commit()
    finally:
        conn.close()
    return out_db

# --- DuckDB helper ---
import duckdb
def duckdb_query(sql: str, tables: dict[str, str], out_path: str) -> str:
    con = duckdb.connect()
    try:
        for name, path in tables.items():
            if path.lower().endswith('.parquet'):
                con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{path}')")
            else:
                con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_csv_auto('{path}')")
        df = con.execute(sql).df()
        df.to_csv(out_path, index=False)
        return out_path
    finally:
        con.close()
