import os
from typing import List, Dict, Any
from agent.llm import llm_json
from app.settings import settings
from agent.prompts import PLANNER_SYSTEM, PLANNER_USER_TEMPLATE

def plan_from_questions(questions_txt: str, upload_paths: List[str]) -> Dict[str, Any]:
    attachments = "\n".join(f"- {os.path.basename(p)}" for p in upload_paths)
    user = PLANNER_USER_TEMPLATE.format(questions_txt=questions_txt, attachments=attachments)
    plan = llm_json(PLANNER_SYSTEM, user, model=settings.MODEL_PLANNER)
    # Minimal validation & defaults
    for key in ("scrapes", "ingest", "python_jobs", "artefacts_contract"):
        if key not in plan:
            plan.setdefault(key, [] if key != "artefacts_contract" else {})
    return plan
