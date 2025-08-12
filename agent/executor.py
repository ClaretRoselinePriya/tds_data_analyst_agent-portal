from __future__ import annotations
import os, json, shutil
from typing import Dict, Any
from app.settings import settings
from agent.tools import (
    http_fetch, html_table_to_csv, pdf_to_text, pdf_tables_to_csv, image_ocr_to_text,
    csv_to_df, excel_to_df, json_load, sql_to_sqlite
)
from agent.sandbox import python_exec, python_exec_with_venv

def execute_plan(plan: Dict[str, Any], workdir: str, max_plot_bytes: int=100000) -> Dict[str, Any]:
    artefacts: Dict[str, Any] = {}
    derived_dir = os.path.join(workdir, "derived")
    os.makedirs(derived_dir, exist_ok=True)

    # 1) Scrapes
    for s in plan.get("scrapes", []):
        tool = s.get("tool")
        writes = s.get("writes", {})
        if tool == "http_fetch":
            url = s["args"]["url"]
            data = http_fetch(url, allowlist=settings.HTTP_ALLOWLIST)
            out_html = os.path.join(derived_dir, writes.get("html", "page.html"))
            with open(out_html, "wb") as f:
                f.write(data)
            artefacts[writes.get("html") or "html"] = out_html
        elif tool == "html_table_to_csv":
            html_spec = s["args"]["html"]
            if isinstance(html_spec, str) and html_spec.startswith("$"):
                src = artefacts[html_spec[1:]]
                html = open(src, "r", encoding="utf-8", errors="ignore").read()
            else:
                html = html_spec
            out_csv = os.path.join(derived_dir, writes.get("csv", "table.csv"))
            html_table_to_csv(html, s["args"].get("css_selector"), out_csv)
            artefacts[writes.get("csv") or "csv"] = out_csv
        else:
            raise RuntimeError(f"Unsupported scrape tool: {tool}")

    # 2) Ingest
    for a in plan.get("ingest", []):
        tool = a.get("tool")
        writes = a.get("writes", {})
        args = a.get("args", {})
        if tool == "pdf_to_text":
            p = args["path"].replace("$UPLOADS/", os.path.join(workdir, "uploads") + "/")
            out = pdf_to_text(p)
            artefacts[writes.get("text") or os.path.basename(out)] = out
        elif tool == "pdf_tables_to_csv":
            p = args["path"].replace("$UPLOADS/", os.path.join(workdir, "uploads") + "/")
            out_dir = os.path.join(derived_dir, "pdf_tables")
            paths = pdf_tables_to_csv(p, out_dir)
            artefacts[writes.get("csvs") or "csvs"] = paths
        elif tool == "image_ocr_to_text":
            p = args["path"].replace("$UPLOADS/", os.path.join(workdir, "uploads") + "/")
            out = image_ocr_to_text(p)
            artefacts[writes.get("text") or os.path.basename(out)] = out
        elif tool == "excel_to_df":
            p = args["path"].replace("$UPLOADS/", os.path.join(workdir, "uploads") + "/")
            df = excel_to_df(p)
            out = os.path.join(derived_dir, writes.get("df", os.path.basename(p) + ".csv"))
            df.to_csv(out, index=False)
            artefacts[writes.get("df") or os.path.basename(out)] = out
        elif tool == "csv_to_df":
            p = args["path"].replace("$UPLOADS/", os.path.join(workdir, "uploads") + "/")
            df = csv_to_df(p)
            out = os.path.join(derived_dir, writes.get("df", os.path.basename(p)))
            df.to_csv(out, index=False)
            artefacts[writes.get("df") or os.path.basename(out)] = out
        elif tool == "json_load":
            p = args["path"].replace("$UPLOADS/", os.path.join(workdir, "uploads") + "/")
            obj = json_load(p)
            out = os.path.join(derived_dir, writes.get("json", os.path.basename(p)))
            with open(out, "w", encoding="utf-8") as f: json.dump(obj, f)
            artefacts[writes.get("json") or os.path.basename(out)] = out
        elif tool == "sql_to_sqlite":
            sql_path = args.get("sql_path")
            sql_str = args.get("sql_str")
            if sql_path:
                sql_path = sql_path.replace("$UPLOADS/", os.path.join(workdir, "uploads") + "/")
            out_db = os.path.join(derived_dir, writes.get("db", "tmp.sqlite"))
            db = sql_to_sqlite(sql_path, sql_str, out_db)
            artefacts[writes.get("db") or "db"] = db
        else:
            raise RuntimeError(f"Unsupported ingest tool: {tool}")

    # 3) Python jobs
    for pj in plan.get("python_jobs", []):
        job_dir = os.path.join(derived_dir, pj.get("id", "job"))
        os.makedirs(job_dir, exist_ok=True)

        # Materialize inputs
        reads = pj.get("reads", {})
        for name, ref in reads.items():
            if isinstance(ref, str) and ref.startswith("$"):
                refkey = ref[1:]
                src = artefacts[refkey]
            else:
                src = ref
            alias = os.path.join(job_dir, f"{name}")
            if os.path.isdir(src):
                # Copy directory if needed
                if alias != src:
                    if os.path.exists(alias): shutil.rmtree(alias)
                    shutil.copytree(src, alias)
                artefacts[name] = alias
            else:
                with open(src, "rb") as fsrc, open(alias, "wb") as fdst:
                    fdst.write(fsrc.read())
                artefacts[name] = alias

        # Run code (optionally with venv)
        pkgs = pj.get("pkgs")
        if pkgs:
            rc, out, err = python_exec_with_venv(pj["code"], job_dir, pkgs=pkgs, timeout_sec=settings.TOOL_TIMEOUT)
        else:
            rc, out, err = python_exec(pj["code"], job_dir, timeout_sec=settings.TOOL_TIMEOUT)
        if rc != 0:
            raise RuntimeError(f"python_exec failed: {err[:800]}")

        # Collect writes
        for k, relpath in pj.get("writes", {}).items():
            path = os.path.join(job_dir, relpath)
            if not os.path.exists(path):
                raise RuntimeError(f"Expected output missing: {path}")
            if path.endswith(".datauri"):
                data = open(path, "r", encoding="utf-8").read()
                if len(data.encode("utf-8")) > max_plot_bytes:
                    raise RuntimeError("Plot exceeds size limit")
                artefacts[k] = data
            elif path.endswith(".json"):
                artefacts[k] = json.load(open(path, "r", encoding="utf-8"))
            else:
                artefacts[k] = path

    # 4) Validate artefacts against contract
    contract = plan.get('artefacts_contract', {})
    for name, expect in contract.items():
        if name not in artefacts:
            raise RuntimeError(f"Missing artefact: {name}")
        v = artefacts[name]
        if 'json scalar/int' in expect and not isinstance(v, int):
            raise RuntimeError(f"{name} not int")
        if 'json scalar/float' in expect and not isinstance(v, float):
            raise RuntimeError(f"{name} not float")
        if 'json scalar/string' in expect and not isinstance(v, str):
            raise RuntimeError(f"{name} not string")
        if 'data_uri' in expect and not (isinstance(v, str) and v.startswith('data:image/')):
            raise RuntimeError(f"{name} not data_uri")

    return artefacts
