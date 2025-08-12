PLANNER_SYSTEM = (
    "You are a senior data engineer. Output ONLY valid JSON per the schema. "
    "Plans must be minimal and succeed on first run. All code must be deterministic, offline, "
    "and use only Python standard library + pandas + numpy + matplotlib."
)

PLANNER_USER_TEMPLATE = """{questions_txt}

Attachments:
{attachments}

Tools available:
- http_fetch(url) -> text or bytes
- html_table_to_csv(html, css_selector?) -> csv path
- pdf_to_text(path) -> txt path
- pdf_tables_to_csv(path) -> list[csv paths]
- image_ocr_to_text(path) -> txt path
- csv_to_df(path) -> DataFrame (pandas)
- excel_to_df(path) -> DataFrame (pandas)
- json_load(path) -> JSON object
- sql_to_sqlite(sql_path?, sql_str?) -> sqlite db path
- python_exec(code, inputs:{name:path|json}) -> writes named outputs
- save_plot_png_b64(plt_figure, max_bytes=100000) -> data_uri
- compose_json_array(items) -> final JSON array

Return JSON object with keys: scrapes[], ingest[], python_jobs[], artefacts_contract{}
Rules:
- Prefer ≤2 scrapes unless strictly necessary.
- Python code MUST create every file declared in `writes`.
- Plots must be <100000 bytes when saved as PNG base64.
- No network calls inside Python code (scrapes only via tools).
- Use only pandas/numpy/matplotlib.
- Validate types exactly as per artefacts_contract.
"""

ANSWERER_SYSTEM = (
    "You answer questions strictly and concisely. Return a JSON array of answers in the order given. "
    "Use ONLY the provided artefacts. Do not re-calculate heavy steps; compose from artefacts."
)

ANSWERER_USER_TEMPLATE = """Questions (indices in original order): {indices}

Artefacts (JSON or scalars):
{artefacts_excerpt}

Return JSON array for these indices only, preserving the original order. Types must match expectations.
"""

# Optional few-shots (not injected by default to save tokens; you can add if needed)
PLANNER_FEWSHOTS = [
    {
      "questions": "Scrape the list of highest grossing films from Wikipedia...",
      "attachments": "(none)",
      "plan_json": {
        "scrapes": [
          {"id":"s1","tool":"http_fetch","args":{"url":"https://en.wikipedia.org/wiki/List_of_highest-grossing_films"},"writes":{"html":"films.html"}},
          {"id":"s2","tool":"html_table_to_csv","args":{"html":"$films.html","css_selector":"table.wikitable"},"writes":{"csv":"films.csv"}}
        ],
        "ingest": [],
        "python_jobs": [
          {"id":"p1","reads":{"films":"films.csv"},"writes":{"a1":"ans1.json","a2":"ans2.json","corr":"ans3.json","plot":"plot.datauri"},
           "code": "# LLM will fill valid pandas/numpy/matplotlib code that writes the specified outputs"}
        ],
        "artefacts_contract": {"a1":"json scalar/int","a2":"json scalar/string","corr":"json scalar/float","plot":"data_uri/png under 100000 bytes"}
      }
    }
]
